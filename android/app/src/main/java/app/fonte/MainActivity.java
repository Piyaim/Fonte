// SPDX-License-Identifier: AGPL-3.0-or-later
package app.fonte;

import android.app.Activity;
import android.content.ActivityNotFoundException;
import android.content.ComponentName;
import android.content.Intent;
import android.content.pm.PackageManager;
import android.net.Uri;
import android.os.Build;
import android.os.Bundle;
import android.provider.Settings;
import android.view.ViewGroup;
import android.view.WindowManager;
import android.webkit.JavascriptInterface;
import android.webkit.ValueCallback;
import android.webkit.WebChromeClient;
import android.webkit.WebResourceRequest;
import android.webkit.WebResourceResponse;
import android.webkit.WebSettings;
import android.webkit.WebView;
import android.webkit.WebViewClient;
import android.widget.FrameLayout;
import android.widget.Toast;

import java.io.ByteArrayInputStream;
import java.io.IOException;
import java.io.InputStream;
import java.io.OutputStream;
import java.nio.charset.StandardCharsets;
import java.util.Collections;
import java.util.Locale;

/**
 * Fonte fonctionne seule sur le téléphone : l'appli web est embarquée dans l'APK (dossier assets) et
 * servie à une WebView par shouldInterceptRequest. Les données sont stockées par la page elle-même
 * (IndexedDB, voir server/static/local-backend.js). Aucune requête vers l'extérieur n'est autorisée.
 */
public class MainActivity extends Activity {

    private static final String HOST = "appassets.androidplatform.net";
    private static final String START_URL = "https://" + HOST + "/";
    private static final int REQ_FILE = 1;
    private static final int REQ_SAVE = 2;
    private static final int REQ_NOTIF = 3;

    private WebView web;
    private ValueCallback<Uri[]> fileCallback;
    private String pendingText;

    @Override
    protected void onCreate(Bundle savedInstanceState) {
        super.onCreate(savedInstanceState);
        web = new WebView(this);
        configureWebView();
        setContentView(web, new FrameLayout.LayoutParams(ViewGroup.LayoutParams.MATCH_PARENT, ViewGroup.LayoutParams.MATCH_PARENT));
        web.loadUrl(START_URL);
        migrateIcon();
    }

    /** 0.5.3 : l'ancienne entrée noir et blanc (.IconMono) est remplacée par .IconNoirBlanc, que le lanceur n'a jamais vue. */
    private void migrateIcon() {
        PackageManager pm = getPackageManager();
        try {
            ComponentName old = new ComponentName(getPackageName(), LEGACY_MONO);
            if (pm.getComponentEnabledSetting(old) != PackageManager.COMPONENT_ENABLED_STATE_ENABLED) return;
            // la nouvelle d'abord, pour qu'il y ait toujours une icône dans le lanceur
            pm.setComponentEnabledSetting(new ComponentName(getPackageName(), "app.fonte.IconNoirBlanc"), PackageManager.COMPONENT_ENABLED_STATE_ENABLED, PackageManager.DONT_KILL_APP);
            pm.setComponentEnabledSetting(old, PackageManager.COMPONENT_ENABLED_STATE_DISABLED, PackageManager.DONT_KILL_APP);
        } catch (RuntimeException ignored) {
            // système qui refuse : l'ancienne entrée reste, l'appli reste accessible
        }
    }

    private void configureWebView() {
        WebSettings st = web.getSettings();
        st.setJavaScriptEnabled(true);
        st.setDomStorageEnabled(true);
        st.setAllowFileAccess(false);
        st.setMediaPlaybackRequiresUserGesture(true);

        web.setWebViewClient(new WebViewClient() {
            @Override
            public WebResourceResponse shouldInterceptRequest(WebView view, WebResourceRequest request) {
                Uri u = request.getUrl();
                String scheme = u.getScheme();
                boolean network = "http".equalsIgnoreCase(scheme) || "https".equalsIgnoreCase(scheme);
                if (!network) return null;                       // blob:, data: ... gérés par la WebView
                if (!HOST.equalsIgnoreCase(u.getHost())) return answer(403, "Forbidden", "text/plain", new byte[0]);
                return asset(u.getPath());
            }

            @Override
            public boolean shouldOverrideUrlLoading(WebView view, WebResourceRequest request) {
                Uri u = request.getUrl();
                if (HOST.equalsIgnoreCase(u.getHost())) return false;
                try {
                    startActivity(new Intent(Intent.ACTION_VIEW, u));
                } catch (ActivityNotFoundException ignored) {
                    // aucune appli pour ce lien
                }
                return true;
            }
        });

        web.setWebChromeClient(new WebChromeClient() {
            @Override
            public boolean onShowFileChooser(WebView view, ValueCallback<Uri[]> callback, FileChooserParams params) {
                if (fileCallback != null) fileCallback.onReceiveValue(null);
                fileCallback = callback;
                try {
                    startActivityForResult(params.createIntent(), REQ_FILE);
                } catch (ActivityNotFoundException e) {
                    fileCallback = null;
                    return false;
                }
                return true;
            }
        });

        web.addJavascriptInterface(new Bridge(), "FonteApp");
        Notifs.channels(this);
    }

    private static WebResourceResponse answer(int code, String reason, String mime, byte[] data) {
        String enc = mime.startsWith("text/") || mime.endsWith("javascript") || mime.endsWith("json") ? "utf-8" : null;
        return new WebResourceResponse(mime, enc, code, reason, Collections.singletonMap("Cache-Control", "no-cache"), new ByteArrayInputStream(data));
    }

    private WebResourceResponse asset(String rawPath) {
        String path = rawPath == null || rawPath.equals("/") ? "/index.html" : rawPath;
        if (path.startsWith("/static/")) path = path.substring(7);
        path = path.substring(1);
        if (path.isEmpty() || path.contains("..")) return answer(404, "Not Found", "text/plain", new byte[0]);
        try {
            InputStream in = getAssets().open(path);
            String enc = null;
            String mime = mimeOf(path);
            if (mime.startsWith("text/") || mime.endsWith("javascript") || mime.endsWith("json")) enc = "utf-8";
            return new WebResourceResponse(mime, enc, 200, "OK", Collections.singletonMap("Cache-Control", "no-cache"), in);
        } catch (IOException e) {
            return answer(404, "Not Found", "text/plain", new byte[0]);
        }
    }

    private static String mimeOf(String path) {
        String p = path.toLowerCase(Locale.ROOT);
        if (p.endsWith(".html")) return "text/html";
        if (p.endsWith(".js")) return "text/javascript";
        if (p.endsWith(".json")) return "application/json";
        if (p.endsWith(".webmanifest")) return "application/manifest+json";
        if (p.endsWith(".png")) return "image/png";
        if (p.endsWith(".svg")) return "image/svg+xml";
        if (p.endsWith(".css")) return "text/css";
        return "application/octet-stream";
    }

    private static final String[] ICONS = {"orange", "blue", "green", "violet", "red", "mono"};
    private static final String LEGACY_MONO = "app.fonte.IconMono";   // entrée noir et blanc d'avant la 0.5.3

    /** Appelé par la page (local-backend.js) pour enregistrer une sauvegarde : le système demande où la ranger. */
    private class Bridge {
        @JavascriptInterface
        public void saveFile(final String name, final String mime, final String text) {
            runOnUiThread(new Runnable() {
                @Override
                public void run() {
                    pendingText = text;
                    Intent i = new Intent(Intent.ACTION_CREATE_DOCUMENT);
                    i.addCategory(Intent.CATEGORY_OPENABLE);
                    i.setType(mime);
                    i.putExtra(Intent.EXTRA_TITLE, name);
                    try {
                        startActivityForResult(i, REQ_SAVE);
                    } catch (ActivityNotFoundException e) {
                        pendingText = null;
                        Toast.makeText(MainActivity.this, R.string.save_failed, Toast.LENGTH_LONG).show();
                    }
                }
            });
        }

        /* ---------------------------------------------------------- notifications (voir Notifs et server/static/notif.js) */

        /** État pour la page : autorisation (granted, ask = Android peut encore afficher sa demande, settings = refus définitif),
         *  « Alarmes et rappels », canaux réglables (Android 8 et plus), événements déjà notifiés. */
        @JavascriptInterface
        public String notifStatus() {
            StringBuilder sent = new StringBuilder();
            for (String k : Notifs.sent(MainActivity.this)) sent.append(sent.length() == 0 ? "" : ",").append(org.json.JSONObject.quote(k));
            return "{\"sdk\":" + Build.VERSION.SDK_INT + ",\"perm\":\"" + permState() + "\",\"exact\":" + Notifs.exactAllowed(MainActivity.this)
                + ",\"exactNeeded\":" + Notifs.exactNeeded() + ",\"channels\":" + (Build.VERSION.SDK_INT >= 26) + ",\"sent\":[" + sent + "]}";
        }

        /** Demande système, une seule fois dans la vie de l'appli (Android 13 et plus) ; ensuite, seulement depuis la page Notifications. */
        @JavascriptInterface
        public void notifAskOnce() {
            runOnUiThread(() -> {
                if (Build.VERSION.SDK_INT < 33 || hasNotifPermission() || Notifs.prefs(MainActivity.this).getBoolean("asked", false)) return;
                askNotif();
            });
        }

        /** Bouton « Activer les notifications » : la demande système si Android peut encore l'afficher, sinon les réglages de l'appli. */
        @JavascriptInterface
        public void notifRequest() {
            runOnUiThread(() -> {
                if ("ask".equals(permState())) { askNotif(); return; }
                Intent i;
                if (Build.VERSION.SDK_INT >= 26) i = new Intent(Settings.ACTION_APP_NOTIFICATION_SETTINGS).putExtra(Settings.EXTRA_APP_PACKAGE, getPackageName());
                else i = new Intent(Settings.ACTION_APPLICATION_DETAILS_SETTINGS, Uri.fromParts("package", getPackageName(), null));
                open(i);
            });
        }

        @JavascriptInterface
        public void notifPlan(String plan) { Notifs.setPlan(MainActivity.this, plan); }

        @JavascriptInterface
        public void notifTest(String title, String text) { Notifs.test(MainActivity.this, title, text); }

        @JavascriptInterface
        public boolean restStart(int seconds, String title, String text) {
            return Notifs.restStart(MainActivity.this, System.currentTimeMillis() + seconds * 1000L, title, text);
        }

        @JavascriptInterface
        public void restCancel() { Notifs.restCancel(MainActivity.this); }

        /** Écran allumé pendant la séance (un exercice à la fois, ou repos en cours) ; la page l'enlève ensuite, et le réglage du menu peut le couper. */
        @JavascriptInterface
        public void keepScreenOn(final boolean on) {
            runOnUiThread(() -> {
                if (on) getWindow().addFlags(WindowManager.LayoutParams.FLAG_KEEP_SCREEN_ON);
                else getWindow().clearFlags(WindowManager.LayoutParams.FLAG_KEEP_SCREEN_ON);
            });
        }

        /** Bouton « Son et vibration » : le réglage Android du canal (Android 8 et plus). */
        @JavascriptInterface
        public void openChannel(final String id) {
            if (Build.VERSION.SDK_INT < 26) return;
            runOnUiThread(() -> {
                Notifs.channels(MainActivity.this);
                open(new Intent(Settings.ACTION_CHANNEL_NOTIFICATION_SETTINGS).putExtra(Settings.EXTRA_APP_PACKAGE, getPackageName()).putExtra(Settings.EXTRA_CHANNEL_ID, id));
            });
        }

        /** Écran « Alarmes et rappels » de l'appli (Android 12 et plus), demandé seulement quand on active la fin du repos. */
        @JavascriptInterface
        public void exactRequest() {
            if (!Notifs.exactNeeded()) return;
            runOnUiThread(() -> open(new Intent(Settings.ACTION_REQUEST_SCHEDULE_EXACT_ALARM, Uri.fromParts("package", getPackageName(), null))));
        }

        /** Change l'icône de l'écran d'accueil : active l'entrée de lanceur de la couleur choisie, désactive les autres. */
        @JavascriptInterface
        public void setIcon(final String key) {
            runOnUiThread(new Runnable() {
                @Override
                public void run() {
                    boolean known = false;
                    for (String k : ICONS) if (k.equals(key)) known = true;
                    if (!known) return;
                    PackageManager pm = getPackageManager();
                    try {
                        // la nouvelle d'abord, pour qu'il y ait toujours une icône dans le lanceur
                        pm.setComponentEnabledSetting(alias(key), PackageManager.COMPONENT_ENABLED_STATE_ENABLED, PackageManager.DONT_KILL_APP);
                        for (String k : ICONS) {
                            if (!k.equals(key)) pm.setComponentEnabledSetting(alias(k), PackageManager.COMPONENT_ENABLED_STATE_DISABLED, PackageManager.DONT_KILL_APP);
                        }
                        pm.setComponentEnabledSetting(new ComponentName(getPackageName(), LEGACY_MONO), PackageManager.COMPONENT_ENABLED_STATE_DISABLED, PackageManager.DONT_KILL_APP);
                    } catch (RuntimeException ignored) {
                        // lanceur ou système qui refuse : l'icône reste celle d'avant
                    }
                }
            });
        }

        private ComponentName alias(String key) {
            String nom = key.equals("mono") ? "NoirBlanc" : Character.toUpperCase(key.charAt(0)) + key.substring(1);
            return new ComponentName(MainActivity.this.getPackageName(), "app.fonte.Icon" + nom);
        }
    }

    private boolean hasNotifPermission() {
        if (Build.VERSION.SDK_INT >= 33 && checkSelfPermission("android.permission.POST_NOTIFICATIONS") != PackageManager.PERMISSION_GRANTED) return false;
        return Notifs.enabled(this);
    }

    /** granted ; ask : Android peut afficher sa demande ; settings : refusée deux fois (Android ne l'affiche plus) ou coupée dans les réglages. */
    private String permState() {
        if (hasNotifPermission()) return "granted";
        if (Build.VERSION.SDK_INT >= 33 && checkSelfPermission("android.permission.POST_NOTIFICATIONS") != PackageManager.PERMISSION_GRANTED
            && (!Notifs.prefs(this).getBoolean("asked", false) || shouldShowRequestPermissionRationale("android.permission.POST_NOTIFICATIONS"))) return "ask";
        return "settings";
    }

    private void askNotif() {
        Notifs.prefs(this).edit().putBoolean("asked", true).apply();
        requestPermissions(new String[]{"android.permission.POST_NOTIFICATIONS"}, REQ_NOTIF);
    }

    private void open(Intent i) {
        try {
            startActivity(i);
        } catch (ActivityNotFoundException e) {
            try {
                startActivity(new Intent(Settings.ACTION_APPLICATION_DETAILS_SETTINGS, Uri.fromParts("package", getPackageName(), null)));
            } catch (ActivityNotFoundException ignored) {
                // réglages introuvables sur ce téléphone
            }
        }
    }

    /** Prévient la page qu'une autorisation a pu changer (retour des réglages Android, réponse à la demande). */
    private void notifChanged() {
        if (web != null) web.evaluateJavascript("window.NOTIF && NOTIF.onStatus()", null);
    }

    @Override
    public void onRequestPermissionsResult(int requestCode, String[] permissions, int[] grantResults) {
        if (requestCode == REQ_NOTIF) notifChanged();
    }

    @Override
    protected void onActivityResult(int requestCode, int resultCode, Intent data) {
        if (requestCode == REQ_FILE) {
            if (fileCallback != null) {
                fileCallback.onReceiveValue(WebChromeClient.FileChooserParams.parseResult(resultCode, data));
                fileCallback = null;
            }
            return;
        }
        if (requestCode == REQ_SAVE) {
            String text = pendingText;
            pendingText = null;
            if (resultCode == RESULT_OK && data != null && data.getData() != null && text != null) {
                try (OutputStream out = getContentResolver().openOutputStream(data.getData())) {
                    if (out == null) throw new IOException("flux indisponible");
                    out.write(text.getBytes(StandardCharsets.UTF_8));
                    Toast.makeText(this, R.string.saved, Toast.LENGTH_SHORT).show();
                } catch (IOException | RuntimeException e) {
                    Toast.makeText(this, R.string.save_failed, Toast.LENGTH_LONG).show();
                }
            }
            return;
        }
        super.onActivityResult(requestCode, resultCode, data);
    }

    @Override
    protected void onResume() {
        super.onResume();
        Notifs.visible = true;
        Notifs.cancelRestNotification(this);
        web.onResume();
        notifChanged();
    }

    @Override
    protected void onPause() {
        Notifs.visible = false;
        web.onPause();
        super.onPause();
    }

    @Override
    protected void onDestroy() {
        web.destroy();
        super.onDestroy();
    }
}
