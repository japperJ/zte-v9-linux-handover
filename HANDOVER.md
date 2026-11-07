# HANDOVER — ZTE V9 (Light Tab) Linux Conversion via Windows

> **Purpose:** This document hands off the task of converting a ZTE V9 tablet to run Linux to an AI coding agent operating on a **Windows** machine. The Linux-side investigation is complete; what remains requires Windows-only tooling (ZTE MultiDL) and hardware access.

---

## 1. Mission

Make the ZTE V9 (Light Tab, Telia variant) run a Linux-based operating system, or at minimum a minimal Linux environment, instead of its stock Android 2.2. The device has a badly damaged display and is intended for headless use.

**Realistic scope note (read first):** This is a 2010 device (ARMv6, 512 MB RAM/ROM). There is no mainline Linux kernel port and no postmarketOS support. A full native Linux port would be a multi-month kernel project. The practical goals for a Windows agent are:

1. **Get ADB/root access** so a Linux chroot (old Debian `armel`) can be installed on top of Android, OR
2. **Flash a minimal firmware image** via ZTE's DFU mode to replace Android with something lighter, OR
3. **Document blockers** and recommend abandoning the device if neither is achievable.

Do not promise a full modern Linux desktop on this hardware.

---

## 2. Device Identification

| Field | Value |
|---|---|
| USB serial | `V9_Telia` |
| Normal mode VID:PID | `19d2:0083` (ZTE HSUSB Device, mass-storage/PC-Suite virtual CD-ROM, interface class 08) |
| DFU/download mode VID:PID | `19d2:0112` (ZTE HSUSB Device, vendor-specific class ff) |
| Manufacturer | ZTE Incorporated |
| Product string | "ZTE HSUSB Device" |
| Model | ZTE V9 / "ZTE Light Tab" (Telia-branded) |
| Release | 2010/2011 |
| SoC | Qualcomm MSM7227 (ARM1136EJ-S, ARMv6, 600 MHz, 65 nm) |
| GPU | Qualcomm Adreno 200 |
| RAM | 512 MB SDRAM |
| ROM | 512 MB (≈170 MB user-accessible) |
| Storage expansion | microSD up to 32 GB |
| Display | 7" resistive TFT, 800×480, 262K colors |
| Original OS | Android 2.1 (Eclair) → 2.2 (Froyo), kernel 2.6.32 |
| Battery | Li-Ion 3400 mAh, **removable** |
| Connectivity | 3G (HSDPA 7.2 / HSUPA 2.0), Wi-Fi b/g/n, Bluetooth 2.1, GPS, microUSB 2.0 |
| Physical | 192×110×12.6 mm, 403 g |

**Serial port (if UART is used):** 115200 baud, 8N1, no flow control (typical for MSM7227).

---

## 3. Current State

- Device boots into Android 2.2 (stock or near-stock).
- USB debugging is **not** exposing an ADB interface. The device only presents a mass-storage/PC-Suite interface (`19d2:0083`, class 08) regardless of the "USB debugging" checkbox state.
- The `51-android.rules` udev rules on Linux do **not** cover PID `0083`, and more importantly the device never exposes an ADB interface (class `ff`) in any tested mode.
- The display is badly damaged — on-device navigation is extremely difficult.
- The device has been successfully put into and recovered from DFU mode (Vol Down + Power → `19d2:0112`; recovery via battery removal).

---

## 4. What Was Tried on Linux (and Failed)

1. **USB detection:** `adb devices` always empty. `fastboot devices` always empty (device is not in standard fastboot).
2. **DFU mode entry:** Vol Down + Power → `19d2:0112` (ZTE proprietary DFU, NOT Qualcomm EDL `05c6:9008`, NOT standard fastboot). No Linux tool can talk to this mode.
3. **USB debugging toggle:** Enabled in Settings → Applications → Development → USB debugging. No effect on USB descriptors; no ADB interface appeared.
4. **Udev rules:** Checked `/usr/lib/udev/rules.d/51-android.rules` — PID `0083` is not covered. Even if it were, the device doesn't expose an ADB interface, so permissions are not the blocker.
5. **Recovery:** Battery removal for ~10 s successfully returned device to Android mode.

**Conclusion from Linux:** Software-only access is blocked. The remaining paths require either Windows tooling (DFU flash) or hardware-level access (UART).

---

## 5. What the Windows Agent Must Do

### Step A — Verify and document the device state

- Connect the tablet via USB. Confirm it enumerates as `19d2:0083` (use Device Manager or `lsusb`-equivalent; on Windows use `usbview` or Device Manager → "Universal Serial Bus controllers").
- Check whether ADB is available: install Android platform-tools, run `adb devices`. If empty (expected), proceed to Step B or C.

### Step B — Attempt to gain ADB access (preferred, lowest risk)

Goal: get `adb shell` working so we can root and install a Linux chroot.

1. **Switch USB mode on the device.** On Android 2.2 ZTE, pull down the notification shade → tap "USB connected" → select **"Charge only"** (or "PC Suite"). Some modes expose ADB; "Disk drive" mode often disables it.
2. **Re-enable USB debugging:** Settings → Applications → Development → check "USB debugging". (Display is damaged — use a USB OTG mouse if needed.)
3. **Re-plug USB** and run `adb devices`. If a device appears, run `adb shell` and check `id` / `getprop ro.build.version.release`.
4. **If ADB works**, attempt root. Known root methods for ZTE V9 / MSM7227 (Android 2.2):
   - `z4root` (one-click, may work on 2.2)
   - `SuperOneClick` (Windows tool, uses multiple exploits)
   - Manual exploit via `adb` (e.g., `rageagainstthecage`, `zergRush` — these target specific kernel versions; verify compatibility with 2.6.32)
5. **Once rooted**, install a Linux chroot:
   - Use an old version of **Linux Deploy** (supports Android 2.1+) or manually set up a Debian `armel` rootfs.
   - Debian `armel` (soft-float ARMv5/ARMv6) is the only viable distro; `armhf` requires ARMv7.
   - Recommended: Debian 6 (Squeeze) or 7 (Wheezy) `armel` rootfs, since modern Debian dropped armel.
   - Provide SSH access (dropbear or openssh) for headless use.
   - Disable the display / lock screen for headless operation.

### Step C — DFU flash (if ADB is impossible)

Goal: replace Android with a minimal image via ZTE's proprietary DFU mode.

1. **Enter DFU mode:** Power off → hold Volume Down + Power for ~5 s. Device enumerates as `19d2:0112`.
2. **Install ZTE USB drivers** on Windows (the PC-Suite CD-ROM that mounts in normal mode contains `ZTE_HS_Driver_Setup.exe` — run it).
3. **Install ZTE MultiDL Tool** (Windows-only). Search for "ZTE MultiDL" or "ZTE Download Tool" for MSM7227 devices.
4. **Obtain a firmware image** for ZTE V9. Sources: 4PDA.ru forums, XDA Developers, or ZTE's support site. Look for stock ROMs or CyanogenMod 7 ports (CM7 was ported to ZTE V9). A lighter Android ROM is more realistic than full Linux.
5. **Flash via MultiDL:** Load the firmware, connect device in DFU mode, flash. Follow the tool's instructions carefully.
6. **Recovery:** If the flash fails or bricks, re-enter DFU mode (Vol Down + Power) and re-flash. The battery is removable, so a hard reset (battery pull) always recovers from a hung state.

**Important:** There is no known mainline Linux image for this device. Flashing a "Linux" image would require building one from scratch (kernel + rootfs + bootloader), which is a research project. The realistic outcome of Step C is a lighter/debloated Android ROM, not Linux.

### Step D — Hardware UART (if both software paths fail)

Goal: get a root shell via serial console, bypassing USB entirely.

1. **Disassemble** the tablet (screws under rubber feet / back panel).
2. **Locate the UART** on the MSM7227 board. Common locations:
   - Test points labeled TX/RX/GND near the SoC.
   - Sometimes routed to the headphone jack (requires a resistor divider: 10kΩ series on TX, 10kΩ to GND).
3. **Connect a USB-UART adapter** (CP2102, FT232, or CH340) at 115200 baud, 8N1.
4. **Power on** and observe the boot log. A root shell (`#`) may appear if the kernel console is enabled.
5. **From the shell**, remount rootfs read-write, enable ADB (`setprop service.adb.tcp.port 5555` or start `adbd`), and proceed with rooting/chroot as in Step B.

---

## 6. Tools Required on Windows

| Tool | Purpose | Where to get |
|---|---|---|
| Android Platform Tools (adb/fastboot) | ADB access | developer.android.com |
| ZTE USB Drivers (`ZTE_HS_Driver_Setup.exe`) | Device enumeration | On the tablet's PC-Suite CD-ROM, or ZTE support |
| ZTE MultiDL Tool | DFU flashing | Search "ZTE MultiDL" / XDA / 4PDA |
| USB OTG adapter + mouse | On-device navigation with broken screen | Any electronics shop |
| USB-UART adapter (CP2102/FT232/CH340) | Hardware serial console | Any electronics shop |
| Multimeter | Identify UART pins | — |
| Firmware image (stock ROM or CM7) | Flash target | 4PDA.ru, XDA Developers |

---

## 7. Key Risks

- **Bricking:** DFU flash can brick the device if interrupted or if the wrong image is used. Recovery is via re-entering DFU mode (Vol Down + Power) and re-flashing. Battery removal always recovers from a hung state.
- **No Linux image exists:** Don't expect to flash a ready-made Linux. The realistic deliverable is a rooted Android with a Debian `armel` chroot, or a lighter Android ROM.
- **Display:** The broken screen makes on-device navigation nearly impossible without a USB OTG mouse or blind tapping.
- **ARMv6 limitation:** Only `armel` (soft-float) distros work. No `armhf`, no modern distro.

---

## 8. Success Criteria

The task is "done" if any of the following is achieved:

1. **ADB shell access** is working (`adb shell` returns a prompt), and the device is rooted.
2. **A Linux chroot** (Debian armel) is running on the device with SSH access.
3. **A lighter ROM** has been flashed via DFU, debloating the device.
4. **A root shell** is obtained via UART.
5. **Documented blockers** if none of the above are achievable, with a recommendation to abandon the device.

---

## 9. Repository Contents

- `HANDOVER.md` — this document.
- `DEVICE-NOTES.md` — detailed Linux-side investigation notes (device IDs, what was tried, feasibility assessment).

---

## 10. Contact / Context

- Linux-side investigation performed by: jptrs (Omarchy Linux, Nov 2026).
- GitHub repo: https://github.com/japperJ/zte-v9-linux-handover
- The Linux machine has `adb`, `fastboot`, and the device was tested in both normal (`19d2:0083`) and DFU (`19d2:0112`) modes.

---

*Handover prepared: Nov 2026*
