#!/data/local/tmp/linux/bin/sh
L=/data/local/tmp/linux
WWW="$L/www"

# Parse params
name=""
curpath=""
case "$QUERY_STRING" in
  *name=*) name="${QUERY_STRING#*name=}"; name="${name%%&*}" ;;
esac
case "$QUERY_STRING" in
  *path=*) curpath="${QUERY_STRING#*path=}"; curpath="${curpath%%&*}" ;;
esac

# URL-decode
name=$(/data/local/tmp/linux/bin/busybox echo "$name" | /data/local/tmp/linux/bin/busybox sed 's/%20/ /g; s/+/ /g')
curpath=$(/data/local/tmp/linux/bin/busybox echo "$curpath" | /data/local/tmp/linux/bin/busybox sed 's/%20/ /g; s/%2F/\//g; s/+/ /g')
# Security
curpath=$(/data/local/tmp/linux/bin/busybox echo "$curpath" | /data/local/tmp/linux/bin/busybox sed 's/\.\.//g; s|^/||; s|/$||')
name=$(/data/local/tmp/linux/bin/busybox echo "$name" | /data/local/tmp/linux/bin/busybox sed 's/\.\.//g; s/\///g; s/\\//g')

if [ -z "$name" ]; then
    name="upload_$(/data/local/tmp/linux/bin/busybox date +%s 2>/dev/null || echo $$)"
fi

# Build destination path
if [ -z "$curpath" ]; then
    dest="$WWW/$name"
else
    dest="$WWW/$curpath/$name"
    # Ensure directory exists
    /data/local/tmp/linux/bin/busybox mkdir -p "$WWW/$curpath" 2>/dev/null
fi

# Security: ensure inside WWW
case "$dest" in
    $WWW*) ;;
    *) dest="$WWW/$name" ;;
esac

cat > "$dest"
size=$($L/bin/busybox wc -c < "$dest" 2>/dev/null)
size=${size%% *}
echo "OK: uploaded $name ($size bytes)"