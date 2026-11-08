# DEV HANDOVER — PandP Home (ZTE V9)

> **Purpose:** Complete handover for an AI coding agent to continue developing
> the PandP Home web app on the ZTE V9 device. Read this + `AGENTS.md` +
> `HANDOVER.md` before starting any work.

---

## 1. Project Overview

**PandP Home** is a mobile-first PWA (Progressive Web App) that runs as a
web server on a ZTE V9 tablet (2010, Android 2.1, ARMv6). The device runs a
rootless Linux userspace (BusyBox + dropbear SSH) on top of stock Android.
The web server (port 8080) serves HTML pages with CGI backends (BusyBox sh
scripts) that persist data in flat files.

### What it does
- **Dashboard** (`index.html`) — home screen with app cards
- **Chat room** (`chat.cgi`) — text chat with bubbles, grouping, date dividers
- **Task list** (`tasks.cgi`) — to-do list, tap to toggle done
- **Calendar** (`calendar.cgi`) — monthly calendar with events
- **Grocery list** (`grocery.cgi`) — shopping list with quantities, check off purchased
- **Recipes** (`recipes.cgi`) — recipe collection
- **File browser** (`browse.cgi`) — list/download files from the device
- **Upload** (`upload.cgi`) — upload files via browser

### Tech stack
- **Frontend:** Plain HTML/CSS/JS (no framework). Mobile-first, PWA.
- **Backend:** BusyBox sh CGI scripts (`/data/local/tmp/linux/www/cgi-bin/`)
- **Data:** Flat files (`*.log`, `*.txt`) in `/data/local/tmp/linux/www/`
- **Server:** BusyBox httpd on port 8080
- **SSH:** dropbear on port 2222 (via adb forward)
- **No root, no flashing** — everything runs as the shell user (uid 2000)

---

## 2. Device Access

### Device specs
- ZTE V9 (Light Tab, Telia variant), 2010
- Android 2.1 (Eclair), kernel 2.6.32
- Qualcomm MSM7227 (ARMv6, 600 MHz), 512 MB RAM, 512 MB ROM
- 7" resistive TFT, 800×480
- Battery: Li-Ion 3400 mAh, removable

### USB modes
| VID:PID | Meaning |
|---|---|
| `19d2:0083` | Default after boot: mass storage + virtual CD-ROM. **No ADB.** |
| `19d2:1354` | ADB composite. **This is what you want.** |
| `19d2:0112` | ZTE DFU/download mode. |

### Getting ADB (Windows)
The device boots into `19d2:0083`. The ZTE driver installer re-issues the mode
switch to `19d2:1354`:

```powershell
.\connect.ps1   # from device/ folder — handles everything
```

Or manually:
```powershell
# Run ZTE driver installer (elevated)
Start-Process -FilePath 'ZTE_HS_Driver_Setup.exe' -ArgumentList '/VERYSILENT','/SUPPRESSMSGBOXES','/NORESTART','/SP-' -Verb RunAs -Wait
# Then check
adb devices   # should show V9_Telia  device
```

### Critical ADB notes
- **Use the real adb.** `C:\WINDOWS\adb.exe` (v1.0.26 from 2010) shadows the
  modern one on PATH. Use `%LOCALAPPDATA%\Microsoft\WinGet\Packages\Google.PlatformTools_*\platform-tools\adb.exe`.
- Always pass `-s V9_Telia`.
- The device reboots out of ADB mode — re-run `connect.ps1` after every reboot.

### SSH access
```powershell
ssh -i ~\.ssh\zte_v9 -p 2222 root@127.0.0.1
```
Or telnet (no SSH):
```powershell
adb forward tcp:2323 tcp:2323
telnet 127.0.0.1 2323
```

### Web access
```
http://<device-ip>:8080/
```
The device IP is on the local network. Use `adb shell` to find it:
```powershell
adb shell "ifconfig wlan0 2>/dev/null | grep 'inet addr'"
```

---

## 3. Project Structure

```
/home/jptrs/adndriod-zte/
├── AGENTS.md              # UI/UX & implementation conventions (MUST READ)
├── HANDOVER.md            # Device access handover
├── DEV-HANDOVER.md        # This file
├── DEVICE-NOTES.md        # Linux-side investigation notes
├── device/
│   ├── README.md          # Device setup & deploy instructions
│   ├── connect.ps1        # One-command device recovery (Windows)
│   ├── deploy.ps1         # Deploy web app to device (Windows)
│   ├── build-dropbear.sh  # Build dropbear SSH server (WSL)
│   ├── install-autostart.ps1
│   ├── build-autostart.ps1
│   ├── autostart/         # Boot APK (self-starting, no root)
│   │   ├── build-autostart.ps1
│   │   ├── src/com/zte/v9boot/BootReceiver.java
│   │   └── src/com/zte/v9boot/BootService.java
│   ├── dropbear/          # dropbear patches + ztpw.c
│   │   ├── 0001-default-path.patch
│   │   ├── 0002-session-env.patch
│   │   └── ztpw.c
│   └── fs/                # The Linux filesystem deployed to device
│       ├── linux.sh       # Interactive login shell
│       ├── profile        # Shell profile (aliases, PATH)
│       ├── start-ssh.sh   # Starts dropbear
│       └── www/           # Web app root (deployed to /data/local/tmp/linux/www/)
│           ├── index.html # Dashboard
│           ├── nav.css     # Shared navigation styles
│           ├── nav.js      # Shared navigation JS
│           ├── manifest.json
│           ├── sw.js       # Service worker
│           ├── icon-192.png
│           ├── icon-512.png
│           └── cgi-bin/   # CGI backend scripts
│               ├── browse.cgi
│               ├── calendar.cgi
│               ├── chat.cgi
│               ├── delete.cgi
│               ├── grocery.cgi
│               ├── lang.inc
│               ├── mkdir.cgi
│               ├── recipes.cgi
│               ├── tasks.cgi
│               └── upload.cgi
```

### Deployed paths on device
```
/data/local/tmp/linux/          # Linux userspace root
├── bin/                        # 397 BusyBox applet symlinks
├── sbin/                       # dropbear, dropbearkey
├── etc/                        # profile, dropbear_rsa_host_key
├── root/                       # HOME, .ssh/authorized_keys
├── linux.sh                    # interactive login shell
├── start-ssh.sh                # starts dropbear
└── www/                        # Web app (served on port 8080)
    ├── index.html
    ├── nav.css, nav.js
    ├── manifest.json, sw.js
    ├── icon-*.png
    └── cgi-bin/                # CGI scripts (chmod 755)
        ├── *.cgi
        └── lang.inc
```

---

## 4. Development Conventions (from AGENTS.md)

### Visual identity
- **Background**: page `#1a1a2e`; panels/cards `#16213e` (or `#161b22` for chat)
- **Accent**: `#4fc3f7` (links, primary buttons) or `#58a6ff` (chat/task screens)
- **Success**: `#238636`, **Danger**: `#b71c1c`/`#ff5252`
- **Text**: primary `#eee`/`#e6edf3`, muted `#8b949e`/`#aaa`
- **Borders**: `#30363d` / `#333`. Border radius 6-8px.
- **Font**: system stack
- **Touch targets**: minimum 44-48px height, font size 16px+ on inputs

### Layout
- Mobile-first, responsive. Max content width 800-900px, centered.
- Header bar: colored background, centered title, subtitle line.
- Home link button (`.homebtn`) at top of every sub-page.
- Use `.container` / `.wrap` / `.card` classes.

### Components
- **Buttons**: `.btn` (filled accent) for primary, `.homebtn` for navigation, `.del` (red) for destructive.
- **File input**: NEVER use native `<input type="file">` visible. Hide it, use styled `<label class="filebtn">`.
- **Links**: accent color, no underline until hover.
- **Empty states**: centered muted italic (`.empty-msg`).

### PWA (every page MUST have)
- `<link rel="manifest" href="/manifest.json">`
- `<meta name="theme-color" content="#16213e">`
- `<link rel="apple-touch-icon" href="/icon-192.png">`
- Service worker registration
- Viewport meta with `maximum-scale=1.0, user-scalable=no`

### CGI / backend
- Scripts in `/data/local/tmp/linux/www/cgi-bin/`, chmod 755
- Use BusyBox applets explicitly (`$L/bin/busybox ...`)
- URL-decode with shared `urldecode()` function
- Persist data in `/data/local/tmp/linux/www/*.log` (or `*.txt`), one record per line
- Skip data files and CGI scripts in `browse.cgi`
- LF line endings (not CRLF) — BusyBox sh is strict
- Return `Content-type: ...; charset=UTF-8` and `Access-Control-Allow-Origin: *`

### Cross-device input
- All 'add' flows must work on mobile, iPad, and desktop
- Touch targets >= 44px, inputs font-size >= 16px
- Test on narrow (<=480px), tablet, and desktop widths

### Do NOT
- Introduce new color schemes or fonts
- Expose native file inputs
- Store data outside `/data/local/tmp/linux/www/`
- Break existing card/button styling

---

## 5. How to Deploy

### From Windows (PowerShell)
```powershell
.\deploy.ps1
```
This pushes all files from `device/fs/` to the device, creates applet symlinks,
generates host key on first run, starts dropbear, and sets up adb forwards.

### Manual deploy via ADB
```powershell
# Push web files
adb -s V9_Telia push device/fs/www /data/local/tmp/linux/www
# Push scripts
adb -s V9_Telia push device/fs/linux.sh /data/local/tmp/linux/linux.sh
adb -s V9_Telia push device/fs/profile /data/local/tmp/linux/etc/profile
adb -s V9_Telia push device/fs/start-ssh.sh /data/local/tmp/linux/start-ssh.sh
# Fix permissions
adb -s V9_Telia shell "chmod 755 /data/local/tmp/linux/www/cgi-bin/*.cgi"
adb -s V9_Telia shell "chmod 755 /data/local/tmp/linux/linux.sh /data/local/tmp/linux/start-ssh.sh"
```

### Test via curl
```powershell
# After adb forward tcp:8080 tcp:8080
curl http://127.0.0.1:8080/
curl http://127.0.0.1:8080/cgi-bin/chat.cgi
```

---

## 6. Current State

### What's implemented
- Dashboard (index.html) with app cards
- Chat room with bubbles, grouping, date dividers, composer
- Task list (add, toggle done)
- Calendar (monthly view, tap day to add event)
- Grocery list (items with quantities, check off purchased, clear purchased)
- Recipes collection
- File browser (list/download)
- Upload (file upload via browser)
- Navigation (shared nav.css/nav.js across all pages)
- PWA (manifest, service worker, icons)
- DA/EN language support (lang.inc)
- Deep-linking calendar todos from dashboard

### Git history (recent)
```
6149676 Update: SD card accessible, contains Android ROM not Linux
c5edc32 Merge PR #2: calendar-todo-deeplink
1ffa4dc Deep-link calendar todos from dashboard to event editor
06cd530 Merge PR #1: pandp-home-app
0c7d3e8 Redesign chat with bubbles, grouping, date dividers, composer
42083e6 Add dashboard home, recipes app, shared nav and DA/EN across all pages
71b6264 Restore task list app and add link on home page
e78a1c9 Add 'Download as PDF' button to grocery list
10e28fc Revert grocery to simple server-side list
4b3670a Fix grocery sync: preserve offline changes, add conflict resolution
19ad5f7 Fix grocery sync conflict
2533a36 Fix grocery sync: use ; separator
83d16ee Add iOS PWA meta tags
6139a7c Add offline support to grocery list
615e794 Fix index.html: remove trailing PowerShell code
```

### Known issues
- Device not currently accessible via ADB from this Linux machine
- Need Windows PC + ZTE driver installer to switch to ADB mode
- The `connect.ps1` script handles the full recovery flow

---

## 7. How to Work on This Project

### If you have ADB access (Windows):
1. Run `.\connect.ps1` to get ADB + SSH working
2. Edit files in `device/fs/www/` (HTML, CSS, JS, CGI)
3. Run `.\deploy.ps1` to push changes to device
4. Test via browser: `http://<device-ip>:8080/`
5. Or test CGI via curl: `curl http://127.0.0.1:8080/cgi-bin/<script>.cgi`

### If you DON'T have ADB access (this Linux machine):
1. Edit files in `device/fs/www/` (HTML, CSS, JS, CGI)
2. Commit and push changes
3. Deploy later from Windows via `.\deploy.ps1`

### Editing CGI scripts
- Files are in `device/fs/www/cgi-bin/`
- They are BusyBox sh scripts
- Must have LF line endings (not CRLF)
- Must be chmod 755 on device
- Use `$L/bin/busybox` for all commands
- URL-decode with shared `urldecode()` function
- Persist data in `/data/local/tmp/linux/www/*.log`

### Adding a new page
1. Create HTML file in `device/fs/www/`
2. Add PWA meta tags (manifest, theme-color, apple-touch-icon, SW registration)
3. Add `.homebtn` link back to index.html
4. Include nav.css and nav.js
5. If backend needed, create CGI script in `device/fs/www/cgi-bin/`
6. Add card to index.html dashboard
7. Update `browse.cgi` to skip the new data files

### Adding a new CGI endpoint
1. Create `device/fs/www/cgi-bin/<name>.cgi`
2. Start with `#!/bin/sh` and set `L=/data/local/tmp/linux`
3. Add `Content-type: text/html; charset=UTF-8` and `Access-Control-Allow-Origin: *`
4. Use `urldecode()` for user input
5. Persist data in `/data/local/tmp/linux/www/<name>.log`
6. chmod 755 on device

---

## 8. Key Files to Read First

1. **AGENTS.md** — UI/UX and implementation conventions (MUST READ)
2. **device/README.md** — Device setup, build, deploy instructions
3. **HANDOVER.md** — Device access and ADB recovery
4. **device/fs/www/index.html** — Dashboard (entry point)
5. **device/fs/www/cgi-bin/chat.cgi** — Example CGI script (good reference)
6. **device/fs/www/nav.js** — Shared navigation
7. **device/fs/www/nav.css** — Shared styles

---

## 9. Environment Variables on Device

```
ROOT=/data/local/tmp/linux
PATH=$ROOT/bin:$ROOT/sbin:/system/bin:/system/xbin
HOME=$ROOT/root
TERM=xterm (or as set)
ENV=$ROOT/etc/profile
L=/data/local/tmp/linux  (used in CGI scripts)
```

### CGI environment (BusyBox httpd)
```
REQUEST_METHOD, QUERY_STRING, CONTENT_TYPE, CONTENT_LENGTH
HTTP_COOKIE, HTTP_HOST, REMOTE_ADDR
```

---

## 10. Git Workflow

- **Repo:** https://github.com/japperJ/zte-v9-linux-handover (or the actual project repo)
- **Branch:** main
- **PRs:** Feature branches merged via PRs (see git history)
- **Commit style:** Descriptive messages, e.g., "Add dashboard home, recipes app, shared nav and DA/EN across all pages"

### To create a feature branch
```bash
git checkout -b feature/my-feature
# ... make changes ...
git commit -m "Description of changes"
git push -u origin feature/my-feature
# Create PR via GitHub
```

---

## 11. Troubleshooting

### "adb: device not found"
- Device is in mass-storage mode (19d2:0083). Run `connect.ps1` on Windows.
- Or re-run ZTE driver installer manually.

### "SSH connection refused"
- dropbear not running. Start it: `adb shell /data/local/tmp/linux/start-ssh.sh`
- Or reboot and let the boot APK start it.

### "CGI script returns 500"
- Check LF line endings (not CRLF)
- Check chmod 755
- Check for syntax errors: `adb shell sh -n /data/local/tmp/linux/www/cgi-bin/script.cgi`

### "Data not persisting"
- Check file permissions (uid 2000 = shell)
- Check path: must be in `/data/local/tmp/linux/www/`
- Check that the file is not in browse.cgi's skip list

### "PWA not installing"
- HTTPS required for service worker (or localhost)
- Check manifest.json is valid
- Check icon paths are correct

---

*Handover prepared: Nov 2026*
*Project: PandP Home — ZTE V9 web server*
