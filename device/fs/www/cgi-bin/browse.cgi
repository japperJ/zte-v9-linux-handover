#!/data/local/tmp/linux/bin/sh
echo "Content-type: text/html"
echo ""
echo "<html><head><title>ZTE V9 File Browser</title>"
echo "<style>body{font-family:sans-serif;margin:20px;background:#1a1a2e;color:#eee} a{color:#4fc3f7} table{border-collapse:collapse;width:100%} th,td{padding:8px;text-align:left;border-bottom:1px solid #333} tr:hover{background:#2a2a3e} h1{color:#4fc3f7}</style>"
echo "</head><body>"
echo "<h1>File Browser</h1>"
echo "<table><tr><th>Name</th><th>Size</th><th>Action</th></tr>"
L=/data/local/tmp/linux
for f in $L/www/*; do
    [ -f "$f" ] || continue
    name="${f##*/}"
    [ "$name" = "index.html" ] && continue
    [ "$name" = "browse.cgi" ] && continue
    [ "$name" = "upload.cgi" ] && continue
    size=$($L/bin/busybox wc -c < "$f" 2>/dev/null)
    size=${size%% *}
    echo "<tr><td>$name</td><td>$size bytes</td><td><a href=\"/$name\">Download</a></td></tr>"
done
echo "</table>"
echo "<hr><p><a href=\"/\">Home</a> | <a href=\"/cgi-bin/browse.cgi\">Refresh</a></p>"
echo "</body></html>"
