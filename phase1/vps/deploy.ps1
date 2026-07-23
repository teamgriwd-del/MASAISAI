# MASAISAI Phase-1 deploy for WINDOWS SERVER. Run as Administrator from the
# deploy folder (e.g. C:\masaisai-deploy). Idempotent - safe to re-run.
param(
    [int]$DbPort = 1097,
    [string]$AppDir = "C:\masaisai"
)
$ErrorActionPreference = "Stop"
$Deploy = $PSScriptRoot

Write-Host "== 1/8 App layout =="
New-Item -ItemType Directory -Force $AppDir | Out-Null
Copy-Item -Recurse -Force "$Deploy\src" "$AppDir\src"
Copy-Item -Recurse -Force "$Deploy\data" "$AppDir\data"
Copy-Item -Force "$Deploy\ingest_service.py" "$AppDir\"
Copy-Item -Force "$Deploy\live_dashboard.py" "$AppDir\"

Write-Host "== 2/8 Python =="
$py = $null
foreach ($cand in @("python", "py")) {
    try { $v = & $cand --version 2>$null; if ($v -match "Python 3") { $py = $cand; break } } catch {}
}
if (-not $py) {
    Write-Host "   Installing Python 3.12..."
    $exe = "$env:TEMP\python-installer.exe"
    Invoke-WebRequest "https://www.python.org/ftp/python/3.12.8/python-3.12.8-amd64.exe" -OutFile $exe
    Start-Process $exe -ArgumentList "/quiet InstallAllUsers=1 PrependPath=1 Include_test=0" -Wait
    $env:Path = [Environment]::GetEnvironmentVariable("Path", "Machine")
    $py = "python"
}
Write-Host "   Using: $(& $py --version)"

Write-Host "== 3/8 venv + packages =="
if (-not (Test-Path "$AppDir\venv")) { & $py -m venv "$AppDir\venv" }
& "$AppDir\venv\Scripts\python.exe" -m pip install --quiet --upgrade pip
& "$AppDir\venv\Scripts\python.exe" -m pip install --quiet -r "$Deploy\requirements-live.txt"

Write-Host "== 4/8 Secrets =="
function New-RandomSecret([int]$len) {
    -join ((65..90) + (97..122) + (48..57) | Get-Random -Count $len | ForEach-Object { [char]$_ })
}
$envFile = "$AppDir\.env"
if (Test-Path $envFile) {
    Write-Host "   existing .env kept"
    $envMap = @{}
    Get-Content $envFile | ForEach-Object { if ($_ -match "^([^=]+)=(.*)$") { $envMap[$Matches[1]] = $Matches[2] } }
} else {
    $envMap = @{
        MQTT_BROKER_HOST = "127.0.0.1"; MQTT_BROKER_PORT = "1883"
        MQTT_USER = "masaisai_node";    MQTT_PASS = (New-RandomSecret 20)
        DB_HOST = "127.0.0.1";          DB_PORT = "$DbPort"
        DB_USER = "masaisai_app";       DB_PASS = (New-RandomSecret 24)
        DB_NAME = "masaisai"
    }
    $envMap.GetEnumerator() | ForEach-Object { "$($_.Key)=$($_.Value)" } | Out-File $envFile -Encoding ascii
}

Write-Host "== 5/8 Mosquitto broker =="
$mosqDir = "C:\Program Files\mosquitto"
if (-not (Test-Path "$mosqDir\mosquitto.exe")) {
    $exe = "$env:TEMP\mosquitto-install.exe"
    Invoke-WebRequest "https://mosquitto.org/files/binary/win64/mosquitto-2.0.18-install-windows-x64.exe" -OutFile $exe
    Start-Process $exe -ArgumentList "/S" -Wait
}
& "$mosqDir\mosquitto_passwd.exe" -c -b "$mosqDir\masaisai_passwd" "masaisai_node" $envMap.MQTT_PASS
@"
listener 1883 0.0.0.0
allow_anonymous false
password_file $mosqDir\masaisai_passwd
"@ | Out-File "$mosqDir\mosquitto.conf" -Encoding ascii
try { & "$mosqDir\mosquitto.exe" install 2>$null } catch {}
Set-Service mosquitto -StartupType Automatic
Restart-Service mosquitto

Write-Host "== 6/8 MySQL schema + app user (port $DbPort) =="
$sqlOut = "$Deploy\setup_db.sql"
@"
CREATE USER IF NOT EXISTS 'masaisai_app'@'localhost' IDENTIFIED BY '$($envMap.DB_PASS)';
CREATE USER IF NOT EXISTS 'masaisai_app'@'127.0.0.1' IDENTIFIED BY '$($envMap.DB_PASS)';
ALTER USER 'masaisai_app'@'localhost' IDENTIFIED BY '$($envMap.DB_PASS)';
ALTER USER 'masaisai_app'@'127.0.0.1' IDENTIFIED BY '$($envMap.DB_PASS)';
GRANT ALL PRIVILEGES ON masaisai.* TO 'masaisai_app'@'localhost';
GRANT ALL PRIVILEGES ON masaisai.* TO 'masaisai_app'@'127.0.0.1';
FLUSH PRIVILEGES;
"@ | Out-File $sqlOut -Encoding ascii
Get-Content "$Deploy\schema.sql" | Add-Content $sqlOut
$mysqlExe = Get-ChildItem "C:\Program Files\MySQL\*\bin\mysql.exe" -ErrorAction SilentlyContinue | Select-Object -First 1
$dbDone = $false
if ($mysqlExe) {
    try {
        Get-Content $sqlOut | & $mysqlExe.FullName --protocol=TCP -h 127.0.0.1 -P $DbPort -u root 2>$null
        if ($LASTEXITCODE -eq 0) { $dbDone = $true }
    } catch {}
}
if ($dbDone) { Write-Host "   schema + user applied via mysql.exe (root, no password)" }
else { Write-Host "   COULD NOT run SQL automatically. Run $sqlOut in your MySQL client as root/admin." -ForegroundColor Yellow }

Write-Host "== 7/8 NSSM services (auto-start, auto-restart) =="
$nssm = "$AppDir\nssm.exe"
if (-not (Test-Path $nssm)) {
    $zip = "$env:TEMP\nssm.zip"
    Invoke-WebRequest "https://nssm.cc/release/nssm-2.24.zip" -OutFile $zip
    Expand-Archive $zip -DestinationPath "$env:TEMP\nssm" -Force
    Copy-Item "$env:TEMP\nssm\nssm-2.24\win64\nssm.exe" $nssm
}
$envExtra = ($envMap.GetEnumerator() | ForEach-Object { "$($_.Key)=$($_.Value)" }) -join "`r`n"
foreach ($svc in @(
    @{ Name = "masaisai-ingest";    Args = "`"$AppDir\ingest_service.py`"" },
    @{ Name = "masaisai-dashboard"; Args = "-m streamlit run `"$AppDir\live_dashboard.py`" --server.port 8501 --server.address 0.0.0.0 --server.headless true" }
)) {
    & $nssm stop $svc.Name 2>$null | Out-Null
    & $nssm remove $svc.Name confirm 2>$null | Out-Null
    & $nssm install $svc.Name "$AppDir\venv\Scripts\python.exe" $svc.Args | Out-Null
    & $nssm set $svc.Name AppDirectory $AppDir | Out-Null
    & $nssm set $svc.Name AppEnvironmentExtra $envExtra | Out-Null
    & $nssm set $svc.Name Start SERVICE_AUTO_START | Out-Null
    & $nssm set $svc.Name AppExit Default Restart | Out-Null
    & $nssm set $svc.Name AppRestartDelay 5000 | Out-Null
    & $nssm set $svc.Name AppStdout "$AppDir\$($svc.Name).log" | Out-Null
    & $nssm set $svc.Name AppStderr "$AppDir\$($svc.Name).log" | Out-Null
    & $nssm start $svc.Name | Out-Null
    Write-Host "   service $($svc.Name): installed + started"
}

Write-Host "== 8/8 Firewall =="
foreach ($p in @(1883, 8501)) {
    if (-not (Get-NetFirewallRule -DisplayName "MASAISAI $p" -ErrorAction SilentlyContinue)) {
        New-NetFirewallRule -DisplayName "MASAISAI $p" -Direction Inbound -Protocol TCP -LocalPort $p -Action Allow | Out-Null
    }
}

Write-Host ""
Write-Host "======================================================"
Write-Host " MASAISAI Phase-1 deployed (Windows Server)"
Write-Host "   MQTT broker : port 1883  user=masaisai_node  pass=$($envMap.MQTT_PASS)"
Write-Host "   Dashboard   : http://<server-ip>:8501"
Write-Host "   Services    : masaisai-ingest, masaisai-dashboard, mosquitto (Automatic start)"
if (-not $dbDone) { Write-Host "   ACTION NEEDED: run setup_db.sql in MySQL as root" -ForegroundColor Yellow }
Write-Host "======================================================"
