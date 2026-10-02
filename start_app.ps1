$ErrorActionPreference = 'Stop'

$root = Split-Path -Parent $MyInvocation.MyCommand.Path
$backendDir = Join-Path $root "backend"
$frontendDir = Join-Path $root "frontend"
$feLog = Join-Path $env:TEMP "job-lister-frontend.log"

# start backend hidden
$backend = Start-Process -FilePath "python" -ArgumentList "main.py" `
    -WorkingDirectory $backendDir -WindowStyle Hidden -PassThru

# start frontend hidden, log output so we can read the actual dev-server URL
$frontend = Start-Process -FilePath "cmd.exe" -ArgumentList "/c npm run dev > `"$feLog`" 2>&1" `
    -WorkingDirectory $frontendDir -WindowStyle Hidden -PassThru

# vite.config.js pins the port with strictPort, so it's always this -- just
# wait for it to come up instead of scraping the URL from vite's own log
# (that log is ANSI-colored, which splits "Local:" and silently breaks a
# regex match, so this used to lock onto vite's OLD default port forever).
$feUrl = "http://localhost:5180"
$deadline = (Get-Date).AddSeconds(30)
while ((Get-Date) -lt $deadline) {
    if (Test-NetConnection -ComputerName localhost -Port 5180 -InformationLevel Quiet -WarningAction SilentlyContinue) { break }
    Start-Sleep -Milliseconds 500
}
Start-Sleep -Seconds 1

# open frontend in its own dedicated browser window/process (own profile so
# it doesn't just become a tab in an already-running browser)
$profileDir = Join-Path $env:TEMP "job-lister-app-profile"
$edge = "C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe"
$chrome = "C:\Program Files\Google\Chrome\Application\chrome.exe"
$browserExe = if (Test-Path $edge) { $edge } elseif (Test-Path $chrome) { $chrome } else { $null }

if ($browserExe) {
    $browser = Start-Process -FilePath $browserExe `
        -ArgumentList "--app=$feUrl", "--user-data-dir=$profileDir", "--start-maximized" -PassThru
    $browser.WaitForExit()
} else {
    Start-Process $feUrl
    # no dedicated window to watch -> just wait for the backend/frontend processes directly
    Wait-Process -Id $backend.Id, $frontend.Id -ErrorAction SilentlyContinue
}

# browser window closed -> stop backend + frontend (and their child processes)
foreach ($p in @($backend.Id, $frontend.Id)) {
    if ($p) {
        Start-Process -FilePath "taskkill.exe" -ArgumentList "/PID $p /T /F" -WindowStyle Hidden -Wait -ErrorAction SilentlyContinue
    }
}
