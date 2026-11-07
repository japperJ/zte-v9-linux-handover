#!/data/local/tmp/linux/bin/sh
L=/data/local/tmp/linux
GROC="$L/www/groceries.log"

urldecode() {
    input="$1"
    input=$(/data/local/tmp/linux/bin/busybox echo "$input" | /data/local/tmp/linux/bin/busybox tr '+' ' ')
    output=""
    i=1
    len=$(/data/local/tmp/linux/bin/busybox echo -n "$input" | /data/local/tmp/linux/bin/busybox wc -c)
    while [ $i -le $len ]; do
        c=$(/data/local/tmp/linux/bin/busybox echo -n "$input" | /data/local/tmp/linux/bin/busybox cut -c $i)
        if [ "$c" = "%" ]; then
            hex=$(/data/local/tmp/linux/bin/busybox echo -n "$input" | /data/local/tmp/linux/bin/busybox cut -c $((i+1))-$((i+2)))
            case "$hex" in
                [0-9A-Fa-f][0-9A-Fa-f])
                    dec=$(/data/local/tmp/linux/bin/busybox printf "%d" "0x$hex" 2>/dev/null)
                    if [ -n "$dec" ]; then
                        ch=$(/data/local/tmp/linux/bin/busybox awk "BEGIN{printf \"%c\", $dec}")
                        output="$output$ch"
                        i=$((i+3))
                        continue
                    fi
                    ;;
            esac
        fi
        output="$output$c"
        i=$((i+1))
    done
    /data/local/tmp/linux/bin/busybox echo -n "$output"
}

[ -f "$GROC" ] || /data/local/tmp/linux/bin/busybox touch "$GROC"

POSTDATA=""
if [ "$REQUEST_METHOD" = "POST" ]; then
    POSTDATA=$(cat)
fi

del_id=""
toggle_id=""
clear_done=0
sync_mode=0
case "$QUERY_STRING" in *delete=*) del_id="${QUERY_STRING#*delete=}"; del_id="${del_id%%&*}" ;; esac
case "$QUERY_STRING" in *toggle=*) toggle_id="${QUERY_STRING#*toggle=}"; toggle_id="${toggle_id%%&*}" ;; esac
case "$QUERY_STRING" in *clear=1*) clear_done=1 ;; esac
case "$QUERY_STRING" in *sync=1*) sync_mode=1 ;; esac

# AJAX sync endpoint
if [ "$sync_mode" = "1" ]; then
    if [ -n "$POSTDATA" ]; then
        raw_data=$(echo "$POSTDATA" | /data/local/tmp/linux/bin/busybox sed -n 's/^data=//p')
        urldecode "$raw_data" | /data/local/tmp/linux/bin/busybox tr ';' '\n' > "$GROC" 2>/dev/null
    fi
    echo "Content-type: text/plain; charset=UTF-8"
    echo "Access-Control-Allow-Origin: *"
    echo ""
    if [ -f "$GROC" ]; then
        /data/local/tmp/linux/bin/busybox cat "$GROC"
    fi
    exit 0
fi

if [ "$clear_done" = "1" ]; then
    tmp="$GROC.tmp"
    : > "$tmp"
    while IFS= read -r line; do
        [ -z "$line" ] && continue
        done="${line##*|}"
        if [ "$done" != "1" ]; then
            echo "$line" >> "$tmp"
        fi
    done < "$GROC"
    /data/local/tmp/linux/bin/busybox mv "$tmp" "$GROC" 2>/dev/null
elif [ -n "$del_id" ]; then
    tmp="$GROC.tmp"
    : > "$tmp"
    while IFS= read -r line; do
        [ -z "$line" ] && continue
        eid="${line%%|*}"
        if [ "$eid" != "$del_id" ]; then
            echo "$line" >> "$tmp"
        fi
    done < "$GROC"
    /data/local/tmp/linux/bin/busybox mv "$tmp" "$GROC" 2>/dev/null
elif [ -n "$toggle_id" ]; then
    tmp="$GROC.tmp"
    : > "$tmp"
    while IFS= read -r line; do
        [ -z "$line" ] && continue
        eid="${line%%|*}"
        if [ "$eid" = "$toggle_id" ]; then
            rest="${line#*|}"
            name="${rest%%|*}"
            rest2="${rest#*|}"
            qty="${rest2%%|*}"
            done="${rest2##*|}"
            if [ "$done" = "1" ]; then new=0; else new=1; fi
            echo "$eid|$name|$qty|$new" >> "$tmp"
        else
            echo "$line" >> "$tmp"
        fi
    done < "$GROC"
    /data/local/tmp/linux/bin/busybox mv "$tmp" "$GROC" 2>/dev/null
else
    has_item=0
    echo "$POSTDATA" | /data/local/tmp/linux/bin/busybox grep -q 'item=' && has_item=1
    if [ "$has_item" = "1" ]; then
        raw_item=$(echo "$POSTDATA" | /data/local/tmp/linux/bin/busybox sed -n 's/.*item=\([^&]*\).*/\1/p')
        raw_qty=$(echo "$POSTDATA" | /data/local/tmp/linux/bin/busybox sed -n 's/.*qty=\([^&]*\).*/\1/p')
        item=$(urldecode "$raw_item")
        qty=$(urldecode "$raw_qty")
        [ -z "$qty" ] && qty="1"
        if [ -n "$item" ]; then
            item=$(echo "$item" | /data/local/tmp/linux/bin/busybox sed 's/|/-/g')
            qty=$(echo "$qty" | /data/local/tmp/linux/bin/busybox sed 's/|/-/g')
            eid=$(/data/local/tmp/linux/bin/busybox date +%s 2>/dev/null)
            eid="${eid}_$(/data/local/tmp/linux/bin/busybox wc -l < "$GROC" 2>/dev/null)"
            eid=${eid%% *}
            echo "$eid|$item|$qty|0" >> "$GROC"
        fi
    fi
fi

IS_AJAX=0
echo "$QUERY_STRING" | /data/local/tmp/linux/bin/busybox grep -q "ajax=1" && IS_AJAX=1

if [ "$IS_AJAX" = "1" ]; then
    echo "Content-type: text/plain; charset=UTF-8"
    echo "Access-Control-Allow-Origin: *"
    echo ""
    if [ -f "$GROC" ]; then
        /data/local/tmp/linux/bin/busybox cat "$GROC"
    fi
    exit 0
fi

echo "Content-type: text/html; charset=UTF-8"
echo "Access-Control-Allow-Origin: *"
echo ""
echo "<!DOCTYPE html><html><head><title>PandP Home server</title>"
echo "<meta charset='UTF-8'>"
echo "<meta name='viewport' content='width=device-width, initial-scale=1.0, maximum-scale=1.0, user-scalable=no'>"
echo "<meta name='theme-color' content='#16213e'>"
echo "<link rel='manifest' href='/manifest.json'>"
echo "<link rel='apple-touch-icon' href='/icon-192.png'>"
echo "<style>body{font-family:-apple-system,BlinkMacSystemFont,Segoe UI,Roboto,sans-serif;margin:0;background:#0d1117;color:#e6edf3;min-height:100vh;display:flex;flex-direction:column} .header{background:#161b22;padding:12px 16px;text-align:center;border-bottom:1px solid #30363d;flex-shrink:0} .header h1{color:#58a6ff;margin:0;font-size:1.2em} .header p{color:#8b949e;margin:4px 0 0;font-size:0.8em} .wrap{max-width:900px;width:100%;margin:0 auto;display:flex;flex-direction:column;flex:1;min-height:0;padding:0 12px} .list{flex:1;overflow-y:auto;padding:12px 0;min-height:200px;-webkit-overflow-scrolling:touch} .item{display:flex;align-items:center;gap:10px;padding:10px 12px;border-bottom:1px solid #21262d;background:#161b22;margin-bottom:8px;border-radius:8px} .item.done{opacity:0.5} .item.done .iname{text-decoration:line-through;color:#8b949e} .cb{width:24px;height:24px;border-radius:6px;border:2px solid #30363d;background:#0d1117;cursor:pointer;display:flex;align-items:center;justify-content:center;color:#238636;font-weight:bold;flex-shrink:0} .item.done .cb{background:#238636;color:#fff;border-color:#238636} .iname{flex:1;word-wrap:break-word} .iqty{color:#8b949e;font-size:0.85em;min-width:40px;text-align:right} .del{background:#b71c1c;color:#fff;border:none;padding:6px 10px;border-radius:6px;cursor:pointer;font-size:0.8em;min-height:32px;flex-shrink:0} .formbox{background:#161b22;border:1px solid #30363d;border-radius:8px;padding:12px;margin:8px 0} .formbox input{width:100%;box-sizing:border-box;padding:10px 12px;border:1px solid #30363d;border-radius:8px;background:#0d1117;color:#e6edf3;font-size:16px;min-height:44px;margin-bottom:8px} .formbox .row{display:flex;gap:8px} .formbox button{background:#238636;color:#fff;border:none;padding:10px 16px;border-radius:8px;cursor:pointer;font-weight:bold;min-height:44px;flex:1} .formbox .clearbtn{background:#b71c1c} .homebtn{display:inline-block;background:#21262d;color:#58a6ff;padding:6px 16px;border-radius:6px;text-decoration:none;font-weight:bold;margin:8px 0;border:1px solid #30363d;min-height:36px;line-height:24px} .homebtn:hover{background:#30363d} .empty-msg{color:#8b949e;text-align:center;padding:40px 20px;font-style:italic} .syncstatus{font-size:0.75em;text-align:center;margin:4px 0;padding:6px;border-radius:4px} .sync-ok{color:#3fb950;background:rgba(63,185,80,0.1)} .sync-warn{color:#f0883e;background:rgba(240,136,62,0.1)} .conflict{background:#161b22;border:2px solid #f0883e;border-radius:8px;padding:16px;margin:12px 0;text-align:center} .conflict h3{color:#f0883e;margin-top:0} .conflict p{color:#8b949e;font-size:0.85em;margin:8px 0} .conflict .btns{display:flex;gap:8px;margin-top:12px} .conflict .btns button{flex:1;padding:10px;border:none;border-radius:6px;cursor:pointer;font-weight:bold;min-height:40px} .btn-server{background:#58a6ff;color:#fff} .btn-local{background:#238636;color:#fff} .btn-merge{background:#8b949e;color:#fff} @media (max-width:480px){.wrap{padding:0 8px}.formbox .row{flex-direction:column}.formbox button{width:100%}.homebtn{width:100%;text-align:center;box-sizing:border-box}.conflict .btns{flex-direction:column}}</style>"
echo "</head><body>"
echo "<div class='header'><h1>PandP Home server</h1><p>Grocery List</p></div>"
echo "<div style='text-align:center;margin:4px 0'><a href='/' class='homebtn'>Home</a></div>"
echo "<div class='wrap'>"
echo "<div class='syncstatus' id='syncstatus'>Loading...</div>"
echo "<div id='conflictbox' style='display:none'></div>"
echo "<div class='formbox'>"
echo "<input type='text' id='itemname' placeholder='Item name' autofocus>"
echo "<input type='text' id='itemqty' placeholder='Quantity (e.g. 2, 500g)'>"
echo "<div class='row'>"
echo "<button onclick='addItem()'>Add Item</button>"
echo "<button class='clearbtn' onclick='clearDone()'>Clear Purchased</button>"
echo "</div>"
echo "</div>"
echo "<div class='list' id='list'></div>"
echo "<p style='color:#8b949e;font-size:0.75em;text-align:center'>Tap checkbox to mark purchased. Works offline. Server is master.</p>"
echo "</div>"
echo "<script>"
echo "var items=[];"
echo "var STORAGE_KEY='pandp_groceries';"
echo "var SERVER_KEY='pandp_groceries_server';"
echo "var DIRTY_KEY='pandp_groceries_dirty';"
echo "var SERVER='/cgi-bin/grocery.cgi';"
echo "function parseItem(line){var p1=line.indexOf('|');var p2=line.indexOf('|',p1+1);var p3=line.indexOf('|',p2+1);if(p1<0||p2<0||p3<0)return null;return{id:line.substring(0,p1),name:line.substring(p1+1,p2),qty:line.substring(p2+1,p3),done:line.substring(p3+1)==='1'};}"
echo "function escHtml(s){var d=document.createElement('div');d.textContent=s;return d.innerHTML;}"
echo "function itemsToText(arr){return arr.map(function(it){return it.id+'|'+it.name+'|'+it.qty+'|'+(it.done?'1':'0');}).join('\n');}"
echo "function textToItems(txt){var arr=[];var lines=txt.split('\n');for(var i=0;i<lines.length;i++){var l=lines[i].trim();if(!l)continue;var p=parseItem(l);if(p)arr.push(p);}return arr;}"
echo "function loadLocal(){try{var d=localStorage.getItem(STORAGE_KEY);if(d){items=textToItems(d);}var dd=localStorage.getItem(DIRTY_KEY);return dd==='1';}catch(e){return false;}}"
echo "function saveLocal(){try{localStorage.setItem(STORAGE_KEY,itemsToText(items));}catch(e){}}"
echo "function loadServerSnapshot(){try{return localStorage.getItem(SERVER_KEY)||'';}catch(e){return '';}}"
echo "function saveServerSnapshot(txt){try{localStorage.setItem(SERVER_KEY,txt);}catch(e){}}"
echo "function setDirty(v){try{localStorage.setItem(DIRTY_KEY,v?'1':'0');}catch(e){}}"
echo "function isDirty(){try{return localStorage.getItem(DIRTY_KEY)==='1';}catch(e){return false;}}"
echo "function setSyncStatus(msg,cls){var el=document.getElementById('syncstatus');if(!el)return;el.textContent=msg;el.className='syncstatus '+(cls||'');}"
echo "function render(){var el=document.getElementById('list');if(!el)return;if(items.length===0){el.innerHTML=\"<div class='empty-msg'>No items. Add some above!</div>\";return;}var html='';for(var i=0;i<items.length;i++){var it=items[i];html+='<div class=\"item'+(it.done?' done':'')+'\">';html+='<div class=\"cb\" onclick=\"toggleItem(\\''+it.id+'\\')\">'+(it.done?'✓':'')+'</div>';html+='<div class=\"iname\">'+escHtml(it.name)+'</div>';html+='<div class=\"iqty\">'+escHtml(it.qty)+'</div>';html+='<button class=\"del\" onclick=\"delItem(\\''+it.id+'\\')\">x</button>';html+='</div>';}el.innerHTML=html;}"
echo "function addItem(){var n=document.getElementById('itemname').value.trim();var q=document.getElementById('itemqty').value.trim();if(!n){alert('Item name required');return;}var id='local_'+Date.now();items.push({id:id,name:n,qty:q||'1',done:false});saveLocal();render();setDirty(true);document.getElementById('itemname').value='';document.getElementById('itemqty').value='';document.getElementById('itemname').focus();syncToServer();}"
echo "function toggleItem(id){for(var i=0;i<items.length;i++){if(items[i].id===id){items[i].done=!items[i].done;break;}}saveLocal();render();setDirty(true);syncToServer();}"
echo "function delItem(id){items=items.filter(function(it){return it.id!==id;});saveLocal();render();setDirty(true);syncToServer();}"
echo "function clearDone(){if(!confirm('Remove all purchased items?'))return;items=items.filter(function(it){return !it.done;});saveLocal();render();setDirty(true);syncToServer();}"
echo "function syncToServer(){var data=itemsToText(items);fetch(SERVER+'?sync=1',{method:'POST',headers:{'Content-Type':'application/x-www-form-urlencoded'},body:'data='+encodeURIComponent(data)}).then(function(r){return r.text();}).then(function(t){saveServerSnapshot(t);setDirty(false);setSyncStatus('Synced with server','sync-ok');}).catch(function(e){setSyncStatus('Offline - changes saved locally','sync-warn');});}"
echo "function showConflict(serverItems){var box=document.getElementById('conflictbox');var serverText=serverItems.map(function(it){return it.id+'|'+it.name+'|'+it.qty+'|'+(it.done?'1':'0');}).join('\\n');var localText=itemsToText(items);var html='<div class=\"conflict\"><h3>Sync Conflict Detected</h3>';html+='<p>Server and local data differ. Choose which to keep:</p>';html+='<div class=\"btns\">';html+='<button class=\"btn-server\" onclick=\"resolveConflict(\\'server\\')\">Use Server ('+serverItems.length+' items)</button>';html+='<button class=\"btn-local\" onclick=\"resolveConflict(\\'local\\')\">Use Local ('+items.length+' items)</button>';html+='<button class=\"btn-merge\" onclick=\"resolveConflict(\\'merge\\')\">Merge Both</button>';html+='</div></div>';box.innerHTML=html;box.style.display='block';}"
echo "function resolveConflict(choice){var box=document.getElementById('conflictbox');box.style.display='none';if(choice==='server'){items=lastServerItems;saveLocal();render();saveServerSnapshot(itemsToText(items));setDirty(false);setSyncStatus('Resolved','sync-ok');}else if(choice==='local'){syncToServer();setDirty(false);setSyncStatus('Resolved','sync-ok');}else if(choice==='merge'){var serverItems=lastServerItems;var localIds=items.map(function(it){return it.id;});for(var i=0;i<serverItems.length;i++){if(localIds.indexOf(serverItems[i].id)<0){items.push(serverItems[i]);}}saveLocal();render();syncToServer();setDirty(false);setSyncStatus('Resolved','sync-ok');}}"
echo "var lastServerItems=[];"
echo "function loadFromServer(){fetch(SERVER+'?ajax=1').then(function(r){return r.text();}).then(function(t){var serverItems=textToItems(t);lastServerItems=serverItems;var serverText=t.trim();var localText=itemsToText(items).trim();var lastServer=loadServerSnapshot().trim();var dirty=isDirty();if(serverText!==localText&&dirty&&lastServer!==''&&serverText!==lastServer){showConflict(serverItems);}else if(serverText!==localText){if(dirty){syncToServer();}else{items=serverItems;saveLocal();render();saveServerSnapshot(serverText);setDirty(false);setSyncStatus('Synced with server','sync-ok');}}else{saveServerSnapshot(serverText);setDirty(false);setSyncStatus('Synced with server','sync-ok');}}).catch(function(e){setSyncStatus('Offline - using local data','sync-warn');});}"
echo "window.onload=function(){loadLocal();render();setSyncStatus('Loading...',false);loadFromServer();document.getElementById('itemname').addEventListener('keydown',function(e){if(e.key==='Enter')addItem();});}"
echo "</script>"
echo "<script>if('serviceWorker' in navigator){navigator.serviceWorker.register('/sw.js').catch(function(){});}</script>"
echo "</body></html>"
'@
[IO.File]::WriteAllText("$env:TEMP\v9-grocery.cgi", ($groceryCgi -replace "`r`n","`n"), (New-Object System.Text.UTF8Encoding($false)))
$adb = "C:\Users\jptrs\AppData\Local\Microsoft\WinGet\Packages\Google.PlatformTools_Microsoft.Winget.Source_8wekyb3d8bbwe\platform-tools\adb.exe"
& $adb -s V9_Telia push "$env:TEMP\v9-grocery.cgi" "/data/local/tmp/linux/www/cgi-bin/grocery.cgi" 2>&1
& $adb -s V9_Telia shell 'chmod 755 /data/local/tmp/linux/www/cgi-bin/grocery.cgi' 2>&1
Copy-Item "$env:TEMP\v9-grocery.cgi" "C:\Users\jptrs\zte-v9-linux-handover\device\fs\www\cgi-bin\grocery.cgi" -Force
Write-Host "deployed"