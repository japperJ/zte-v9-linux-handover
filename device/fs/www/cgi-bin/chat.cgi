#!/data/local/tmp/linux/bin/sh
L=/data/local/tmp/linux
DATA="${PAND_DATA:-$L/www}"
CHATLOG="$DATA/chat.log"
MAXMSGS=50

# Shared language detection (query param + cookie)
. /data/local/tmp/linux/www/cgi-bin/lang.inc

# Language strings
if [ "$lang" = "en" ]; then
    t_title="PandP Home server"
    t_sub="Chat"
    t_today="Today"
    t_yesterday="Yesterday"
    t_earlier="Earlier"
    t_new="New messages"
    t_auto="Auto-updating"
    t_nick_ph="Nickname"
    t_choose_nick="Choose a nickname"
    t_change_nick="Change nickname"
    t_nick_prompt="You need a nickname before you can chat."
    t_join="Join chat"
    t_save="Save"
    t_type_msg="Type a message..."
    t_send="Send"
    t_no_msgs="No messages yet. Be the first!"
    t_msgs_stored="Messages are stored on the device - max 50"
    t_nick_req="Set a nickname first"
    t_nick_empty="Nickname cannot be empty"
    t_send_fail="Send failed: "
    t_nick_err="Nickname required"
    t_back="Back"
else
    t_title="PandP Home server"
    t_sub="Chat"
    t_today="I dag"
    t_yesterday="I går"
    t_earlier="Tidligere"
    t_new="Nye beskeder"
    t_auto="Auto-opdaterer"
    t_nick_ph="Kaldenavn"
    t_choose_nick="Vælg et kaldenavn"
    t_change_nick="Skift kaldenavn"
    t_nick_prompt="Du skal vælge et kaldenavn før du kan chatte."
    t_join="Deltag i chat"
    t_save="Gem"
    t_type_msg="Skriv en besked..."
    t_send="Send"
    t_no_msgs="Ingen beskeder endnu. Vær den første!"
    t_msgs_stored="Beskeder gemmes på enheden - max 50"
    t_nick_req="Vælg et kaldenavn først"
    t_nick_empty="Kaldenavnet må ikke være tomt"
    t_send_fail="Afsendelse fejlede: "
    t_nick_err="Kaldenavn påkrævet"
    t_back="Tilbage"
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
    nick=$(/data/local/tmp/linux/bin/busybox printf '%s' "$nick" | /data/local/tmp/linux/bin/busybox tr '\r\n' '  ' | /data/local/tmp/linux/bin/busybox sed 's/|/-/g')
    msg=$(/data/local/tmp/linux/bin/busybox printf '%s' "$msg" | /data/local/tmp/linux/bin/busybox tr '\r\n' '  ' | /data/local/tmp/linux/bin/busybox sed 's/|/-/g')
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
            echo "<!DOCTYPE html><html lang='$lang'><head><title>$t_title</title><meta charset='UTF-8'></head><body style='background:#1a1a2e;color:#eee;font-family:sans-serif;padding:20px'><p style='color:#ff5252'>$t_nick_err</p><a href='/cgi-bin/chat.cgi?lang=$lang' style='color:#4fc3f7'>$t_back</a></body></html>"
        fi
        exit 0
    elif [ -n "$msg" ]; then
        ts=$($L/bin/busybox date '+%Y-%m-%d|%H:%M:%S' 2>/dev/null)
        [ -z "$ts" ] && ts="1970-01-01|00:00:00"
        echo "$ts|$nick|$msg" >> "$CHATLOG"
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
        /data/local/tmp/linux/bin/busybox tail -n $MAXMSGS "$CHATLOG"
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
echo "<link rel='stylesheet' href='/nav.css?v=16'>"
echo "<style>"
echo "*{box-sizing:border-box}"
echo "body{font-family:-apple-system,BlinkMacSystemFont,'Segoe UI',Roboto,sans-serif;margin:0;background:#1a1a2e;color:#eee;height:100vh;height:100dvh;display:flex;flex-direction:column;overflow:hidden}"
echo ".chat{flex:1;min-height:0;display:flex;flex-direction:column;width:100%;max-width:900px;margin:0 auto;padding:10px 12px 6px}"
echo ".chatcard{flex:1;min-height:0;display:flex;flex-direction:column;background:#16213e;border:1px solid #222a3d;border-radius:12px;overflow:hidden;position:relative}"
echo ".convo{display:none;align-items:center;gap:10px;padding:9px 12px;border-bottom:1px solid #222a3d;flex-shrink:0}"
echo ".cavatar{width:34px;height:34px;border-radius:50%;display:flex;align-items:center;justify-content:center;font-weight:800;color:#fff;font-size:14px;flex-shrink:0;background:#1f6feb}"
echo ".cmeta{flex:1;min-width:0}"
echo ".cname{font-size:14px;font-weight:700;color:#e6edf3;white-space:nowrap;overflow:hidden;text-overflow:ellipsis}"
echo ".cstatus{font-size:10.5px;color:#8b949e;display:flex;align-items:center;gap:5px;margin-top:1px}"
echo ".cstatus i{width:6px;height:6px;border-radius:50%;background:#3fb950;display:inline-block}"
echo ".cnick{background:#21262d;color:#8b949e;border:1px solid #30363d;border-radius:8px;padding:6px 10px;font-size:11px;cursor:pointer;min-height:34px}"
echo ".cnick:hover{background:#30363d;color:#e6edf3}"
echo ".msgs{flex:1;min-height:0;overflow-y:auto;padding:12px 12px 6px;background:#0f1526;-webkit-overflow-scrolling:touch}"
echo ".day{display:flex;justify-content:center;margin:10px 0 8px}"
echo ".day span{background:rgba(139,148,158,.14);color:#9aa4af;font-size:10.5px;padding:3px 10px;border-radius:10px}"
echo ".row{display:flex;align-items:flex-end;gap:8px;margin-top:2px}"
echo ".row.first{margin-top:10px}"
echo ".row.out{flex-direction:row-reverse}"
echo ".av{width:30px;height:30px;border-radius:50%;flex-shrink:0;display:flex;align-items:center;justify-content:center;color:#fff;font-size:12px;font-weight:800;margin-bottom:2px}"
echo ".col{display:flex;flex-direction:column;align-items:flex-start;max-width:78%;min-width:0}"
echo ".row.out .col{align-items:flex-end}"
echo ".nm{font-size:10.5px;font-weight:700;margin:0 0 3px 8px;max-width:100%;white-space:nowrap;overflow:hidden;text-overflow:ellipsis}"
echo ".bubble{display:flex;align-items:flex-end;gap:8px;padding:7px 10px 6px;border-radius:16px;font-size:14.5px;line-height:1.38;max-width:100%;word-wrap:break-word;overflow-wrap:break-word;background:#1b2740;border:1px solid #253152}"
echo ".row.in.last .bubble{border-bottom-left-radius:5px}"
echo ".row.out .bubble{background:#1f6feb;border-color:#1f6feb;color:#fff}"
echo ".row.out.last .bubble{border-bottom-right-radius:5px}"
echo ".txt{min-width:0;word-wrap:break-word;overflow-wrap:break-word;white-space:pre-wrap}"
echo ".tm{font-size:9.5px;opacity:.65;white-space:nowrap;flex-shrink:0;transform:translateY(1px)}"
echo ".row.out .tm{color:rgba(255,255,255,.85)}"
echo ".bubble a{color:#9fd4ff;text-decoration:underline}"
echo ".row.out .bubble a{color:#fff}"
echo ".empty{display:flex;flex-direction:column;align-items:center;justify-content:center;height:100%;min-height:180px;color:#8b949e;text-align:center;gap:10px;padding:20px;font-size:13px}"
echo ".empty svg{width:42px;height:42px;fill:none;stroke:#4b5563;stroke-width:1.6;stroke-linecap:round;stroke-linejoin:round}"
echo ".jump{position:absolute;right:14px;bottom:74px;background:#1f6feb;color:#fff;border:none;border-radius:18px;padding:7px 12px;font-size:11.5px;font-weight:700;cursor:pointer;display:none;box-shadow:0 4px 14px rgba(0,0,0,.4);z-index:3}"
echo ".composer{display:none;align-items:center;gap:8px;padding:9px 10px;border-top:1px solid #222a3d;flex-shrink:0;background:#16213e}"
echo ".composer input{flex:1;min-width:0;height:46px;border-radius:23px;border:1px solid #30363d;background:#0d1117;color:#e6edf3;font-size:16px;padding:0 16px;outline:none}"
echo ".composer input:focus{border-color:#4fc3f7}"
echo ".send{width:46px;height:46px;border-radius:50%;border:none;background:#1f6feb;color:#fff;display:flex;align-items:center;justify-content:center;cursor:pointer;flex-shrink:0}"
echo ".send:disabled{opacity:.4;cursor:default}"
echo ".send svg{width:20px;height:20px;fill:none;stroke:currentColor;stroke-width:2;stroke-linecap:round;stroke-linejoin:round}"
echo ".hint{text-align:center;color:#6b7280;font-size:10px;padding:6px 0 2px;margin:0;flex-shrink:0}"
echo ".overlay{position:fixed;top:0;left:0;right:0;bottom:0;background:rgba(5,8,15,.78);display:none;align-items:center;justify-content:center;padding:16px;z-index:50}"
echo ".ncard{background:#16213e;border:1px solid #2a3550;border-radius:16px;padding:24px 22px;width:360px;max-width:100%;text-align:center;box-shadow:0 20px 50px rgba(0,0,0,.5)}"
echo ".navatar{width:64px;height:64px;border-radius:50%;margin:0 auto 12px;display:flex;align-items:center;justify-content:center;font-size:26px;font-weight:800;color:#fff;background:#1f6feb}"
echo ".ncard h2{margin:0 0 6px;color:#e6edf3;font-size:17px}"
echo ".ncard p{margin:0 0 14px;color:#8b949e;font-size:12.5px;line-height:1.4}"
echo ".ncard input{width:100%;height:46px;border-radius:10px;border:1px solid #30363d;background:#0d1117;color:#e6edf3;font-size:16px;padding:0 14px;margin-bottom:12px;outline:none}"
echo ".ncard input:focus{border-color:#4fc3f7}"
echo ".ncard button{width:100%;height:46px;border:none;border-radius:10px;background:#1f6feb;color:#fff;font-size:15px;font-weight:700;cursor:pointer}"
echo "@media (max-width:480px){.chat{padding:8px 8px 4px}.col{max-width:84%}.bubble{font-size:14px}.hint{display:none}}"
echo "</style>"
echo "<script>if('serviceWorker' in navigator){navigator.serviceWorker.register('/sw.js').catch(function(){});}</script>"
echo "</head><body>"
echo "<div class='header'><h1>PandP Home</h1><p>$t_sub</p></div>"
echo "<script src='/nav.js?v=16'></script>"
echo "<div class='chat'>"
echo "<div class='chatcard'>"
echo "<div class='convo' id='convo'><span class='cavatar' id='cavatar'></span><div class='cmeta'><div class='cname' id='cname'></div><div class='cstatus'><i></i>$t_auto</div></div><button type='button' class='cnick' onclick='openNick()'>$t_change_nick</button></div>"
echo "<div class='msgs' id='msgs' role='log' aria-live='polite'></div>"
echo "<button type='button' class='jump' id='jump' onclick='jumpBottom()'>&#8595; $t_new</button>"
echo "<form class='composer' id='composer' onsubmit='return sendMsg()'>"
echo "<input type='text' id='msginput' maxlength='500' placeholder='$t_type_msg' autocomplete='off'>"
echo "<button type='submit' class='send' id='sendbtn' aria-label='$t_send' disabled><svg viewBox='0 0 24 24'><path d='M22 2L11 13'/><path d='M22 2l-7 20-4-9-9-4 20-7z'/></svg></button>"
echo "</form>"
echo "</div>"
echo "<p class='hint'>$t_msgs_stored</p>"
echo "</div>"
echo "<div class='overlay' id='overlay'>"
echo "<div class='ncard'>"
echo "<div class='navatar' id='nickavatar'>?</div>"
echo "<h2 id='nicktitle'>$t_choose_nick</h2>"
echo "<p>$t_nick_prompt</p>"
echo "<input id='nickinput' maxlength='24' placeholder='$t_nick_ph' oninput='previewNick()' onkeydown='if(event.key===\"Enter\"){event.preventDefault();saveNick();}'>"
echo "<button type='button' onclick='saveNick()' id='nickbtn'>$t_join</button>"
echo "</div></div>"
echo "<script>"
echo "var I18N={today:'$t_today',yesterday:'$t_yesterday',earlier:'$t_earlier',newmsgs:'$t_new',noMsgs:'$t_no_msgs',nickReq:'$t_nick_req',nickEmpty:'$t_nick_empty',sendFail:'$t_send_fail',save:'$t_save',choose:'$t_choose_nick',change:'$t_change_nick',join:'$t_join'};"
echo "var chatNick=localStorage.getItem('chatNick')||'';"
echo "var msgsEl=document.getElementById('msgs');"
echo "var lastRaw=null,atBottom=true;"
echo "function esc(s){var d=document.createElement('div');d.textContent=s;return d.innerHTML;}"
echo "function hue(s){var h=0;for(var i=0;i<s.length;i++){h=(h*31+s.charCodeAt(i))%360;}return h;}"
echo "function initial(s){return (s.charAt(0)||'?').toUpperCase();}"
echo "function linkify(t){return t.replace(/(https?:\/\/[^\s<]+)/g,function(u){var safe=u.replace(/\"/g,'%22').replace(/'/g,'%27');return '<a href=\"'+safe+'\" target=\"_blank\" rel=\"noopener\">'+u+'</a>';});}"
echo "function pad(n){return n<10?'0'+n:''+n;}"
echo "function ymd(d){return d.getFullYear()+'-'+pad(d.getMonth()+1)+'-'+pad(d.getDate());}"
echo "function todayStr(){return ymd(new Date());}"
echo "function dayLabel(ds){if(!ds)return I18N.earlier;var t=todayStr();if(ds===t)return I18N.today;var y=new Date();y.setDate(y.getDate()-1);if(ds===ymd(y))return I18N.yesterday;var p=ds.split('-');var m=['januar','februar','marts','april','maj','juni','juli','august','september','oktober','november','december'];var mi=parseInt(p[1],10)-1;return parseInt(p[2],10)+'. '+(m[mi]||'')+' '+p[0];}"
echo "function toMin(t){if(!t)return -1;var p=t.split(':');return parseInt(p[0],10)*60+parseInt(p[1],10);}"
echo "function parse(raw){var out=[],lines=(raw||'').split('\n');for(var i=0;i<lines.length;i++){var l=lines[i];if(!l)continue;if(l.charAt(0)==='['){var m=l.match(/^\[(\d\d:\d\d:\d\d)\]\s*([^:]+):\s?([\s\S]*)$/);if(m)out.push({date:'',time:m[1],nick:m[2],text:m[3]});}else{var p=l.split('|');if(p.length>=4)out.push({date:p[0],time:p[1],nick:p[2],text:p.slice(3).join('|')});}}return out;}"
echo "function sameGroup(a,b){if(!a||!b)return false;if(a.nick!==b.nick||a.date!==b.date)return false;var d=toMin(b.time)-toMin(a.time);return d>=0&&d<=5;}"
echo "function render(stick){var list=parse(lastRaw);if(!list.length){msgsEl.innerHTML='<div class=\"empty\"><svg viewBox=\"0 0 24 24\"><path d=\"M21 15a2 2 0 0 1-2 2H7l-4 4V5a2 2 0 0 1 2-2h14a2 2 0 0 1 2 2z\"/></svg><div>'+esc(I18N.noMsgs)+'</div></div>';return;}var html='',lastDay='##';for(var i=0;i<list.length;i++){var m=list[i],prev=i>0?list[i-1]:null,next=i<list.length-1?list[i+1]:null;var own=m.nick===chatNick;var gs=!sameGroup(prev,m),ge=!sameGroup(m,next);if(m.date!==lastDay){var dv=m.date?dayLabel(m.date):I18N.earlier;if(m.date||lastDay==='##'){html+='<div class=\"day\"><span>'+esc(dv)+'</span></div>';}lastDay=m.date;gs=true;}var cls='row '+(own?'out':'in')+(gs?' first':'')+(ge?' last':'');html+='<div class=\"'+cls+'\">';if(!own){var h=hue(m.nick);html+='<span class=\"av\"'+(gs?' style=\"background:hsl('+h+',45%,38%)\"':' style=\"visibility:hidden\"')+'>'+(gs?esc(initial(m.nick)):'')+'</span>';}html+='<div class=\"col\">';if(!own&&gs){var hh=hue(m.nick);html+='<div class=\"nm\" style=\"color:hsl('+hh+',62%,64%)\">'+esc(m.nick)+'</div>';}html+='<div class=\"bubble\"><span class=\"txt\">'+linkify(esc(m.text))+'</span>';if(m.time)html+='<span class=\"tm\">'+esc(m.time.substring(0,5))+'</span>';html+='</div></div></div>';}msgsEl.innerHTML=html;if(stick){msgsEl.scrollTop=msgsEl.scrollHeight;atBottom=true;hideJump();}}"
echo "function showJump(){document.getElementById('jump').style.display='block';}"
echo "function hideJump(){document.getElementById('jump').style.display='none';}"
echo "function jumpBottom(){msgsEl.scrollTop=msgsEl.scrollHeight;atBottom=true;hideJump();}"
echo "function load(force){fetch('/cgi-bin/chat.cgi?ajax=1&lang=$lang&t='+Date.now()).then(function(r){return r.text();}).then(function(t){if(t===lastRaw&&!force)return;var stick=force||atBottom;lastRaw=t;render(stick);if(!stick)showJump();}).catch(function(){});}"
echo "function updateSend(){var v=document.getElementById('msginput').value.trim();document.getElementById('sendbtn').disabled=(v.length===0);}"
echo "function pendingRow(text){var d=new Date();var tm=pad(d.getHours())+':'+pad(d.getMinutes());return '<div class=\"row out last\" id=\"pendingrow\"><div class=\"col\"><div class=\"bubble\"><span class=\"txt\">'+linkify(esc(text))+'</span><span class=\"tm\">'+tm+'</span></div></div></div>';}"
echo "function sendMsg(){var inp=document.getElementById('msginput');var v=inp.value.trim();if(!v)return false;if(!chatNick){alert(I18N.nickReq);return false;}inp.value='';updateSend();msgsEl.insertAdjacentHTML('beforeend',pendingRow(v));msgsEl.scrollTop=msgsEl.scrollHeight;hideJump();fetch('/cgi-bin/chat.cgi?ajax=1&lang=$lang&t='+Date.now(),{method:'POST',headers:{'Content-Type':'application/x-www-form-urlencoded'},body:'nick='+encodeURIComponent(chatNick)+'&msg='+encodeURIComponent(v)}).then(function(r){return r.text();}).then(function(){load(true);}).catch(function(e){var p=document.getElementById('pendingrow');if(p)p.parentNode.removeChild(p);inp.value=v;updateSend();alert(I18N.sendFail+e);});return false;}"
echo "function previewNick(){var v=document.getElementById('nickinput').value.trim();var a=document.getElementById('nickavatar');a.textContent=initial(v);a.style.background=v?'hsl('+hue(v)+',45%,40%)':'#1f6feb';}"
echo "function openNick(){document.getElementById('nicktitle').textContent=chatNick?I18N.change:I18N.choose;document.getElementById('nickbtn').textContent=chatNick?I18N.save:I18N.join;var i=document.getElementById('nickinput');i.value=chatNick;previewNick();document.getElementById('overlay').style.display='flex';setTimeout(function(){i.focus();},60);}"
echo "function saveNick(){var v=document.getElementById('nickinput').value.trim();if(!v){alert(I18N.nickEmpty);return;}chatNick=v;localStorage.setItem('chatNick',v);applyNick();document.getElementById('overlay').style.display='none';lastRaw=null;load(true);}"
echo "function applyNick(){var h=hue(chatNick);document.getElementById('cname').textContent=chatNick;var a=document.getElementById('cavatar');a.textContent=initial(chatNick);a.style.background='hsl('+h+',45%,40%)';document.getElementById('convo').style.display='flex';document.getElementById('composer').style.display='flex';document.getElementById('nickavatar').textContent=initial(chatNick);document.getElementById('nickavatar').style.background='hsl('+h+',45%,40%)';updateSend();}"
echo "window.onload=function(){msgsEl.addEventListener('scroll',function(){atBottom=(msgsEl.scrollHeight-msgsEl.scrollTop-msgsEl.clientHeight)<70;if(atBottom)hideJump();});document.getElementById('msginput').addEventListener('input',updateSend);if(chatNick){applyNick();}else{openNick();}load(true);setInterval(function(){if(!document.hidden)load(false);},3500);};"
echo "</script>"
echo "</body></html>"
