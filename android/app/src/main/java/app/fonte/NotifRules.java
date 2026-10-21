// SPDX-License-Identifier: AGPL-3.0-or-later
package app.fonte;

import java.util.ArrayList;
import java.util.Collections;
import java.util.List;
import java.util.Set;

/**
 * Règles des notifications programmées, sans rien d'Android (testées sur le PC par tests/notif_java).
 * La page (notif.js) calcule le plan ; ces règles le vérifient à nouveau au moment d'envoyer : rien pendant les heures calmes,
 * une notification par jour au plus, une seule fois par événement, rien de périmé (téléphone éteint, alarme très en retard).
 */
final class NotifRules {
    /** Au-delà, une notification arrivée en retard n'est plus envoyée. */
    static final long LATE_MAX = 2 * 3600_000L;

    static final class Item {
        final long at;
        final String key, channel, title, text;

        Item(long at, String key, String channel, String title, String text) {
            this.at = at; this.key = key; this.channel = channel; this.title = title; this.text = text;
        }
    }

    static final class Plan {
        int quietFrom = -1, quietTo = -1;   // minutes depuis minuit ; -1 = pas d'heures calmes
        final List<Item> items = new ArrayList<>();
    }

    private NotifRules() {}

    /** « 21:00 » → 1260 ; -1 si illisible. */
    static int minutes(String hm) {
        if (hm == null || !hm.matches("\\d\\d:\\d\\d")) return -1;
        int h = Integer.parseInt(hm.substring(0, 2)), m = Integer.parseInt(hm.substring(3));
        return h < 24 && m < 60 ? h * 60 + m : -1;
    }

    /** Format de notif.js : « calme␉21:00␉08:00 », puis une ligne par notification « heure␉clé␉canal␉titre␉texte ». */
    static Plan parse(String s) {
        Plan p = new Plan();
        if (s == null) return p;
        for (String line : s.split("\n")) {
            String[] f = line.split("\t", -1);
            if (f.length == 3 && f[0].equals("calme")) { p.quietFrom = minutes(f[1]); p.quietTo = minutes(f[2]); continue; }
            if (f.length != 5) continue;
            try {
                p.items.add(new Item(Long.parseLong(f[0]), f[1], f[2], f[3], f[4]));
            } catch (NumberFormatException ignored) {
                // ligne abîmée : ignorée
            }
        }
        Collections.sort(p.items, (a, b) -> Long.compare(a.at, b.at));
        return p;
    }

    static boolean quiet(int minute, int from, int to) {
        if (from < 0 || to < 0 || from == to) return false;
        return from < to ? minute >= from && minute < to : minute >= from || minute < to;
    }

    /**
     * Raison pour laquelle la notification ne part pas, ou null si elle part.
     * minuteNow et dayNow (« 2026-10-21 ») sont l'heure et le jour du téléphone ; lastDay, le jour de la dernière notification envoyée.
     */
    static String refuse(Item it, Plan p, long now, int minuteNow, String dayNow, String lastDay, Set<String> sent) {
        if (sent.contains(it.key)) return "déjà envoyée";
        if (now - it.at > LATE_MAX) return "trop en retard";
        if (quiet(minuteNow, p.quietFrom, p.quietTo)) return "heures calmes";
        if (dayNow.equals(lastDay)) return "déjà une notification aujourd'hui";
        return null;
    }

    /** Notifications à traiter maintenant : celles dont l'heure est passée et qui n'ont pas encore été traitées. */
    static List<Item> due(Plan p, long now, long handledUntil) {
        List<Item> out = new ArrayList<>();
        for (Item it : p.items) if (it.at > handledUntil && it.at <= now + 60_000L) out.add(it);
        return out;
    }

    /** Prochaine heure à programmer, ou -1 s'il n'y a plus rien. */
    static long next(Plan p, long handledUntil) {
        for (Item it : p.items) if (it.at > handledUntil) return it.at;
        return -1;
    }
}
