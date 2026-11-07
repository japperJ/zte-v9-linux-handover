# Rootless Linux userspace for the ZTE V9

Everything in this directory rebuilds the environment that currently runs on the
device: a static BusyBox tree at `/data/local/tmp/linux`, plus a statically
linked dropbear SSH server listening on the device's loopback interface and
reached from the host through `adb forward`.

No root, no flashing, no kernel changes. The device keeps running its stock
Android 2.1; Linux is a userspace on top of it.

```
/data/local/tmp/linux
├── bin/            397 BusyBox applet symlinks -> busybox
├── sbin/           dropbear, dropbearkey
├── etc/            profile, dropbear_rsa_host_key
├── root/           HOME, .ssh/authorized_keys
├── linux.sh        interactive login shell (telnet)
└── start-ssh.sh    starts dropbear
```

## Prerequisites

| Thing | Notes |
|---|---|
| ADB access | See `../HANDOVER.md` §2 — the ZTE installer is what switches the device to ADB mode. |
| Zig 0.17 | `winget install zig.zig`. Used as the C compiler; no gcc/make needed. |
| dropbear 2022.83 source | `https://matt.ucc.asn.au/dropbear/releases/dropbear-2022.83.tar.bz2`, extracted next to this README as `dropbear-2022.83/`. |
| BusyBox armv5l | `https://busybox.net/downloads/binaries/1.31.0-defconfig-multiarch-musl/busybox-armv5l` → save as `vendor/busybox-armv5l` (SHA256 `69BBB65CCD70481EC2DF19B8770B2E979AEB75DDDF08D2FC5B0230F892989C40`). |
| Client key | `ssh-keygen -t ed25519 -f ~/.ssh/zte_v9` on the host, public half concatenated into `authorized_keys`. |
| Android SDK + JDK | Only for the boot APK. Android Studio's bundled JBR works; no Gradle needed. |

## Build

```bash
wsl -e bash -c 'cd /mnt/c/.../device && ./build-dropbear.sh'
```

The script copies `dropbear/ztpw.c` into the tree, applies the two patches in
`dropbear/`, regenerates `default_options_guard.h`, builds libtommath and
libtomcrypt from their own Makefile object lists, then compiles and links
`dropbear` and `dropbearkey` with `zig cc -target arm-linux-musleabi
-mcpu=arm1136j_s`. First run takes a few minutes; the two `.a` files are cached
afterwards (delete them to force a rebuild). Output lands in
`dropbear-2022.83/`.

## Deploy

```powershell
.\deploy.ps1
```

Pushes everything, creates the applet symlinks, generates the host key on first
run, starts dropbear and sets up `adb forward tcp:2222 tcp:2222`.

## Connect

```powershell
ssh -i ~\.ssh\zte_v9 -p 2222 root@127.0.0.1
```

Or, for a plain shell without SSH:

```powershell
adb forward tcp:2323 tcp:2323
# then: telnet 127.0.0.1 2323
```

## After a reboot

The device comes back as `19d2:0083` (no ADB), but `/data` is untouched. One
command handles the whole recovery:

```powershell
.\connect.ps1
```

It locates the real adb, re-runs the ZTE driver installer elevated when needed,
waits for the device, starts dropbear if nothing is listening on 2222, sets up
the forwards and verifies the SSH login. Use `-NoDriver` if the device is
already in ADB mode and you do not want the UAC prompt, `-Timeout` to wait
longer, `-NoVerify` to skip the smoke test.

## Boot APK (self-starting, no root)

`autostart/` is a small APK (`com.zte.v9boot`) that receives `BOOT_COMPLETED`
and starts dropbear as its own app uid on `0.0.0.0:2222`. It is the only
non-root way to run anything after a reboot on a stock 2.1 build.

```powershell
.\autostart\build-autostart.ps1    # aapt2 + d8 + apksigner, no Gradle
.\install-autostart.ps1            # adb install, then trigger the service
```

Requires the Android SDK (build-tools + a platform) and a JDK; the build script
finds Android Studio's bundled JBR automatically. The signing key
(`autostart/v9boot.keystore`) is created on first build and is git-ignored —
keep it if you want to update the app in place.

Because the app uid cannot read the shell-owned home, the APK keeps its own home
under `/data/data/com.zte.v9boot/files/home` with its own `authorized_keys`
(copied from the host keys at build time) and host key. That daemon logs to
`files/home/dropbear.log` and cannot be killed from `adb shell`; use
`adb uninstall com.zte.v9boot` or reboot.

## Patches

| Patch | Why |
|---|---|
| `0001-default-path.patch` | dropbear hands each session a fixed environment; its `DEFAULT_PATH` pointed at `/usr/bin:/bin`, which does not exist here, so every command failed with "not found". |
| `0002-session-env.patch` | Adds `ENV` to that fixed environment so BusyBox ash sources `etc/profile` for interactive logins (prompt, aliases). |

`ztpw.c` is not a patch: it *defines* `getpwnam`/`getpwuid`/`getusershell` so
the statically linked musl never reads `/etc/passwd` or `/etc/shells`, neither
of which can exist without root. The synthetic account comes from `ZT_HOME`,
`ZT_SHELL` and `ZT_UID`, which `start-ssh.sh` exports.

## Gotchas

- **Never run dropbear without `-F` when you need logs.** Daemonizing sends
  stderr to `/dev/null`; there is no syslog in this build. Use
  `start-ssh.sh -F`.
- **`adb shell` hangs after dropbear daemonizes.** It waits for the pty to
  close. `deploy.ps1` starts it detached and ignores the stuck client.
- **The device reboots out of ADB mode.** Re-run the ZTE driver installer to
  get `19d2:1354` back, then `deploy.ps1` again — nothing in `/data` is lost.
- **Two silent authentication failures exist upstream**: an `authorized_keys`
  that fails the permission check, and a shell that is not in `getusershell()`.
  Both reject the login without logging anything, which makes them look like a
  key problem. `~/` must be owned by the login uid and not group/other-writable.
- **The client key must have no passphrase.** A key created with a passphrase
  (even an empty-looking one) makes the client accept `PK_OK` and then fail to
  sign, which looks exactly like a server-side rejection.
- **Only one daemon can own port 2222.** If the boot APK's daemon is running,
  `deploy.ps1` will not start a second one and uid 2000 cannot kill the app's
  daemon; reboot or `adb uninstall com.zte.v9boot` to get rid of it.
- **`am` on 2.1 has no `startservice`**, and `adb install`/`pm` can leave the
  pty open after printing. Scripts that need them must use a host-side timeout.
