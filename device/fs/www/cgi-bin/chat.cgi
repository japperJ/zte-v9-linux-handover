#!/data/local/tmp/linux/bin/sh
L=/data/local/tmp/linux
CHATLOG="$L/www/chat.log"
MAXMSGS=50

# URL-decode function (handles %XX and + for spaces, preserves UTF-8)
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

# Read POST body if present
POSTDATA=""
if [ "$REQUEST_METHOD" = "POST" ]; then
    POSTDATA=$(cat)
fi

# Parse message and nick from POST
if [ -n "$POSTDATA" ]; then
    raw_nick=$(echo "$POSTDATA" | /data/local/tmp/linux/bin/busybox sed -n 's/.*nick=\([^&]*\).*/\1/p')
    raw_msg=$(echo "$POSTDATA" | /data/local/tmp/linux/bin/busybox sed -n 's/.*msg=\([^&]*\).*/\1/p')
    nick=$(urldecode "$raw_nick")
    msg=$(urldecode "$raw_msg")
    if [ -z "$nick" ] || [ "$nick" = "anon" ]; then
        if echo "$QUERY_STRING" | /data/local/tmp/linux/bin/busybox grep -q "ajax=1"; then
            echo "Content-type: text/plain; charset=UTF-8"
            echo "Access-Control-Allow-Origin: *"
            echo ""
            echo "ERROR: nickname required"
        else
            echo "Content-type: text/html; charset=UTF-8"
            echo "Access-Control-Allow-Origin: *"
            echo ""
            echo "<!DOCTYPE html><html><head><title>PandP Home server</title><meta charset='UTF-8'></head><body style='background:#1a1a2e;color:#eee;font-family:sans-serif;padding:20px'><p style='color:#ff5252'>Nickname required</p><a href='/cgi-bin/chat.cgi' style='color:#4fc3f7'>Back</a></body></html>"
        fi
        exit 0
    elif [ -n "$msg" ]; then
        ts=$($L/bin/busybox date '+%H:%M:%S' 2>/dev/null || echo "--:--:--")
        echo "[$ts] $nick: $msg" >> "$CHATLOG"
        $L/bin/busybox tail -n $MAXMSGS "$CHATLOG" > "$CHATLOG.tmp" 2>/dev/null
        $L/bin/busybox mv "$CHATLOG.tmp" "$CHATLOG" 2>/dev/null
    fi
    IS_AJAX=0
    echo "$QUERY_STRING" | /data/local/tmp/linux/bin/busybox grep -q "ajax=1" && IS_AJAX=1
    if [ "$IS_AJAX" = "1" ]; then
        echo "Content-type: text/plain; charset=UTF-8"
        echo "Access-Control-Allow-Origin: *"
        echo ""
        echo "OK"
        exit 0
    fi
fi

# Check ajax for GET
IS_AJAX=0
echo "$QUERY_STRING" | /data/local/tmp/linux/bin/busybox grep -q "ajax=1" && IS_AJAX=1

if [ "$IS_AJAX" = "1" ]; then
    echo "Content-type: text/plain; charset=UTF-8"
    echo "Access-Control-Allow-Origin: *"
    echo ""
    if [ -f "$CHATLOG" ]; then
        /data/local/tmp/linux/bin/busybox cat "$CHATLOG"
    fi
    exit 0
fi

# Full page
echo "Content-type: text/html; charset=UTF-8"
echo "Access-Control-Allow-Origin: *"
echo ""
echo "<!DOCTYPE html><html><head><title>PandP Home server</title>"
echo "<meta charset='UTF-8'>"
echo "<meta name='viewport' content='width=device-width, initial-scale=1.0, maximum-scale=1.0, user-scalable=no'>"
echo "<style>"
echo "body{font-family:-apple-system,BlinkMacSystemFont,Segoe UI,Roboto,sans-serif;margin:0;background:#0d1117;color:#e6edf3;min-height:100vh;display:flex;flex-direction:column}"
echo ".header{background:#161b22;padding:12px 16px;text-align:center;border-bottom:1px solid #30363d;flex-shrink:0}"
echo ".header h1{color:#58a6ff;margin:0;font-size:1.2em}"
echo ".header p{color:#8b949e;margin:4px 0 0;font-size:0.8em}"
echo ".chat{max-width:900px;width:100%;margin:0 auto;display:flex;flex-direction:column;flex:1;min-height:0;padding:0 12px}"
echo ".msgs{flex:1;overflow-y:auto;padding:12px 0;min-height:200px;-webkit-overflow-scrolling:touch}"
echo ".msg-row{display:flex;margin-bottom:8px;gap:8px;align-items:flex-end}"
echo ".msg-row.own{flex-direction:row-reverse}"
echo ".avatar{width:36px;height:36px;border-radius:50%;display:flex;align-items:center;justify-content:center;font-size:0.75em;font-weight:bold;color:#fff;flex-shrink:0;text-transform:uppercase}"
echo ".bubble{max-width:75%;padding:8px 12px;border-radius:12px;position:relative;word-wrap:break-word;line-height:1.4}"
echo ".bubble.own{background:#1f6feb;color:#fff;border-bottom-right-radius:4px}"
echo ".bubble.other{background:#21262d;color:#e6edf3;border-bottom-left-radius:4px}"
echo ".msg-name{font-size:0.75em;font-weight:bold;margin-bottom:2px;opacity:0.8}"
echo ".msg-time{font-size:0.65em;opacity:0.6;margin-top:2px;text-align:right}"
echo ".bubble.own .msg-time{text-align:right}"
echo ".bubble.other .msg-time{text-align:left}"
echo ".form-area{padding:12px 0;border-top:1px solid #30363d;flex-shrink:0}"
echo ".form{display:flex;gap:8px}"
echo ".form input[type=text]{flex:1;min-width:0;padding:12px 14px;border:1px solid #30363d;border-radius:8px;background:#0d1117;color:#e6edf3;font-size:16px;min-height:48px;outline:none}"
echo ".form input[type=text]:focus{border-color:#58a6ff}"
echo ".form button{background:#238636;color:#fff;border:none;padding:12px 20px;border-radius:8px;cursor:pointer;font-weight:bold;font-size:1em;min-height:48px;flex-shrink:0}"
echo ".form button:active{background:#2ea043}"
echo ".nickbar{background:#0d1117;padding:8px 12px;border-radius:8px;margin-bottom:8px;display:none;align-items:center;gap:8px;flex-wrap:wrap;border:1px solid #30363d}"
echo ".nickbar span{color:#58a6ff;font-weight:bold}"
echo ".nickbar button{background:#21262d;color:#e6edf3;border:1px solid #30363d;padding:4px 10px;border-radius:4px;cursor:pointer;font-size:0.8em;min-height:32px}"
echo ".overlay{position:fixed;top:0;left:0;width:100%;height:100%;background:rgba(0,0,0,0.9);display:none;align-items:center;justify-content:center;z-index:100;padding:16px;box-sizing:border-box}"
echo ".overlay-box{background:#161b22;padding:24px;border-radius:12px;text-align:center;max-width:360px;width:100%;border:1px solid #30363d}"
echo ".overlay-box h2{color:#58a6ff;margin-top:0;font-size:1.2em}"
echo ".overlay-box input{width:100%;box-sizing:border-box;margin:10px 0;padding:10px;border:1px solid #30363d;border-radius:6px;background:#0d1117;color:#e6edf3;font-size:1em}"
echo ".overlay-box button{width:100%;min-height:44px;font-size:1em;background:#238636;color:#fff;border:none;border-radius:6px;cursor:pointer;font-weight:bold}"
echo ".homebtn{display:inline-block;background:#21262d;color:#58a6ff;padding:6px 16px;border-radius:6px;text-decoration:none;font-weight:bold;margin:8px 0;border:1px solid #30363d;min-height:36px;line-height:24px}"
echo ".homebtn:hover{background:#30363d}"
echo ".empty-msg{color:#8b949e;text-align:center;padding:40px 20px;font-style:italic}"
echo "@media (max-width:480px){.chat{padding:0 8px}.msgs{min-height:150px}.form{flex-direction:column}.form button{width:100%}.header h1{font-size:1.1em}.homebtn{width:100%;text-align:center;box-sizing:border-box} input{font-size:16px}.bubble{max-width:85%}}"
echo "</style>"
echo "</head><body>"
echo "<div class='header'><h1>PandP Home server</h1><p>Chat Room</p></div>"
echo "<div style='text-align:center;margin:4px 0'><a href='/' class='homebtn'>Home</a></div>"
echo "<div class='chat'>"
echo "<div class='nickbar' id='nickbar' style='display:none'><span id='nickdisplay'></span><button onclick='changeNick()'>Change Nickname</button></div>"
echo "<div class='msgs' id='msgs'></div>"
echo "<div class='form-area'>"
echo "<form class='form' id='chatform' style='display:none' accept-charset='UTF-8' onsubmit='return submitMsg()'>"
echo "<input type='hidden' name='nick' id='nickfield'>"
echo "<input type='text' name='msg' id='msginput' placeholder='Type a message...' autofocus>"
echo "<button type='submit'>Send</button>"
echo "</form>"
echo "</div>"
echo "<p style='color:#8b949e;font-size:0.75em;text-align:center'>Messages stored on device. Auto-refreshes every 5s.</p>"
echo "</div>"
echo "<div class='overlay' id='overlay'>"
echo "<div class='overlay-box'>"
echo "<h2>Choose a Nickname</h2>"
echo "<p style='color:#8b949e'>You must set a nickname before chatting.</p>"
echo "<input id='nickinput' placeholder='Your nickname' autofocus onkeydown='if(event.key===\"Enter\")setNick()'>"
echo "<button onclick='setNick()'>Join Chat</button>"
echo "</div></div>"
echo "<script>"
# Color palette for avatars
echo "var COLORS=['#e91e63','#9c27b0','#673ab7','#3f51b5','#2196f3','#00bcd4','#009688','#4caf50','#ff9800','#ff5722','#795548','#607d8b'];"
echo "function hashStr(s){var h=0;for(var i=0;i<s.length;i++){h=((h<<5)-h)+s.charCodeAt(i);h=h&h;}return Math.abs(h);}"
echo "function colorFor(nick){return COLORS[hashStr(nick)%COLORS.length];}"
echo "function getInitial(nick){var n=nick.trim();if(n.length<=1)return n.toUpperCase();if(n.length===2)return n.toUpperCase();return (n.charAt(0)+n.charAt(n.length-1)).toUpperCase();}"
echo "var chatNick=localStorage.getItem('chatNick')||'';"
echo "function getNick(){return chatNick;}"
echo "function setNick(){var n=document.getElementById('nickinput').value.trim();if(!n){alert('Nickname cannot be empty');return;}chatNick=n;localStorage.setItem('chatNick',n);applyNick(n);}"
echo "function applyNick(n){document.getElementById('nickbar').style.display='flex';document.getElementById('nickdisplay').textContent=n;document.getElementById('nickfield').value=n;document.getElementById('chatform').style.display='flex';document.getElementById('overlay').style.display='none';var m=document.getElementById('msginput');if(m)m.focus();}"
echo "function changeNick(){var n=prompt('New nickname:',chatNick);if(n&&n.trim()){chatNick=n.trim();localStorage.setItem('chatNick',chatNick);applyNick(chatNick);renderMsgs(lastMsgs);}}"
echo "function escHtml(s){var d=document.createElement('div');d.textContent=s;return d.innerHTML;}"
echo "function parseMsg(line){var m=line.match(/^\[([^\]]+)\]\s*(.+?):\s*(.*)$/);if(!m)return null;return{time:m[1],nick:m[2],text:m[3]};}"
echo "var lastMsgs='';"
echo "function renderMsgs(raw){lastMsgs=raw;var el=document.getElementById('msgs');if(!el)return;var lines=raw.split('\n').filter(function(l){return l.trim().length>0;});if(lines.length===0){el.innerHTML=\"<div class='empty-msg'>No messages yet. Set a nickname and be the first!</div>\";return;}var html='';var prevNick='';for(var i=0;i<lines.length;i++){var p=parseMsg(lines[i]);if(!p){html+='<div class=\"msg\">'+escHtml(lines[i])+'</div>';continue;}var isOwn=(p.nick===chatNick);var color=colorFor(p.nick);var initial=getInitial(p.nick);var showName=(p.nick!==prevNick);html+='<div class=\"msg-row'+(isOwn?' own':'')+'\">';if(!isOwn){html+='<div class=\"avatar\" style=\"background:'+color+'\">'+escHtml(initial)+'</div>';}html+='<div class=\"bubble '+(isOwn?'own':'other')+'\">';if(!isOwn&&showName){html+='<div class=\"msg-name\" style=\"color:'+color+'\">'+escHtml(p.nick)+'</div>';}html+='<div>'+escHtml(p.text)+'</div>';html+='<div class=\"msg-time\">'+escHtml(p.time)+'</div>';html+='</div>';if(isOwn){html+='<div class=\"avatar\" style=\"background:'+color+'\">'+escHtml(initial)+'</div>';}html+='</div>';prevNick=p.nick;}el.innerHTML=html;el.scrollTop=el.scrollHeight;}"
echo "function submitMsg(){var m=document.getElementById('msginput').value.trim();if(!m)return false;var n=chatNick;if(!n){alert('Set a nickname first');return false;}fetch('/cgi-bin/chat.cgi?ajax=1',{method:'POST',headers:{'Content-Type':'application/x-www-form-urlencoded'},body:'nick='+encodeURIComponent(n)+'&msg='+encodeURIComponent(m)}).then(function(r){return r.text();}).then(function(t){document.getElementById('msginput').value='';refreshMsgs();}).catch(function(e){alert('Send failed: '+e);});return false;}"
echo "function refreshMsgs(){fetch('/cgi-bin/chat.cgi?ajax=1').then(function(r){return r.text();}).then(function(t){renderMsgs(t);}).catch(function(e){});}"
echo "window.onload=function(){if(chatNick){applyNick(chatNick);}else{document.getElementById('overlay').style.display='flex';document.getElementById('nickinput').focus();}refreshMsgs();setInterval(refreshMsgs,4000);}"
echo "</script>"
echo "</body></html>"
'@
[IO.File]::WriteAllText("$env:TEMP\v9-chat.cgi", ($chatCgi -replace "`r`n","`n"), (New-Object System.Text.UTF8Encoding($false)))
$adb = "C:\Users\jptrs\AppData\Local\Microsoft\WinGet\Packages\Google.PlatformTools_Microsoft.Winget.Source_8wekyb3d8bbwe\platform-tools\adb.exe"
& $adb -s V9_Telia push "$env:TEMP\v9-chat.cgi" "/data/local/tmp/linux/www/cgi-bin/chat.cgi" 2>&1
& $adb -s V9_Telia shell 'chmod 755 /data/local/tmp/linux/www/cgi-bin/chat.cgi' 2>&1
Copy-Item "$env:TEMP\v9-chat.cgi" "C:\Users\jptrs\zte-v9-linux-handover\device\fs\www\cgi-bin\chat.cgi" -Force
Write-Host "deployed"