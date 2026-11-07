<#
.SYNOPSIS
    One command to get back onto the device after a reboot.

.DESCRIPTION
    The device boots into USB mode 19d2:0083, which has no ADB. The ZTE driver
    installer is what re-issues the mode switch to 19d2:1354. After that the
    userspace in /data is still intact, so nothing has to be re-deployed - only
    the daemon has to be started and the adb forwards re-created.

    This script does all of that:
      1. finds the real adb (C:\WINDOWS\adb.exe is a 2010 build that must not be used)
      2. if the device is not visible, re-runs the ZTE driver installer elevated
      3. waits for the device to appear
      4. starts dropbear if it is not already running
      5. (re-)creates the adb forwards for ssh (2222) and telnet (2323)
      6. verifies the SSH login

.PARAMETER Serial
    Device serial. Defaults to V9_Telia.

.PARAMETER Adb
    Path to adb.exe. By default the modern platform-tools build is located
    under %LOCALAPPDATA%\Microsoft\WinGet.

.PARAMETER DriverInstaller
    Path to ZTE_HS_Driver_Setup.exe. Searched for in a few usual places when
    omitted.

.PARAMETER Timeout
    Seconds to wait for the device to show up after the driver runs.

.PARAMETER NoDriver
    Never run the driver installer; just fail if the device is not in ADB mode.

.PARAMETER NoVerify
    Skip the SSH smoke test at the end.

.EXAMPLE
    .\connect.ps1
    .\connect.ps1 -Timeout 180
    .\connect.ps1 -DriverInstaller 'C:\Temp\zte-driver\ZTE_HS_Driver_Setup.exe'
#>
[CmdletBinding()]
param(
    [string]$Serial = 'V9_Telia',
    [string]$Adb,
    [string]$DriverInstaller,
    [int]$Timeout = 120,
    [switch]$NoDriver,
    [switch]$NoVerify
)

$ErrorActionPreference = 'Stop'
$L = '/data/local/tmp/linux'

# --- adb -------------------------------------------------------------------
function Resolve-RealAdb {
    param([string]$Explicit)
    if ($Explicit) {
        if (-not (Test-Path $Explicit)) { throw "adb not found: $Explicit" }
        return (Resolve-Path $Explicit).Path
    }
    $winget = Get-ChildItem "$env:LOCALAPPDATA\Microsoft\WinGet\Packages\Google.PlatformTools_*\platform-tools\adb.exe" `
        -ErrorAction SilentlyContinue | Select-Object -First 1
    if ($winget) { return $winget.FullName }
    foreach ($p in @("$env:ProgramFiles\platform-tools\adb.exe", "$env:LOCALAPPDATA\Android\Sdk\platform-tools\adb.exe")) {
        if (Test-Path $p) { return $p }
    }
    $cmd = Get-Command adb -ErrorAction SilentlyContinue
    if ($cmd) {
        if ($cmd.Source -like '*\Windows\adb.exe') {
            throw "only the 2010 C:\WINDOWS\adb.exe is on PATH; install platform-tools or pass -Adb"
        }
        return $cmd.Source
    }
    throw "adb.exe not found; install Google platform-tools or pass -Adb"
}

$Adb = Resolve-RealAdb -Explicit $Adb
Write-Host "adb: $Adb"

function Invoke-Adb {
    param([Parameter(ValueFromRemainingArguments = $true)][string[]]$Args)
    & $Adb -s $Serial @Args
}
function Get-DeviceState {
    $line = (& $Adb devices) | Select-String -SimpleMatch $Serial | Select-Object -First 1
    if (-not $line) { return $null }
    $parts = ($line.ToString() -split '\s+') | Where-Object { $_ }
    if ($parts.Count -ge 2) { return $parts[1] }
    return $null
}

# --- driver mode switch ----------------------------------------------------
function Find-DriverInstaller {
    if ($DriverInstaller) {
        if (-not (Test-Path $DriverInstaller)) { throw "driver installer not found: $DriverInstaller" }
        return (Resolve-Path $DriverInstaller).Path
    }
    $candidates = @(
        "$env:TEMP\zte-driver\ZTE_HS_Driver_Setup.exe",
        "C:\ZTE\ZTE_HS_Driver_Setup.exe",
        "$env:USERPROFILE\Downloads\ZTE_HS_Driver_Setup.exe"
    )
    $found = $candidates | Where-Object { Test-Path $_ } | Select-Object -First 1
    if ($found) { return $found }
    $hit = Get-ChildItem 'C:\Program Files (x86)\ZTE', 'C:\Program Files\ZTE' `
        -Recurse -Filter 'ZTE_HS_Driver_Setup.exe' -ErrorAction SilentlyContinue |
        Select-Object -First 1
    if ($hit) { return $hit.FullName }
    return $null
}

function Invoke-DriverModeSwitch {
    $exe = Find-DriverInstaller
    if (-not $exe) {
        throw "device is not in ADB mode and ZTE_HS_Driver_Setup.exe was not found; pass -DriverInstaller"
    }
    Write-Host "== switching USB mode via $exe"
    $p = Start-Process -FilePath $exe `
        -ArgumentList '/VERYSILENT', '/SUPPRESSMSGBOXES', '/NORESTART', '/SP-' `
        -Verb RunAs -PassThru
    $null = $p.WaitForExit(300000)
    Write-Host "   installer exited: $($p.ExitCode)"
}

# --- main ------------------------------------------------------------------
$state = Get-DeviceState
if ($state -ne 'device') {
    Write-Host "== device '$Serial' not in ADB mode (state: $($state ?? 'absent'))"
    if ($NoDriver) { throw "device not in ADB mode and -NoDriver was given" }
    Invoke-DriverModeSwitch

    $deadline = (Get-Date).AddSeconds($Timeout)
    while ((Get-Date) -lt $deadline) {
        Start-Sleep -Seconds 3
        $state = Get-DeviceState
        if ($state -eq 'device') { break }
    }
    if ($state -ne 'device') {
        $usb = Get-PnpDevice -PresentOnly -ErrorAction SilentlyContinue |
            Where-Object { $_.InstanceId -like 'USB\VID_19D2*' } |
            Select-Object Status, Class, FriendlyName, InstanceId
        throw "device did not come back in ADB mode after $Timeout s; USB devices seen: $(($usb | Format-Table -AutoSize | Out-String).Trim())"
    }
}

$model = (Invoke-Adb shell getprop ro.product.model) -join ''
$sdk = (Invoke-Adb shell getprop ro.build.version.sdk) -join ''
Write-Host "== connected: $($model.Trim()) (SDK $($sdk.Trim()))"

# --- daemon ----------------------------------------------------------------
# Two daemons can exist: the shell one started by deploy.ps1 (127.0.0.1:2222,
# uid 2000) and the one started by the boot APK (0.0.0.0:2222, app uid). Only
# one can own the port, so test /proc/net/tcp instead of pid files.
function Get-PortListener {
    param([int]$Port)
    $hex = '{0:X4}' -f $Port
    $tcp = (Invoke-Adb shell 'cat /proc/net/tcp') -join "`n"
    foreach ($line in ($tcp -split "`n")) {
        $f = ($line.Trim() -split '\s+')
        if ($f.Count -ge 10 -and $f[1] -match ":$hex$" -and $f[3] -eq '0A') {
            return [pscustomobject]@{ Address = $f[1]; Uid = $f[7] }
        }
    }
    return $null
}

$listener = Get-PortListener -Port 2222
if ($listener) {
    $owner = if ($listener.Uid -eq '2000') { 'shell daemon' } else { "uid $($listener.Uid) (boot APK)" }
    Write-Host "== dropbear already listening on 2222 - $owner"
} else {
    Write-Host '== starting dropbear'
    $log = Join-Path $env:TEMP 'v9-dropbear-start.log'
    Start-Process -FilePath $Adb `
        -ArgumentList @('-s', $Serial, 'shell', "$L/bin/sh $L/start-ssh.sh; $L/bin/busybox sleep 600") `
        -WindowStyle Hidden -RedirectStandardOutput $log -RedirectStandardError "$log.err" | Out-Null
    Start-Sleep -Seconds 3
    $listener = Get-PortListener -Port 2222
    if ($listener) {
        Write-Host "   dropbear listening (uid $($listener.Uid))"
    } else {
        throw "dropbear did not start; see $log and $log.err"
    }
}

# --- forwards --------------------------------------------------------------
Write-Host '== forwarding ports'
Invoke-Adb forward tcp:2222 tcp:2222 | Out-Null
Invoke-Adb forward tcp:2323 tcp:2323 | Out-Null

# --- verify ----------------------------------------------------------------
if (-not $NoVerify) {
    $key = @("$env:USERPROFILE\.ssh\zte_v9_ed", "$env:USERPROFILE\.ssh\zte_v9") |
        Where-Object { Test-Path $_ } | Select-Object -First 1
    if (-not $key) {
        Write-Warning 'no host key found in %USERPROFILE%\.ssh; skipping the SSH smoke test'
    } elseif (-not (Get-Command ssh -ErrorAction SilentlyContinue)) {
        Write-Warning 'ssh client not found; skipping the SSH smoke test'
    } else {
        $who = (& ssh -i $key -p 2222 -o BatchMode=yes -o StrictHostKeyChecking=no `
                -o UserKnownHostsFile=NUL -o LogLevel=ERROR -o ConnectTimeout=8 root@127.0.0.1 'id -u; uname -r' 2>&1) -join ' '
        if ($LASTEXITCODE -eq 0) {
            Write-Host "== SSH ok: uid/kernel = $($who.Trim())"
        } else {
            Write-Warning "SSH smoke test failed: $who"
        }
    }
}

Write-Host '== ready'
Write-Host '   ssh -i ~/.ssh/zte_v9 -p 2222 root@127.0.0.1'
Write-Host '   telnet 127.0.0.1 2323'
