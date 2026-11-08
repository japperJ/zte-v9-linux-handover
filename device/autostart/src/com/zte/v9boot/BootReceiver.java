package com.zte.v9boot;

import android.content.BroadcastReceiver;
import android.content.Context;
import android.content.Intent;
import android.util.Log;

/**
 * Starts {@link BootService} on BOOT_COMPLETED. This is the only non-root way to
 * get code running after a reboot on a stock Android 2.1 build.
 */
public class BootReceiver extends BroadcastReceiver {
    @Override
    public void onReceive(Context context, Intent intent) {
        Log.i(BootService.TAG, "received " + intent.getAction());
        // Forward the original intent (action + extras) to the service instead of
        // dropping it, so WIFI_WIPE / WIFI_SETUP commands reach onStartCommand.
        Intent svc = new Intent(context, BootService.class);
        if (intent.getAction() != null) {
            svc.setAction(intent.getAction());
        }
        if (intent.getExtras() != null) {
            svc.putExtras(intent.getExtras());
        }
        context.startService(svc);
    }
}
