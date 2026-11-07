# AGENTS.md — PandP Home server design & implementation guide

This document is the single source of truth for UI/UX and implementation
conventions for the PandP Home server (ZTE V9). Any new or changed feature
MUST follow it so the app stays visually and behaviorally consistent.

## 1. Visual identity

- **Background**: page `#1a1a2e`; panels/cards `#16213e` (or `#161b22` for
  chat-style screens); input background `#0d1117`.
- **Accent**: `#4fc3f7` (links, primary buttons on light cards) or `#58a6ff`
  (chat/task screens). Success `#238636`, danger `#b71c1c`/`#ff5252`.
- **Text**: primary `#eee`/`#e6edf3`, muted `#8b949e`/`#aaa`.
- **Borders**: `#30363d` / `#333`. Border radius 6-8px. Cards have 8px radius.
- **Font**: system stack `-apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif`.
- **Touch targets**: minimum 44-48px height for buttons/inputs. Font size 16px+
  on inputs to prevent iOS zoom.

## 2. Layout

- Mobile-first, responsive. Max content width 800-900px, centered.
- Header bar: colored background, centered title, subtitle line.
- Home link button (`.homebtn`) at top of every sub-page.
- Use `.container` / `.wrap` / `.card` classes. Prefer flex column on mobile.

## 3. Components

- **Buttons**: use `.btn` (filled accent) for primary actions, `.homebtn` for
  navigation, `.del` (red) for destructive. Minimum height 44px.
- **File input**: NEVER use the native `<input type="file">` visible. Hide it
  (`display:none`) and use a styled `<label class="filebtn">Choose file</label>`
  pointing at it via `for`. Show selected filename in a muted span.
- **Links**: accent color, no underline until hover.
- **Empty states**: centered muted italic message (`.empty-msg`).

## 4. PWA requirements (every page)

Every HTML page MUST include:
- `<link rel="manifest" href="/manifest.json">`
- `<meta name="theme-color" content="#16213e">`
- `<link rel="apple-touch-icon" href="/icon-192.png">`
- Service worker registration:
  `if('serviceWorker' in navigator){navigator.serviceWorker.register('/sw.js').catch(function(){});}`
- Viewport meta with `maximum-scale=1.0, user-scalable=no`.

Manifest and icons live at the web root (`/manifest.json`, `/icon-*.png`,
`/sw.js`). New pages must not break these paths.

## 5. CGI / backend conventions

- Scripts live in `/data/local/tmp/linux/www/cgi-bin/` and are deployed + chmod 755.
- Use BusyBox applets explicitly (`$L/bin/busybox ...`).
- URL-decode user input with the shared `urldecode()` function (handles %XX, +, UTF-8).
- Persist data in `/data/local/tmp/linux/www/*.log` (or `*.txt`), one record per line.
- Skip data files and CGI scripts in `browse.cgi`.
- Keep line endings LF (not CRLF) — BusyBox sh is strict.
- Return `Content-type: ...; charset=UTF-8` and `Access-Control-Allow-Origin: *`.

## 6. Consistency checklist for new features

- [ ] Matches color palette and spacing above.
- [ ] Touch targets >= 44px.
- [ ] Includes all PWA meta + SW registration.
- [ ] File inputs use styled label pattern.
- [ ] Persisted files skipped in browse.cgi.
- [ ] LF line endings.
- [ ] Tested on device via curl + browser.

## 7. Do not

- Do not introduce new color schemes or fonts.
- Do not expose native file inputs.
- Do not store data outside `/data/local/tmp/linux/www/`.
- Do not break the existing card/button styling.

## 8. Cross-device input (mobile, iPad, PC)

- All 'add' flows (forms, buttons) must work on mobile, iPad, and desktop PC.
- Use responsive layouts (flex/grid) and avoid hover-only interactions.
- Touch targets >= 44px; inputs font-size >= 16px to avoid iOS zoom.
- Test add flows on narrow (<=480px), tablet, and desktop widths.
