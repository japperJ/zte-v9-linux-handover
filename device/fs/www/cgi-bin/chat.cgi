#!/data/local/tmp/linux/bin/sh
L=/data/local/tmp/linux
CHATLOG="$L/www/chat.log"
MAXMSGS=50

# Read POST body if present
POSTDATA=""
if [ "$REQUEST_METHOD" = "POST" ]; then
    POSTDATA=$(cat)
fi

# Parse message and nick from POST
if [ -n "$POSTDATA" ]; then
    nick=$(echo "$POSTDATA" | /data/local/tmp/linux/bin/busybox sed -n 's/.*nick=\([^&]*\).*/\1/p')
    msg=$(echo "$POSTDATA" | /data/local/tmp/linux/bin/busybox sed -n 's/.*msg=\([^&]*\).*/\1/p')
    # URL decode basic
    nick=$(/data/local/tmp/linux/bin/busybox echo "$nick" | /data/local/tmp/linux/bin/busybox sed 's/%20/ /g; s/+/ /g')
    msg=$(/data/local/tmp/linux/bin/busybox echo "$msg" | /data/local/tmp/linux/bin/busybox sed 's/%20/ /g; s/+/ /g; s/%3A/:/g; s/%2C/,/g')
    # Server-side: reject if no nick
    if [ -z "$nick" ] || [ "$nick" = "anon" ]; then
        # Still show page but with error
        NICK_ERROR=1
    elif [ -n "$msg" ]; then
        ts=$($L/bin/busybox date '+%H:%M:%S' 2>/dev/null || echo "--:--:--")
        echo "[$ts] $nick: $msg" >> "$CHATLOG"
        $L/bin/busybox tail -n $MAXMSGS "$CHATLOG" > "$CHATLOG.tmp" 2>/dev/null
        $L/bin/busybox mv "$CHATLOG.tmp" "$CHATLOG" 2>/dev/null
    fi
fi

# Output HTML
echo "Content-type: text/html"
echo "Access-Control-Allow-Origin: *"
echo ""
echo "<!DOCTYPE html><html><head><title>ZTE V9 Chat</title>"
echo "<meta http-equiv='refresh' content='5'>"
echo "<style>body{font-family:sans-serif;margin:0;background:#1a1a2e;color:#eee} .header{background:#16213e;padding:15px;text-align:center} .header h1{color:#4fc3f7;margin:0} .chat{max-width:700px;margin:20px auto;padding:0 20px} .msgs{background:#16213e;border-radius:8px;padding:15px;min-height:300px;max-height:500px;overflow-y:auto;margin-bottom:15px} .msg{padding:5px 0;border-bottom:1px solid #2a2a3e} .ts{color:#888;font-size:0.8em} .nick{color:#4fc3f7;font-weight:bold} .form{display:flex;gap:8px} input{padding:8px;border:1px solid #333;border-radius:4px;background:#0d1117;color:#eee;flex:1} button{background:#4fc3f7;color:#1a1a2e;border:none;padding:8px 16px;border-radius:4px;cursor:pointer;font-weight:bold} .nickbar{background:#0d1117;padding:10px;border-radius:8px;margin-bottom:15px;display:flex;align-items:center;gap:10px} .nickbar span{color:#4fc3f7;font-weight:bold} .nickbar button{background:#333;color:#eee;border:1px solid #555;padding:5px 10px;border-radius:4px;cursor:pointer;font-size:0.85em} .overlay{position:fixed;top:0;left:0;width:100%;height:100%;background:rgba(0,0,0,0.85);display:flex;align-items:center;justify-content:center;z-index:100} .overlay-box{background:#16213e;padding:30px;border-radius:12px;text-align:center;max-width:400px} .overlay-box h2{color:#4fc3f7;margin-top:0} .overlay-box input{width:100%;box-sizing:border-box;margin:10px 0} .overlay-box button{width:100%}</style>"
echo "</head><body>"
echo "<div class='header'><h1>ZTE V9 Chat Room</h1><p style='color:#aaa;margin:5px 0'>Polling every 5s | $(/data/local/tmp/linux/bin/busybox wc -l < "$CHATLOG" 2>/dev/null || echo 0) messages</p></div>"
echo "<div class='chat'>"
# Nickname bar (shown when nick is set)
echo "<div class='nickbar' id='nickbar' style='display:none'><span id='nickdisplay'></span><button onclick='changeNick()'>Change Nickname</button></div>"
# Messages
echo "<div class='msgs'>"
if [ -f "$CHATLOG" ]; then
    /data/local/tmp/linux/bin/busybox tail -n 30 "$CHATLOG" | while IFS= read -r line; do
        echo "<div class='msg'>$line</div>"
    done
else
    echo "<div class='msg' style='color:#888'>No messages yet. Set a nickname and be the first!</div>"
fi
echo "</div>"
# Chat form (hidden until nick is set)
echo "<form method='POST' action='/cgi-bin/chat.cgi' class='form' id='chatform' style='display:none' onsubmit='return submitMsg()'>"
echo "<input type='hidden' name='nick' id='nickfield'>"
echo "<input name='msg' id='msginput' placeholder='Type a message...' autofocus>"
echo "<button type='submit'>Send</button>"
echo "</form>"
echo "<p style='color:#888;font-size:0.8em'>Messages stored on device. Max $MAXMSGS messages kept.</p>"
echo "</div>"
# Nickname overlay
echo "<div class='overlay' id='overlay'>"
echo "<div class='overlay-box'>"
echo "<h2>Choose a Nickname</h2>"
echo "<p style='color:#aaa'>You must set a nickname before chatting.</p>"
echo "<input id='nickinput' placeholder='Your nickname' autofocus onkeydown='if(event.key===\"Enter\")setNick()'>"
echo "<button onclick='setNick()'>Join Chat</button>"
echo "</div></div>"
# JavaScript
echo "<script>"
echo "function getNick(){return localStorage.getItem('chatNick')||'';}"
echo "function setNick(){var n=document.getElementById('nickinput').value.trim();if(!n){alert('Nickname cannot be empty');return;}localStorage.setItem('chatNick',n);applyNick(n);}"
echo "function applyNick(n){document.getElementById('nickdisplay').textContent=n;document.getElementById('nickfield').value=n;document.getElementById('nickbar').style.display='flex';document.getElementById('chatform').style.display='flex';document.getElementById('overlay').style.display='none';}"
echo "function changeNick(){var n=prompt('New nickname:',getNick());if(n&&n.trim()){localStorage.setItem('chatNick',n.trim());applyNick(n.trim());}}"
echo "window.onload=function(){var n=getNick();if(n){applyNick(n);}else{document.getElementById('overlay').style.display='flex';document.getElementById('nickinput').focus();}}"
echo "function submitMsg(){var m=document.getElementById('msginput').value.trim();if(!m)return false;document.getElementById('nickfield').value=getNick();return true;}"
echo "</script>"
echo "</body></html>"