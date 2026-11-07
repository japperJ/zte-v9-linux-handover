package com.zte.v9boot;

import android.app.Service;
import android.content.Intent;
import android.net.wifi.WifiConfiguration;
import android.net.wifi.WifiInfo;
import android.net.wifi.WifiManager;
import android.os.IBinder;
import android.os.Process;
import android.util.Log;

import java.io.File;
import java.io.FileOutputStream;
import java.io.InputStream;
import java.io.OutputStream;
import java.util.List;

/**
 * Starts the rootless Linux userspace at boot.
 *
 * <p>dropbear runs as this app's uid, not as uid 2000. That is deliberate: the
 * app cannot read shell-owned files, but dropbear's permission checks only
 * require the login account's home to be owned by the login uid. So the app
 * keeps its own home (with key and host key) under its data directory and tells
 * dropbear about it through the ZT_* variables that ztpw.c reads.</p>
 */
public class BootService extends Service {
    static final String TAG = "V9Boot";

    private static final String L = "/data/local/tmp/linux";
    private static final int PORT = 2222;

    private static WifiManager.WifiLock wifiLock;

    @Override
    public IBinder onBind(Intent intent) {
        return null;
    }

    @Override
    public int onStartCommand(Intent intent, int flags, int startId) {
        Log.i(TAG, "start requested");
        try {
            keepWifiAwake();
        } catch (Throwable t) {
            Log.w(TAG, "wifi lock failed: " + t);
        }
        try {
            ensureWifi();
        } catch (Throwable t) {
            Log.w(TAG, "wifi bring-up failed: " + t);
        }
        try {
            ensureHome();
        } catch (Throwable t) {
            Log.e(TAG, "home setup failed: " + t);
        }
        try {
            ensureDropbear();
        } catch (Throwable t) {
            Log.e(TAG, "dropbear start failed: " + t);
        }
        // Sticky so that a low-memory kill also restarts the daemon check.
        return START_STICKY;
    }

    // ---------------------------------------------------------------- wifi

    private void keepWifiAwake() {
        WifiManager wm = wifiManager();
        if (wm == null) {
            return;
        }
        if (wifiLock == null) {
            wifiLock = wm.createWifiLock(WifiManager.WIFI_MODE_FULL, "v9boot");
        }
        if (!wifiLock.isHeld()) {
            wifiLock.acquire();
            Log.i(TAG, "wifi lock held");
        }
    }

    /** Turn the radio on and reconnect to whatever network is already saved. */
    private void ensureWifi() {
        WifiManager wm = wifiManager();
        if (wm == null) {
            Log.w(TAG, "no WifiManager");
            return;
        }
        if (!wm.isWifiEnabled()) {
            Log.i(TAG, "enabling wifi");
            wm.setWifiEnabled(true);
        }
        WifiInfo info = wm.getConnectionInfo();
        if (info != null && info.getNetworkId() >= 0) {
            Log.i(TAG, "wifi already connected: " + info.getSSID());
            return;
        }
        List<WifiConfiguration> nets = wm.getConfiguredNetworks();
        if (nets == null || nets.isEmpty()) {
            Log.w(TAG, "no saved wifi networks; the radio will stay disconnected");
            return;
        }
        WifiConfiguration best = nets.get(0);
        Log.i(TAG, "reconnecting to saved network " + best.SSID);
        wm.enableNetwork(best.networkId, true);
        wm.reconnect();
    }

    private WifiManager wifiManager() {
        return (WifiManager) getSystemService(WIFI_SERVICE);
    }

    // ---------------------------------------------------------------- home

    private File home() {
        File h = new File(getFilesDir(), "home");
        if (!h.exists()) {
            h.mkdirs();
        }
        return h;
    }

    private void ensureHome() throws Exception {
        File h = home();
        File ssh = new File(h, ".ssh");
        if (!ssh.exists()) {
            ssh.mkdirs();
        }

        File keys = new File(ssh, "authorized_keys");
        if (!keys.exists() || keys.length() == 0) {
            InputStream in = getAssets().open("authorized_keys");
            OutputStream out = new FileOutputStream(keys);
            byte[] buf = new byte[4096];
            int n;
            while ((n = in.read(buf)) > 0) {
                out.write(buf, 0, n);
            }
            out.close();
            in.close();
            Log.i(TAG, "installed authorized_keys (" + keys.length() + " bytes)");
        }

        File hostKey = new File(h, "dropbear_rsa_host_key");
        if (!hostKey.exists()) {
            Log.i(TAG, "generating host key");
            runAndWait(new String[] {
                L + "/bin/sh", "-c",
                L + "/sbin/dropbearkey -t rsa -s 2048 -f " + q(hostKey.getAbsolutePath())
            }, 60000);
            if (!hostKey.exists()) {
                throw new IllegalStateException("dropbearkey produced no host key");
            }
        }
    }

    // ------------------------------------------------------------- daemon

    private void ensureDropbear() throws Exception {
        File h = home();
        File pidFile = new File(h, "dropbear.pid");
        if (isRunning(pidFile)) {
            Log.i(TAG, "dropbear already running (pid " + readPid(pidFile) + ")");
            return;
        }

        String script =
            "L=" + L + "; H=" + q(h.getAbsolutePath()) + "; " +
            "export ZT_HOME=\"$H\" ZT_SHELL=\"$L/bin/sh\" ZT_UID=" + Process.myUid() + " " +
            "HOME=\"$H\" PATH=\"$L/bin:$PATH\" TERM=xterm; " +
            "exec \"$L/sbin/dropbear\" -r \"$H/dropbear_rsa_host_key\" " +
            "-p 0.0.0.0:" + PORT + " -s -P \"$H/dropbear.pid\" " +
            ">>\"$H/dropbear.log\" 2>&1";

        Log.i(TAG, "starting dropbear as uid " + Process.myUid() + " on 0.0.0.0:" + PORT);
        Runtime.getRuntime().exec(new String[] { L + "/bin/sh", "-c", script });
        Thread.sleep(1500);

        if (isRunning(pidFile)) {
            Log.i(TAG, "dropbear running, pid " + readPid(pidFile));
        } else {
            Log.e(TAG, "dropbear did not start; see " + new File(h, "dropbear.log"));
        }
    }

    private boolean isRunning(File pidFile) {
        String pid = readPid(pidFile);
        if (pid == null) {
            return false;
        }
        return new File("/proc/" + pid).exists();
    }

    private String readPid(File pidFile) {
        try {
            byte[] buf = new byte[32];
            java.io.FileInputStream in = new java.io.FileInputStream(pidFile);
            int n = in.read(buf);
            in.close();
            if (n <= 0) {
                return null;
            }
            String s = new String(buf, 0, n).trim();
            return s.matches("\\d+") ? s : null;
        } catch (Exception e) {
            return null;
        }
    }

    private void runAndWait(String[] cmd, long timeoutMs) throws Exception {
        java.lang.Process p = Runtime.getRuntime().exec(cmd);
        long deadline = System.currentTimeMillis() + timeoutMs;
        while (System.currentTimeMillis() < deadline) {
            try {
                int rc = p.exitValue();
                if (rc != 0) {
                    Log.w(TAG, cmd[0] + " exited " + rc);
                }
                return;
            } catch (IllegalThreadStateException stillRunning) {
                Thread.sleep(200);
            }
        }
        Log.w(TAG, "timed out waiting for " + cmd[0]);
    }

    private static String q(String s) {
        return "'" + s.replace("'", "'\\''") + "'";
    }
}
