#!/data/local/tmp/linux/bin/sh
L=/data/local/tmp/linux
CHATLOG="$L/www/chat.log"
MAXMSGS=50

# Read POST body if present
POSTDATA=""
if [ "$REQUEST_METHOD" = "POST" ]; then
    POSTDATA=$(cat)
fi

# Parse message from POST (format: nick=NAME&msg=TEXT)
if [ -n "$POSTDATA" ]; then
    nick=$(echo "$POSTDATA" | /data/local/tmp/linux/bin/busybox sed -n 's/.*nick=\([^&]*\).*/\1/p')
    msg=$(echo "$POSTDATA" | /data/local/tmp/linux/bin/busybox sed -n 's/.*msg=\([^&]*\).*/\1/p')
    # URL decode basic
    nick=$(/data/local/tmp/linux/bin/busybox echo "$nick" | /data/local/tmp/linux/bin/busybox sed 's/%20/ /g; s/+/ /g')
    msg=$(/data/local/tmp/linux/bin/busybox echo "$msg" | /data/local/tmp/linux/bin/busybox sed 's/%20/ /g; s/+/ /g; s/%3A/:/g; s/%2C/,/g')
    if [ -n "$msg" ]; then
        ts=$($L/bin/busybox date '+%H:%M:%S' 2>/dev/null || echo "--:--:--")
        if [ -z "$nick" ]; then nick="anon"; fi
        echo "[$ts] $nick: $msg" >> "$CHATLOG"
        # Trim log to last MAXMSGS lines
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
echo "<style>body{font-family:sans-serif;margin:0;background:#1a1a2e;color:#eee} .header{background:#16213e;padding:15px;text-align:center} .header h1{color:#4fc3f7;margin:0} .chat{max-width:700px;margin:20px auto;padding:0 20px} .msgs{background:#16213e;border-radius:8px;padding:15px;min-height:300px;max-height:500px;overflow-y:auto;margin-bottom:15px} .msg{padding:5px 0;border-bottom:1px solid #2a2a3e} .ts{color:#888;font-size:0.8em} .nick{color:#4fc3f7;font-weight:bold} .form{display:flex;gap:8px} input{padding:8px;border:1px solid #333;border-radius:4px;background:#0d1117;color:#eee;flex:1} button{background:#4fc3f7;color:#1a1a2e;border:none;padding:8px 16px;border-radius:4px;cursor:pointer;font-weight:bold}</style>"
echo "</head><body>"
echo "<div class='header'><h1>ZTE V9 Chat Room</h1><p style='color:#aaa;margin:5px 0'>Polling every 5s | $(/data/local/tmp/linux/bin/busybox wc -l < "$CHATLOG" 2>/dev/null || echo 0) messages</p></div>"
echo "<div class='chat'>"
echo "<div class='msgs'>"
if [ -f "$CHATLOG" ]; then
    /data/local/tmp/linux/bin/busybox tail -n 30 "$CHATLOG" | while IFS= read -r line; do
        echo "<div class='msg'>$line</div>"
    done
else
    echo "<div class='msg' style='color:#888'>No messages yet. Be the first!</div>"
fi
echo "</div>"
echo "<form method='POST' action='/cgi-bin/chat.cgi' class='form'>"
echo "<input name='nick' placeholder='Nickname' style='max-width:120px'>"
echo "<input name='msg' placeholder='Type a message...' autofocus>"
echo "<button type='submit'>Send</button>"
echo "</form>"
echo "<p style='color:#888;font-size:0.8em'>Messages are stored on the device. Max $MAXMSGS messages kept.</p>"
echo "</div></body></html>"