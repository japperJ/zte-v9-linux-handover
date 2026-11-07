#!/data/local/tmp/linux/bin/sh
L=/data/local/tmp/linux
CHATLOG="$L/www/chat.log"
MAXMSGS=50

# Parse lang parameter (default: da)
lang="da"
case "$QUERY_STRING" in
  *lang=*) lang="${QUERY_STRING#*lang=}"; lang="${lang%%&*}" ;;
esac
case "$lang" in
  en|da) ;;
  *) lang="da" ;;
esac

# Language strings
if [ "$lang" = "en" ]; then
    t_title="PandP Home server"
    t_home="Home"
    t_choose_nick="Choose a Nickname"
    t_nick_prompt="You must set a nickname before chatting."
    t_join="Join Chat"
    t_change_nick="Change Nickname"
    t_type_msg="Type a message..."
    t_send="Send"
    t_no_msgs="No messages yet. Set a nickname and be the first!"
    t_msgs_stored="Messages stored on device. Max 50 messages kept."
    t_auto_updating="Auto-updating"
    t_lang_toggle="DA"
else
    t_title="PandP Home server"
    t_home="Hjem"
    t_choose_nick="Vælg et kaldenavn"
    t_nick_prompt="Du skal vælge et kaldenavn før du kan chatte."
    t_join="Deltag i chat"
    t_change_nick="Skift kaldenavn"
    t_type_msg="Skriv en besked..."
    t_send="Send"
    t_no_msgs="Ingen beskeder endnu. Vælg et kaldenavn og vær den første!"
    t_msgs_stored="Beskeder gemmes på enheden. Max 50 beskeder."
    t_auto_updating="Auto-opdatering"
    t_lang_toggle="EN"
fi

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
            echo "<!DOCTYPE html><html><head><title>$t_title</title><meta charset='UTF-8'></head><body style='background:#1a1a2e;color:#eee;font-family:sans-serif;padding:20px'><p style='color:#ff5252'>Nickname required</p><a href='/cgi-bin/chat.cgi?lang=$lang' style='color:#4fc3f7'>Back</a></body></html>"
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
    echo "Content-type: text/html; charset=UTF-8"
    echo "Access-Control-Allow-Origin: *"
    echo ""
    if [ -f "$CHATLOG" ]; then
        /data/local/tmp/linux/bin/busybox tail -n 30 "$CHATLOG" | while IFS= read -r line; do
            echo "<div class='msg'>$line</div>"
        done
    else
        echo "<div class='msg' style='color:#8b949e'>No messages yet. Set a nickname and be the first!</div>"
    fi
    exit 0
fi

# Full page
echo "Content-type: text/html; charset=UTF-8"
echo "Access-Control-Allow-Origin: *"
echo ""
echo "<!DOCTYPE html><html lang='$lang'><head><title>$t_title</title>"
echo "<meta charset='UTF-8'>"
echo "<meta name='viewport' content='width=device-width, initial-scale=1.0, maximum-scale=1.0, user-scalable=no'>"
echo "<meta name='theme-color' content='#16213e'>"
echo "<meta name='apple-mobile-web-app-capable' content='yes'>"
echo "<meta name='apple-mobile-web-app-status-bar-style' content='black-translucent'>"
echo "<link rel='manifest' href='/manifest.json'>"
echo "<link rel='apple-touch-icon' href='/icon-192.png'>"
echo "<style>body{font-family:-apple-system,BlinkMacSystemFont,Segoe UI,Roboto,sans-serif;margin:0;background:#1a1a2e;color:#eee} .header{background:#16213e;padding:12px 16px;text-align:center;position:relative} .header h1{color:#4fc3f7;margin:0;font-size:1.3em} .lang-toggle{position:absolute;top:10px;right:12px;background:#21262d;color:#4fc3f7;border:1px solid #30363d;padding:4px 10px;border-radius:6px;cursor:pointer;font-size:0.8em;text-decoration:none;min-height:32px;display:inline-flex;align-items:center} .lang-toggle:hover{background:#30363d} .chat{max-width:900px;margin:16px auto;padding:0 16px} .msgs{background:#16213e;border-radius:8px;padding:12px;min-height:300px;max-height:55vh;overflow-y:auto;margin-bottom:12px;-webkit-overflow-scrolling:touch} .msg{padding:6px 0;border-bottom:1px solid #2a2a3e;word-wrap:break-word} .ts{color:#888;font-size:0.8em} .nick{color:#4fc3f7;font-weight:bold} .form{display:flex;gap:8px} .form input[type=text]{flex:1;min-width:0;padding:12px 14px;border:1px solid #444;border-radius:6px;background:#0d1117;color:#eee;font-size:18px;min-height:48px} .form button{background:#4fc3f7;color:#1a1a2e;border:none;padding:12px 20px;border-radius:6px;cursor:pointer;font-weight:bold;font-size:1.05em;min-height:48px;flex-shrink:0} .nickbar{background:#0d1117;padding:10px;border-radius:8px;margin-bottom:12px;display:none;align-items:center;gap:10px;flex-wrap:wrap} .nickbar span{color:#4fc3f7;font-weight:bold} .nickbar button{background:#333;color:#eee;border:1px solid #555;padding:6px 10px;border-radius:4px;cursor:pointer;font-size:0.85em;min-height:36px} .overlay{position:fixed;top:0;left:0;width:100%;height:100%;background:rgba(0,0,0,0.9);display:none;align-items:center;justify-content:center;z-index:100;padding:16px;box-sizing:border-box} .overlay-box{background:#16213e;padding:24px;border-radius:12px;text-align:center;max-width:360px;width:100%} .overlay-box h2{color:#4fc3f7;margin-top:0;font-size:1.2em} .overlay-box input{width:100%;box-sizing:border-box;margin:10px 0;padding:10px;border:1px solid #333;border-radius:4px;background:#0d1117;color:#eee;font-size:1em} .overlay-box button{width:100%;min-height:44px;font-size:1em} .homebtn{display:inline-block;background:#4fc3f7;color:#1a1a2e;padding:8px 20px;border-radius:5px;text-decoration:none;font-weight:bold;margin:10px 0;min-height:44px;line-height:28px} @media (max-width:480px){.chat{padding:0 8px;margin:8px auto}.msgs{padding:8px;min-height:150px}.form{flex-direction:column}.form button{width:100%}.header h1{font-size:1.1em}.homebtn{width:100%;text-align:center;box-sizing:border-box} input{font-size:18px}}</style>"
echo "<script>if('serviceWorker' in navigator){navigator.serviceWorker.register('/sw.js').catch(function(){});}</script>"
echo "</head><body>"
echo "<div class='header'><h1>$t_title</h1><a href='/cgi-bin/chat.cgi?lang=$([ $lang = da ] && echo en || echo da)' class='lang-toggle'>$t_lang_toggle</a></div>"
echo "<div style='text-align:center;margin:8px 0'><a href='/' class='homebtn'>$t_home</a></div>"
echo "<div class='chat'>"
echo "<div class='nickbar' id='nickbar' style='display:none'><span id='nickdisplay'></span><button onclick='changeNick()'>$t_change_nick</button></div>"
echo "<div class='msgs' id='msgs'>"
if [ -f "$CHATLOG" ]; then
    /data/local/tmp/linux/bin/busybox tail -n 30 "$CHATLOG" | while IFS= read -r line; do
        echo "<div class='msg'>$line</div>"
    done
else
    echo "<div class='msg' style='color:#888'>$t_no_msgs</div>"
fi
echo "</div>"
echo "<form class='form' id='chatform' style='display:none' accept-charset='UTF-8' onsubmit='return submitMsg()'>"
echo "<input type='hidden' name='nick' id='nickfield'>"
echo "<input type='text' name='msg' id='msginput' placeholder='$t_type_msg' autofocus>"
echo "<button type='submit'>$t_send</button>"
echo "</form>"
echo "<p style='color:#888;font-size:0.8em'>$t_msgs_stored</p>"
echo "</div>"
echo "<div class='overlay' id='overlay'>"
echo "<div class='overlay-box'>"
echo "<h2>$t_choose_nick</h2>"
echo "<p style='color:#aaa'>$t_nick_prompt</p>"
echo "<input id='nickinput' placeholder='$t_type_msg' autofocus onkeydown='if(event.key===\"Enter\")setNick()'>"
echo "<button onclick='setNick()'>$t_join</button>"
echo "</div></div>"
echo "<script>"
echo "var chatNick=localStorage.getItem('chatNick')||'';"
echo "function getNick(){return chatNick;}"
echo "function setNick(){var n=document.getElementById('nickinput').value.trim();if(!n){alert('Nickname cannot be empty');return;}chatNick=n;localStorage.setItem('chatNick',n);applyNick(n);}"
echo "function applyNick(n){document.getElementById('nickdisplay').textContent=n;document.getElementById('nickfield').value=n;document.getElementById('nickbar').style.display='flex';document.getElementById('chatform').style.display='flex';document.getElementById('overlay').style.display='none';var m=document.getElementById('msginput');if(m)m.focus();}"
echo "function changeNick(){var n=prompt('New nickname:',chatNick);if(n&&n.trim()){chatNick=n.trim();localStorage.setItem('chatNick',chatNick);applyNick(chatNick);}}"
echo "function submitMsg(){var m=document.getElementById('msginput').value.trim();if(!m)return false;var n=chatNick;if(!n){alert('Set a nickname first');return false;}fetch('/cgi-bin/chat.cgi?ajax=1&lang=$lang',{method:'POST',headers:{'Content-Type':'application/x-www-form-urlencoded'},body:'nick='+encodeURIComponent(n)+'&msg='+encodeURIComponent(m)}).then(function(r){return r.text();}).then(function(t){document.getElementById('msginput').value='';refreshMsgs();}).catch(function(e){alert('Send failed: '+e);});return false;}"
echo "function refreshMsgs(){fetch('/cgi-bin/chat.cgi?ajax=1&lang=$lang').then(function(r){return r.text();}).then(function(t){var el=document.getElementById('msgs');if(el)el.innerHTML=t;}).catch(function(e){});}"
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