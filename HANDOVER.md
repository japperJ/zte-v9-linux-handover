# HANDOVER — ZTE V9 (Light Tab) Linux conversion

**Status: a rootless Linux userspace is deployed and working, reachable over SSH
and telnet through ADB. Root is not available and no Linux OS replacement was
attempted.**

The device keeps running its stock Android 2.1. On top of it sits a statically
linked BusyBox tree with a dropbear SSH daemon, all inside `/data/local/tmp`
(no root, nothing flashed, nothing persistent outside `/data`).

```
host ──USB──> adb forward ──> 127.0.0.1:2222 ──> dropbear ──> BusyBox sh (uid 2000)
                            └> 127.0.0.1:2323 ──> telnetd
```

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
  `deploy.ps1`.
- **Daemon has no logging** unless started with `-F` (this build has no
  syslog; daemonizing sends stderr to `/dev/null`).
- **~29 MB free on `/data`.** Do not install large trees.
- **No package manager.** It is BusyBox, not a distro.
- **The device still boots Android** and drains battery on standby; there is no
  way to power it off or boot straight into the userspace without root.
- **No sftp/scp server**: BusyBox has no `scp` applet, so use `adb push` for
  file transfer.

---

## 8. Possible next steps

1. **Make it self-starting**: nothing can be added to `init.rc` without root, so
   the daemon still has to be started over ADB after each boot.
2. **Trim `/data` usage**: BusyBox is 1.2 MB and dropbear 280 kB; if space is
   ever needed, install only the applets actually used.
3. **Blind UI driving**: `sendevent` against `/dev/input/event*` works without
   root but is only useful if some on-device feature is ever needed.
4. **Pre-rooted FTM/MultiDL flash**: only if root becomes essential, and only
   with a recovery path — there is none today.

---

## 9. Repo layout

```
HANDOVER.md              this file: status, reproduction, decisions
DEVICE-NOTES.md          field notes: quirks, exact commands, corrections
device/README.md         build and deploy the userspace
device/build-dropbear.sh cross-build dropbear with zig (no make/gcc)
device/deploy.ps1        push everything and start sshd
device/dropbear/         ztpw.c + the two source patches
device/fs/               profile, linux.sh, start-ssh.sh
```