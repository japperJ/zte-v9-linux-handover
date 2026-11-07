#!/data/local/tmp/linux/bin/sh
L=/data/local/tmp/linux
WWW="$L/www"

# Parse params
fname=""
curpath=""
isdir=0
case "$QUERY_STRING" in
  *file=*) fname="${QUERY_STRING#*file=}"; fname="${fname%%&*}" ;;
esac
case "$QUERY_STRING" in
  *path=*) curpath="${QUERY_STRING#*path=}"; curpath="${curpath%%&*}" ;;
esac
case "$QUERY_STRING" in
  *dir=1*) isdir=1 ;;
esac

# URL-decode
fname=$(/data/local/tmp/linux/bin/busybox echo "$fname" | /data/local/tmp/linux/bin/busybox sed 's/%20/ /g; s/+/ /g')
curpath=$(/data/local/tmp/linux/bin/busybox echo "$curpath" | /data/local/tmp/linux/bin/busybox sed 's/%20/ /g; s/%2F/\//g; s/+/ /g')
# Security
curpath=$(/data/local/tmp/linux/bin/busybox echo "$curpath" | /data/local/tmp/linux/bin/busybox sed 's/\.\.//g; s|^/||; s|/$||')
fname=$(/data/local/tmp/linux/bin/busybox echo "$fname" | /data/local/tmp/linux/bin/busybox sed 's/\.\.//g; s/\///g; s/\\//g')

if [ -z "$fname" ]; then
    echo "Content-type: text/plain; charset=UTF-8"
    echo "Access-Control-Allow-Origin: *"
    echo ""
    echo "ERROR: no filename given"
    exit 0
fi

# Build full path
if [ -z "$curpath" ]; then
    target="$WWW/$fname"
else
    target="$WWW/$curpath/$fname"
fi

# Security: ensure inside WWW
case "$target" in
    $WWW*) ;;
    *) target="$WWW/$fname" ;;
esac

# Block system files
case "$fname" in
    index.html|browse.cgi|upload.cgi|chat.cgi|delete.cgi|mkdir.cgi)
        echo "Content-type: text/plain; charset=UTF-8"
        echo "Access-Control-Allow-Origin: *"
        echo ""
        echo "ERROR: cannot delete system file: $fname"
        exit 0
        ;;
esac
case "$fname" in
    cgi-bin)
        echo "Content-type: text/plain; charset=UTF-8"
        echo "Access-Control-Allow-Origin: *"
        echo ""
        echo "ERROR: cannot delete cgi-bin"
        exit 0
        ;;
esac

if [ "$isdir" = "1" ]; then
    if [ ! -d "$target" ]; then
        echo "Content-type: text/plain; charset=UTF-8"
        echo "Access-Control-Allow-Origin: *"
        echo ""
        echo "ERROR: folder not found: $fname"
        exit 0
    fi
    # Only delete if empty
    contents=$(/data/local/tmp/linux/bin/busybox ls -A "$target" 2>/dev/null)
    if [ -n "$contents" ]; then
        echo "Content-type: text/plain; charset=UTF-8"
        echo "Access-Control-Allow-Origin: *"
        echo ""
        echo "ERROR: folder not empty: $fname"
        exit 0
    fi
    /data/local/tmp/linux/bin/busybox rmdir "$target" 2>/dev/null
    if [ -d "$target" ]; then
        echo "Content-type: text/plain; charset=UTF-8"
        echo "Access-Control-Allow-Origin: *"
        echo ""
        echo "ERROR: failed to delete folder $fname"
    else
        echo "Content-type: text/plain; charset=UTF-8"
        echo "Access-Control-Allow-Origin: *"
        echo ""
        echo "OK: deleted folder $fname"
    fi
else
    if [ ! -f "$target" ]; then
        echo "Content-type: text/plain; charset=UTF-8"
        echo "Access-Control-Allow-Origin: *"
        echo ""
        echo "ERROR: file not found: $fname"
        exit 0
    fi
    /data/local/tmp/linux/bin/busybox rm "$target" 2>/dev/null
    if [ -f "$target" ]; then
        echo "Content-type: text/plain; charset=UTF-8"
        echo "Access-Control-Allow-Origin: *"
        echo ""
        echo "ERROR: failed to delete $fname"
    else
        echo "Content-type: text/plain; charset=UTF-8"
        echo "Access-Control-Allow-Origin: *"
        echo ""
        echo "OK: deleted $fname"
    fi
fi