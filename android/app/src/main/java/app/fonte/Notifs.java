// SPDX-License-Identifier: AGPL-3.0-or-later
package app.fonte;

import android.app.AlarmManager;
import android.app.Notification;
import android.app.NotificationChannel;
import android.app.NotificationManager;
import android.app.PendingIntent;
import android.content.Context;
import android.content.Intent;
import android.content.SharedPreferences;
import android.os.Build;

import java.util.Calendar;
import java.util.HashSet;
import java.util.List;
import java.util.Locale;
import java.util.Set;

/**
 * Notifications programmées par la page (voir server/static/notif.js), envoyées même appli fermée. Tout est local :
 * AlarmManager réveille AlarmReceiver, qui envoie la notification et programme la suivante ; BootReceiver reprogramme
 * après un redémarrage (Android efface alors les alarmes).
 * - Rappels, étapes, bon retour, bilan : alarme approximative (setWindow, fenêtre de 10 minutes), aucune autorisation spéciale.
 * - Fin du repos : alarme à la seconde près, seulement avec l'autorisation « Alarmes et rappels » (vérifiée avant chaque appel :
 *   sans elle, setExact lève une SecurityException).
 * Trois canaux (Android 8 et plus), que l'utilisateur règle dans Android : rappels, fin du repos (importance haute), programme
 * et bilan. Avant Android 8, il n'y a pas de canaux : son et vibration par défaut du téléphone, réglés sur chaque notification.
 */
final class Notifs {
    static final String CH_RAPPELS = "rappels", CH_REPOS = "repos", CH_PROGRAMME = "programme";
    static final String ACTION_PLAN = "app.fonte.NOTIF_PLAN", ACTION_REPOS = "app.fonte.NOTIF_REPOS";
    private static final String PREFS = "notif";
    private static final int ID_PLAN = 1, ID_TEST = 2, ID_REPOS = 3;
    private static final long WINDOW = 10 * 60_000L;

    /** Vrai quand l'appli est à l'écran : la fin du repos sonne alors dans la page, pas en notification. */
    static volatile boolean visible;

    private Notifs() {}

    static SharedPreferences prefs(Context c) { return c.getSharedPreferences(PREFS, Context.MODE_PRIVATE); }

    static void channels(Context c) {
        if (Build.VERSION.SDK_INT < 26) return;
        NotificationManager nm = c.getSystemService(NotificationManager.class);
        NotificationChannel r = new NotificationChannel(CH_RAPPELS, c.getString(R.string.ch_rappels), NotificationManager.IMPORTANCE_DEFAULT);
        NotificationChannel p = new NotificationChannel(CH_PROGRAMME, c.getString(R.string.ch_programme), NotificationManager.IMPORTANCE_DEFAULT);
        NotificationChannel f = new NotificationChannel(CH_REPOS, c.getString(R.string.ch_repos), NotificationManager.IMPORTANCE_HIGH);
        f.enableVibration(true);
        f.setVibrationPattern(new long[]{0, 300, 100, 300});
        nm.createNotificationChannel(r);
        nm.createNotificationChannel(p);
        nm.createNotificationChannel(f);
    }

    static boolean enabled(Context c) {
        NotificationManager nm = (NotificationManager) c.getSystemService(Context.NOTIFICATION_SERVICE);
        return nm != null && nm.areNotificationsEnabled();
    }

    static boolean exactNeeded() { return Build.VERSION.SDK_INT >= 31; }

    static boolean exactAllowed(Context c) {
        if (!exactNeeded()) return true;
        AlarmManager am = (AlarmManager) c.getSystemService(Context.ALARM_SERVICE);
        return am != null && am.canScheduleExactAlarms();
    }

    private static PendingIntent openApp(Context c) {
        Intent i = new Intent(Intent.ACTION_MAIN).addCategory(Intent.CATEGORY_LAUNCHER).setClass(c, MainActivity.class)
            .addFlags(Intent.FLAG_ACTIVITY_NEW_TASK | Intent.FLAG_ACTIVITY_RESET_TASK_IF_NEEDED);
        return PendingIntent.getActivity(c, 0, i, PendingIntent.FLAG_IMMUTABLE | PendingIntent.FLAG_UPDATE_CURRENT);
    }

    @SuppressWarnings("deprecation")
    static void post(Context c, int id, String channel, String title, String text) {
        if (!enabled(c)) return;
        channels(c);
        Notification.Builder b = Build.VERSION.SDK_INT >= 26 ? new Notification.Builder(c, channel) : new Notification.Builder(c);
        b.setSmallIcon(R.drawable.ic_notif).setContentTitle(title).setContentText(text).setAutoCancel(true)
            .setContentIntent(openApp(c)).setStyle(new Notification.BigTextStyle().bigText(text));
        if (Build.VERSION.SDK_INT < 26) {   // pas de canaux : son et vibration par défaut, la fin du repos s'affiche en haut de l'écran
            b.setDefaults(Notification.DEFAULT_SOUND | Notification.DEFAULT_VIBRATE)
                .setPriority(CH_REPOS.equals(channel) ? Notification.PRIORITY_HIGH : Notification.PRIORITY_DEFAULT);
        }
        if (CH_REPOS.equals(channel)) b.setCategory(Notification.CATEGORY_ALARM);
        try {
            ((NotificationManager) c.getSystemService(Context.NOTIFICATION_SERVICE)).notify(id, b.build());
        } catch (RuntimeException ignored) {
            // autorisation retirée entre-temps : rien n'est envoyé
        }
    }

    static void test(Context c, String title, String text) { post(c, ID_TEST, CH_RAPPELS, title, text); }

    /* ------------------------------------------------------------ plan (rappels, étapes, bon retour, bilan) */

    static void setPlan(Context c, String plan) {
        prefs(c).edit().putString("plan", plan == null ? "" : plan).apply();
        schedule(c);
    }

    private static PendingIntent planIntent(Context c) {
        Intent i = new Intent(c, AlarmReceiver.class).setAction(ACTION_PLAN);
        return PendingIntent.getBroadcast(c, ID_PLAN, i, PendingIntent.FLAG_IMMUTABLE | PendingIntent.FLAG_UPDATE_CURRENT);
    }

    /** Programme l'alarme de la prochaine notification du plan (ou l'annule s'il n'y a plus rien). */
    static void schedule(Context c) {
        AlarmManager am = (AlarmManager) c.getSystemService(Context.ALARM_SERVICE);
        if (am == null) return;
        SharedPreferences sp = prefs(c);
        NotifRules.Plan p = NotifRules.parse(sp.getString("plan", ""));
        long handled = sp.getLong("handled", 0), now = System.currentTimeMillis();
        if (handled > now) handled = now;   // horloge reculée
        long at = NotifRules.next(p, handled);
        PendingIntent pi = planIntent(c);
        if (at < 0) { am.cancel(pi); return; }
        am.setWindow(AlarmManager.RTC_WAKEUP, Math.max(at, now + 1000), WINDOW, pi);
    }

    static String day(Calendar k) {
        return String.format(Locale.ROOT, "%04d-%02d-%02d", k.get(Calendar.YEAR), k.get(Calendar.MONTH) + 1, k.get(Calendar.DAY_OF_MONTH));
    }

    /** Alarme du plan : envoie ce qui est dû (une seule notification au plus), puis programme la suivante. */
    static void fire(Context c) {
        SharedPreferences sp = prefs(c);
        NotifRules.Plan p = NotifRules.parse(sp.getString("plan", ""));
        long now = System.currentTimeMillis(), handled = sp.getLong("handled", 0);
        Calendar k = Calendar.getInstance();
        int minute = k.get(Calendar.HOUR_OF_DAY) * 60 + k.get(Calendar.MINUTE);
        String today = day(k), last = sp.getString("last_day", "");
        Set<String> sent = new HashSet<>(sp.getStringSet("sent", new HashSet<>()));
        List<NotifRules.Item> due = NotifRules.due(p, now, handled);
        SharedPreferences.Editor ed = sp.edit();
        for (NotifRules.Item it : due) {
            handled = Math.max(handled, it.at);
            if (NotifRules.refuse(it, p, now, minute, today, last, sent) != null) continue;
            post(c, ID_PLAN, it.channel, it.title, it.text);
            // seuls les événements (phase, semaine légère, bon retour) sont gardés : rappels et bilans sont datés, le plafond du jour suffit
            if (!it.key.startsWith("rappel:") && !it.key.startsWith("bilan:")) sent.add(it.key);
            last = today;
        }
        ed.putLong("handled", handled).putString("last_day", last).putStringSet("sent", sent).apply();
        schedule(c);
    }

    static Set<String> sent(Context c) { return prefs(c).getStringSet("sent", new HashSet<>()); }

    /* ------------------------------------------------------------ fin du repos */

    private static PendingIntent restIntent(Context c, String title, String text) {
        Intent i = new Intent(c, AlarmReceiver.class).setAction(ACTION_REPOS).putExtra("title", title).putExtra("text", text);
        return PendingIntent.getBroadcast(c, ID_REPOS, i, PendingIntent.FLAG_IMMUTABLE | PendingIntent.FLAG_UPDATE_CURRENT);
    }

    /** Vrai si l'alarme est programmée ; faux sans l'autorisation « Alarmes et rappels » (la fin du repos reste alors dans l'appli). */
    static boolean restStart(Context c, long at, String title, String text) {
        AlarmManager am = (AlarmManager) c.getSystemService(Context.ALARM_SERVICE);
        cancelRestNotification(c);
        if (am == null || !enabled(c) || !exactAllowed(c)) return false;
        try {
            am.setExactAndAllowWhileIdle(AlarmManager.RTC_WAKEUP, at, restIntent(c, title, text));
            return true;
        } catch (SecurityException e) {
            return false;
        }
    }

    static void restCancel(Context c) {
        AlarmManager am = (AlarmManager) c.getSystemService(Context.ALARM_SERVICE);
        if (am != null) am.cancel(restIntent(c, "", ""));
        cancelRestNotification(c);
    }

    static void cancelRestNotification(Context c) {
        NotificationManager nm = (NotificationManager) c.getSystemService(Context.NOTIFICATION_SERVICE);
        if (nm != null) nm.cancel(ID_REPOS);
    }

    static void restFire(Context c, String title, String text) {
        if (!visible) post(c, ID_REPOS, CH_REPOS, title, text);
    }
}
