<#
.SYNOPSIS
    Deploy the rootless Linux userspace (BusyBox + dropbear) to a ZTE V9 over ADB.

.DESCRIPTION
    Pushes BusyBox, the login scripts and the cross-built dropbear to
    /data/local/tmp/linux, creates the applet symlinks, generates the host key
    if needed, and starts sshd on 127.0.0.1:2222.

    Requires:
      device/vendor/busybox-armv5l          (see README for the download)
      device-dropbear build output           (run device/build-dropbear.sh first)

.EXAMPLE
    .\deploy.ps1
    .\deploy.ps1 -Serial V9_Telia -NoStart
#>
[CmdletBinding()]
param(
    [string]$Serial = 'V9_Telia',
    [string]$Adb,
    [string]$PublicKeyPath,
    [string]$BuildDir,
    [switch]$NoStart
)

$ErrorActionPreference = 'Stop'
$here = Split-Path -Parent $MyInvocation.MyCommand.Path
$root = Split-Path -Parent $here
$L = '/data/local/tmp/linux'

if (-not $Adb) {
    $candidates = @(
        "$env:LOCALAPPDATA\Microsoft\WinGet\Packages\Google.PlatformTools_Microsoft.Winget.Source_8wekyb3d8bbwe\platform-tools\adb.exe",
        "$env:ProgramFiles\platform-tools\adb.exe"
    )
    $Adb = $candidates | Where-Object { Test-Path $_ } | Select-Object -First 1
    if (-not $Adb) { $Adb = 'adb' }
}

function Invoke-Adb {
    param([Parameter(ValueFromRemainingArguments = $true)][string[]]$Args)
    & $Adb -s $Serial @Args
}

function Push-File {
    param([string]$Local, [string]$Remote)
    if (-not (Test-Path $Local)) { throw "missing local file: $Local" }
    Invoke-Adb push $Local $Remote | Out-Null
}

Write-Host '== waiting for device'
Invoke-Adb wait-for-device | Out-Null
$model = (Invoke-Adb shell getprop ro.product.model) -join ''
Write-Host "   connected: $model"

Write-Host '== creating directory tree'
Invoke-Adb shell "mkdir -p $L/bin $L/sbin $L/etc $L/root/.ssh $L/tmp" | Out-Null
Invoke-Adb shell "chmod 755 $L/root; chmod 700 $L/root/.ssh" | Out-Null

Write-Host '== installing BusyBox'
$busybox = Join-Path $here 'vendor\busybox-armv5l'
if (Test-Path $busybox) {
    Push-File $busybox "$L/bin/busybox"
    Invoke-Adb shell "chmod 755 $L/bin/busybox" | Out-Null
} elseif (-not ((Invoke-Adb shell "test -f $L/bin/busybox && echo yes") -join '').Trim()) {
    throw "no $busybox and no BusyBox on the device - see README for the download"
}
Invoke-Adb shell "chmod 755 $L/bin/busybox; cd $L/bin || exit 1; ./busybox --install -s ." | Out-Null
$n = (Invoke-Adb shell "$L/bin/busybox ls $L/bin | $L/bin/busybox wc -l") -join ''
Write-Host "   applets installed: $($n.Trim())"

Write-Host '== installing login scripts'
# BusyBox ash treats a stray CR as part of the command; normalize on the way out
# so a Windows checkout with autocrlf still produces usable scripts.
foreach ($name in 'profile', 'linux.sh', 'start-ssh.sh') {
    $src = Join-Path $here "fs\$name"
    if (-not (Test-Path $src)) { throw "missing local file: $src" }
    $stage = Join-Path $env:TEMP "v9-$name"
    [IO.File]::WriteAllText($stage, (([IO.File]::ReadAllText($src)) -replace "`r`n", "`n"),
        (New-Object System.Text.UTF8Encoding($false)))
    $dest = if ($name -eq 'profile') { "$L/etc/profile" } else { "$L/$name" }
    Push-File $stage $dest
}
Invoke-Adb shell "chmod 755 $L/linux.sh $L/start-ssh.sh" | Out-Null

Write-Host '== installing web files'
$www = Join-Path $here 'fs\www'
if (Test-Path $www) {
    Invoke-Adb shell "mkdir -p $L/www/cgi-bin" | Out-Null
    Get-ChildItem (Join-Path $www '*') -File | ForEach-Object {
        $dest = "$L/www/$($_.Name)"
        Push-File $_.FullName $dest
    }
    Get-ChildItem (Join-Path $www 'cgi-bin' '*') -File -ErrorAction SilentlyContinue | ForEach-Object {
        $dest = "$L/www/cgi-bin/$($_.Name)"
        Push-File $_.FullName $dest
        Invoke-Adb shell "chmod 755 $dest" | Out-Null
    }
    Write-Host '   web root ready'
}

Write-Host '== installing dropbear'
if (-not $BuildDir) { $BuildDir = Join-Path $root 'dropbear-2022.83' }
if (-not (Test-Path (Join-Path $BuildDir 'dropbear'))) {
    throw "no dropbear build in $BuildDir - run device/build-dropbear.sh or pass -BuildDir"
}
Push-File (Join-Path $BuildDir 'dropbear') "$L/sbin/dropbear"
Push-File (Join-Path $BuildDir 'dropbearkey') "$L/sbin/dropbearkey"
Invoke-Adb shell "chmod 755 $L/sbin/dropbear $L/sbin/dropbearkey" | Out-Null

$haveKey = (Invoke-Adb shell "test -f $L/etc/dropbear_rsa_host_key && echo yes") -join ''
if ($haveKey.Trim() -ne 'yes') {
    Write-Host '== generating RSA host key'
    Invoke-Adb shell "$L/sbin/dropbearkey -t rsa -s 2048 -f $L/etc/dropbear_rsa_host_key" | Out-Null
}
# The boot APK runs as a different uid and reuses this key so the host
# fingerprint stays stable. Make it readable to that uid.
Invoke-Adb shell "chmod 644 $L/etc/dropbear_rsa_host_key" | Out-Null

$pubKeys = @($PublicKeyPath | Where-Object { $_ } | Where-Object { Test-Path $_ })
if ($pubKeys.Count -eq 0) {
    $pubKeys = @("$env:USERPROFILE\.ssh\zte_v9.pub", "$env:USERPROFILE\.ssh\zte_v9_ed.pub") |
        Where-Object { Test-Path $_ }
}
if ($pubKeys.Count -gt 0) {
    Write-Host "== installing authorized_keys ($($pubKeys.Count) key(s))"
    $tmp = Join-Path $env:TEMP 'v9-authorized_keys'
    $lines = foreach ($k in $pubKeys) { (Get-Content $k) -join "`n" }
    [IO.File]::WriteAllText($tmp, ($lines -join "`n") + "`n")
    Push-File $tmp "$L/root/.ssh/authorized_keys"
    Invoke-Adb shell "chmod 600 $L/root/.ssh/authorized_keys" | Out-Null
} elseif (-not ((Invoke-Adb shell "test -f $L/root/.ssh/authorized_keys && echo yes") -join '').Trim()) {
    Write-Warning "no public keys found and no authorized_keys on the device - public key auth will fail"
}

if ($NoStart) {
    Write-Host '== skipping daemon start (-NoStart)'
    return
}

Write-Host '== starting dropbear'
# The boot APK (device/autostart) runs its own daemon as the app uid on
# 0.0.0.0:2222. uid 2000 cannot kill it, and a second daemon cannot bind the
# port, so detect an existing listener first and leave it alone.
$tcp = (Invoke-Adb shell 'cat /proc/net/tcp') -join "`n"
$busy = $false
foreach ($line in ($tcp -split "`n")) {
    $f = ($line.Trim() -split '\s+')
    if ($f.Count -ge 10 -and $f[1] -match ':08AE$' -and $f[3] -eq '0A') { $busy = $true; break }
}
if ($busy) {
    Write-Host '   port 2222 already has a listener (boot APK or an earlier daemon); not starting another'
} else {
    Invoke-Adb shell "$L/bin/busybox killall dropbear 2>/dev/null; true" | Out-Null
    Start-Sleep -Milliseconds 500

    # adb shell allocates a pty and never reports EOF once dropbear daemonizes, so
    # fire it off detached and let the daemon detach itself from the pty.
    $log = Join-Path $env:TEMP 'v9-dropbear-start.log'
    Start-Process -FilePath $Adb `
        -ArgumentList @('-s', $Serial, 'shell', "$L/bin/sh $L/start-ssh.sh; $L/bin/busybox sleep 600") `
        -WindowStyle Hidden -RedirectStandardOutput $log -RedirectStandardError "$log.err"
    Start-Sleep -Seconds 3

    $dbPid = (Invoke-Adb shell "cat $L/dropbear.pid 2>/dev/null") -join ''
    if ($dbPid.Trim() -match '^\d+$') {
        Write-Host "   dropbear running, pid $($dbPid.Trim())"
    } else {
        Write-Warning "dropbear did not start; see $log"
    }
}

Invoke-Adb forward tcp:2222 tcp:2222 | Out-Null
Write-Host '== ready'
Write-Host '   ssh -i ~/.ssh/zte_v9 -p 2222 root@127.0.0.1'
