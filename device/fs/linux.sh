#!/data/local/tmp/linux/bin/sh
# Interactive login shell for the V9 Linux userspace.
# Used as the telnetd shell and as ZT_SHELL when a dropbear session falls back
# to a plain login. Exports the environment that Android's shell does not give
# us, then hands over to BusyBox sh.
ROOT=/data/local/tmp/linux
PATH=$ROOT/bin:$ROOT/sbin:/system/bin:/system/xbin
HOME=$ROOT/root
TERM=${TERM:-xterm}
ENV=$ROOT/etc/profile
export ROOT PATH HOME TERM ENV
cd "$HOME" 2>/dev/null
exec $ROOT/bin/sh -i
