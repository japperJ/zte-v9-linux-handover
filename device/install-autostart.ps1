<#
.SYNOPSIS
    Install (or update) the boot APK that auto-starts the userspace.

.DESCRIPTION
    Builds nothing - run autostart\build-autostart.ps1 first. Then:
      * installs bin\v9boot.apk with adb install -r
      * stops a shell-owned dropbear so the APK's daemon can own port 2222
      * triggers the service now (Android 2.1's `am` has no startservice, so an
        explicit broadcast is used)
      * shows the service log and verifies the listener

    After a reboot the receiver starts the service by itself; this script is only
    needed to install or to restart the daemon by hand.

    Note on hangs: several 2.1 shell commands (`am`, `pm`, `install`) leave the
    pty open after printing their result, so every adb shell call here is run
    with a host-side timeout and its output is read back from a file.

.PARAMETER Serial
    Device serial. Defaults to V9_Telia.

.PARAMETER Adb
    Path to adb.exe.

.PARAMETER Apk
    APK to install. Defaults to autostart\bin\v9boot.apk.
#>
[CmdletBinding()]
param(
    [string]$Serial = 'V9_Telia',
    [string]$Adb,
    [string]$Apk
)

$ErrorActionPreference = 'Stop'
$here = Split-Path -Parent $MyInvocation.MyCommand.Path
$L = '/data/local/tmp/linux'
$pkg = 'com.zte.v9boot'

if (-not $Apk) { $Apk = Join-Path $here 'autostart\bin\v9boot.apk' }
if (-not (Test-Path $Apk)) { throw "no APK at $Apk - run autostart\build-autostart.ps1 first" }

if (-not $Adb) {
    $found = Get-ChildItem "$env:LOCALAPPDATA\Microsoft\WinGet\Packages\Google.PlatformTools_*\platform-tools\adb.exe" `
        -ErrorAction SilentlyContinue | Select-Object -First 1
    if ($found) { $Adb = $found.FullName }
    elseif (Test-Path "$env:LOCALAPPDATA\Android\Sdk\platform-tools\adb.exe") {
        $Adb = "$env:LOCALAPPDATA\Android\Sdk\platform-tools\adb.exe"
    } else { $Adb = 'adb' }
}

# Run adb with a hard host-side timeout. Returns captured output.
function Invoke-AdbTimed {
    param(
        [string[]]$AdbArgs,
        [int]$TimeoutSeconds = 20
    )
    $psi = [System.Diagnostics.ProcessStartInfo]::new($Adb)
    foreach ($a in (@('-s', $Serial) + $AdbArgs)) { $psi.ArgumentList.Add($a) }
    $psi.UseShellExecute = $false
    $psi.RedirectStandardOutput = $true
    $psi.RedirectStandardError = $true
    $proc = [System.Diagnostics.Process]::new()
    $proc.StartInfo = $psi
    $null = $proc.Start()
    $outTask = $proc.StandardOutput.ReadToEndAsync()
    $errTask = $proc.StandardError.ReadToEndAsync()
    if (-not $proc.WaitForExit($TimeoutSeconds * 1000)) {
        try { $proc.Kill() } catch { }
        Write-Verbose "adb $($AdbArgs -join ' ') timed out after $TimeoutSeconds s"
    }
    $null = $proc.WaitForExit(5000)
    $text = @()
    $text += ($outTask.Result -split "`r?`n" | Where-Object { $_ -ne '' })
    $text += ($errTask.Result -split "`r?`n" | Where-Object { $_ -ne '' })
    return $text
}

function Invoke-AdbShell {
    param([string]$Command, [int]$TimeoutSeconds = 20)
    return Invoke-AdbTimed -AdbArgs @('shell', $Command) -TimeoutSeconds $TimeoutSeconds
}

Write-Host "== installing $Apk"
$installOut = Invoke-AdbTimed -AdbArgs @('install', '-r', $Apk) -TimeoutSeconds 120
if ((($installOut -join "`n") -notmatch 'Success')) {
    throw "adb install did not report Success: $($installOut -join ' ')"
}
$path = (Invoke-AdbShell "pm path $pkg") -join ''
Write-Host "   installed: $($path.Trim())"

# The APK's daemon binds 0.0.0.0:2222. If the shell daemon from deploy.ps1 still
# owns the port, the new one cannot bind, so stop it first.
$pidFile = (Invoke-AdbShell "cat $L/dropbear.pid 2>/dev/null") -join ''
if ($pidFile.Trim() -match '^\d+$') {
    $alive = (Invoke-AdbShell "test -d /proc/$($pidFile.Trim()) && echo yes") -join ''
    if ($alive.Trim() -eq 'yes') {
        Write-Host "== stopping shell-owned dropbear (pid $($pidFile.Trim()))"
        # shell can only kill its own processes; if this is the app daemon the
        # kill is silently denied and the broadcast below does nothing harmful.
        $null = Invoke-AdbShell "kill $($pidFile.Trim()) 2>/dev/null; true"
        Start-Sleep -Seconds 2
    }
}

Write-Host '== triggering the boot service'
# Android 2.1 `am` only knows start/broadcast/instrument/profile. An explicit
# broadcast reaches the receiver without needing an intent-filter match.
$null = Invoke-AdbShell "am broadcast -a com.zte.v9boot.START -n $pkg/.BootReceiver" -TimeoutSeconds 15
Start-Sleep -Seconds 4

Write-Host '== V9Boot log'
(Invoke-AdbTimed -AdbArgs @('logcat', '-d', '-s', 'V9Boot:*') -TimeoutSeconds 15) |
    Select-Object -Last 20

# Verify the listener and who owns it.
$hex = '{0:X4}' -f 2222
$tcp = (Invoke-AdbShell 'cat /proc/net/tcp') -join "`n"
$listen = $null
foreach ($line in ($tcp -split "`n")) {
    $f = ($line.Trim() -split '\s+')
    if ($f.Count -ge 10 -and $f[1] -match ":$hex$" -and $f[3] -eq '0A') { $listen = $f; break }
}
if ($listen) {
    if ($listen[7] -eq '2000') {
        Write-Warning 'port 2222 is owned by uid 2000 - the shell daemon won, not the APK'
    } else {
        Write-Host "== dropbear listening on 0.0.0.0:2222 as uid $($listen[7])"
    }
} else {
    throw 'nothing is listening on 2222; check the V9Boot log above'
}

$null = Invoke-AdbTimed -AdbArgs @('forward', 'tcp:2222', 'tcp:2222') -TimeoutSeconds 10
Write-Host '== ready'
Write-Host '   ssh -i ~/.ssh/zte_v9 -p 2222 root@127.0.0.1'
