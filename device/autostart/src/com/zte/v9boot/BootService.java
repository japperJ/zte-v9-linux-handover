package com.zte.v9boot;

import android.app.Service;
import android.content.Intent;
import android.net.wifi.WifiConfiguration;
import android.net.wifi.WifiInfo;
import android.net.wifi.WifiManager;
import android.os.IBinder;
import android.os.Process;
import android.util.Log;

import java.io.BufferedReader;
import java.io.File;
import java.io.FileReader;
import java.io.FileInputStream;
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
        String action = (intent != null) ? intent.getAction() : null;
        Log.i(TAG, "start requested: " + action);

        if ("com.zte.v9boot.WIFI_WIPE".equals(action)) {
            try { wipeWifi(); } catch (Throwable t) { Log.e(TAG, "wifi wipe failed: " + t); }
            return START_NOT_STICKY;
        }
        if ("com.zte.v9boot.WIFI_SETUP".equals(action) || "com.zte.v9boot.WIFI_ADD".equals(action)) {
            try { setupWifi(intent); } catch (Throwable t) { Log.e(TAG, "wifi setup failed: " + t); }
            return START_NOT_STICKY;
        }
        if ("com.zte.v9boot.RESTART_SSH".equals(action) || "com.zte.v9boot.RESTART".equals(action)) {
            try {
                File h = home();
                File pidFile = new File(h, "dropbear.pid");
                String pid = readPid(pidFile);
                if (pid != null) {
                    Log.i(TAG, "killing dropbear pid " + pid);
                    Runtime.getRuntime().exec(new String[] { "/system/bin/kill", pid });
                    Thread.sleep(1000);
                }
                ensureDropbear();
            } catch (Throwable t) { Log.e(TAG, "restart failed: " + t); }
            return START_NOT_STICKY;
        }

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
        File shared = new File("/data/local/tmp/linux/etc/dropbear_rsa_host_key");
        if (shared.exists() && shared.canRead()) {
            // Reuse the shell daemon's host key so the fingerprint stays stable
            // across the two daemons (no "host key changed" warning for the user).
            try {
                InputStream in = new FileInputStream(shared);
                OutputStream out = new FileOutputStream(hostKey);
                byte[] buf = new byte[4096];
                int n;
                while ((n = in.read(buf)) > 0) out.write(buf, 0, n);
                out.close(); in.close();
                Log.i(TAG, "copied shared host key");
            } catch (Exception e) {
                Log.w(TAG, "could not copy shared host key: " + e);
                if (!hostKey.exists()) generateHostKey(hostKey);
            }
        } else if (!hostKey.exists()) {
            generateHostKey(hostKey);
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

    // --------------------------------------------------------------- wifi mgmt

    /** Remove every saved network and turn the radio off. */
    private void wipeWifi() {
        WifiManager wm = wifiManager();
        if (wm == null) { Log.w(TAG, "no WifiManager"); return; }
        List<WifiConfiguration> nets = wm.getConfiguredNetworks();
        int n = 0;
        if (nets != null) {
            for (WifiConfiguration c : nets) {
                if (wm.removeNetwork(c.networkId)) n++;
            }
        }
        wm.saveConfiguration();
        wm.setWifiEnabled(false);
        Log.i(TAG, "wiped " + n + " saved network(s); wifi disabled");
        writeStatus("wiped " + n + " network(s); wifi disabled");
    }

    /** Read SSID/PSK from intent extras or /data/local/tmp/wifi.txt and add it. */
    private void setupWifi(Intent intent) {
        String ssid = null, psk = null;
        boolean open = false;
        if (intent != null && intent.hasExtra("ssid")) {
            ssid = intent.getStringExtra("ssid");
            psk = intent.getStringExtra("psk");
            open = intent.getBooleanExtra("open", false);
        }
        if (ssid == null) {
            // Fall back to a world-readable file so passwords never hit the
            // command line. /sdcard is FAT (no exec) but readable/writable by
            // everyone, including this app; /data/local/tmp is shell-owned only.
            String[] candidates = { "/sdcard/wifi.txt", "/data/local/tmp/wifi.txt" };
            for (String path : candidates) {
                try {
                    BufferedReader r = new BufferedReader(new FileReader(path));
                    String line;
                    while ((line = r.readLine()) != null) {
                        line = line.trim();
                        if (line.startsWith("SSID=")) ssid = line.substring(5);
                        else if (line.startsWith("PSK=")) psk = line.substring(4);
                        else if (line.equals("OPEN=1")) open = true;
                    }
                    r.close();
                    if (ssid != null) break;
                } catch (Exception e) {
                    // try next candidate
                }
            }
            if (ssid == null) {
                Log.w(TAG, "could not read wifi.txt from any candidate path");
            }
        }
        if (ssid == null || ssid.length() == 0) {
            Log.e(TAG, "no SSID given (intent extra 'ssid' or /data/local/tmp/wifi.txt)");
            writeStatus("ERROR: no SSID given");
            return;
        }

        WifiManager wm = wifiManager();
        if (wm == null) { Log.w(TAG, "no WifiManager"); return; }
        if (!wm.isWifiEnabled()) wm.setWifiEnabled(true);

        // Start from a clean slate so a forgotten password no longer matters.
        List<WifiConfiguration> old = wm.getConfiguredNetworks();
        if (old != null) for (WifiConfiguration c : old) wm.removeNetwork(c.networkId);
        wm.saveConfiguration();

        WifiConfiguration c = new WifiConfiguration();
        c.SSID = q2(ssid);
        if (open) {
            c.allowedKeyManagement.set(WifiConfiguration.KeyMgmt.NONE);
        } else {
            c.preSharedKey = q2(psk == null ? "" : psk);
            c.allowedKeyManagement.set(WifiConfiguration.KeyMgmt.WPA_PSK);
        }
        int id = wm.addNetwork(c);
        Log.i(TAG, "addNetwork(" + ssid + ") -> " + id);
        if (id < 0) { Log.e(TAG, "addNetwork failed"); writeStatus("ERROR: addNetwork failed for " + ssid); return; }
        wm.enableNetwork(id, true);
        wm.reconnect();
        writeStatus("configured " + ssid + " (networkId=" + id + "); reconnecting");
    }

    private void writeStatus(String msg) {
        try {
            java.io.FileWriter w = new java.io.FileWriter(new File(home(), "wifi-status.txt"));
            w.write(msg + "\\n");
            w.close();
        } catch (Exception e) { Log.w(TAG, "status write failed: " + e); }
    }

    private static String q2(String s) {
        return "\"" + s + "\"";
    }

    private void generateHostKey(File hostKey) throws Exception {
        Log.i(TAG, "generating host key");
        runAndWait(new String[] {
            L + "/bin/sh", "-c",
            L + "/sbin/dropbearkey -t rsa -s 2048 -f " + q(hostKey.getAbsolutePath())
        }, 60000);
        if (!hostKey.exists()) {
            throw new IllegalStateException("dropbearkey produced no host key");
        }
    }

    private static String q(String s) {
        return "'" + s.replace("'", "'\\''") + "'";
    }
}
