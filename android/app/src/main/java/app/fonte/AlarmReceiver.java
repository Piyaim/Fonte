// SPDX-License-Identifier: AGPL-3.0-or-later
package app.fonte;

import android.content.BroadcastReceiver;
import android.content.Context;
import android.content.Intent;

/** Réveillé par AlarmManager : notification du plan ou fin du repos (voir Notifs). */
public class AlarmReceiver extends BroadcastReceiver {
    @Override
    public void onReceive(Context c, Intent i) {
        String a = i.getAction();
        if (Notifs.ACTION_PLAN.equals(a)) Notifs.fire(c);
        else if (Notifs.ACTION_REPOS.equals(a)) Notifs.restFire(c, i.getStringExtra("title"), i.getStringExtra("text"));
    }
}
