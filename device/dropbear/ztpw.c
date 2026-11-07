/*
 * musl resolves accounts by reading /etc/passwd, which this device does not
 * have and which we cannot create without root. Dropbear looks the login name
 * up with getpwnam() at authentication time and again when the session starts,
 * so supply a synthetic account instead. Defining the symbol here means the
 * static linker never pulls musl's implementation in.
 *
 * The home directory drives where authorized_keys is read from, and the shell
 * field decides what gets exec'd, so both are taken from the environment that
 * launches dropbear.
 */
#include <pwd.h>
#include <stdio.h>
#include <stdlib.h>
#include <unistd.h>
#include <sys/types.h>

static struct passwd pw;
static char namebuf[128];
static char dirbuf[512];
static char shellbuf[512];

static void fill(void)
{
	const char *home = getenv("ZT_HOME");
	const char *sh = getenv("ZT_SHELL");
	const char *uid = getenv("ZT_UID");

	if (home == NULL)
		home = "/data/local/tmp/linux/root";
	if (sh == NULL)
		sh = "/data/local/tmp/linux/bin/sh";

	snprintf(dirbuf, sizeof dirbuf, "%s", home);
	snprintf(shellbuf, sizeof shellbuf, "%s", sh);

	pw.pw_passwd = "*";
	pw.pw_uid = uid ? (uid_t)atoi(uid) : getuid();
	pw.pw_gid = uid ? (gid_t)atoi(uid) : getgid();
	pw.pw_gecos = "v9";
	pw.pw_dir = dirbuf;
	pw.pw_shell = shellbuf;
}

struct passwd *getpwnam(const char *name)
{
	fill();
	snprintf(namebuf, sizeof namebuf, "%s", name ? name : "v9");
	pw.pw_name = namebuf;
	return &pw;
}

struct passwd *getpwuid(uid_t uid)
{
	(void)uid;
	fill();
	snprintf(namebuf, sizeof namebuf, "v9");
	pw.pw_name = namebuf;
	return &pw;
}

/*
 * Dropbear also rejects a login whose shell is not listed in /etc/shells.
 * musl falls back to a built-in list when the file is missing, and there is
 * no /etc on this device, so answer the check with the configured shell.
 */
static int shellseen;

void setusershell(void)
{
	shellseen = 0;
}

char *getusershell(void)
{
	if (shellseen++)
		return NULL;
	fill();
	return shellbuf;
}

void endusershell(void)
{
	shellseen = 0;
}
