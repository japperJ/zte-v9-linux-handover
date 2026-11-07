#!/data/local/tmp/linux/bin/sh
echo "Content-type: text/plain"
echo "Access-Control-Allow-Origin: *"
echo ""
name=""
case "$QUERY_STRING" in
  name=*) name="${QUERY_STRING#name=}" ;;
esac
# Remove path separators and dangerous sequences (use full paths - CGI PATH is minimal)
name=$(/data/local/tmp/linux/bin/busybox echo "$name" | /data/local/tmp/linux/bin/busybox sed 's/\.\.//g; s/\///g; s/\\//g')
if [ -z "$name" ]; then
    name="upload_$(/data/local/tmp/linux/bin/busybox date +%s 2>/dev/null || echo $$)"
fi
L=/data/local/tmp/linux
dest="$L/www/$name"
cat > "$dest"
size=$($L/bin/busybox wc -c < "$dest" 2>/dev/null)
size=${size%% *}
echo "OK: uploaded $name ($size bytes)"
