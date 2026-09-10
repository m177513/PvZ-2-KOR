$ErrorActionPreference = 'Stop'
Set-Location -LiteralPath $PSScriptRoot
try {
    $pythonCommand = Get-Command py -ErrorAction SilentlyContinue
    $pythonArgs = @('-3')
    if (-not $pythonCommand) {
        $pythonCommand = Get-Command python -ErrorAction SilentlyContinue
        $pythonArgs = @()
    }
    if (-not $pythonCommand) { throw 'Install Python 3.11+ first. See README-KO.md.' }
    & $pythonCommand.Source @pythonArgs -c 'import sys; sys.exit(0 if sys.version_info >= (3,11) else 1)'
    if ($LASTEXITCODE -ne 0) { throw 'Python 3.11+ is required.' }
    $adbPath = Join-Path $PSScriptRoot 'platform-tools\adb.exe'
    if (-not (Test-Path -LiteralPath $adbPath)) {
        $adbCommand = Get-Command adb -ErrorAction SilentlyContinue
        if ($adbCommand) { $adbPath = $adbCommand.Source }
        else { $adbPath = (Read-Host 'Full path to adb.exe (see README-KO.md)').Trim('"') }
    }
    if (-not (Test-Path -LiteralPath $adbPath)) { throw 'adb.exe not found.' }
    $devices = & $adbPath devices
    if ($LASTEXITCODE -ne 0) { throw 'adb devices failed.' }
    $serials = @($devices | ForEach-Object { if ($_ -match '^(\S+)\s+device\s*$') { $Matches[1] } })
    if ($serials.Count -eq 0) { throw 'Connect phone and authorize USB debugging, then retry.' }
    if ($serials.Count -eq 1) { $deviceSerial = $serials[0] }
    else {
        $serials | ForEach-Object { Write-Host $_ }
        $deviceSerial = Read-Host 'Choose one device serial from the list'
        if ($serials -notcontains $deviceSerial) { throw 'Device serial is not in the list.' }
    }
    Write-Host 'Installing Korean beta. Keep USB connected and do not open the game until finished.'
    & $pythonCommand.Source @pythonArgs (Join-Path $PSScriptRoot 'release_patch.py') install --adb $adbPath --serial $deviceSerial
    if ($LASTEXITCODE -ne 0) { throw 'Installation failed. Keep backups and read the error above.' }
    Write-Host 'Finished. You can open the game on the phone.'
} catch {
    Write-Host $_.Exception.Message -ForegroundColor Red
    exit 1
}
