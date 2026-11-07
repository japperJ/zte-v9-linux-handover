# Shared UI language: sets lang to da or en.
# Query param wins, then cookie, then Danish.
raw_lang=""
case "$QUERY_STRING" in
    *lang=*) raw_lang="${QUERY_STRING#*lang=}"; raw_lang="${raw_lang%%&*}" ;;
esac
if [ "$raw_lang" = "en" ] || [ "$raw_lang" = "da" ]; then
    lang="$raw_lang"
else
    lang="da"
    case "$HTTP_COOKIE" in
        *lang=en*) lang="en" ;;
    esac
fi
