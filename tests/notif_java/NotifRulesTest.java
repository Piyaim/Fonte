// SPDX-License-Identifier: AGPL-3.0-or-later
package app.fonte;

import java.util.HashSet;
import java.util.List;
import java.util.Set;

/** Règles de la coque (NotifRules), sans Android. Lancé par tests/notif_java.py. Chaque contrôle affiche OK ou ÉCHEC. */
public class NotifRulesTest {
    static int fails;

    static void ok(boolean c, String m) {
        System.out.println((c ? "OK     " : "ÉCHEC  ") + m);
        if (!c) fails++;
    }

    public static void main(String[] a) {
        long H = 3600_000L, T = 1_800_000_000_000L;   // une heure ; un instant quelconque
        String plan = "calme\t21:00\t08:00\n"
            + (T + 2 * H) + "\trappel:2027-01-15\trappels\tSéance B prête : 6 exercices\tTouche pour commencer.\n"
            + T + "\tretour:2027-01-08\tprogramme\tBon retour quand tu veux\tTa séance B est prête, à ton rythme.\n"
            + "ligne abîmée\n"
            + "abc\tx\ty\tz\tw\n";
        NotifRules.Plan p = NotifRules.parse(plan);
        ok(p.quietFrom == 21 * 60 && p.quietTo == 8 * 60, "heures calmes lues : 21:00 à 08:00");
        ok(p.items.size() == 2, "2 notifications lues, les lignes abîmées ignorées (" + p.items.size() + ")");
        ok(p.items.get(0).key.startsWith("retour:"), "notifications triées par heure");
        ok(p.items.get(1).title.equals("Séance B prête : 6 exercices"), "accents et deux-points conservés");

        // heures calmes, à cheval sur minuit et dans la journée
        ok(NotifRules.quiet(22 * 60, 21 * 60, 8 * 60), "22:00 est dans 21:00-08:00");
        ok(NotifRules.quiet(7 * 60 + 59, 21 * 60, 8 * 60), "07:59 est dans 21:00-08:00");
        ok(!NotifRules.quiet(8 * 60, 21 * 60, 8 * 60), "08:00 n'est plus dans 21:00-08:00");
        ok(!NotifRules.quiet(18 * 60, 21 * 60, 8 * 60), "18:00 n'est pas dans 21:00-08:00");
        ok(NotifRules.quiet(13 * 60, 12 * 60, 14 * 60) && !NotifRules.quiet(11 * 60, 12 * 60, 14 * 60), "heures calmes dans la journée (12:00-14:00)");
        ok(!NotifRules.quiet(3 * 60, -1, -1), "sans heures calmes, rien n'est bloqué");

        NotifRules.Item r = p.items.get(1);
        Set<String> none = new HashSet<>();
        ok(NotifRules.refuse(r, p, r.at, 18 * 60, "2027-01-15", "2027-01-14", none) == null, "rappel à 18:00 : envoyé");
        ok("heures calmes".equals(NotifRules.refuse(r, p, r.at, 21 * 60 + 5, "2027-01-15", "", none)), "rappel arrivé à 21:05 (alarme en retard) : bloqué par les heures calmes");
        ok("déjà une notification aujourd'hui".equals(NotifRules.refuse(r, p, r.at, 18 * 60, "2027-01-15", "2027-01-15", none)), "plafond : une seule notification par jour");
        ok("trop en retard".equals(NotifRules.refuse(r, p, r.at + 3 * H, 18 * 60, "2027-01-15", "", none)), "téléphone rallumé 3 h après : rien de périmé n'est envoyé");
        Set<String> sent = new HashSet<>();
        sent.add("retour:2027-01-08");
        NotifRules.Item b = p.items.get(0);
        ok("déjà envoyée".equals(NotifRules.refuse(b, p, b.at, 18 * 60, "2027-01-15", "", sent)), "« Bon retour » : une seule fois par pause");
        ok(NotifRules.refuse(b, p, b.at, 18 * 60, "2027-01-15", "", none) == null, "(témoin : le même « Bon retour » part s'il n'a jamais été envoyé)");

        // ce qui est dû, et l'alarme suivante
        List<NotifRules.Item> d = NotifRules.due(p, T + 1000, 0);
        ok(d.size() == 1 && d.get(0) == b, "à l'heure du premier : seul le premier est dû");
        ok(NotifRules.next(p, T) == T + 2 * H, "l'alarme suivante vise le rappel");
        ok(NotifRules.next(p, T + 2 * H) == -1, "plus rien après le dernier : alarme annulée");
        ok(NotifRules.due(p, T + 2 * H, T + 2 * H).isEmpty(), "une notification traitée n'est pas traitée deux fois");
        ok(NotifRules.minutes("24:00") == -1 && NotifRules.minutes("8:00") == -1 && NotifRules.minutes("08:30") == 510, "heures illisibles refusées");

        System.out.println(fails == 0 ? "Tout est bon." : fails + " ÉCHEC(S)");
        System.exit(fails == 0 ? 0 : 1);
    }
}
