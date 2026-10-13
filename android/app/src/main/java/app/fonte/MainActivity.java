// SPDX-License-Identifier: AGPL-3.0-or-later
package app.fonte;

import android.app.Activity;
import android.content.ActivityNotFoundException;
import android.content.Intent;
import android.content.SharedPreferences;
import android.net.Uri;
import android.net.http.SslError;
import android.os.Bundle;
import android.text.InputType;
import android.view.View;
import android.view.ViewGroup;
import android.webkit.JavascriptInterface;
import android.webkit.SslErrorHandler;
import android.webkit.ValueCallback;
import android.webkit.WebChromeClient;
import android.webkit.WebResourceError;
import android.webkit.WebResourceRequest;
import android.webkit.WebSettings;
import android.webkit.WebView;
import android.webkit.WebViewClient;
import android.widget.Button;
import android.widget.EditText;
import android.widget.FrameLayout;
import android.widget.LinearLayout;
import android.widget.TextView;

/**
 * Coque minimale : affiche dans une WebView l'appli web Fonte hébergée sur le serveur de l'utilisateur.
 * L'adresse du serveur est saisie au premier lancement puis modifiable ("Changer le serveur").
 * Aucune bibliothèque tierce, aucun traceur, une seule permission (INTERNET).
 */
public class MainActivity extends Activity {

    private static final String PREFS = "fonte";
    private static final String KEY_URL = "server_url";
    private static final int REQ_FILE = 1;

    private SharedPreferences prefs;
    private WebView web;
    private View setup;
    private EditText input;
    private String base;
    private ValueCallback<Uri[]> fileCallback;

    @Override
    protected void onCreate(Bundle savedInstanceState) {
        super.onCreate(savedInstanceState);
        prefs = getSharedPreferences(PREFS, MODE_PRIVATE);
        base = prefs.getString(KEY_URL, null);

        FrameLayout root = new FrameLayout(this);
        web = new WebView(this);
        configureWebView();
        root.addView(web, new FrameLayout.LayoutParams(ViewGroup.LayoutParams.MATCH_PARENT, ViewGroup.LayoutParams.MATCH_PARENT));
        setup = buildSetup();
        root.addView(setup, new FrameLayout.LayoutParams(ViewGroup.LayoutParams.MATCH_PARENT, ViewGroup.LayoutParams.MATCH_PARENT));
        setContentView(root);

        if (base == null) {
            showSetup();
        } else {
            setup.setVisibility(View.GONE);
            web.loadUrl(base);
        }
    }

    private int dp(int v) {
        return Math.round(v * getResources().getDisplayMetrics().density);
    }

    private View buildSetup() {
        LinearLayout box = new LinearLayout(this);
        box.setOrientation(LinearLayout.VERTICAL);
        box.setPadding(dp(24), dp(48), dp(24), dp(24));
        box.setBackgroundColor(getResources().getColor(R.color.window_bg));

        TextView title = new TextView(this);
        title.setText(R.string.setup_title);
        title.setTextSize(24);
        box.addView(title);

        TextView help = new TextView(this);
        help.setText(R.string.setup_help);
        help.setPadding(0, dp(12), 0, dp(12));
        box.addView(help);

        input = new EditText(this);
        input.setHint(R.string.setup_hint);
        input.setSingleLine(true);
        input.setInputType(InputType.TYPE_CLASS_TEXT | InputType.TYPE_TEXT_VARIATION_URI);
        box.addView(input);

        Button save = new Button(this);
        save.setText(R.string.setup_save);
        save.setOnClickListener(new View.OnClickListener() {
            @Override
            public void onClick(View v) {
                saveAddress();
            }
        });
        box.addView(save);
        return box;
    }

    private void showSetup() {
        input.setText(base == null ? "" : base);
        input.setError(null);
        setup.setVisibility(View.VISIBLE);
        web.setVisibility(View.GONE);
    }

    private void saveAddress() {
        String v = normalize(input.getText().toString());
        if (v == null) {
            input.setError(getString(R.string.setup_invalid));
            return;
        }
        base = v;
        prefs.edit().putString(KEY_URL, v).apply();
        setup.setVisibility(View.GONE);
        web.setVisibility(View.VISIBLE);
        web.loadUrl(base);
    }

    /** Renvoie l'adresse nettoyée, ou null si elle n'est pas utilisable. */
    static String normalize(String raw) {
        String s = raw == null ? "" : raw.trim();
        if (s.isEmpty()) return null;
        if (!s.contains("://")) s = "https://" + s;
        Uri u = Uri.parse(s);
        String scheme = u.getScheme();
        String host = u.getHost();
        if (scheme == null || host == null || host.isEmpty()) return null;
        if (!scheme.equalsIgnoreCase("http") && !scheme.equalsIgnoreCase("https")) return null;
        while (s.endsWith("/")) s = s.substring(0, s.length() - 1);
        return s;
    }

    private void configureWebView() {
        WebSettings st = web.getSettings();
        st.setJavaScriptEnabled(true);
        st.setDomStorageEnabled(true);
        st.setAllowFileAccess(false);
        st.setMediaPlaybackRequiresUserGesture(true);

        web.setWebViewClient(new WebViewClient() {
            @Override
            public boolean shouldOverrideUrlLoading(WebView view, WebResourceRequest request) {
                Uri u = request.getUrl();
                String s = u.toString();
                if (s.equals("fonte:retry")) {
                    if (base != null) web.loadUrl(base);
                    return true;
                }
                if (s.equals("fonte:change")) {
                    showSetup();
                    return true;
                }
                if (isSameServer(u)) return false;
                openExternal(u);
                return true;
            }

            @Override
            public void onReceivedError(WebView view, WebResourceRequest request, WebResourceError error) {
                if (request.isForMainFrame()) showError(String.valueOf(error.getDescription()));
            }

            @Override
            public void onReceivedSslError(WebView view, SslErrorHandler handler, SslError error) {
                handler.cancel();
                showError(getString(R.string.err_ssl));
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

        // L'export JSON est un téléchargement : on le confie au navigateur du téléphone.
        web.setDownloadListener((url, userAgent, contentDisposition, mimeType, contentLength) -> openExternal(Uri.parse(url)));
        web.addJavascriptInterface(new Bridge(), "FonteApp");
    }

    private boolean isSameServer(Uri u) {
        if (base == null) return false;
        Uri b = Uri.parse(base);
        return b.getScheme() != null && b.getScheme().equalsIgnoreCase(u.getScheme())
                && b.getHost() != null && b.getHost().equalsIgnoreCase(u.getHost())
                && b.getPort() == u.getPort();
    }

    private void openExternal(Uri u) {
        try {
            startActivity(new Intent(Intent.ACTION_VIEW, u));
        } catch (ActivityNotFoundException ignored) {
            // aucune appli pour ouvrir ce lien : on ne fait rien
        }
    }

    private static String esc(String s) {
        return s.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;").replace("\"", "&quot;");
    }

    private void showError(String detail) {
        String html = "<!doctype html><meta name='viewport' content='width=device-width,initial-scale=1'>"
                + "<body style='font-family:sans-serif;padding:24px;background:#0e161c;color:#e8eef2'>"
                + "<h2>" + esc(getString(R.string.err_title)) + "</h2>"
                + "<p>" + esc(base == null ? "" : base) + "</p>"
                + "<p style='color:#8fa0ac'>" + esc(detail) + "</p>"
                + "<p><a style='color:#ff7a1a;font-size:18px' href='fonte:retry'>" + esc(getString(R.string.err_retry)) + "</a></p>"
                + "<p><a style='color:#ff7a1a;font-size:18px' href='fonte:change'>" + esc(getString(R.string.err_change)) + "</a></p>"
                + "</body>";
        web.loadDataWithBaseURL(null, html, "text/html", "UTF-8", null);
    }

    /** Appelé par la page web (bouton « Changer le serveur » du menu). */
    private class Bridge {
        @JavascriptInterface
        public void changeServer() {
            runOnUiThread(new Runnable() {
                @Override
                public void run() {
                    showSetup();
                }
            });
        }
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
        super.onActivityResult(requestCode, resultCode, data);
    }

    @Override
    public void onBackPressed() {
        if (setup.getVisibility() == View.VISIBLE) {
            if (base != null) {
                setup.setVisibility(View.GONE);
                web.setVisibility(View.VISIBLE);
            } else {
                finish();
            }
        } else if (web.canGoBack()) {
            web.goBack();
        } else {
            super.onBackPressed();
        }
    }

    @Override
    protected void onResume() {
        super.onResume();
        web.onResume();
    }

    @Override
    protected void onPause() {
        web.onPause();
        super.onPause();
    }

    @Override
    protected void onDestroy() {
        web.destroy();
        super.onDestroy();
    }
}
