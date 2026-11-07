# HANDOVER — ZTE V9 (Light Tab) Linux conversion

**Status: a rootless Linux userspace is deployed and working, reachable over SSH
and telnet through ADB, and it now starts by itself after a reboot (via a small
non-root boot APK). Root is not available and no Linux OS replacement was
attempted.**

The device keeps running its stock Android 2.1. On top of it sits a statically
linked BusyBox tree with a dropbear SSH daemon, all inside `/data/local/tmp`
(no root, nothing flashed, nothing persistent outside `/data`).

```
host ──USB──> adb forward ──> 127.0.0.1:2222 ──> dropbear ──> BusyBox sh (uid 2000 or app uid)
                            └> 127.0.0.1:2323 ──> telnetd

after reboot: BOOT_COMPLETED -> com.zte.v9boot -> dropbear on 0.0.0.0:2222 (app uid)
```

The daemon started by the boot APK listens on all interfaces, so once Wi-Fi has
an address the host can reach it directly (`ssh -p 2222 root@<device-ip>`)
without ADB. Only public-key auth is enabled.

---

## 1. TL;DR for whoever picks this up

| Question | Answer |
|---|---|
| Does ADB work? | **Yes.** `19d2:1354` after running the ZTE driver installer. See §3. |
| Is the device rooted? | **No.** uid 2000 (`shell`). `CVE-2010-EASY` is structurally impossible here — see §6. |
| Is there a Linux shell? | **Yes.** BusyBox 1.31 with 397 applets, over SSH or telnet. |
| Is it a real Linux OS? | **No.** It is a userspace on the Android kernel (`Linux 2.6.29 armv6l`). No chroot, no package manager, no init. |
| Was a full OS port attempted? | **No.** MSM7227/ARMv6 has no mainline or postmarketOS support; it would be a multi-month kernel project with a broken display and no recovery path. |
| Is it usable headless? | **Yes** — that is the whole point of the SSH setup. |
| Does it come back by itself after a reboot? | **Yes.** The boot APK (`device/autostart/`) receives `BOOT_COMPLETED` and starts dropbear. ADB still needs the ZTE mode switch. See §4a. |
| One command after a reboot? | `device\connect.ps1` — does the mode switch, starts the daemon if needed, re-creates the forwards and tests SSH. |

---

## 2. Device facts (verified on hardware)

| Field | Value |
|---|---|
| ADB serial | `V9_Telia` |
| Model / build | ZTE V9 "Light Tab" (Telia), `Light_V9V1.0.0B06` |
| Android | **2.1-update1, SDK 7** (`ro.build.version.release=2.1-update1`) |
| Kernel | **`Linux 2.6.29 #8 PREEMPT Fri Nov 19 2010 armv6l`** |
| SoC | Qualcomm MSM7227, ARM1136EJ-S, **ARMv6**, 600 MHz |
| Shell uid | **2000** (`shell`), supplementary groups 1003,1004,1007,1011,1015,3001-3003 |
| `/data` | 162.5 MB, **29.5 MB free** — the binding constraint |
| `/system` | read-only, ~92 MB free |
| `/sdcard` | 118 MB FAT — no exec bit, no symlinks |
| Display | 7" 800×480, badly damaged (framebuffer is readable, but not usable) |

> The original version of this document claimed Android 2.2 / kernel 2.6.32 and
> that ADB was impossible. Both were wrong; see `DEVICE-NOTES.md` §1.

### USB modes

| VID:PID | Meaning |
|---|---|
| `19d2:0083` | Default after boot: ZTE composite, mass storage + virtual CD-ROM. **No ADB.** |
| `19d2:1354` | ADB composite. **This is what you want.** |
| `19d2:0112` | ZTE DFU/download mode. |

---

## 3. Getting ADB back (do this after every reboot)

The device always boots into `19d2:0083`. The switch to `19d2:1354` is done by
the vendor driver installer, which re-issues the mode-switch command:

```powershell
Start-Process -FilePath 'C:\Program Files (x86)\ZTE\...\ZTE_HS_Driver_Setup.exe' `
  -ArgumentList '/VERYSILENT','/SUPPRESSMSGBOXES','/NORESTART','/SP-' -Verb RunAs -Wait
```

Then:

```powershell
adb devices          # V9_Telia  device
```

Notes:

- **Use the real adb.** `C:\WINDOWS\adb.exe` (v1.0.26 from 2010) shadows the
  modern one on PATH and will not work. Use
  `%LOCALAPPDATA%\Microsoft\WinGet\Packages\Google.PlatformTools_*\platform-tools\adb.exe`.
- Always pass `-s V9_Telia`.
- Nothing in `/data` is lost across reboots, so the Linux tree survives; only
  the USB mode has to be restored.

---

## 4. Using the device

```powershell
# once per boot
adb forward tcp:2222 tcp:2222

# shell with a real PATH, HOME, prompt and aliases
ssh -i ~\.ssh\zte_v9 -p 2222 root@127.0.0.1
```

```powershell
# no SSH? telnet works too
adb forward tcp:2323 tcp:2323
telnet 127.0.0.1 2323
```

Both land in BusyBox `sh` as uid 2000 with
`PATH=/data/local/tmp/linux/bin:...`, i.e. `ls`, `vi`, `top`, `wget`, `nc`,
`tar`, `gzip`, `awk`, `sed` etc. all work.

Public-key authentication is configured for RSA-2048 and Ed25519; password auth
is disabled (`-s`). Host key fingerprint (regenerated only if the file is
deleted):

```
SHA256:RtDRTnAWCNAUdtXhKiiTPSov/KAa/8A5z67B1L9pxpc
```

Host-side keys live in `%USERPROFILE%\.ssh\zte_v9*`. **They must have no
passphrase** — a passphrase-protected key makes the client accept `PK_OK` and
then fail to sign, which is indistinguishable from a server rejection.

If the daemon is not running (after a reboot):

```powershell
device\deploy.ps1
```

---

## 4a. After a reboot — and self-starting without root

A reboot always drops ADB (device returns as `19d2:0083`), but `/data` survives,
so nothing has to be re-deployed. Two pieces make recovery cheap:

```powershell
device\connect.ps1
```

finds the real adb, re-runs the ZTE installer elevated when the device is not in
ADB mode, waits for it, starts dropbear if nothing is listening yet, re-creates
the `2222`/`2323` forwards and (unless `-NoVerify`) proves the login works.
`-NoDriver` skips the mode switch, `-Timeout` changes the wait.

Self-starting is handled on-device by `device/autostart/`, a 8 kB APK
(`com.zte.v9boot`, target SDK 7). It is not a system app and needs no root:

| What | How |
|---|---|
| Trigger | `BOOT_COMPLETED` receiver → sticky service. That is the only non-root hook that runs after boot on a stock 2.1 build. |
| Daemon | Runs dropbear **as the app's own uid** (`app_49` / uid 10049 here), not uid 2000. |
| Home / keys | `ztpw.c` takes the account from `ZT_HOME`/`ZT_SHELL`/`ZT_UID`, so the app keeps its own home under `/data/data/com.zte.v9boot/files/home` with its own `authorized_keys` and host key. It cannot read the shell-owned `/data/local/tmp/linux/root/.ssh`, and it does not try. |
| Bind | `0.0.0.0:2222`, so it is reachable over Wi-Fi *and* through `adb forward`. Public-key auth only (`-s`). |
| Wi-Fi | Holds a `WifiLock` and, if not connected, reconnects to the first saved network. No credentials are stored by this app. |

Host key of the app daemon (regenerated if the app's data is cleared):

```
SHA256:pUa47nhQLiI2yh+WnxZ/PC/VNHSTEusthIfNhbbJAbw
```

Build and install (Android Studio's JBR + SDK build-tools, no Gradle):

```powershell
device\autostart\build-autostart.ps1
device\install-autostart.ps1
```

The installer pushes the APK, stops a shell-owned daemon if it owns the port,
then triggers the service with an explicit broadcast — Android 2.1's `am` has no
`startservice` subcommand.

Limits worth knowing:

- **The app daemon cannot be killed from `adb shell`.** It runs as a different
  uid, so `killall dropbear` (uid 2000) does not touch it. Use
  `adb uninstall com.zte.v9boot`, or reboot.
- **A data wipe or `adb uninstall` removes the app home**, including its host
  key and `authorized_keys`; the boot service recreates both on the next start.
- **The APK signs with a local keystore** (`device/autostart/v9boot.keystore`,
  git-ignored). Keep it, or updates must be uninstall/reinstall.
- **Wi-Fi still needs a saved network in range.** The app can only reconnect to
  networks the device already knows; there is no way to type a passphrase with
  a broken screen, and no root to write `wpa_supplicant.conf`.

---

## 5. Rebuilding

Everything is reproducible from this repo; the details are in
[`device/README.md`](device/README.md).

```bash
wsl -e bash -c 'cd /mnt/c/.../device && ./build-dropbear.sh'
```

| Artifact | Size | Notes |
|---|---|---|
| `dropbear` | 276,628 B | static, ARM EABI5, `zig cc -target arm-linux-musleabi -mcpu=arm1136j_s` |
| `dropbearkey` | 151,932 B | same |
| BusyBox | 1,205,504 B | upstream `1.31.0-defconfig-multiarch-musl/busybox-armv5l` |

Three source changes are needed and are carried as patches in
`device/dropbear/`: the default session `PATH`, and passing `ENV` so the login
profile is sourced. A third change is not a patch but a file: `ztpw.c` supplies
the account (`getpwnam`/`getpwuid`/`getusershell`) that would normally come from
`/etc/passwd`, which cannot exist without root.

The build is reproducible: extracting a pristine `dropbear-2022.83` and running
`device/build-dropbear.sh` produces a byte-identical `dropbear`
(SHA256 `DE47D347B4F7A591A6DFB89706A6EABFBCA800A67E80BA09AFB1A79E57D0EE25`).
`device/deploy.ps1` then pushes it and restarts the daemon; that path has been
run end-to-end on the device.

---

## 6. Ruled out (with evidence)

### `CVE-2010-EASY` — the classic "get root on Android 2.x" — does not work here

The exploit forks until `RLIMIT_NPROC` is hit, then lets `setuid()` fail in
`adbd`'s child, leaving it running as root. On this device `set_user()` in
`adbd` contains **no `RLIMIT_NPROC` check at all**, so `setuid()` can never
fail: the exploit's precondition does not exist.

Measured: with 3,754 tasks alive, `adbd` still came back as `pid=13994
uid=2000`. Run four times, including after fixing the SIGHUP race that killed
the forked children early (children need `setsid()` and
`HUP/INT/QUIT/TERM/PIPE` masked, because closing `adbd`'s pty kills the
foreground process group).

### Everything else that needs root, needs root

- `/etc` cannot be mounted or created → the profile is sourced via `$ENV`
  instead of `/etc/profile`.
- A Debian `armel` chroot needs `mount`/`chroot` capability the shell does not
  have.
- Hotplug/`/dev` tricks and `init` replacement are root-only.
- ZTE DFU (`19d2:0112`) is a proprietary MultiDL protocol, not Qualcomm EDL and
  not fastboot; flashing is only worth attempting if root becomes essential,
  and there is no recovery image for a device with a broken screen.

---

## 7. Limits of what is deployed

- **Not persistent across `/data` wipe or factory reset.** Re-run
  `device\deploy.ps1` and then `device\install-autostart.ps1`.
- **`/data` has ~29.4 MB free** (166.4 MB total, 82% used). The Linux tree is
  1.8 MB (`bin` 1.4 MB, `sbin` 0.4 MB); the boot APK's data is 14 kB. Left over
  from the root investigation are `ratc2`, `su`, `probe` and `fb.raw` in
  `/data/local/tmp` — about 1.6 MB that can be deleted if space is ever needed.
- **No package manager.** It is BusyBox, not a distro.
- **The device still boots Android** and drains battery on standby; there is no
  way to power it off or boot straight into the userspace without root.
- **No sftp/scp server**: BusyBox has no `scp` applet, so use `adb push` for
  file transfer.
- **The app-started daemon logs** to
  `/data/data/com.zte.v9boot/files/home/dropbear.log` (readable over the SSH
  session, which runs as the same uid). The uid-2000 daemon from `deploy.ps1`
  still has no log unless started with `-F`.
- **The app daemon listens on all interfaces.** That is what makes Wi-Fi access
  possible, but it also means the port is exposed to the local network; only
  public-key auth is enabled and password auth is off (`-s`).
- **Only one daemon can own 2222.** `deploy.ps1` and `connect.ps1` detect an
  existing listener instead of fighting over the port; uid 2000 cannot kill the
  app daemon.

---

## 8. Next steps

1. ~~**Make it self-starting**~~ — **done.** The boot APK in `device/autostart/`
   starts dropbear on `BOOT_COMPLETED` without root (§4a). ADB itself still has
   to be restored by the ZTE installer after each reboot; `connect.ps1` wraps
   that.
2. **Trim `/data` usage** — measured: tree 1.8 MB, app data 14 kB, 29.4 MB free.
   Only the ~1.6 MB of old root-investigation binaries is obviously
   disposable. A smaller BusyBox build (fewer applets) is possible but would
   complicate the tree for little gain.
3. **Blind UI driving**: `sendevent` against `/dev/input/event*` works without
   root but is only useful if some on-device feature is ever needed. Untouched —
   the panel is physically damaged, so the framebuffer is not navigable.
4. **Pre-rooted FTM/MultiDL flash**: only if root becomes essential, and only
   with a recovery path — there is none today. Deliberately not attempted.

---

## 9. Repo layout

```
HANDOVER.md              this file: status, reproduction, decisions
DEVICE-NOTES.md          field notes: quirks, exact commands, corrections
device/README.md         build and deploy the userspace
device/connect.ps1       one command after a reboot: mode switch, daemon, forwards, SSH test
device/deploy.ps1        push everything and start sshd
device/build-dropbear.sh cross-build dropbear with zig (no make/gcc)
device/dropbear/         ztpw.c + the two source patches
device/fs/               profile, linux.sh, start-ssh.sh
device/autostart/        boot APK: AndroidManifest, Java sources, build + install scripts
```