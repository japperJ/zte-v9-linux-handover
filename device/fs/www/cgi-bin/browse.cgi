#!/data/local/tmp/linux/bin/sh
echo "Content-type: text/html"
echo ""
echo "<!DOCTYPE html><html><head><title>ZTE V9 File Browser</title>"
echo "<meta name='viewport' content='width=device-width, initial-scale=1.0, maximum-scale=1.0, user-scalable=no'>"
echo "<style>body{font-family:-apple-system,BlinkMacSystemFont,Segoe UI,Roboto,sans-serif;margin:0;background:#1a1a2e;color:#eee} .header{background:#16213e;padding:12px 16px;text-align:center} .header h1{color:#4fc3f7;margin:0;font-size:1.3em} .container{max-width:800px;margin:12px auto;padding:0 12px} table{border-collapse:collapse;width:100%;font-size:0.9em} th,td{padding:8px 6px;text-align:left;border-bottom:1px solid #333} th{color:#4fc3f7} tr:hover{background:#2a2a3e} a{color:#4fc3f7;text-decoration:none} a:hover{text-decoration:underline} .homebtn{display:inline-block;background:#4fc3f7;color:#1a1a2e;padding:8px 20px;border-radius:5px;text-decoration:none;font-weight:bold;margin:10px 0;min-height:44px;line-height:28px} @media (max-width:480px){.container{padding:0 8px}table{font-size:0.85em}th,td{padding:6px 4px} .homebtn{width:100%;text-align:center;box-sizing:border-box}}</style>"
echo "</head><body>"
echo "<div class='header'><h1>File Browser</h1></div>"
echo "<div style='text-align:center;margin:8px 0'><a href='/' class='homebtn'>Home</a></div>"
echo "<div class='container'>"
echo "<table><tr><th>Name</th><th>Size</th><th>Action</th></tr>"
L=/data/local/tmp/linux
for f in $L/www/*; do
    [ -f "$f" ] || continue
    name="${f##*/}"
    [ "$name" = "index.html" ] && continue
    [ "$name" = "browse.cgi" ] && continue
    [ "$name" = "upload.cgi" ] && continue
    [ "$name" = "chat.cgi" ] && continue
    size=$($L/bin/busybox wc -c < "$f" 2>/dev/null)
    size=${size%% *}
    echo "<tr><td>$name</td><td>$size B</td><td><a href=\"/$name\">Download</a></td></tr>"
done
echo "</table>"
echo "<hr><p style='text-align:center'><a href='/cgi-bin/browse.cgi'>Refresh</a></p>"
echo "</div></body></html>"