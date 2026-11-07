#!/data/local/tmp/linux/bin/sh
L=/data/local/tmp/linux
EVENTS="$L/www/events.log"

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

[ -f "$EVENTS" ] || /data/local/tmp/linux/bin/busybox touch "$EVENTS"

POSTDATA=""
if [ "$REQUEST_METHOD" = "POST" ]; then
    POSTDATA=$(cat)
fi

# delete by id
del_id=""
case "$QUERY_STRING" in
    *delete=*) del_id="${QUERY_STRING#*delete=}"; del_id="${del_id%%&*}" ;;
esac

if [ -n "$del_id" ]; then
    tmp="$EVENTS.tmp"
    : > "$tmp"
    while IFS= read -r line; do
        [ -z "$line" ] && continue
        eid="${line%%|*}"
        if [ "$eid" != "$del_id" ]; then
            echo "$line" >> "$tmp"
        fi
    done < "$EVENTS"
    /data/local/tmp/linux/bin/busybox mv "$tmp" "$EVENTS" 2>/dev/null
fi

# add event
has_date=0
echo "$POSTDATA" | /data/local/tmp/linux/bin/busybox grep -q 'date=' && has_date=1
if [ "$has_date" = "1" ] && [ -z "$del_id" ]; then
    raw_date=$(echo "$POSTDATA" | /data/local/tmp/linux/bin/busybox sed -n 's/.*date=\([^&]*\).*/\1/p')
    raw_title=$(echo "$POSTDATA" | /data/local/tmp/linux/bin/busybox sed -n 's/.*title=\([^&]*\).*/\1/p')
    evdate=$(urldecode "$raw_date")
    evtitle=$(urldecode "$raw_title")
    if [ -n "$evdate" ] && [ -n "$evtitle" ]; then
        eid=$(/data/local/tmp/linux/bin/busybox date +%s 2>/dev/null)
        eid="${eid}_$(/data/local/tmp/linux/bin/busybox wc -l < "$EVENTS" 2>/dev/null)"
        eid=${eid%% *}
        # sanitize pipes in title
        evtitle=$(echo "$evtitle" | /data/local/tmp/linux/bin/busybox sed 's/|/-/g')
        echo "$eid|$evdate|$evtitle" >> "$EVENTS"
    fi
fi

IS_AJAX=0
echo "$QUERY_STRING" | /data/local/tmp/linux/bin/busybox grep -q "ajax=1" && IS_AJAX=1

if [ "$IS_AJAX" = "1" ]; then
    echo "Content-type: text/plain; charset=UTF-8"
    echo "Access-Control-Allow-Origin: *"
    echo ""
    if [ -f "$EVENTS" ]; then
        /data/local/tmp/linux/bin/busybox cat "$EVENTS"
    fi
    exit 0
fi
echo "Content-type: text/html; charset=UTF-8"
echo "Access-Control-Allow-Origin: *"
echo ""
echo "<!DOCTYPE html><html><head><title>PandP Home server</title>"
echo "<meta charset='UTF-8'>"
echo "<meta name='viewport' content='width=device-width, initial-scale=1.0, maximum-scale=1.0, user-scalable=no'>"
echo "<link rel='manifest' href='/manifest.json'>"
echo "<meta name='theme-color' content='#16213e'>"
echo "<link rel='apple-touch-icon' href='/icon-192.png'>"
echo "<style>"
echo "body{font-family:-apple-system,BlinkMacSystemFont,Segoe UI,Roboto,sans-serif;margin:0;background:#0d1117;color:#e6edf3;min-height:100vh;display:flex;flex-direction:column}"
echo ".header{background:#161b22;padding:12px 16px;text-align:center;border-bottom:1px solid #30363d;flex-shrink:0}"
echo ".header h1{color:#58a6ff;margin:0;font-size:1.2em}"
echo ".header p{color:#8b949e;margin:4px 0 0;font-size:0.8em}"
echo ".wrap{max-width:900px;width:100%;margin:0 auto;display:flex;flex-direction:column;flex:1;min-height:0;padding:0 12px}"
echo ".nav{display:flex;align-items:center;justify-content:space-between;padding:12px 0;gap:8px}"
echo ".nav button{background:#21262d;color:#58a6ff;border:1px solid #30363d;padding:8px 14px;border-radius:6px;cursor:pointer;font-weight:bold;min-height:40px}"
echo ".nav .title{font-size:1.1em;font-weight:bold;color:#58a6ff}"
echo ".weekdays{display:grid;grid-template-columns:repeat(7,1fr);text-align:center;color:#8b949e;font-size:0.8em;padding:4px 0;border-bottom:1px solid #30363d}"
echo ".grid{display:grid;grid-template-columns:repeat(7,1fr);gap:4px;padding:8px 0}"
echo ".day{background:#161b22;border:1px solid #21262d;border-radius:8px;min-height:70px;padding:6px;cursor:pointer;position:relative;display:flex;flex-direction:column;gap:4px}"
echo ".day:hover{border-color:#58a6ff}"
echo ".day.other{opacity:0.35}"
echo ".day.today{border-color:#58a6ff;background:#1f2a44}"
echo ".daynum{font-size:0.85em;color:#8b949e;font-weight:bold}"
echo ".ev{background:#1f6feb;color:#fff;font-size:0.72em;padding:2px 4px;border-radius:4px;word-wrap:break-word;line-height:1.2}"
echo ".ev .del{float:right;cursor:pointer;color:#ff8a80;font-weight:bold;margin-left:4px}"
echo ".formbox{background:#161b22;border:1px solid #30363d;border-radius:8px;padding:12px;margin:8px 0;display:none}"
echo ".formbox input[type=text]{width:100%;box-sizing:border-box;padding:10px 12px;border:1px solid #30363d;border-radius:8px;background:#0d1117;color:#e6edf3;font-size:16px;min-height:44px;margin-bottom:8px}"
echo ".formbox .row{display:flex;gap:8px}"
echo ".formbox button{background:#238636;color:#fff;border:none;padding:10px 16px;border-radius:8px;cursor:pointer;font-weight:bold;min-height:44px;flex:1}"
echo ".formbox .cancel{background:#21262d;color:#e6edf3;border:1px solid #30363d}"
echo ".homebtn{display:inline-block;background:#21262d;color:#58a6ff;padding:6px 16px;border-radius:6px;text-decoration:none;font-weight:bold;margin:8px 0;border:1px solid #30363d;min-height:36px;line-height:24px}"
echo ".homebtn:hover{background:#30363d}"
echo ".hint{color:#8b949e;font-size:0.75em;text-align:center;padding:8px 0}"
echo "@media (max-width:480px){.wrap{padding:0 8px}.day{min-height:56px;padding:4px}.ev{font-size:0.65em}.nav .title{font-size:0.95em}}"
echo "</style>"
echo "</head><body>"
echo "<div class='header'><h1>PandP Home server</h1><p>Calendar</p></div>"
echo "<div style='text-align:center;margin:4px 0'><a href='/' class='homebtn'>Home</a></div>"
echo "<div class='wrap'>"
echo "<div class='nav'>"
echo "<button onclick='prevPeriod()'>&#9664; Prev</button>"
echo "<div class='title' id='viewtitle'></div>"
echo "<button onclick='nextPeriod()'>Next &#9654;</button>"
echo "</div>"
echo "<div style='display:flex;gap:6px;justify-content:center;padding-bottom:8px'>"
echo "<button onclick=\"setView('month')\" id='btnmonth' style='background:#1f6feb;color:#fff;border:none;padding:6px 12px;border-radius:6px;cursor:pointer;min-height:36px'>Month</button>"
echo "<button onclick=\"setView('week')\" id='btnweek' style='background:#21262d;color:#58a6ff;border:1px solid #30363d;padding:6px 12px;border-radius:6px;cursor:pointer;min-height:36px'>Week</button>"
echo "<button onclick=\"setView('day')\" id='btnday' style='background:#21262d;color:#58a6ff;border:1px solid #30363d;padding:6px 12px;border-radius:6px;cursor:pointer;min-height:36px'>Day</button>"
echo "</div>"
echo "<div class='weekdays'><div>Sun</div><div>Mon</div><div>Tue</div><div>Wed</div><div>Thu</div><div>Fri</div><div>Sat</div></div>"
echo "<div class='grid' id='grid'></div>"
echo "<div class='formbox' id='formbox'>"
echo "<div style='color:#58a6ff;font-weight:bold;margin-bottom:6px' id='formtitle'>Add event</div>"
echo "<input type='text' id='evdate' readonly>"
echo "<input type='text' id='evtext' placeholder='Event title' autofocus>"
echo "<div class='row'>"
echo "<button onclick='saveEvent()'>Add</button>"
echo "<button class='cancel' onclick='closeForm()'>Cancel</button>"
echo "</div>"
echo "</div>"
echo "<p class='hint'>Tap a day to add an event. Tap x on an event to delete.</p>"
echo "</div>"
echo "<script>"
echo "var events=[];"
echo "var cur=new Date();"
echo "function pad(n){return n<10?'0'+n:n;}"
echo "function ymd(d){return d.getFullYear()+'-'+pad(d.getMonth()+1)+'-'+pad(d.getDate());}"
echo "function loadEvents(){fetch('/cgi-bin/calendar.cgi?ajax=1').then(function(r){return r.text();}).then(function(t){events=[];var lines=t.split('\\n');for(var i=0;i<lines.length;i++){var l=lines[i].trim();if(!l)continue;var p1=l.indexOf('|');var p2=l.indexOf('|',p1+1);if(p1<0||p2<0)continue;events.push({id:l.substring(0,p1),date:l.substring(p1+1,p2),title:l.substring(p2+1)});}render();}).catch(function(e){});}"
echo "var view='month';"
echo "function setView(v){view=v;var ids=['btnmonth','btnweek','btnday'];var vals=['month','week','day'];for(var i=0;i<ids.length;i++){var b=document.getElementById(ids[i]);if(!b)continue;if(vals[i]===v){b.style.background='#1f6feb';b.style.color='#fff';b.style.border='none';}else{b.style.background='#21262d';b.style.color='#58a6ff';b.style.border='1px solid #30363d';}}render();}"
echo "function render(){if(view==='month')renderMonth();else if(view==='week')renderWeek();else renderDay();}"
echo "function renderMonth(){var y=cur.getFullYear(),m=cur.getMonth();document.getElementById('viewtitle').textContent=cur.toLocaleString(undefined,{month:'long',year:'numeric'});var first=new Date(y,m,1);var startDay=first.getDay();var daysInMonth=new Date(y,m+1,0).getDate();var grid=document.getElementById('grid');grid.innerHTML='';var today=ymd(new Date());for(var i=0;i<startDay;i++){var c=document.createElement('div');c.className='day other';grid.appendChild(c);}for(var d=1;d<=daysInMonth;d++){var date=new Date(y,m,d);var ds=ymd(date);var cell=document.createElement('div');cell.className='day'+(ds===today?' today':'');cell.innerHTML='<div class=\"daynum\">'+d+'</div>';var dayEvents=events.filter(function(e){return e.date===ds;});for(var j=0;j<dayEvents.length;j++){var ev=dayEvents[j];var el=document.createElement('div');el.className='ev';el.innerHTML=escHtml(ev.title)+'<span class=\"del\" onclick=\"delEvent(\\''+ev.id+'\\',event)\">x</span>';cell.appendChild(el);}cell.addEventListener('click',function(ds){return function(){openForm(ds);};}(ds));grid.appendChild(cell);}var total=startDay+daysInMonth;var rem=total%7;if(rem){for(var i=0;i<7-rem;i++){var c=document.createElement('div');c.className='day other';grid.appendChild(c);}}}"
echo "function renderWeek(){var start=new Date(cur);start.setDate(cur.getDate()-cur.getDay());var grid=document.getElementById('grid');grid.innerHTML='';var today=ymd(new Date());for(var i=0;i<7;i++){var d=new Date(start);d.setDate(start.getDate()+i);var ds=ymd(d);var cell=document.createElement('div');cell.className='day'+(ds===today?' today':'');cell.style.minHeight='120px';cell.innerHTML='<div class=\"daynum\">'+d.toLocaleString(undefined,{weekday:'short'})+' '+d.getDate()+'</div>';var dayEvents=events.filter(function(e){return e.date===ds;});for(var j=0;j<dayEvents.length;j++){var ev=dayEvents[j];var el=document.createElement('div');el.className='ev';el.innerHTML=escHtml(ev.title)+'<span class=\"del\" onclick=\"delEvent(\\''+ev.id+'\\',event)\">x</span>';cell.appendChild(el);}cell.addEventListener('click',function(ds){return function(){openForm(ds);};}(ds));grid.appendChild(cell);}document.getElementById('viewtitle').textContent='Week of '+start.toLocaleString(undefined,{month:'short',day:'numeric',year:'numeric'});}"
echo "function renderDay(){var ds=ymd(cur);var grid=document.getElementById('grid');grid.innerHTML='';var cell=document.createElement('div');cell.className='day today';cell.style.minHeight='220px';cell.style.gridColumn='1 / -1';cell.innerHTML='<div class=\"daynum\">'+cur.toLocaleString(undefined,{weekday:'long',month:'long',day:'numeric',year:'numeric'})+'</div>';var dayEvents=events.filter(function(e){return e.date===ds;});if(dayEvents.length===0){var e=document.createElement('div');e.className='empty-msg';e.textContent='No events. Tap to add.';cell.appendChild(e);}for(var j=0;j<dayEvents.length;j++){var ev=dayEvents[j];var el=document.createElement('div');el.className='ev';el.innerHTML=escHtml(ev.title)+'<span class=\"del\" onclick=\"delEvent(\\''+ev.id+'\\',event)\">x</span>';cell.appendChild(el);}cell.addEventListener('click',function(){openForm(ds);});grid.appendChild(cell);document.getElementById('viewtitle').textContent=cur.toLocaleString(undefined,{weekday:'long',month:'long',day:'numeric'});}"
echo "function escHtml(s){var d=document.createElement('div');d.textContent=s;return d.innerHTML;}"
echo "function openForm(ds){document.getElementById('evdate').value=ds;document.getElementById('evtext').value='';document.getElementById('formtitle').textContent='Add event on '+ds;document.getElementById('formbox').style.display='block';document.getElementById('evtext').focus();}"
echo "function closeForm(){document.getElementById('formbox').style.display='none';}"
echo "function saveEvent(){var ds=document.getElementById('evdate').value;var t=document.getElementById('evtext').value.trim();if(!t){alert('Title cannot be empty');return;}fetch('/cgi-bin/calendar.cgi?ajax=1',{method:'POST',headers:{'Content-Type':'application/x-www-form-urlencoded'},body:'date='+encodeURIComponent(ds)+'&title='+encodeURIComponent(t)}).then(function(r){return r.text();}).then(function(){closeForm();loadEvents();}).catch(function(e){alert('Save failed: '+e);});}"
echo "function delEvent(id,e){e.stopPropagation();if(!confirm('Delete this event?'))return;fetch('/cgi-bin/calendar.cgi?delete='+encodeURIComponent(id)+'&ajax=1').then(function(r){return r.text();}).then(function(){loadEvents();}).catch(function(e){});}"
echo "function prevPeriod(){if(view==='month')cur.setMonth(cur.getMonth()-1);else if(view==='week')cur.setDate(cur.getDate()-7);else cur.setDate(cur.getDate()-1);render();}"
echo "function nextPeriod(){if(view==='month')cur.setMonth(cur.getMonth()+1);else if(view==='week')cur.setDate(cur.getDate()+7);else cur.setDate(cur.getDate()+1);render();}"
echo "window.onload=function(){loadEvents();setView('month');}"
echo "</script>"
echo "<script>if('serviceWorker' in navigator){navigator.serviceWorker.register('/sw.js').catch(function(){});}</script>"
echo "</body></html>"