#!/data/local/tmp/linux/bin/sh
L=/data/local/tmp/linux
. /data/local/tmp/linux/www/cgi-bin/lang.inc

if [ "$lang" = "en" ]; then
  t_sub="Calendar"
  t_prev="Prev"
  t_next="Next"
  t_month="Month"
  t_week="Week"
  t_day="Day"
  t_todo="Todo"
  t_wd1="Sun"; t_wd2="Mon"; t_wd3="Tue"; t_wd4="Wed"; t_wd5="Thu"; t_wd6="Fri"; t_wd7="Sat"
  t_add_event="Add event"
  t_edit_event="Edit event"
  t_add_on="Add event on"
  t_ev_title="Event title"
  t_start_ph="Start time (HH:MM)"
  t_end_ph="End time (HH:MM)"
  t_date_ph="Date (YYYY-MM-DD)"
  t_until_ph="Repeat until (YYYY-MM-DD, optional)"
  t_fullday="Full day"
  t_no_repeat="No repeat"
  t_daily="Daily"
  t_weekly="Weekly"
  t_monthly="Monthly"
  t_yearly="Yearly"
  t_save="Save"
  t_add="Add"
  t_delete="Delete"
  t_cancel="Cancel"
  t_hint="Tap a day to add an event. Tap x on an event to delete."
  t_upcoming="Upcoming (next 30 days)"
  t_no_upcoming="No upcoming events."
  t_no_events="No events. Tap to add."
  t_week_of="Week of "
  t_title_req="Title cannot be empty"
  t_save_fail="Save failed: "
  t_date_title_req="Date and title required"
  t_del_confirm="Delete this event?"
else
  t_sub="Kalender"
  t_prev="Forrige"
  t_next="Næste"
  t_month="Måned"
  t_week="Uge"
  t_day="Dag"
  t_todo="Opgaver"
  t_wd1="Søn"; t_wd2="Man"; t_wd3="Tir"; t_wd4="Ons"; t_wd5="Tor"; t_wd6="Fre"; t_wd7="Lør"
  t_add_event="Tilføj begivenhed"
  t_edit_event="Rediger begivenhed"
  t_add_on="Tilføj begivenhed på"
  t_ev_title="Begivenhedstitel"
  t_start_ph="Starttid (TT:MM)"
  t_end_ph="Sluttid (TT:MM)"
  t_date_ph="Dato (ÅÅÅÅ-MM-DD)"
  t_until_ph="Gentag indtil (ÅÅÅÅ-MM-DD, valgfri)"
  t_fullday="Hele dagen"
  t_no_repeat="Ingen gentagelse"
  t_daily="Dagligt"
  t_weekly="Ugentligt"
  t_monthly="Månedligt"
  t_yearly="Årligt"
  t_save="Gem"
  t_add="Tilføj"
  t_delete="Slet"
  t_cancel="Annuller"
  t_hint="Tryk på en dag for at tilføje en begivenhed. Tryk på x for at slette."
  t_upcoming="Kommende (næste 30 dage)"
  t_no_upcoming="Ingen kommende begivenheder."
  t_no_events="Ingen begivenheder. Tryk for at tilføje."
  t_week_of="Uge fra "
  t_title_req="Titlen må ikke være tom"
  t_save_fail="Gem fejlede: "
  t_date_title_req="Dato og titel påkrævet"
  t_del_confirm="Slet denne begivenhed?"
fi
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
edit_id=""
raw_edit=$(echo "$POSTDATA" | /data/local/tmp/linux/bin/busybox sed -n 's/.*edit=\([^&]*\).*/\1/p')
if [ -n "$raw_edit" ]; then
    edit_id=$(urldecode "$raw_edit")
fi
if [ -n "$edit_id" ]; then
    raw_date=$(echo "$POSTDATA" | /data/local/tmp/linux/bin/busybox sed -n 's/.*date=\([^&]*\).*/\1/p')
    raw_title=$(echo "$POSTDATA" | /data/local/tmp/linux/bin/busybox sed -n 's/.*title=\([^&]*\).*/\1/p')
    raw_recur=$(echo "$POSTDATA" | /data/local/tmp/linux/bin/busybox sed -n 's/.*recur=\([^&]*\).*/\1/p')
    raw_until=$(echo "$POSTDATA" | /data/local/tmp/linux/bin/busybox sed -n 's/.*until=\([^&]*\).*/\1/p')
    raw_start=$(echo "$POSTDATA" | /data/local/tmp/linux/bin/busybox sed -n 's/.*start=\([^&]*\).*/\1/p')
    raw_end=$(echo "$POSTDATA" | /data/local/tmp/linux/bin/busybox sed -n 's/.*end=\([^&]*\).*/\1/p')
    raw_fd=$(echo "$POSTDATA" | /data/local/tmp/linux/bin/busybox sed -n 's/.*fullday=\([^&]*\).*/\1/p')
    evdate=$(urldecode "$raw_date")
    evtitle=$(urldecode "$raw_title")
    evrecur=$(urldecode "$raw_recur")
    evuntil=$(urldecode "$raw_until")
    evstart=$(urldecode "$raw_start")
    evend=$(urldecode "$raw_end")
    evfd=$(urldecode "$raw_fd")
    [ -z "$evrecur" ] && evrecur="none"
    [ -z "$evfd" ] && evfd="0"
    if [ -n "$evdate" ] && [ -n "$evtitle" ]; then
        evtitle=$(echo "$evtitle" | /data/local/tmp/linux/bin/busybox sed 's/|/-/g')
        tmp="$EVENTS.tmp"
        : > "$tmp"
        while IFS= read -r line; do
            [ -z "$line" ] && continue
            eid="${line%%|*}"
            if [ "$eid" = "$edit_id" ]; then
                echo "$eid|$evdate|$evtitle|$evrecur|$evuntil|$evstart|$evend|$evfd" >> "$tmp"
            else
                echo "$line" >> "$tmp"
            fi
        done < "$EVENTS"
        /data/local/tmp/linux/bin/busybox mv "$tmp" "$EVENTS" 2>/dev/null
    fi
fi
has_date=0
echo "$POSTDATA" | /data/local/tmp/linux/bin/busybox grep -q 'date=' && has_date=1
if [ "$has_date" = "1" ] && [ -z "$del_id" ] && [ -z "$edit_id" ]; then
    raw_date=$(echo "$POSTDATA" | /data/local/tmp/linux/bin/busybox sed -n 's/.*date=\([^&]*\).*/\1/p')
    raw_title=$(echo "$POSTDATA" | /data/local/tmp/linux/bin/busybox sed -n 's/.*title=\([^&]*\).*/\1/p')
    raw_recur=$(echo "$POSTDATA" | /data/local/tmp/linux/bin/busybox sed -n 's/.*recur=\([^&]*\).*/\1/p')
    raw_until=$(echo "$POSTDATA" | /data/local/tmp/linux/bin/busybox sed -n 's/.*until=\([^&]*\).*/\1/p')
    raw_start=$(echo "$POSTDATA" | /data/local/tmp/linux/bin/busybox sed -n 's/.*start=\([^&]*\).*/\1/p')
    raw_end=$(echo "$POSTDATA" | /data/local/tmp/linux/bin/busybox sed -n 's/.*end=\([^&]*\).*/\1/p')
    raw_fd=$(echo "$POSTDATA" | /data/local/tmp/linux/bin/busybox sed -n 's/.*fullday=\([^&]*\).*/\1/p')
    evdate=$(urldecode "$raw_date")
    evtitle=$(urldecode "$raw_title")
    evrecur=$(urldecode "$raw_recur")
    evuntil=$(urldecode "$raw_until")
    evstart=$(urldecode "$raw_start")
    evend=$(urldecode "$raw_end")
    evfd=$(urldecode "$raw_fd")
    [ -z "$evrecur" ] && evrecur="none"
    [ -z "$evfd" ] && evfd="0"
    if [ -n "$evdate" ] && [ -n "$evtitle" ]; then
        eid=$(/data/local/tmp/linux/bin/busybox date +%s 2>/dev/null)
        eid="${eid}_$(/data/local/tmp/linux/bin/busybox wc -l < "$EVENTS" 2>/dev/null)"
        eid=${eid%% *}
        # sanitize pipes in title
        evtitle=$(echo "$evtitle" | /data/local/tmp/linux/bin/busybox sed 's/|/-/g')
        echo "$eid|$evdate|$evtitle|$evrecur|$evuntil|$evstart|$evend|$evfd" >> "$EVENTS"
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
echo "<!DOCTYPE html><html lang='$lang'><head><title>PandP Home server</title>"
echo "<meta charset='UTF-8'>"
echo "<meta name='viewport' content='width=device-width, initial-scale=1.0, maximum-scale=1.0, user-scalable=no'>"
echo "<link rel='manifest' href='/manifest.json'>"
echo "<meta name='theme-color' content='#16213e'>"
echo "<link rel='apple-touch-icon' href='/icon-192.png'>"
echo "<link rel='stylesheet' href='/nav.css?v=16'>"
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
echo ".day{background:#161b22;border:1px solid #21262d;border-radius:8px;min-height:100px;padding:6px;cursor:pointer;position:relative;display:flex;flex-direction:column;gap:4px}"
echo ".day:hover{border-color:#58a6ff}"
echo ".day.other{opacity:0.35}"
echo ".day.today{border-color:#58a6ff;background:#1f2a44}"
echo ".daynum{font-size:0.85em;color:#8b949e;font-weight:bold}"
echo ".ev{background:#1f6feb;color:#fff;font-size:0.72em;padding:2px 4px;border-radius:4px;word-wrap:break-word;line-height:1.2}"
echo ".ev-timed{background:#1f6feb}"
echo ".ev-allday{background:#d4a017;color:#1a1a2e}"
echo ".ev-untimed{background:#6e7681}"
echo ".allday-bar{position:absolute;left:0;top:4px;bottom:4px;width:4px;background:#d4a017;border-radius:2px}"
echo ".ev .del{float:right;cursor:pointer;color:#ff8a80;font-weight:bold;margin-left:4px}"
echo ".formbox{background:#161b22;border:1px solid #30363d;border-radius:8px;padding:12px;margin:8px 0;display:none}"
echo ".formbox input[type=text]{width:100%;box-sizing:border-box;padding:10px 12px;border:1px solid #30363d;border-radius:8px;background:#0d1117;color:#e6edf3;font-size:16px;min-height:44px;margin-bottom:8px}"
echo ".formbox .row{display:flex;gap:8px}"
echo ".formbox button{background:#238636;color:#fff;border:none;padding:10px 16px;border-radius:8px;cursor:pointer;font-weight:bold;min-height:44px;flex:1}"
echo ".formbox .cancel{background:#21262d;color:#e6edf3;border:1px solid #30363d}"
echo ".homebtn{display:inline-block;background:#21262d;color:#58a6ff;padding:6px 16px;border-radius:6px;text-decoration:none;font-weight:bold;margin:8px 0;border:1px solid #30363d;min-height:36px;line-height:24px}"
echo ".homebtn:hover{background:#30363d}"
echo ".hint{color:#8b949e;font-size:0.75em;text-align:center;padding:8px 0}"
echo "@media (max-width:480px){.wrap{padding:0 8px}.grid{overflow-x:auto}.weekdays{overflow-x:auto}.day{min-height:60px;padding:4px;min-width:90px}.ev{font-size:0.65em}.nav .title{font-size:0.95em}.nav button{padding:6px 10px;font-size:0.85em}}"
echo ".overlay{position:fixed;top:0;left:0;width:100%;height:100%;background:rgba(0,0,0,0.7);display:none;align-items:center;justify-content:center;z-index:200;padding:16px;box-sizing:border-box}"
echo ".modal{background:#161b22;border:1px solid #30363d;border-radius:12px;padding:20px;max-width:420px;width:100%}"
echo ".modal h3{color:#58a6ff;margin-top:0}"
echo ".modal input{width:100%;box-sizing:border-box;padding:10px 12px;border:1px solid #30363d;border-radius:8px;background:#0d1117;color:#e6edf3;font-size:16px;min-height:44px;margin-bottom:8px}"
echo ".modal .row{display:flex;gap:8px}"
echo ".modal button{flex:1;min-height:44px;border:none;border-radius:8px;cursor:pointer;font-weight:bold;padding:10px}"
echo ".modal .save{background:#238636;color:#fff}"
echo ".modal .del{background:#b71c1c;color:#fff}"
echo ".modal .cancel{background:#21262d;color:#e6edf3;border:1px solid #30363d}"
echo ".agendaday{background:#161b22;border:1px solid #21262d;border-radius:8px;padding:10px;margin-bottom:8px;cursor:pointer}"
echo ".agendaday.today{border-color:#58a6ff;background:#1f2a44}"
echo ".agendaday .dtitle{font-weight:bold;color:#58a6ff;margin-bottom:4px}"
echo ".agendaday .ev{margin-top:4px}"
echo "</style>"
echo "</head><body>"
echo "<div class='header'><h1>PandP Home</h1><p>$t_sub</p></div>"
echo "<script src='/nav.js?v=16'></script>"
echo "<div class='wrap'>"
echo "<div class='nav'>"
echo "<button onclick='prevPeriod()'>&#9664; $t_prev</button>"
echo "<div class='title' id='viewtitle'></div>"
echo "<button onclick='nextPeriod()'>$t_next &#9654;</button>"
echo "</div>"
echo "<div style='display:flex;gap:6px;justify-content:center;padding-bottom:8px'>"
echo "<button onclick=\"setView('month')\" id='btnmonth' style='background:#1f6feb;color:#fff;border:none;padding:6px 12px;border-radius:6px;cursor:pointer;min-height:36px'>$t_month</button>"
echo "<button onclick=\"setView('week')\" id='btnweek' style='background:#21262d;color:#58a6ff;border:1px solid #30363d;padding:6px 12px;border-radius:6px;cursor:pointer;min-height:36px'>$t_week</button>"
echo "<button onclick=\"setView('day')\" id='btnday' style='background:#21262d;color:#58a6ff;border:1px solid #30363d;padding:6px 12px;border-radius:6px;cursor:pointer;min-height:36px'>$t_day</button>"
echo "<button onclick=\"setView('todo')\" id='btntodo' style='background:#21262d;color:#58a6ff;border:1px solid #30363d;padding:6px 12px;border-radius:6px;cursor:pointer;min-height:36px'>$t_todo</button>"
echo "</div>"
echo "<div class='weekdays'><div>$t_wd1</div><div>$t_wd2</div><div>$t_wd3</div><div>$t_wd4</div><div>$t_wd5</div><div>$t_wd6</div><div>$t_wd7</div></div>"
echo "<div class='grid' id='grid'></div>"
echo "<div class='formbox' id='formbox'>"
echo "<div style='color:#58a6ff;font-weight:bold;margin-bottom:6px' id='formtitle'>$t_add_event</div>"
echo "<input type='text' id='evdate'>"
echo "<input type='text' id='evtext' placeholder='$t_ev_title' autofocus>"
echo "<input type='text' id='evstart' placeholder='$t_start_ph'>"
echo "<input type='text' id='evend' placeholder='$t_end_ph'>"
echo "<label style='display:flex;align-items:center;gap:8px;margin-bottom:8px;color:#e6edf3'><input type='checkbox' id='evfullday' style='width:18px;height:18px'> $t_fullday</label>"
echo "<select id='recur' style='width:100%;box-sizing:border-box;padding:10px 12px;border:1px solid #30363d;border-radius:8px;background:#0d1117;color:#e6edf3;font-size:16px;min-height:44px;margin-bottom:8px'><option value='none'>$t_no_repeat</option><option value='daily'>$t_daily</option><option value='weekly'>$t_weekly</option><option value='monthly'>$t_monthly</option><option value='yearly'>$t_yearly</option></select>"
echo "<input type='text' id='until' placeholder='$t_until_ph'>"
echo "<div class='row'>"
echo "<button id='savebtn' onclick='saveEvent()'>$t_add</button>"
echo "<button class='cancel' onclick='closeForm()'>$t_cancel</button>"
echo "</div>"
echo "</div>"
echo "<div class='overlay' id='evoverlay' onclick='if(event.target===this)closeEventModal()'>"
echo "<div class='modal'>"
echo "<h3>$t_edit_event</h3>"
echo "<input type='text' id='evdate2' placeholder='$t_date_ph'>"
echo "<input type='text' id='evtitle2' placeholder='$t_ev_title'>"
echo "<input type='text' id='evstart2' placeholder='$t_start_ph'>"
echo "<input type='text' id='evend2' placeholder='$t_end_ph'>"
echo "<label style='display:flex;align-items:center;gap:8px;margin-bottom:8px;color:#e6edf3'><input type='checkbox' id='evfullday2' style='width:18px;height:18px'> $t_fullday</label>"
echo "<select id='recur2' style='width:100%;box-sizing:border-box;padding:10px 12px;border:1px solid #30363d;border-radius:8px;background:#0d1117;color:#e6edf3;font-size:16px;min-height:44px;margin-bottom:8px'><option value='none'>$t_no_repeat</option><option value='daily'>$t_daily</option><option value='weekly'>$t_weekly</option><option value='monthly'>$t_monthly</option><option value='yearly'>$t_yearly</option></select>"
echo "<input type='text' id='until2' placeholder='$t_until_ph'>"
echo "<div class='row'>"
echo "<button class='save' onclick='saveEditEvent()'>$t_save</button>"
echo "<button class='del' onclick='deleteEditEvent()'>$t_delete</button>"
echo "<button class='cancel' onclick='closeEventModal()'>$t_cancel</button>"
echo "</div>"
echo "</div>"
echo "</div>"
echo "<p class='hint'>$t_hint</p>"
echo "</div>"
echo "<script>"
echo "var LANG='$lang'; var events=[];"
echo "var currentEditId='';"
echo "var editId=''";
echo "var cur=new Date();"
echo "function pad(n){return n<10?'0'+n:n;}"
echo "function ymd(d){return d.getFullYear()+'-'+pad(d.getMonth()+1)+'-'+pad(d.getDate());}"
echo "function expandEvent(base){var recur=base.recur||'none';var until=base.until?new Date(base.until+'T00:00:00'):null;var start=new Date(base.date+'T00:00:00');if(recur==='none'){events.push({id:base.id,date:base.date,title:base.title,origId:base.id,recur:recur,until:base.until,start:base.start,end:base.end,fullday:base.fullday});return;}if(!until){until=new Date(start);until.setFullYear(until.getFullYear()+1);}var cur=new Date(start);var count=0;while(cur<=until && count<366){events.push({id:base.id+'_'+ymd(cur),date:ymd(cur),title:base.title,origId:base.id,recur:recur,until:base.until,start:base.start,end:base.end,fullday:base.fullday});if(recur==='daily')cur.setDate(cur.getDate()+1);else if(recur==='weekly')cur.setDate(cur.getDate()+7);else if(recur==='monthly')cur.setMonth(cur.getMonth()+1);else if(recur==='yearly')cur.setFullYear(cur.getFullYear()+1);else break;count++;}}"
echo "function loadEvents(){fetch('/cgi-bin/calendar.cgi?ajax=1').then(function(r){return r.text();}).then(function(t){events=[];var lines=t.split('\\n');for(var i=0;i<lines.length;i++){var l=lines[i].trim();if(!l)continue;var p1=l.indexOf('|');var p2=l.indexOf('|',p1+1);var p3=l.indexOf('|',p2+1);var p4=l.indexOf('|',p3+1);var p5=l.indexOf('|',p4+1);var p6=l.indexOf('|',p5+1);var p7=l.indexOf('|',p6+1);if(p1<0||p2<0)continue;var base={id:l.substring(0,p1),date:l.substring(p1+1,p2),title:l.substring(p2+1,p3<0?l.length:p3),recur:(p3<0?'none':l.substring(p3+1,p4<0?l.length:p4)),until:(p4<0?'':l.substring(p4+1,p5<0?l.length:p5)),start:(p5<0?'':l.substring(p5+1,p6<0?l.length:p6)),end:(p6<0?'':l.substring(p6+1,p7<0?l.length:p7)),fullday:(p7<0?'0':l.substring(p7+1))};expandEvent(base);}render();openLinkedEvent();}).catch(function(e){});}"
echo "function linkedParam(n){var m=location.search.match(new RegExp('[?&]'+n+'=([^&]*)'));return m?decodeURIComponent(m[1]):'';}"
echo "function openLinkedEvent(){var eid=linkedParam('edit');if(!eid)return;var d=linkedParam('date');var ev=null;var i;for(i=0;i<events.length;i++){if(events[i].origId===eid&&(!d||events[i].date===d)){ev=events[i];break;}}if(!ev){for(i=0;i<events.length;i++){if(events[i].origId===eid){ev=events[i];break;}}}if(!ev)return;cur=new Date(ev.date+'T00:00:00');render();openEventModal(ev.origId,ev.date,ev.title,ev.recur,ev.until,ev.start,ev.end,ev.fullday);if(history.replaceState){history.replaceState(null,'',location.pathname);}}"
echo "var view='month';"
echo "function setView(v){view=v;var ids=['btnmonth','btnweek','btnday','btntodo'];var vals=['month','week','day','todo'];for(var i=0;i<ids.length;i++){var b=document.getElementById(ids[i]);if(!b)continue;if(vals[i]===v){b.style.background='#1f6feb';b.style.color='#fff';b.style.border='none';}else{b.style.background='#21262d';b.style.color='#58a6ff';b.style.border='1px solid #30363d';}}var wd=document.querySelector('.weekdays');if(wd)wd.style.display=(v==='todo')?'none':'grid';render();}"
echo "function render(){if(view==='month')renderMonth();else if(view==='week')renderWeek();else if(view==='day')renderDay();else renderTodo();}"
echo "function renderMonth(){document.getElementById('grid').style.gridTemplateColumns='repeat(7,1fr)';var y=cur.getFullYear(),m=cur.getMonth();document.getElementById('viewtitle').textContent=cur.toLocaleString(LANG==='da'?'da-DK':'en-GB',{month:'long',year:'numeric'});var first=new Date(y,m,1);var startDay=first.getDay();var daysInMonth=new Date(y,m+1,0).getDate();var grid=document.getElementById('grid');grid.innerHTML='';var today=ymd(new Date());for(var i=0;i<startDay;i++){var c=document.createElement('div');c.className='day other';grid.appendChild(c);}for(var d=1;d<=daysInMonth;d++){var date=new Date(y,m,d);var ds=ymd(date);var cell=document.createElement('div');cell.className='day'+(ds===today?' today':'');cell.innerHTML='<div class=\"daynum\">'+d+'</div>';var dayEvents=sortDayEvents(events.filter(function(e){return e.date===ds;}));for(var j=0;j<dayEvents.length;j++){var ev=dayEvents[j];var el=document.createElement('div');el.className=evClass(ev);el.innerHTML=(evTime(ev)?'<span style=\"opacity:0.75;font-size:0.8em\">'+evTime(ev)+'</span> ':'')+escHtml(ev.title);el.onclick=(function(ev){return function(e){e.stopPropagation();openEventModal(ev.origId,ev.date,ev.title,ev.recur,ev.until,ev.start,ev.end,ev.fullday);};})(ev);cell.appendChild(el);}if(dayEvents.some(function(e){return e.fullday==='1';})) {var bar=document.createElement('div');bar.className='allday-bar';cell.appendChild(bar);}cell.addEventListener('click',function(ds){return function(){openForm(ds);};}(ds));grid.appendChild(cell);}var total=startDay+daysInMonth;var rem=total%7;if(rem){for(var i=0;i<7-rem;i++){var c=document.createElement('div');c.className='day other';grid.appendChild(c);}}}"
echo "function renderWeek(){document.getElementById('grid').style.gridTemplateColumns='repeat(7,1fr)';var start=new Date(cur);start.setDate(cur.getDate()-cur.getDay());var grid=document.getElementById('grid');grid.innerHTML='';var today=ymd(new Date());for(var i=0;i<7;i++){var d=new Date(start);d.setDate(start.getDate()+i);var ds=ymd(d);var cell=document.createElement('div');cell.className='day'+(ds===today?' today':'');cell.style.minHeight='120px';cell.innerHTML='<div class=\"daynum\">'+d.toLocaleString(LANG==='da'?'da-DK':'en-GB',{weekday:'short'})+' '+d.getDate()+'</div>';var dayEvents=sortDayEvents(events.filter(function(e){return e.date===ds;}));for(var j=0;j<dayEvents.length;j++){var ev=dayEvents[j];var el=document.createElement('div');el.className=evClass(ev);el.innerHTML=(evTime(ev)?'<span style=\"opacity:0.75;font-size:0.8em\">'+evTime(ev)+'</span> ':'')+escHtml(ev.title);el.onclick=(function(ev){return function(e){e.stopPropagation();openEventModal(ev.origId,ev.date,ev.title,ev.recur,ev.until,ev.start,ev.end,ev.fullday);};})(ev);cell.appendChild(el);}if(dayEvents.some(function(e){return e.fullday==='1';})) {var bar=document.createElement('div');bar.className='allday-bar';cell.appendChild(bar);}cell.addEventListener('click',function(ds){return function(){openForm(ds);};}(ds));grid.appendChild(cell);}document.getElementById('viewtitle').textContent='$t_week_of'+start.toLocaleString(LANG==='da'?'da-DK':'en-GB',{month:'short',day:'numeric',year:'numeric'});}"
echo "function renderDay(){document.getElementById('grid').style.gridTemplateColumns='repeat(7,1fr)';var ds=ymd(cur);var grid=document.getElementById('grid');grid.innerHTML='';var cell=document.createElement('div');cell.className='day today';cell.style.minHeight='220px';cell.style.gridColumn='1 / -1';cell.innerHTML='<div class=\"daynum\">'+cur.toLocaleString(LANG==='da'?'da-DK':'en-GB',{weekday:'long',month:'long',day:'numeric',year:'numeric'})+'</div>';var dayEvents=sortDayEvents(events.filter(function(e){return e.date===ds;}));if(dayEvents.length===0){var e=document.createElement('div');e.className='empty-msg';e.textContent='$t_no_events';cell.appendChild(e);}for(var j=0;j<dayEvents.length;j++){var ev=dayEvents[j];var el=document.createElement('div');el.className=evClass(ev);el.innerHTML=(evTime(ev)?'<span style=\"opacity:0.75;font-size:0.8em\">'+evTime(ev)+'</span> ':'')+escHtml(ev.title);el.onclick=(function(ev){return function(e){e.stopPropagation();openEventModal(ev.origId,ev.date,ev.title,ev.recur,ev.until,ev.start,ev.end,ev.fullday);};})(ev);cell.appendChild(el);}if(dayEvents.some(function(e){return e.fullday==='1';})) {var bar=document.createElement('div');bar.className='allday-bar';cell.appendChild(bar);}cell.addEventListener('click',function(){openForm(ds);});grid.appendChild(cell);document.getElementById('viewtitle').textContent=cur.toLocaleString(LANG==='da'?'da-DK':'en-GB',{weekday:'long',month:'long',day:'numeric'});}"
echo "function renderTodo(){var today=new Date();today.setHours(0,0,0,0);var end=new Date(today);end.setDate(end.getDate()+30);var upcoming=events.filter(function(e){var d=new Date(e.date+'T00:00:00');return d>=today && d<=end;}).sort(function(a,b){if(a.date!==b.date)return a.date.localeCompare(b.date);var ta=evSortTime(a);var tb=evSortTime(b);if(ta===-1&&tb!==-1)return -1;if(tb===-1&&ta!==-1)return 1;if(ta===tb)return 0;return ta<tb?-1:1;});var grid=document.getElementById('grid');grid.style.gridTemplateColumns='1fr';grid.innerHTML='';document.getElementById('viewtitle').textContent='$t_upcoming';if(upcoming.length===0){grid.innerHTML='<div class="empty-msg">$t_no_upcoming</div>';return;}var curDate='';for(var i=0;i<upcoming.length;i++){var ev=upcoming[i];if(ev.date!==curDate){curDate=ev.date;var h=document.createElement('div');h.className='daynum';h.style.padding='8px 0 2px';h.style.color='#58a6ff';h.textContent=new Date(ev.date+'T00:00:00').toLocaleString(LANG==='da'?'da-DK':'en-GB',{weekday:'long',month:'long',day:'numeric'});grid.appendChild(h);}var el=document.createElement('div');el.className=evClass(ev);el.style.marginBottom='4px';el.style.cursor='pointer';el.style.padding='6px 8px';el.innerHTML=(evTime(ev)?'<span style=\"opacity:0.75;font-size:0.8em\">'+evTime(ev)+'</span> ':'')+escHtml(ev.title);el.onclick=function(ev){return function(e){e.stopPropagation();openEventModal(ev.origId,ev.date,ev.title,ev.recur,ev.until,ev.start,ev.end,ev.fullday);};}(ev);grid.appendChild(el);}}"
echo "function escHtml(s){var d=document.createElement('div');d.textContent=s;return d.innerHTML;}"
echo "function evClass(ev){if(ev.fullday==='1')return 'ev ev-allday';if(ev.start||ev.end)return 'ev ev-timed';return 'ev ev-untimed';}"
echo "function evSortTime(ev){if(ev.fullday==='1'||(!ev.start&&!ev.end))return -1;return ev.start||'99:99';}"
echo "function sortDayEvents(arr){return arr.slice().sort(function(a,b){var ta=evSortTime(a);var tb=evSortTime(b);if(ta===-1 && tb!==-1)return -1;if(tb===-1 && ta!==-1)return 1;if(ta===tb)return 0;return ta<tb?-1:1;});}"
echo "function openForm(ds,title,id){editId=id||'';document.getElementById('evdate').value=ds;document.getElementById('evtext').value=title||'';document.getElementById('formtitle').textContent=(editId?'$t_edit_event':'$t_add_on')+' '+ds;document.getElementById('savebtn').textContent=editId?'$t_save':'$t_add';document.getElementById('recur').value='none';document.getElementById('until').value='';document.getElementById('evstart').value='';document.getElementById('evend').value='';document.getElementById('evfullday').checked=false;document.getElementById('formbox').style.display='block';document.getElementById('evtext').focus();}"
echo "function editEvent(id,date,title,e){e.stopPropagation();openForm(date,title,id);}"
echo "function closeForm(){editId='';document.getElementById('savebtn').textContent='Add';document.getElementById('formbox').style.display='none';}"
echo "function saveEvent(){var ds=document.getElementById('evdate').value;var t=document.getElementById('evtext').value.trim();if(!t){alert('$t_title_req');return;}var r=document.getElementById('recur').value;var u=document.getElementById('until').value.trim();var s=document.getElementById('evstart').value.trim();var e=document.getElementById('evend').value.trim();var f=document.getElementById('evfullday').checked?'1':'0';var body='date='+encodeURIComponent(ds)+'&title='+encodeURIComponent(t)+'&recur='+encodeURIComponent(r)+'&until='+encodeURIComponent(u)+'&start='+encodeURIComponent(s)+'&end='+encodeURIComponent(e)+'&fullday='+encodeURIComponent(f);if(editId)body+='&edit='+encodeURIComponent(editId);fetch('/cgi-bin/calendar.cgi?ajax=1',{method:'POST',headers:{'Content-Type':'application/x-www-form-urlencoded'},body:body}).then(function(r){return r.text();}).then(function(){editId='';document.getElementById('savebtn').textContent='Add';closeForm();loadEvents();}).catch(function(e){alert('$t_save_fail'+e);});}"
echo "function openEventModal(id,date,title,recur,until,start,end,fullday){currentEditId=id;document.getElementById('evdate2').value=date;document.getElementById('evtitle2').value=title;document.getElementById('recur2').value=recur||'none';document.getElementById('until2').value=until||'';document.getElementById('evstart2').value=start||'';document.getElementById('evend2').value=end||'';document.getElementById('evfullday2').checked=(fullday==='1');document.getElementById('evoverlay').style.display='flex';}"
echo "function closeEventModal(){currentEditId='';document.getElementById('evoverlay').style.display='none';}"
echo "function saveEditEvent(){var ds=document.getElementById('evdate2').value.trim();var t=document.getElementById('evtitle2').value.trim();if(!ds||!t){alert('$t_date_title_req');return;}var r=document.getElementById('recur2').value;var u=document.getElementById('until2').value.trim();var s=document.getElementById('evstart2').value.trim();var e=document.getElementById('evend2').value.trim();var f=document.getElementById('evfullday2').checked?'1':'0';var body='date='+encodeURIComponent(ds)+'&title='+encodeURIComponent(t)+'&recur='+encodeURIComponent(r)+'&until='+encodeURIComponent(u)+'&start='+encodeURIComponent(s)+'&end='+encodeURIComponent(e)+'&fullday='+encodeURIComponent(f)+'&edit='+encodeURIComponent(currentEditId);fetch('/cgi-bin/calendar.cgi?ajax=1',{method:'POST',headers:{'Content-Type':'application/x-www-form-urlencoded'},body:body}).then(function(r){return r.text();}).then(function(){closeEventModal();loadEvents();}).catch(function(e){alert('$t_save_fail'+e);});}"
echo "function deleteEditEvent(){if(!confirm('$t_del_confirm'))return;fetch('/cgi-bin/calendar.cgi?delete='+encodeURIComponent(currentEditId)+'&ajax=1').then(function(r){return r.text();}).then(function(){closeEventModal();loadEvents();}).catch(function(e){});}"
echo "function delEvent(id,e){e.stopPropagation();if(!confirm('$t_del_confirm'))return;fetch('/cgi-bin/calendar.cgi?delete='+encodeURIComponent(id)+'&ajax=1').then(function(r){return r.text();}).then(function(){loadEvents();}).catch(function(e){});}"
echo "function prevPeriod(){if(view==='month')cur.setMonth(cur.getMonth()-1);else if(view==='week')cur.setDate(cur.getDate()-7);else cur.setDate(cur.getDate()-1);render();}"
echo "function nextPeriod(){if(view==='month')cur.setMonth(cur.getMonth()+1);else if(view==='week')cur.setDate(cur.getDate()+7);else cur.setDate(cur.getDate()+1);render();}"
echo "window.onload=function(){loadEvents();setView('month');}"
echo "function evTime(ev){if(ev.fullday==='1')return 'All day';if(ev.start&&ev.end)return ev.start+'-'+ev.end;if(ev.start)return ev.start;return '';}"
echo "</script>"
echo "<script>if('serviceWorker' in navigator){navigator.serviceWorker.register('/sw.js').catch(function(){});}</script>"
echo "</body></html>"
