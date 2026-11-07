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
        context.startService(new Intent(context, BootService.class));
    }
}
