#!/data/local/tmp/linux/bin/sh
L=/data/local/tmp/linux
WWW="$L/www"

# Get filename from query string
fname=""
case "$QUERY_STRING" in
  file=*) fname="${QUERY_STRING#file=}" ;;
esac

# URL-decode
fname=$(/data/local/tmp/linux/bin/busybox echo "$fname" | /data/local/tmp/linux/bin/busybox sed 's/%20/ /g; s/+/ /g')
# Security: strip path separators and dangerous sequences
fname=$(/data/local/tmp/linux/bin/busybox echo "$fname" | /data/local/tmp/linux/bin/busybox sed 's/\.\.//g; s/\///g; s/\\//g')

# Validate
if [ -z "$fname" ]; then
    echo "Content-type: text/plain; charset=UTF-8"
    echo "Access-Control-Allow-Origin: *"
    echo ""
    echo "ERROR: no filename given"
    exit 0
fi

target="$WWW/$fname"

# Security: ensure target is inside www and is a regular file (not cgi-bin)
case "$fname" in
    index.html|browse.cgi|upload.cgi|chat.cgi|delete.cgi) 
        echo "Content-type: text/plain; charset=UTF-8"
        echo "Access-Control-Allow-Origin: *"
        echo ""
        echo "ERROR: cannot delete system file: $fname"
        exit 0
        ;;
esac
case "$fname" in
    cgi-bin*) 
        echo "Content-type: text/plain; charset=UTF-8"
        echo "Access-Control-Allow-Origin: *"
        echo ""
        echo "ERROR: cannot delete from cgi-bin"
        exit 0
        ;;
esac

if [ ! -f "$target" ]; then
    echo "Content-type: text/plain; charset=UTF-8"
    echo "Access-Control-Allow-Origin: *"
    echo ""
    echo "ERROR: file not found: $fname"
    exit 0
fi

# Delete the file
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