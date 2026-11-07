#!/data/local/tmp/linux/bin/sh
L=/data/local/tmp/linux
. /data/local/tmp/linux/www/cgi-bin/lang.inc

if [ "$lang" = "en" ]; then
  t_sub="Recipe List"
  t_search_ph="Search recipes..."
  t_add_title="Add recipe"
  t_edit_title="Edit recipe"
  t_title_ph="Title (e.g. Pasta carbonara)"
  t_url_ph="Link (https://...)"
  t_desc_ph="Short description / notes"
  t_save="Save recipe"
  t_save_changes="Save changes"
  t_cancel="Cancel editing"
  t_hint="Recipes are stored on the device."
  t_empty="No recipes yet. Add one below!"
  t_nomatch="No recipes match "
  t_show_more="Show more"
  t_show_less="Show less"
  t_edit="Edit"
  t_del="Delete"
  t_title_req="Enter a title or a link"
  t_save_fail="Could not save: "
  t_del_confirm="Delete this recipe?"
else
  t_sub="Opskriftsliste"
  t_search_ph="Søg i opskrifter..."
  t_add_title="Tilføj opskrift"
  t_edit_title="Rediger opskrift"
  t_title_ph="Titel (f.eks. Pasta carbonara)"
  t_url_ph="Link (https://...)"
  t_desc_ph="Kort beskrivelse / noter"
  t_save="Gem opskrift"
  t_save_changes="Gem ændringer"
  t_cancel="Annuller redigering"
  t_hint="Opskrifter gemmes på enheden."
  t_empty="Ingen opskrifter endnu. Tilføj en nedenfor!"
  t_nomatch="Ingen opskrifter matcher "
  t_show_more="Vis mere"
  t_show_less="Vis mindre"
  t_edit="Rediger"
  t_del="Slet"
  t_title_req="Angiv en titel eller et link"
  t_save_fail="Kunne ikke gemme: "
  t_del_confirm="Slet denne opskrift?"
fi
RECIPES="$L/www/recipes.log"
MAXRECIPES=500

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

get_field() {
    body="$1"
    want="$2"
    rest="$body"
    while [ -n "$rest" ]; do
        pair="${rest%%&*}"
        if [ "${pair%%=*}" = "$want" ]; then
            /data/local/tmp/linux/bin/busybox printf '%s' "${pair#*=}"
            return 0
        fi
        case "$rest" in
            *'&'*) rest="${rest#*&}" ;;
            *) break ;;
        esac
    done
    return 0
}

clean_text() {
    /data/local/tmp/linux/bin/busybox printf '%s' "$1" | \
        /data/local/tmp/linux/bin/busybox tr '\r\n' '  ' | \
        /data/local/tmp/linux/bin/busybox sed 's/|/-/g'
}

new_id() {
    eid=$(/data/local/tmp/linux/bin/busybox date +%s 2>/dev/null)
    eid="${eid}_$(/data/local/tmp/linux/bin/busybox wc -l < "$RECIPES" 2>/dev/null)"
    /data/local/tmp/linux/bin/busybox printf '%s' "${eid%% *}"
}

[ -f "$RECIPES" ] || /data/local/tmp/linux/bin/busybox touch "$RECIPES"

POSTDATA=""
if [ "$REQUEST_METHOD" = "POST" ]; then
    POSTDATA=$(cat)
fi

del_id=""
case "$QUERY_STRING" in
    *delete=*) del_id="${QUERY_STRING#*delete=}"; del_id="${del_id%%&*}" ;;
esac

if [ -n "$del_id" ]; then
    tmp="$RECIPES.tmp"
    : > "$tmp"
    while IFS= read -r line; do
        [ -z "$line" ] && continue
        eid="${line%%|*}"
        if [ "$eid" != "$del_id" ]; then
            echo "$line" >> "$tmp"
        fi
    done < "$RECIPES"
    /data/local/tmp/linux/bin/busybox mv "$tmp" "$RECIPES" 2>/dev/null
else
    echo "$POSTDATA" | /data/local/tmp/linux/bin/busybox grep -q 'title=' && has_recipe=1 || has_recipe=0
    if [ "$has_recipe" = "1" ]; then
        edit_id=$(urldecode "$(get_field "$POSTDATA" id)")
        case "$edit_id" in
            ''|*[!0-9_]*) edit_id="" ;;
        esac
        title=$(clean_text "$(urldecode "$(get_field "$POSTDATA" title)")")
        url=$(clean_text "$(urldecode "$(get_field "$POSTDATA" url)")")
        desc=$(clean_text "$(urldecode "$(get_field "$POSTDATA" desc)")")
        url=$(echo "$url" | /data/local/tmp/linux/bin/busybox sed 's/ //g')
        case "$url" in
            http://*|https://*) : ;;
            '') : ;;
            *) url="http://$url" ;;
        esac
        if [ -n "$edit_id" ]; then
            tmp="$RECIPES.tmp"
            : > "$tmp"
            found=0
            while IFS= read -r line; do
                [ -z "$line" ] && continue
                eid="${line%%|*}"
                if [ "$eid" = "$edit_id" ]; then
                    found=1
                    if [ -z "$title" ] && [ -z "$url" ]; then
                        echo "$line" >> "$tmp"
                    else
                        echo "$edit_id|$title|$url|$desc" >> "$tmp"
                    fi
                else
                    echo "$line" >> "$tmp"
                fi
            done < "$RECIPES"
            if [ "$found" = "0" ] && { [ -n "$title" ] || [ -n "$url" ]; }; then
                echo "$(new_id)|$title|$url|$desc" >> "$tmp"
            fi
            /data/local/tmp/linux/bin/busybox mv "$tmp" "$RECIPES" 2>/dev/null
        elif [ -n "$title" ] || [ -n "$url" ]; then
            echo "$(new_id)|$title|$url|$desc" >> "$RECIPES"
        fi
    fi
fi

count=$(/data/local/tmp/linux/bin/busybox wc -l < "$RECIPES" 2>/dev/null)
count=${count%% *}
if [ -n "$count" ] && [ "$count" -gt "$MAXRECIPES" ] 2>/dev/null; then
    /data/local/tmp/linux/bin/busybox tail -n "$MAXRECIPES" "$RECIPES" > "$RECIPES.tmp" 2>/dev/null
    /data/local/tmp/linux/bin/busybox mv "$RECIPES.tmp" "$RECIPES" 2>/dev/null
fi

IS_AJAX=0
echo "$QUERY_STRING" | /data/local/tmp/linux/bin/busybox grep -q "ajax=1" && IS_AJAX=1

if [ "$IS_AJAX" = "1" ]; then
    echo "Content-type: text/plain; charset=UTF-8"
    echo "Access-Control-Allow-Origin: *"
    echo ""
    if [ -f "$RECIPES" ]; then
        /data/local/tmp/linux/bin/busybox cat "$RECIPES"
    fi
    exit 0
fi

echo "Content-type: text/html; charset=UTF-8"
echo "Access-Control-Allow-Origin: *"
echo ""
echo "<!DOCTYPE html><html lang='$lang'><head><title>PandP Home server</title>"
echo "<meta charset='UTF-8'>"
echo "<meta name='viewport' content='width=device-width, initial-scale=1.0, maximum-scale=1.0, user-scalable=no'>"
echo "<meta name='theme-color' content='#16213e'>"
echo "<meta name='apple-mobile-web-app-capable' content='yes'>"
echo "<link rel='manifest' href='/manifest.json'>"
echo "<link rel='apple-touch-icon' href='/icon-192.png'>"
echo "<link rel='stylesheet' href='/nav.css?v=16'>"
echo "<style>"
echo "body{font-family:-apple-system,BlinkMacSystemFont,Segoe UI,Roboto,sans-serif;margin:0;background:#0d1117;color:#e6edf3;min-height:100vh;display:flex;flex-direction:column}"
echo ".header{background:#161b22;padding:12px 16px;text-align:center;border-bottom:1px solid #30363d;flex-shrink:0}"
echo ".header h1{color:#58a6ff;margin:0;font-size:1.2em}"
echo ".header p{color:#8b949e;margin:4px 0 0;font-size:0.8em}"
echo ".wrap{max-width:900px;width:100%;margin:0 auto;display:flex;flex-direction:column;flex:1;min-height:0;padding:0 12px}"
echo ".searchbox{padding:12px 0 4px;flex-shrink:0}"
echo ".searchbox input{width:100%;box-sizing:border-box;padding:12px 14px;border:1px solid #30363d;border-radius:8px;background:#0d1117;color:#e6edf3;font-size:16px;min-height:48px;outline:none}"
echo ".searchbox input:focus{border-color:#58a6ff}"
echo ".list{flex:1;overflow-y:auto;padding:8px 0 12px;min-height:200px;-webkit-overflow-scrolling:touch}"
echo ".recipe{background:#161b22;border:1px solid #30363d;border-radius:8px;padding:12px;margin-bottom:10px;display:flex;align-items:flex-start;gap:10px}"
echo ".recipe.editing{border-color:#58a6ff}"
echo ".recipe-thumb{width:56px;height:56px;border-radius:8px;flex-shrink:0;position:relative;display:flex;align-items:center;justify-content:center;background:#21262d;overflow:hidden;text-decoration:none;border:1px solid #30363d}"
echo ".thumb-letter{font-size:24px;font-weight:bold;color:#fff;text-shadow:0 1px 2px rgba(0,0,0,.5)}"
echo ".thumb-icon{position:absolute;top:12px;left:12px;width:32px;height:32px;border:0;background:transparent}"
echo ".recipe-main{flex:1;min-width:0;word-wrap:break-word}"
echo ".recipe-title{font-weight:bold;font-size:1.05em;color:#58a6ff;text-decoration:none;display:inline-block;padding:4px 0}"
echo ".recipe-title:hover{text-decoration:underline}"
echo ".recipe-url{color:#8b949e;font-size:0.78em;display:block;margin-top:2px;overflow:hidden;text-overflow:ellipsis;white-space:nowrap}"
echo ".recipe-desc{color:#c9d1d9;font-size:0.9em;margin-top:6px;line-height:1.4}"
echo ".morebtn{background:none;border:none;color:#58a6ff;padding:0;margin:2px 0;font-size:0.85em;cursor:pointer;min-height:44px;font-family:inherit}"
echo ".recipe-actions{display:flex;gap:8px;margin-top:6px}"
echo ".recipe-edit{background:#21262d;color:#58a6ff;border:1px solid #30363d;padding:8px 12px;border-radius:6px;cursor:pointer;font-size:0.8em;min-height:44px;min-width:44px}"
echo ".recipe-edit:hover{background:#30363d}"
echo ".recipe-del{background:#b71c1c;color:#fff;border:none;padding:8px 12px;border-radius:6px;cursor:pointer;font-size:0.8em;min-height:44px;min-width:44px;flex-shrink:0}"
echo ".form-area{padding:12px 0;border-top:1px solid #30363d;flex-shrink:0}"
echo ".formtitle{color:#8b949e;font-size:0.8em;text-transform:uppercase;letter-spacing:0.05em;margin-bottom:6px}"
echo ".form input,.form textarea{width:100%;box-sizing:border-box;padding:12px 14px;border:1px solid #30363d;border-radius:8px;background:#0d1117;color:#e6edf3;font-size:16px;font-family:inherit;margin-bottom:8px;outline:none}"
echo ".form input{min-height:48px}"
echo ".form textarea{min-height:60px;resize:vertical}"
echo ".form input:focus,.form textarea:focus{border-color:#58a6ff}"
echo ".form button{background:#238636;color:#fff;border:none;padding:12px 20px;border-radius:8px;cursor:pointer;font-weight:bold;font-size:1em;min-height:48px;width:100%}"
echo ".form .cancelbtn{background:#21262d;color:#e6edf3;border:1px solid #30363d;margin-top:8px}"
echo ".homebtn{display:inline-block;background:#21262d;color:#58a6ff;padding:6px 16px;border-radius:6px;text-decoration:none;font-weight:bold;margin:8px 0;border:1px solid #30363d;min-height:36px;line-height:24px}"
echo ".homebtn:hover{background:#30363d}"
echo ".empty-msg{color:#8b949e;text-align:center;padding:40px 20px;font-style:italic}"
echo "@media (max-width:480px){.wrap{padding:0 8px}.header h1{font-size:1.1em}.homebtn{width:100%;text-align:center;box-sizing:border-box}.recipe-thumb{width:48px;height:48px}.thumb-icon{top:8px;left:8px;width:32px;height:32px}}"
echo "</style>"
echo "</head><body>"
echo "<div class='header'><h1>PandP Home</h1><p>$t_sub</p></div>"
echo "<script src='/nav.js?v=16'></script>"
echo "<div class='wrap'>"
echo "<div class='searchbox'><input type='search' id='search' placeholder='$t_search_ph' oninput='render()'></div>"
echo "<div class='list' id='list'></div>"
echo "<div class='form-area'>"
echo "<div class='formtitle' id='formtitle'>$t_add_title</div>"
echo "<form class='form' id='recipeform' onsubmit='return addRecipe()'>"
echo "<input type='hidden' id='rid'>"
echo "<input type='text' id='rtitle' placeholder='$t_title_ph'>"
echo "<input type='text' id='rurl' placeholder='$t_url_ph' inputmode='url' autocapitalize='none'>"
echo "<textarea id='rdesc' placeholder='$t_desc_ph'></textarea>"
echo "<button type='submit' id='formbtn'>$t_save</button>"
echo "<button type='button' id='cancelbtn' class='cancelbtn' style='display:none' onclick='cancelEdit()'>$t_cancel</button>"
echo "</form>"
echo "<p style='color:#8b949e;font-size:0.75em;text-align:center'>$t_hint</p>"
echo "</div>"
echo "</div>"
echo "<script>"
echo "var recipes=[];"
echo "var expanded={};"
echo "var editingId='';"
echo "function escHtml(s){var d=document.createElement('div');d.textContent=s;return d.innerHTML;}"
echo "function escAttr(s){return escHtml(s).replace(/\"/g,'&quot;');}"
echo "function parseRecipe(line){var p1=line.indexOf('|');if(p1<0)return null;var p2=line.indexOf('|',p1+1);if(p2<0)return null;var p3=line.indexOf('|',p2+1);if(p3<0)return null;return{id:line.substring(0,p1),title:line.substring(p1+1,p2),url:line.substring(p2+1,p3),desc:line.substring(p3+1)};}"
echo "function byId(id){for(var i=0;i<recipes.length;i++){if(recipes[i].id===id)return recipes[i];}return null;}"
echo "function hostOf(u){var i=u.indexOf('://');var s=i>=0?u.substring(i+3):u;var j=s.indexOf('/');if(j>=0)s=s.substring(0,j);return s;}"
echo "function hueOf(s){var h=0;for(var i=0;i<s.length;i++){h=(h*31+s.charCodeAt(i))%360;}return h;}"
echo "function shortDesc(d){if(d.length<=160)return d;return d.substring(0,160)+'…';}"
echo "function toggleDesc(id){expanded[id]=!expanded[id];var el=document.getElementById('desc-'+id);var r=byId(id);if(!el||!r)return;if(expanded[id]){el.textContent=r.desc;}else{el.textContent=shortDesc(r.desc);}var b=document.getElementById('more-'+id);if(b)b.textContent=expanded[id]?'Vis mindre':'Vis mere';}"
echo "function render(){var el=document.getElementById('list');if(!el)return;var q=(document.getElementById('search').value||'').toLowerCase().trim();var out=[];for(var i=0;i<recipes.length;i++){var r=recipes[i];var hay=(r.title+' '+r.desc+' '+r.url).toLowerCase();if(!q||hay.indexOf(q)>=0)out.push(r);}if(recipes.length===0){el.innerHTML=\"<div class='empty-msg'>$t_empty</div>\";return;}if(out.length===0){el.innerHTML=\"<div class='empty-msg'>$t_nomatch \\\"\"+escHtml(q)+\"\\\".</div>\";return;}var html='';for(var j=0;j<out.length;j++){var it=out[j];var cls='recipe'+(it.id===editingId?' editing':'');html+='<div class=\"'+cls+'\">';if(it.url){var host=hostOf(it.url);var scheme=it.url.indexOf('http://')===0?'http':'https';var h=hueOf(host);var letter=(host.charAt(0)||'?').toUpperCase();html+='<a class=\"recipe-thumb\" href=\"'+escAttr(it.url)+'\" target=\"_blank\" rel=\"noopener\" title=\"'+escAttr(host)+'\" style=\"background:linear-gradient(135deg,hsl('+h+',55%,38%),hsl('+((h+40)%360)+',55%,26%))\">';html+='<span class=\"thumb-letter\">'+escHtml(letter)+'</span>';html+='<img class=\"thumb-icon\" alt=\"\" src=\"'+escAttr(scheme+'://'+host+'/favicon.ico')+'\" onerror=\"this.style.display=\'none\'\">';html+='</a>';}else{var t=(it.title.charAt(0)||'?').toUpperCase();var th=hueOf(it.title);html+='<span class=\"recipe-thumb\" style=\"background:linear-gradient(135deg,hsl('+th+',45%,32%),hsl('+((th+40)%360)+',45%,22%))\"><span class=\"thumb-letter\">'+escHtml(t)+'</span></span>';}html+='<div class=\"recipe-main\">';if(it.url){html+='<a class=\"recipe-title\" href=\"'+escAttr(it.url)+'\" target=\"_blank\" rel=\"noopener\">'+escHtml(it.title||it.url)+'</a>';html+='<span class=\"recipe-url\">'+escHtml(it.url)+'</span>';}else{html+='<span class=\"recipe-title\">'+escHtml(it.title)+'</span>';}if(it.desc){var shown=expanded[it.id]?it.desc:shortDesc(it.desc);html+='<div class=\"recipe-desc\" id=\"desc-'+escAttr(it.id)+'\">'+escHtml(shown)+'</div>';if(it.desc.length>160){html+='<button type=\"button\" class=\"morebtn\" id=\"more-'+escAttr(it.id)+'\" onclick=\"toggleDesc(\\''+escAttr(it.id)+'\\')\">'+(expanded[it.id]?'$t_show_less':'$t_show_more')+'</button>';}}html+='<div class=\"recipe-actions\">';html+='<button type=\"button\" class=\"recipe-edit\" onclick=\"startEdit(\\''+escAttr(it.id)+'\\')\">$t_edit</button>';html+='<button type=\"button\" class=\"recipe-del\" onclick=\"delRecipe(\\''+escAttr(it.id)+'\\')\">$t_del</button>';html+='</div>';html+='</div>';html+='</div>';}el.innerHTML=html;}"
echo "function loadRecipes(){fetch('/cgi-bin/recipes.cgi?ajax=1&t='+Date.now()).then(function(r){return r.text();}).then(function(t){recipes=[];var lines=t.split('\\n');for(var i=0;i<lines.length;i++){var l=lines[i];if(!l)continue;var p=parseRecipe(l);if(p)recipes.push(p);}render();}).catch(function(e){});}"
echo "function resetForm(){editingId='';document.getElementById('rid').value='';document.getElementById('rtitle').value='';document.getElementById('rurl').value='';document.getElementById('rdesc').value='';document.getElementById('formtitle').textContent='$t_add_title';document.getElementById('formbtn').textContent='$t_save';document.getElementById('cancelbtn').style.display='none';render();}"
echo "function startEdit(id){var r=byId(id);if(!r)return;editingId=id;document.getElementById('rid').value=id;document.getElementById('rtitle').value=r.title;document.getElementById('rurl').value=r.url;document.getElementById('rdesc').value=r.desc;document.getElementById('formtitle').textContent='$t_edit_title';document.getElementById('formbtn').textContent='$t_save_changes';document.getElementById('cancelbtn').style.display='block';render();var f=document.getElementById('recipeform');if(f.scrollIntoView)f.scrollIntoView(true);document.getElementById('rtitle').focus();}"
echo "function cancelEdit(){resetForm();}"
echo "function addRecipe(){var t=document.getElementById('rtitle').value.trim();var u=document.getElementById('rurl').value.trim();var d=document.getElementById('rdesc').value.trim();var id=document.getElementById('rid').value;if(!t&&!u){alert('$t_title_req');return false;}var body='title='+encodeURIComponent(t)+'&url='+encodeURIComponent(u)+'&desc='+encodeURIComponent(d);if(id)body+='&id='+encodeURIComponent(id);fetch('/cgi-bin/recipes.cgi?ajax=1',{method:'POST',headers:{'Content-Type':'application/x-www-form-urlencoded'},body:body}).then(function(r){return r.text();}).then(function(){resetForm();document.getElementById('rtitle').focus();loadRecipes();}).catch(function(e){alert('$t_save_fail'+e);});return false;}"
echo "function delRecipe(id){if(!confirm('$t_del_confirm'))return;fetch('/cgi-bin/recipes.cgi?delete='+encodeURIComponent(id)+'&ajax=1').then(function(r){return r.text();}).then(function(){if(editingId===id)resetForm();loadRecipes();}).catch(function(e){});}"
echo "window.onload=function(){loadRecipes();document.getElementById('rtitle').addEventListener('keydown',function(e){if(e.key==='Enter'){e.preventDefault();document.getElementById('rurl').focus();}});}"
echo "</script>"
echo "<script>if('serviceWorker' in navigator){navigator.serviceWorker.register('/sw.js').catch(function(){});}</script>"
echo "</body></html>"
