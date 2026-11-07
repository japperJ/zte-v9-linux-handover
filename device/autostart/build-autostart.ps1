<#
.SYNOPSIS
    Build the tiny boot APK that starts the userspace after a reboot.

.DESCRIPTION
    Uses only tools from the Android SDK (aapt2, d8, zipalign, apksigner) plus a
    JDK. No Gradle, no network access.

    The APK contains an assets/authorized_keys copied from the host's
    %USERPROFILE%\.ssh keys, so the app can install it into its own home
    directory on first run.

    Output: autostart/bin/v9boot.apk (and a keystore next to it on first run).

.PARAMETER Sdk
    Android SDK root. Defaults to %LOCALAPPDATA%\Android\Sdk.

.PARAMETER Jdk
    JDK with javac. Defaults to Android Studio's bundled JBR, then PATH.

.PARAMETER KeyStore
    Keystore used for signing. Created on first run if missing. Keep it: app
    updates must be signed with the same key.

.PARAMETER Rebuild
    Ignore cached intermediate build output.
#>
[CmdletBinding()]
param(
    [string]$Sdk,
    [string]$Jdk,
    [string]$KeyStore,
    [switch]$Rebuild
)

$ErrorActionPreference = 'Stop'
$here = Split-Path -Parent $MyInvocation.MyCommand.Path
$build = Join-Path $here 'build'
$out = Join-Path $here 'bin'

function Find-Sdk {
    param([string]$Explicit)
    $candidates = @(
        $Explicit,
        $env:ANDROID_HOME,
        $env:ANDROID_SDK_ROOT,
        "$env:LOCALAPPDATA\Android\Sdk",
        "$env:ProgramFiles\Android\Sdk"
    ) | Where-Object { $_ }
    foreach ($c in $candidates) {
        if (Test-Path (Join-Path $c 'build-tools')) { return (Resolve-Path $c).Path }
    }
    throw 'Android SDK not found; pass -Sdk'
}

function Find-Jdk {
    param([string]$Explicit)
    $candidates = @(
        $Explicit,
        "$env:ProgramFiles\Android\Android Studio\jbr",
        $env:JAVA_HOME
    ) | Where-Object { $_ }
    foreach ($c in $candidates) {
        $javac = Join-Path $c 'bin\javac.exe'
        if (Test-Path $javac) { return $c }
    }
    $cmd = Get-Command javac -ErrorAction SilentlyContinue
    if ($cmd) { return (Split-Path -Parent (Split-Path -Parent $cmd.Source)) }
    throw 'javac not found; pass -Jdk'
}

$Sdk = Find-Sdk -Explicit $Sdk
$Jdk = Find-Jdk -Explicit $Jdk

# The .bat wrappers around d8/apksigner look for java through JAVA_HOME.
$env:JAVA_HOME = $Jdk
$env:PATH = "$Jdk\bin;$env:PATH"

# Highest build-tools version, compared as a version number.
function Get-VersionKey {
    param([string]$Name)
    $v = $Name -replace '^[^0-9]*', ''   # android-34 -> 34, 36.1.0 -> 36.1.0
    $v = $v -replace '[^0-9.].*$', ''
    if ($v -notmatch '^\d+(\.\d+)*$') { return [version]'0.0' }
    if ($v -notmatch '\.') { $v = "$v.0" }   # [version] needs at least major.minor
    return [version]$v
}

$buildTools = Get-ChildItem (Join-Path $Sdk 'build-tools') -Directory |
    Sort-Object { Get-VersionKey $_.Name } -Descending |
    Select-Object -First 1
if (-not $buildTools) { throw "no build-tools under $Sdk" }

$platform = Get-ChildItem (Join-Path $Sdk 'platforms') -Directory |
    Sort-Object { Get-VersionKey $_.Name } -Descending |
    Select-Object -First 1
if (-not $platform) { throw "no platforms under $Sdk" }

$aapt2 = Join-Path $buildTools.FullName 'aapt2.exe'
$d8 = Join-Path $buildTools.FullName 'd8.bat'
$zipalign = Join-Path $buildTools.FullName 'zipalign.exe'
$apksigner = Join-Path $buildTools.FullName 'apksigner.bat'
$javac = Join-Path $Jdk 'bin\javac.exe'
$keytool = Join-Path $Jdk 'bin\keytool.exe'
$jar = Join-Path $platform.FullName 'android.jar'

foreach ($tool in @($aapt2, $d8, $zipalign, $apksigner, $javac, $keytool, $jar)) {
    if (-not (Test-Path $tool)) { throw "missing build tool: $tool" }
}

Write-Host "sdk:      $Sdk"
Write-Host "build:    $($buildTools.Name)"
Write-Host "platform: $($platform.Name)"
Write-Host "jdk:      $Jdk"

if ($Rebuild -and (Test-Path $build)) { Remove-Item $build -Recurse -Force }
$null = New-Item -ItemType Directory -Force -Path $build, $out
$classes = Join-Path $build 'classes'
$dexOut = Join-Path $build 'dex'
$assets = Join-Path $here 'assets'
$null = New-Item -ItemType Directory -Force -Path $classes, $dexOut, $assets

# --- assets: the host public keys the app installs into its own home ---------
$pubKeys = @("$env:USERPROFILE\.ssh\zte_v9.pub", "$env:USERPROFILE\.ssh\zte_v9_ed.pub") |
    Where-Object { Test-Path $_ }
if ($pubKeys.Count -eq 0) {
    throw 'no host public keys found (expected ~/.ssh/zte_v9.pub or ~/.ssh/zte_v9_ed.pub)'
}
$lines = foreach ($k in $pubKeys) { (Get-Content $k -Raw).Trim() }
$keysFile = Join-Path $assets 'authorized_keys'
[IO.File]::WriteAllText($keysFile, ($lines -join "`n") + "`n", (New-Object System.Text.UTF8Encoding($false)))
Write-Host "assets:   $($pubKeys.Count) key(s) -> authorized_keys"

# --- compile ----------------------------------------------------------------
Write-Host '== javac'
$sources = (Get-ChildItem (Join-Path $here 'src') -Recurse -Filter '*.java').FullName
& $javac -encoding UTF-8 --release 8 -Xlint:-options -classpath $jar -d $classes $sources
if ($LASTEXITCODE -ne 0) { throw 'javac failed' }

# --- dex --------------------------------------------------------------------
Write-Host '== d8'
$classFiles = (Get-ChildItem $classes -Recurse -Filter '*.class').FullName
& $d8 --min-api 7 --lib $jar --output $dexOut $classFiles
if ($LASTEXITCODE -ne 0) { throw 'd8 failed' }

# --- resources / manifest ---------------------------------------------------
Write-Host '== aapt2 link'
$baseApk = Join-Path $build 'base.apk'
if (Test-Path $baseApk) { Remove-Item $baseApk -Force }
& $aapt2 link -o $baseApk -I $jar --manifest (Join-Path $here 'AndroidManifest.xml') `
    -A $assets --min-sdk-version 7 --target-sdk-version 7 --version-code 1 --version-name '1.0'
if ($LASTEXITCODE -ne 0) { throw 'aapt2 link failed' }

# --- add classes.dex --------------------------------------------------------
Write-Host '== packaging classes.dex'
Add-Type -AssemblyName System.IO.Compression.FileSystem
$zip = [IO.Compression.ZipFile]::Open($baseApk, 'Update')
try {
    $existing = $zip.GetEntry('classes.dex')
    if ($existing) { $existing.Delete() }
    $null = [IO.Compression.ZipFileExtensions]::CreateEntryFromFile(
        $zip, (Join-Path $dexOut 'classes.dex'), 'classes.dex', 'Optimal')
} finally {
    $zip.Dispose()
}

# --- align + sign -----------------------------------------------------------
Write-Host '== zipalign'
$aligned = Join-Path $build 'aligned.apk'
if (Test-Path $aligned) { Remove-Item $aligned -Force }
& $zipalign -f 4 $baseApk $aligned
if ($LASTEXITCODE -ne 0) { throw 'zipalign failed' }

if (-not $KeyStore) { $KeyStore = Join-Path $here 'v9boot.keystore' }
if (-not (Test-Path $KeyStore)) {
    Write-Host "== creating keystore $KeyStore"
    & $keytool -genkeypair -keystore $KeyStore -storetype PKCS12 -alias v9boot `
        -keyalg RSA -keysize 2048 -validity 10000 `
        -dname 'CN=V9 Boot, O=zte-v9-linux-handover' `
        -storepass android -keypass android
    if ($LASTEXITCODE -ne 0) { throw 'keytool failed' }
}

Write-Host '== apksigner'
$apk = Join-Path $out 'v9boot.apk'
if (Test-Path $apk) { Remove-Item $apk -Force }
& $apksigner sign --ks $KeyStore --ks-key-alias v9boot `
    --ks-pass pass:android --key-pass pass:android `
    --min-sdk-version 7 --v1-signing-enabled true `
    --v2-signing-enabled false --v3-signing-enabled false `
    --out $apk $aligned
if ($LASTEXITCODE -ne 0) { throw 'apksigner failed' }

& $apksigner verify --min-sdk-version 7 --print-certs $apk | Select-Object -First 4
if ($LASTEXITCODE -ne 0) { throw 'apksigner verify failed' }

$size = (Get-Item $apk).Length
Write-Host ("== built {0} ({1:N0} bytes)" -f $apk, $size)
