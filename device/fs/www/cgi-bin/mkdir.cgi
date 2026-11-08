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
    echo "Content-type: text/plain; charset=UTF-8"
    echo "Access-Control-Allow-Origin: *"
    echo ""
    echo "ERROR: no folder name given"
    exit 0
fi

# Build full path
if [ -z "$curpath" ]; then
    fullpath="$WWW/$name"
else
    fullpath="$WWW/$curpath/$name"
fi

# Security: ensure inside WWW
case "$fullpath" in
    $WWW*) ;;
    *) fullpath="$WWW/$name" ;;
esac

if [ -e "$fullpath" ]; then
    echo "Content-type: text/plain; charset=UTF-8"
    echo "Access-Control-Allow-Origin: *"
    echo ""
    echo "ERROR: already exists: $name"
    exit 0
fi

# Create directory
/data/local/tmp/linux/bin/busybox mkdir -p "$fullpath" 2>/dev/null
if [ -d "$fullpath" ]; then
    echo "Content-type: text/plain; charset=UTF-8"
    echo "Access-Control-Allow-Origin: *"
    echo ""
    echo "OK: created folder $name"
else
    echo "Content-type: text/plain; charset=UTF-8"
    echo "Access-Control-Allow-Origin: *"
    echo ""
    echo "ERROR: failed to create $name"
fi