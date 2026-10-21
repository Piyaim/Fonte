// SPDX-License-Identifier: AGPL-3.0-or-later
package app.fonte;

import android.content.BroadcastReceiver;
import android.content.Context;
import android.content.Intent;

/**
 * Android efface les alarmes au redémarrage du téléphone (et à la mise à jour de l'appli) : on reprogramme la prochaine
 * notification du plan enregistré. Android ne prévient l'appli du démarrage que si elle a été ouverte au moins une fois.
 * Changement d'heure ou de fuseau : même chose. La fin du repos n'est pas reprogrammée (un repos ne survit pas à un redémarrage).
 */
public class BootReceiver extends BroadcastReceiver {
    @Override
    public void onReceive(Context c, Intent i) {
        Notifs.schedule(c);
    }
}
