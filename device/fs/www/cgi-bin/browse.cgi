#!/data/local/tmp/linux/bin/sh
L=/data/local/tmp/linux
WWW="$L/www"

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
    t_home="Home"
    t_title="PandP Home server"
    t_create_folder="Create Folder"
    t_new_folder="New folder name"
    t_delete="Delete"
    t_download="Download"
    t_refresh="Refresh"
    t_root="Root"
    t_path="Path"
    t_files="Files in"
    t_no_files="No files yet"
    t_lang_toggle="DA"
    t_upload_here="Upload Here"
    t_choose_file="Choose file"
else
    t_home="Hjem"
    t_title="PandP Home server"
    t_create_folder="Opret mappe"
    t_new_folder="Nyt mappenavn"
    t_delete="Slet"
    t_download="Download"
    t_refresh="Opdater"
    t_root="Rod"
    t_path="Sti"
    t_files="Filer i"
    t_no_files="Ingen filer endnu"
    t_lang_toggle="EN"
    t_upload_here="Upload her"
    t_choose_file="Vælg fil"
fi

# Parse path parameter
curpath=""
case "$QUERY_STRING" in
  path=*) curpath="${QUERY_STRING#path=}"; curpath="${curpath%%&*}" ;;
esac
# URL-decode basic
curpath=$(/data/local/tmp/linux/bin/busybox echo "$curpath" | /data/local/tmp/linux/bin/busybox sed 's/%20/ /g; s/%2F/\//g; s/+/ /g')
# Security: strip .. and leading/trailing slashes
curpath=$(/data/local/tmp/linux/bin/busybox echo "$curpath" | /data/local/tmp/linux/bin/busybox sed 's/\.\.//g; s|^/||; s|/$||')

# Build full filesystem path
if [ -z "$curpath" ]; then
    fullpath="$WWW"
    displaypath="/"
else
    fullpath="$WWW/$curpath"
    displaypath="/$curpath"
fi

# Security: ensure fullpath is inside WWW
case "$fullpath" in
    $WWW*) ;;
    *) fullpath="$WWW"; curpath=""; displaypath="/" ;;
esac

# Build lang suffix for links
if [ "$lang" = "en" ]; then
    langsuffix="&lang=en"
else
    langsuffix=""
fi

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
echo "<style>body{font-family:-apple-system,BlinkMacSystemFont,Segoe UI,Roboto,sans-serif;margin:0;background:#1a1a2e;color:#eee} .header{background:#16213e;padding:12px 16px;text-align:center;position:relative} .header h1{color:#4fc3f7;margin:0;font-size:1.3em} .lang-toggle{position:absolute;top:10px;right:12px;background:#21262d;color:#4fc3f7;border:1px solid #30363d;padding:4px 10px;border-radius:6px;cursor:pointer;font-size:0.8em;text-decoration:none;min-height:32px;display:inline-flex;align-items:center} .lang-toggle:hover{background:#30363d} .container{max-width:900px;margin:12px auto;padding:0 12px} table{border-collapse:collapse;width:100%;font-size:1em} th,td{padding:10px 8px;text-align:left;border-bottom:1px solid #333} th{color:#4fc3f7} tr:hover{background:#2a2a3e} a{color:#4fc3f7;text-decoration:none} a:hover{text-decoration:underline} .homebtn{display:inline-block;background:#4fc3f7;color:#1a1a2e;padding:10px 24px;border-radius:6px;text-decoration:none;font-weight:bold;margin:10px 0;min-height:48px;line-height:28px} .delbtn{background:#b71c1c;color:#fff;border:none;padding:6px 12px;border-radius:4px;cursor:pointer;font-size:0.85em;min-height:36px} .delbtn:hover{background:#d32f2f} .mkdirbtn{background:#238636;color:#fff;border:none;padding:8px 14px;border-radius:4px;cursor:pointer;font-size:0.9em;min-height:36px} .breadcrumb{color:#8b949e;font-size:0.9em;margin:8px 0;padding:8px;background:#16213e;border-radius:6px} .breadcrumb a{color:#4fc3f7} .mkdirform{display:flex;gap:8px;margin:12px 0;flex-wrap:wrap} .mkdirform input{flex:1;min-width:120px;padding:8px;border:1px solid #333;border-radius:4px;background:#0d1117;color:#eee;font-size:1em} .uploadbox{background:#16213e;border-radius:6px;padding:12px;margin:12px 0} .filebtn{display:inline-block;background:#21262d;color:#58a6ff;padding:10px 20px;border-radius:6px;border:1px solid #30363d;cursor:pointer;font-weight:bold;min-height:44px;margin:4px 0} .filebtn:hover{background:#30363d} @media (max-width:480px){.container{padding:0 8px}table{font-size:0.85em}th,td{padding:6px 4px} .homebtn{width:100%;text-align:center;box-sizing:border-box} .mkdirform{flex-direction:column} .mkdirform button{width:100%} .uploadbox{flex-direction:column}}</style>"
echo "<script>if('serviceWorker' in navigator){navigator.serviceWorker.register('/sw.js').catch(function(){});}</script>"
echo "</head><body>"
echo "<div class='header'><h1>$t_title</h1><a href='/cgi-bin/browse.cgi?lang=$([ $lang = da ] && echo en || echo da)&path=$curpath' class='lang-toggle'>$t_lang_toggle</a></div>"
echo "<div style='text-align:center;margin:8px 0'><a href='/' class='homebtn'>$t_home</a></div>"
echo "<div class='container'>"

# Breadcrumb
if [ -z "$curpath" ]; then
    echo "<div class='breadcrumb'>/ ($t_root)</div>"
else
    echo "<div class='breadcrumb'>/ <a href='/cgi-bin/browse.cgi?lang=$lang'>$t_root</a> / $curpath</div>"
fi

# Create folder form
echo "<form class='mkdirform' onsubmit='return doMkdir()'>"
echo "<input type='text' id='newfolder' placeholder='$t_new_folder' required>"
echo "<button type='button' class='mkdirbtn' onclick='doMkdir()'>$t_create_folder</button>"
echo "</form>"

# Upload form
echo "<div class='uploadbox'>"
echo "<label class='filebtn' for='upfile'>$t_choose_file</label><input type='file' id='upfile' style='display:none' onchange='document.getElementById(\"upname\").textContent=this.files[0]?this.files[0].name:\"\"'>"
echo "<span id='upname' style='color:#8b949e;margin-left:8px;font-size:0.9em'></span>"
echo "<button class='mkdirbtn' style='margin-left:8px' onclick='doUpload()'>$t_upload_here</button>"
echo "</div>"

echo "<p id='status' style='text-align:center;color:#aaa'></p>"

echo "<table id='filetable'><tr><th>Name</th><th>Size</th><th>Actions</th></tr>"

# List directories first
for f in "$fullpath"/*; do
    [ -d "$f" ] || continue
    name="${f##*/}"
    case "$name" in .*) continue ;; esac
    if [ -z "$curpath" ]; then
        linkpath="$name"
    else
        linkpath="$curpath/$name"
    fi
    echo "<tr id='row-$name'><td>📁 <a href='/cgi-bin/browse.cgi?path=$linkpath&lang=$lang'>$name/</a></td><td>-</td><td><button class='delbtn' onclick=\"delDir('$name')\">$t_delete</button></td></tr>"
done

# List files
for f in "$fullpath"/*; do
    [ -f "$f" ] || continue
    name="${f##*/}"
    case "$name" in
        index.html|browse.cgi|upload.cgi|chat.cgi|delete.cgi|mkdir.cgi) continue ;;
    esac
    case "$name" in cgi-bin) continue ;; esac
    size=$($L/bin/busybox wc -c < "$f" 2>/dev/null)
    size=${size%% *}
    if [ -z "$curpath" ]; then
        filepath="$name"
    else
        filepath="$curpath/$name"
    fi
    echo "<tr id='row-$name'><td>📄 <a href='/$filepath' target='_blank'>$name</a></td><td>$size B</td><td><a href='/$filepath'>$t_download</a> | <button class='delbtn' onclick=\"delFile('$name')\">$t_delete</button></td></tr>"
done
echo "</table>"
echo "<hr><p style='text-align:center'><a href='/cgi-bin/browse.cgi?path=$curpath&lang=$lang'>$t_refresh</a> | <a href='/cgi-bin/browse.cgi?lang=$lang'>$t_root</a></p>"
echo "</div>"
echo "<script>"
echo "var curPath='$curpath'; var curLang='$lang';"
echo "function delFile(name){if(!confirm('Delete '+name+'?'))return;var p=curPath?curPath+'/'+name:name;fetch('/cgi-bin/delete.cgi?file='+encodeURIComponent(p)+'&path='+encodeURIComponent(curPath)).then(function(r){return r.text();}).then(function(t){var s=document.getElementById('status');s.textContent=t;s.style.color=t.indexOf('OK')===0?'#4caf50':'#ff5252';var row=document.getElementById('row-'+name);if(row&&t.indexOf('OK')===0)row.remove();}).catch(function(e){document.getElementById('status').textContent='Error: '+e;});}"
echo "function delDir(name){if(!confirm('Delete folder '+name+'? (must be empty)'))return;var p=curPath?curPath+'/'+name:name;fetch('/cgi-bin/delete.cgi?file='+encodeURIComponent(p)+'&path='+encodeURIComponent(curPath)+'&dir=1').then(function(r){return r.text();}).then(function(t){var s=document.getElementById('status');s.textContent=t;s.style.color=t.indexOf('OK')===0?'#4caf50':'#ff5252';var row=document.getElementById('row-'+name);if(row&&t.indexOf('OK')===0)row.remove();}).catch(function(e){document.getElementById('status').textContent='Error: '+e;});}"
echo "function doMkdir(){var name=document.getElementById('newfolder').value.trim();if(!name){alert('Enter a folder name');return;}fetch('/cgi-bin/mkdir.cgi?name='+encodeURIComponent(name)+'&path='+encodeURIComponent(curPath)+'&lang='+curLang).then(function(r){return r.text();}).then(function(t){var s=document.getElementById('status');s.textContent=t;s.style.color=t.indexOf('OK')===0?'#4caf50':'#ff5252';if(t.indexOf('OK')===0){document.getElementById('newfolder').value='';setTimeout(function(){location.reload();},500);}}).catch(function(e){document.getElementById('status').textContent='Error: '+e;});}"
echo "function doUpload(){var f=document.getElementById('upfile').files[0];if(!f){alert('Choose a file');return;}var r=new FileReader();r.onload=function(e){fetch('/cgi-bin/upload.cgi?name='+encodeURIComponent(f.name)+'&path='+encodeURIComponent(curPath),{method:'POST',body:e.target.result}).then(function(r){return r.text();}).then(function(t){var s=document.getElementById('status');s.textContent=t;s.style.color=t.indexOf('OK')===0?'#4caf50':'#ff5252';if(t.indexOf('OK')===0){document.getElementById('upfile').value='';document.getElementById('upname').textContent='';setTimeout(function(){location.reload();},500);}}).catch(function(e){document.getElementById('status').textContent='Error: '+e;});};r.readAsArrayBuffer(f);}"
echo "</script>"
echo "</body></html>"
'@
[IO.File]::WriteAllText("$env:TEMP\v9-browse.cgi", ($browseCgi -replace "`r`n","`n"), (New-Object System.Text.UTF8Encoding($false)))
$adb = "C:\Users\jptrs\AppData\Local\Microsoft\WinGet\Packages\Google.PlatformTools_Microsoft.Winget.Source_8wekyb3d8bbwe\platform-tools\adb.exe"
& $adb -s V9_Telia push "$env:TEMP\v9-browse.cgi" "/data/local/tmp/linux/www/cgi-bin/browse.cgi" 2>&1
& $adb -s V9_Telia shell 'chmod 755 /data/local/tmp/linux/www/cgi-bin/browse.cgi' 2>&1
Copy-Item "$env:TEMP\v9-browse.cgi" "C:\Users\jptrs\zte-v9-linux-handover\device\fs\www\cgi-bin\browse.cgi" -Force
Write-Host "deployed"