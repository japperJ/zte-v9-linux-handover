#!/data/local/tmp/linux/bin/sh
# Start the dropbear SSH daemon on the device's loopback interface.
#
# Reach it from the host with:
#   adb forward tcp:2222 tcp:2222
#   ssh -i ~/.ssh/zte_v9 -p 2222 root@127.0.0.1
#
# dropbear reads the login account from the environment (see ztpw.c), so the
# ZT_* values must be exported before it starts.
# Pass -F to stay in the foreground and log to stderr (handy for debugging).
L=/data/local/tmp/linux

uid=$($L/bin/id -u 2>/dev/null)
[ -z "$uid" ] && uid=2000

export ZT_HOME=$L/root
export ZT_SHELL=$L/bin/sh
export ZT_UID=$uid
export HOME=$L/root
export PATH=$L/bin:$PATH
export TERM=xterm
export ENV=$L/etc/profile

exec $L/sbin/dropbear -r $L/etc/dropbear_rsa_host_key \
	-p 127.0.0.1:2222 -s -P $L/dropbear.pid "$@"
