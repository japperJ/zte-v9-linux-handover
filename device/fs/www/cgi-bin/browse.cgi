#!/data/local/tmp/linux/bin/sh
echo "Content-type: text/html; charset=UTF-8"
echo "Access-Control-Allow-Origin: *"
echo ""
echo "<!DOCTYPE html><html><head><title>PandP Home server</title>"
echo "<meta charset='UTF-8'>"
echo "<meta name='viewport' content='width=device-width, initial-scale=1.0, maximum-scale=1.0, user-scalable=no'>"
echo "<meta name='theme-color' content='#16213e'>"
echo "<link rel='manifest' href='/manifest.json'>"
echo "<link rel='apple-touch-icon' href='/icon-192.png'>"
echo "<style>body{font-family:-apple-system,BlinkMacSystemFont,Segoe UI,Roboto,sans-serif;margin:0;background:#1a1a2e;color:#eee} .header{background:#16213e;padding:12px 16px;text-align:center} .header h1{color:#4fc3f7;margin:0;font-size:1.3em} .container{max-width:900px;margin:12px auto;padding:0 12px} table{border-collapse:collapse;width:100%;font-size:1em} th,td{padding:10px 8px;text-align:left;border-bottom:1px solid #333} th{color:#4fc3f7} tr:hover{background:#2a2a3e} a{color:#4fc3f7;text-decoration:none} a:hover{text-decoration:underline} .homebtn{display:inline-block;background:#4fc3f7;color:#1a1a2e;padding:10px 24px;border-radius:6px;text-decoration:none;font-weight:bold;margin:10px 0;min-height:48px;line-height:28px} .delbtn{background:#b71c1c;color:#fff;border:none;padding:6px 12px;border-radius:4px;cursor:pointer;font-size:0.85em;min-height:36px} .delbtn:hover{background:#d32f2f} @media (max-width:480px){.container{padding:0 8px}table{font-size:0.85em}th,td{padding:6px 4px} .homebtn{width:100%;text-align:center;box-sizing:border-box}}</style>"
echo "<script>if('serviceWorker' in navigator){navigator.serviceWorker.register('/sw.js').catch(function(){});}</script>"
echo "</head><body>"
echo "<div class='header'><h1>PandP Home server</h1></div>"
echo "<div style='text-align:center;margin:8px 0'><a href='/' class='homebtn'>Home</a></div>"
echo "<div class='container'>"
echo "<table id='filetable'><tr><th>Name</th><th>Size</th><th>Actions</th></tr>"
L=/data/local/tmp/linux
for f in $L/www/*; do
    [ -f "$f" ] || continue
    name="${f##*/}"
    [ "$name" = "index.html" ] && continue
    [ "$name" = "browse.cgi" ] && continue
    [ "$name" = "upload.cgi" ] && continue
    [ "$name" = "chat.cgi" ] && continue
    [ "$name" = "delete.cgi" ] && continue
    size=$($L/bin/busybox wc -c < "$f" 2>/dev/null)
    size=${size%% *}
    echo "<tr id='row-$name'><td>$name</td><td>$size B</td><td><a href='/$name'>Download</a> | <button class='delbtn' onclick=\"delFile('$name')\">Delete</button></td></tr>"
done
echo "</table>"
echo "<p id='status' style='text-align:center;color:#aaa'></p>"
echo "<hr><p style='text-align:center'><a href='/cgi-bin/browse.cgi'>Refresh</a></p>"
echo "</div>"
echo "<script>"
echo "function delFile(name){if(!confirm('Delete '+name+'?'))return;fetch('/cgi-bin/delete.cgi?file='+encodeURIComponent(name)).then(function(r){return r.text();}).then(function(t){var s=document.getElementById('status');s.textContent=t;s.style.color=t.indexOf('OK')===0?'#4caf50':'#ff5252';var row=document.getElementById('row-'+name);if(row&&t.indexOf('OK')===0)row.remove();}).catch(function(e){document.getElementById('status').textContent='Error: '+e;});}"
echo "</script>"
echo "</body></html>"