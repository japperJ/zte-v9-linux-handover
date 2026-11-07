#!/data/local/tmp/linux/bin/sh
L=/data/local/tmp/linux
CHATLOG="$L/www/chat.log"
MAXMSGS=50
AJAX=0

# Check for ajax param
case "$QUERY_STRING" in
  *ajax=1*) AJAX=1 ;;
esac

# Read POST body if present
POSTDATA=""
if [ "$REQUEST_METHOD" = "POST" ]; then
    POSTDATA=$(cat)
fi

# Parse message and nick from POST
if [ -n "$POSTDATA" ]; then
    nick=$(echo "$POSTDATA" | /data/local/tmp/linux/bin/busybox sed -n 's/.*nick=\([^&]*\).*/\1/p')
    msg=$(echo "$POSTDATA" | /data/local/tmp/linux/bin/busybox sed -n 's/.*msg=\([^&]*\).*/\1/p')
    nick=$(/data/local/tmp/linux/bin/busybox echo "$nick" | /data/local/tmp/linux/bin/busybox sed 's/%20/ /g; s/+/ /g')
    msg=$(/data/local/tmp/linux/bin/busybox echo "$msg" | /data/local/tmp/linux/bin/busybox sed 's/%20/ /g; s/+/ /g; s/%3A/:/g; s/%2C/,/g')
    if [ -z "$nick" ] || [ "$nick" = "anon" ]; then
        if [ "$AJAX" = "1" ]; then
            echo "Content-type: text/plain"
            echo "Access-Control-Allow-Origin: *"
            echo ""
            echo "ERROR: nickname required"
        else
            echo "Content-type: text/html"
            echo "Access-Control-Allow-Origin: *"
            echo ""
            echo "<!DOCTYPE html><html><body><p style='color:red'>Nickname required</p><a href='/cgi-bin/chat.cgi'>Back</a></body></html>"
        fi
        exit 0
    elif [ -n "$msg" ]; then
        ts=$($L/bin/busybox date '+%H:%M:%S' 2>/dev/null || echo "--:--:--")
        echo "[$ts] $nick: $msg" >> "$CHATLOG"
        $L/bin/busybox tail -n $MAXMSGS "$CHATLOG" > "$CHATLOG.tmp" 2>/dev/null
        $L/bin/busybox mv "$CHATLOG.tmp" "$CHATLOG" 2>/dev/null
    fi
    # For AJAX POST, return OK
    if [ "$AJAX" = "1" ]; then
        echo "Content-type: text/plain"
        echo "Access-Control-Allow-Origin: *"
        echo ""
        echo "OK"
        exit 0
    fi
fi

# AJAX GET: return just messages
if [ "$AJAX" = "1" ]; then
    echo "Content-type: text/html"
    echo "Access-Control-Allow-Origin: *"
    echo ""
    if [ -f "$CHATLOG" ]; then
        /data/local/tmp/linux/bin/busybox tail -n 30 "$CHATLOG" | while IFS= read -r line; do
            echo "<div class='msg'>$line</div>"
        done
    else
        echo "<div class='msg' style='color:#888'>No messages yet. Set a nickname and be the first!</div>"
    fi
    exit 0
fi

# Full page GET
echo "Content-type: text/html"
echo "Access-Control-Allow-Origin: *"
echo ""
echo "<!DOCTYPE html><html><head><title>ZTE V9 Chat</title>"
echo "<style>body{font-family:sans-serif;margin:0;background:#1a1a2e;color:#eee} .header{background:#16213e;padding:15px;text-align:center} .header h1{color:#4fc3f7;margin:0} .chat{max-width:700px;margin:20px auto;padding:0 20px} .msgs{background:#16213e;border-radius:8px;padding:15px;min-height:300px;max-height:500px;overflow-y:auto;margin-bottom:15px} .msg{padding:5px 0;border-bottom:1px solid #2a2a3e} .ts{color:#888;font-size:0.8em} .nick{color:#4fc3f7;font-weight:bold} .form{display:flex;gap:8px} input{padding:8px;border:1px solid #333;border-radius:4px;background:#0d1117;color:#eee;flex:1} button{background:#4fc3f7;color:#1a1a2e;border:none;padding:8px 16px;border-radius:4px;cursor:pointer;font-weight:bold} .nickbar{background:#0d1117;padding:10px;border-radius:8px;margin-bottom:15px;display:flex;align-items:center;gap:10px} .nickbar span{color:#4fc3f7;font-weight:bold} .nickbar button{background:#333;color:#eee;border:1px solid #555;padding:5px 10px;border-radius:4px;cursor:pointer;font-size:0.85em} .overlay{position:fixed;top:0;left:0;width:100%;height:100%;background:rgba(0,0,0,0.85);display:flex;align-items:center;justify-content:center;z-index:100} .overlay-box{background:#16213e;padding:30px;border-radius:12px;text-align:center;max-width:400px} .overlay-box h2{color:#4fc3f7;margin-top:0} .overlay-box input{width:100%;box-sizing:border-box;margin:10px 0} .overlay-box button{width:100%} .homebtn{display:inline-block;background:#4fc3f7;color:#1a1a2e;padding:8px 20px;border-radius:5px;text-decoration:none;font-weight:bold;margin:10px 0}</style>"
echo "</head><body>"
echo "<div class='header'><h1>ZTE V9 Chat Room</h1><p style='color:#aaa;margin:5px 0'>Auto-refreshing | $(/data/local/tmp/linux/bin/busybox wc -l < "$CHATLOG" 2>/dev/null || echo 0) messages</p></div>"
echo "<div style='text-align:center;margin:10px 0'><a href='/' class='homebtn'>Home</a></div>"
echo "<div class='chat'>"
echo "<div class='nickbar' id='nickbar' style='display:none'><span id='nickdisplay'></span><button onclick='changeNick()'>Change Nickname</button></div>"
echo "<div class='msgs' id='msgs'>"
if [ -f "$CHATLOG" ]; then
    /data/local/tmp/linux/bin/busybox tail -n 30 "$CHATLOG" | while IFS= read -r line; do
        echo "<div class='msg'>$line</div>"
    done
else
    echo "<div class='msg' style='color:#888'>No messages yet. Set a nickname and be the first!</div>"
fi
echo "</div>"
echo "<form class='form' id='chatform' style='display:none' onsubmit='return submitMsg()'>"
echo "<input type='hidden' name='nick' id='nickfield'>"
echo "<input name='msg' id='msginput' placeholder='Type a message...' autofocus>"
echo "<button type='submit'>Send</button>"
echo "</form>"
echo "<p style='color:#888;font-size:0.8em'>Messages stored on device. Max $MAXMSGS messages kept.</p>"
echo "</div>"
echo "<div class='overlay' id='overlay'>"
echo "<div class='overlay-box'>"
echo "<h2>Choose a Nickname</h2>"
echo "<p style='color:#aaa'>You must set a nickname before chatting.</p>"
echo "<input id='nickinput' placeholder='Your nickname' autofocus onkeydown='if(event.key===\"Enter\")setNick()'>"
echo "<button onclick='setNick()'>Join Chat</button>"
echo "</div></div>"
echo "<script>"
echo "var chatNick = localStorage.getItem('chatNick') || '';"
echo "function getNick(){return chatNick;}"
echo "function setNick(){var n=document.getElementById('nickinput').value.trim();if(!n){alert('Nickname cannot be empty');return;}chatNick=n;localStorage.setItem('chatNick',n);applyNick(n);}"
echo "function applyNick(n){document.getElementById('nickdisplay').textContent=n;document.getElementById('nickfield').value=n;document.getElementById('nickbar').style.display='flex';document.getElementById('chatform').style.display='flex';document.getElementById('overlay').style.display='none';}"
echo "function changeNick(){var n=prompt('New nickname:',chatNick);if(n&&n.trim()){chatNick=n.trim();localStorage.setItem('chatNick',chatNick);applyNick(chatNick);}}"
echo "function submitMsg(){var m=document.getElementById('msginput').value.trim();if(!m)return false;var n=chatNick;if(!n){alert('Set a nickname first');return false;}document.getElementById('nickfield').value=n;fetch('/cgi-bin/chat.cgi?ajax=1',{method:'POST',headers:{'Content-Type':'application/x-www-form-urlencoded'},body:'nick='+encodeURIComponent(n)+'&msg='+encodeURIComponent(m)}).then(function(r){return r.text();}).then(function(t){document.getElementById('msginput').value='';refreshMsgs();}).catch(function(e){alert('Send failed: '+e);});return false;}"
echo "function refreshMsgs(){fetch('/cgi-bin/chat.cgi?ajax=1').then(function(r){return r.text();}).then(function(t){document.getElementById('msgs').innerHTML=t;}).catch(function(e){});}"
echo "window.onload=function(){if(chatNick){applyNick(chatNick);}else{document.getElementById('overlay').style.display='flex';document.getElementById('nickinput').focus();}refreshMsgs();setInterval(refreshMsgs,5000);}"
echo "</script>"
echo "</body></html>"