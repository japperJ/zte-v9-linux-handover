#!/data/local/tmp/linux/bin/sh
L=/data/local/tmp/linux
. /data/local/tmp/linux/www/cgi-bin/lang.inc
TASKS="$L/www/tasks.log"
MAXTASKS=200

if [ "$lang" = "en" ]; then
  t_sub="To-dos"
  t_ph="New task..."
  t_add="Add"
  t_hint="Tasks stored on device. Tap to toggle done."
  t_empty="No tasks yet. Add one above!"
  t_del="Delete"
  t_confirm="Delete this task?"
  t_add_fail="Add failed: "
else
  t_sub="Gøremål"
  t_ph="Ny opgave..."
  t_add="Tilføj"
  t_hint="Opgaver gemmes på enheden. Tryk for at markere."
  t_empty="Ingen opgaver endnu. Tilføj en ovenfor!"
  t_del="Slet"
  t_confirm="Slet denne opgave?"
  t_add_fail="Tilføjelse fejlede: "
fi

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

[ -f "$TASKS" ] || /data/local/tmp/linux/bin/busybox touch "$TASKS"

POSTDATA=""
if [ "$REQUEST_METHOD" = "POST" ]; then
    POSTDATA=$(cat)
fi

toggle_idx=""
delete_idx=""
case "$QUERY_STRING" in
    *toggle=*) toggle_idx="${QUERY_STRING#*toggle=}"; toggle_idx="${toggle_idx%%&*}" ;;
esac
case "$QUERY_STRING" in
    *delete=*) delete_idx="${QUERY_STRING#*delete=}"; delete_idx="${delete_idx%%&*}" ;;
esac

case "$toggle_idx" in
    ''|*[!0-9]*) toggle_idx="" ;;
esac
case "$delete_idx" in
    ''|*[!0-9]*) delete_idx="" ;;
esac
if [ -n "$toggle_idx" ]; then
    tmp="$TASKS.tmp"
    : > "$tmp"
    i=0
    while IFS= read -r line; do
        [ -z "$line" ] && continue
        i=$((i+1))
        if [ "$i" = "$toggle_idx" ]; then
            status="${line%%|*}"
            text="${line#*|}"
            if [ "$status" = "1" ]; then new=0; else new=1; fi
            echo "$new|$text" >> "$tmp"
        else
            echo "$line" >> "$tmp"
        fi
    done < "$TASKS"
    /data/local/tmp/linux/bin/busybox mv "$tmp" "$TASKS" 2>/dev/null
elif [ -n "$delete_idx" ]; then
    tmp="$TASKS.tmp"
    : > "$tmp"
    i=0
    while IFS= read -r line; do
        [ -z "$line" ] && continue
        i=$((i+1))
        if [ "$i" != "$delete_idx" ]; then
            echo "$line" >> "$tmp"
        fi
    done < "$TASKS"
    /data/local/tmp/linux/bin/busybox mv "$tmp" "$TASKS" 2>/dev/null
else
    has_task=0
    echo "$POSTDATA" | /data/local/tmp/linux/bin/busybox grep -q 'task=' && has_task=1
    if [ "$has_task" = "1" ]; then
        raw_task=$(echo "$POSTDATA" | /data/local/tmp/linux/bin/busybox sed -n 's/.*task=\([^&]*\).*/\1/p')
        task=$(urldecode "$raw_task")
        if [ -n "$task" ]; then
            echo "0|$task" >> "$TASKS"
        fi
    fi
fi

count=$(/data/local/tmp/linux/bin/busybox wc -l < "$TASKS" 2>/dev/null)
count=${count%% *}
if [ -n "$count" ] && [ "$count" -gt "$MAXTASKS" ] 2>/dev/null; then
    /data/local/tmp/linux/bin/busybox tail -n "$MAXTASKS" "$TASKS" > "$TASKS.tmp" 2>/dev/null
    /data/local/tmp/linux/bin/busybox mv "$TASKS.tmp" "$TASKS" 2>/dev/null
fi

IS_AJAX=0
echo "$QUERY_STRING" | /data/local/tmp/linux/bin/busybox grep -q "ajax=1" && IS_AJAX=1

if [ "$IS_AJAX" = "1" ]; then
    echo "Content-type: text/plain; charset=UTF-8"
    echo "Access-Control-Allow-Origin: *"
    echo ""
    if [ -f "$TASKS" ]; then
        /data/local/tmp/linux/bin/busybox cat "$TASKS"
    fi
    exit 0
fi
echo "Content-type: text/html; charset=UTF-8"
echo "Access-Control-Allow-Origin: *"
echo ""
echo "<!DOCTYPE html><html lang='$lang'><head><title>PandP Home server</title>"
echo "<meta charset='UTF-8'>"
echo "<meta name='viewport' content='width=device-width, initial-scale=1.0, maximum-scale=1.0, user-scalable=no'>"
echo "<link rel='manifest' href='/manifest.json'>"
echo "<meta name='theme-color' content='#16213e'>"
echo "<meta name='apple-mobile-web-app-capable' content='yes'>"
echo "<link rel='apple-touch-icon' href='/icon-192.png'>"
echo "<link rel='stylesheet' href='/nav.css?v=16'>"
echo "<style>"
echo "body{font-family:-apple-system,BlinkMacSystemFont,Segoe UI,Roboto,sans-serif;margin:0;background:#0d1117;color:#e6edf3;min-height:100vh;display:flex;flex-direction:column}"
echo ".header{background:#161b22;padding:12px 16px;text-align:center;border-bottom:1px solid #30363d;flex-shrink:0}"
echo ".header h1{color:#58a6ff;margin:0;font-size:1.2em}"
echo ".header p{color:#8b949e;margin:4px 0 0;font-size:0.8em}"
echo ".wrap{max-width:900px;width:100%;margin:0 auto;display:flex;flex-direction:column;flex:1;min-height:0;padding:0 12px}"
echo ".list{flex:1;overflow-y:auto;padding:12px 0;min-height:200px;-webkit-overflow-scrolling:touch}"
echo ".task{display:flex;align-items:center;gap:10px;padding:10px 12px;border-bottom:1px solid #21262d;background:#161b22;margin-bottom:8px;border-radius:8px}"
echo ".task.done{opacity:0.55}"
echo ".task.done .task-text{text-decoration:line-through;color:#8b949e}"
echo ".task-text{flex:1;word-wrap:break-word;line-height:1.4}"
echo ".cb{width:24px;height:24px;border-radius:6px;border:2px solid #30363d;background:#0d1117;cursor:pointer;display:flex;align-items:center;justify-content:center;color:#238636;font-weight:bold;flex-shrink:0}"
echo ".task.done .cb{background:#238636;color:#fff;border-color:#238636}"
echo ".del{background:#b71c1c;color:#fff;border:none;padding:6px 10px;border-radius:6px;cursor:pointer;font-size:0.8em;min-height:32px;flex-shrink:0}"
echo ".form-area{padding:12px 0;border-top:1px solid #30363d;flex-shrink:0}"
echo ".form{display:flex;gap:8px}"
echo ".form input[type=text]{flex:1;min-width:0;padding:12px 14px;border:1px solid #30363d;border-radius:8px;background:#0d1117;color:#e6edf3;font-size:16px;min-height:48px;outline:none}"
echo ".form input[type=text]:focus{border-color:#58a6ff}"
echo ".form button{background:#238636;color:#fff;border:none;padding:12px 20px;border-radius:8px;cursor:pointer;font-weight:bold;font-size:1em;min-height:48px;flex-shrink:0}"
echo ".homebtn{display:inline-block;background:#21262d;color:#58a6ff;padding:6px 16px;border-radius:6px;text-decoration:none;font-weight:bold;margin:8px 0;border:1px solid #30363d;min-height:36px;line-height:24px}"
echo ".homebtn:hover{background:#30363d}"
echo ".empty-msg{color:#8b949e;text-align:center;padding:40px 20px;font-style:italic}"
echo "@media (max-width:480px){.wrap{padding:0 8px}.form{flex-direction:column}.form button{width:100%}.header h1{font-size:1.1em}.homebtn{width:100%;text-align:center;box-sizing:border-box} input{font-size:16px}}"
echo "</style>"
echo "</head><body>"
echo "<div class='header'><h1>PandP Home</h1><p>$t_sub</p></div>"
echo "<script src='/nav.js?v=16'></script>"
echo "<div class='wrap'>"
echo "<div class='list' id='list'></div>"
echo "<div class='form-area'>"
echo "<form class='form' id='taskform' onsubmit='return addTask()'>"
echo "<input type='text' id='taskinput' placeholder='$t_ph' autofocus>"
echo "<button type='submit'>$t_add</button>"
echo "</form>"
echo "<p style='color:#8b949e;font-size:0.75em;text-align:center'>$t_hint</p>"
echo "</div>"
echo "</div>"
echo "<script>"
echo "function escHtml(s){var d=document.createElement('div');d.textContent=s;return d.innerHTML;}"
echo "function parseTask(line){var idx=line.indexOf('|');if(idx<0)return null;return{done:line.substring(0,idx)==='1',text:line.substring(idx+1)};}"
echo "var tasks=[];"
echo "function renderTasks(){var el=document.getElementById('list');if(!el)return;if(tasks.length===0){el.innerHTML=\"<div class='empty-msg'>$t_empty</div>\";return;}var html='';for(var i=0;i<tasks.length;i++){var t=tasks[i];html+='<div class=\"task'+(t.done?' done':'')+'\">';html+='<div class=\"cb\" onclick=\"toggleTask('+(i+1)+')\">'+(t.done?'✓':'')+'</div>';html+='<div class=\"task-text\">'+escHtml(t.text)+'</div>';html+='<button class=\"del\" onclick=\"deleteTask('+(i+1)+')\">$t_del</button>';html+='</div>';}el.innerHTML=html;}"
echo "function refreshTasks(){fetch('/cgi-bin/tasks.cgi?ajax=1').then(function(r){return r.text();}).then(function(t){tasks=[];var lines=t.split('\\n');for(var i=0;i<lines.length;i++){var l=lines[i].trim();if(!l)continue;var p=parseTask(l);if(p)tasks.push(p);}renderTasks();}).catch(function(e){});}"
echo "function addTask(){var m=document.getElementById('taskinput').value.trim();if(!m)return false;fetch('/cgi-bin/tasks.cgi?ajax=1',{method:'POST',headers:{'Content-Type':'application/x-www-form-urlencoded'},body:'task='+encodeURIComponent(m)}).then(function(r){return r.text();}).then(function(t){document.getElementById('taskinput').value='';refreshTasks();}).catch(function(e){alert('$t_add_fail'+e);});return false;}"
echo "function toggleTask(i){fetch('/cgi-bin/tasks.cgi?toggle='+i+'&ajax=1').then(function(r){return r.text();}).then(function(t){tasks=[];var lines=t.split('\\n');for(var j=0;j<lines.length;j++){var l=lines[j].trim();if(!l)continue;var p=parseTask(l);if(p)tasks.push(p);}renderTasks();}).catch(function(e){});}"
echo "function deleteTask(i){if(!confirm('$t_confirm'))return;fetch('/cgi-bin/tasks.cgi?delete='+i+'&ajax=1').then(function(r){return r.text();}).then(function(t){tasks=[];var lines=t.split('\\n');for(var j=0;j<lines.length;j++){var l=lines[j].trim();if(!l)continue;var p=parseTask(l);if(p)tasks.push(p);}renderTasks();}).catch(function(e){});}"
echo "window.onload=function(){refreshTasks();}"
echo "</script>"
echo "<script>if('serviceWorker' in navigator){navigator.serviceWorker.register('/sw.js').catch(function(){});}</script>"
echo "</body></html>"