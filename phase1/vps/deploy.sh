#!/usr/bin/env bash
# MASAISAI Phase-1 one-shot VPS deploy. Run as root from /opt/masaisai-deploy.
# Idempotent: safe to re-run.
set -euo pipefail

DEPLOY_SRC="$(cd "$(dirname "$0")" && pwd)"
APP=/opt/masaisai
DB_PORT="${DB_PORT:-1097}"

echo "== 1/8 System packages =="
export DEBIAN_FRONTEND=noninteractive
apt-get update -qq
apt-get install -y -qq mosquitto mosquitto-clients python3-venv python3-pip > /dev/null

echo "== 2/8 App layout =="
mkdir -p "$APP"
cp -r "$DEPLOY_SRC/src" "$APP/src"
cp -r "$DEPLOY_SRC/data" "$APP/data"
cp "$DEPLOY_SRC/ingest_service.py" "$DEPLOY_SRC/live_dashboard.py" "$APP/"

echo "== 3/8 Python venv =="
if [ ! -d "$APP/venv" ]; then python3 -m venv "$APP/venv"; fi
"$APP/venv/bin/pip" install -q --upgrade pip
"$APP/venv/bin/pip" install -q -r "$DEPLOY_SRC/requirements-live.txt"

echo "== 4/8 Secrets =="
if [ -f "$APP/.env" ]; then
  echo "   existing .env kept"
  source "$APP/.env"
else
  NODE_PASS="$(tr -dc 'A-Za-z0-9' < /dev/urandom | head -c 20)"
  DB_PASS="$(tr -dc 'A-Za-z0-9' < /dev/urandom | head -c 24)"
  cat > "$APP/.env" <<EOF
MQTT_BROKER_HOST=127.0.0.1
MQTT_BROKER_PORT=1883
MQTT_USER=masaisai_node
MQTT_PASS=$NODE_PASS
DB_HOST=127.0.0.1
DB_PORT=$DB_PORT
DB_USER=masaisai_app
DB_PASS=$DB_PASS
DB_NAME=masaisai
EOF
  chmod 600 "$APP/.env"
fi
source "$APP/.env"

echo "== 5/8 Mosquitto (auth required, internet-facing) =="
touch /etc/mosquitto/passwd
mosquitto_passwd -b /etc/mosquitto/passwd masaisai_node "$MQTT_PASS"
cat > /etc/mosquitto/conf.d/masaisai.conf <<EOF
listener 1883 0.0.0.0
allow_anonymous false
password_file /etc/mosquitto/passwd
EOF
systemctl enable mosquitto > /dev/null
systemctl restart mosquitto

echo "== 6/8 MySQL schema + app user (port $DB_PORT) =="
MYSQL="mysql --protocol=TCP -h 127.0.0.1 -P $DB_PORT"
$MYSQL < "$DEPLOY_SRC/schema.sql"
$MYSQL <<EOF
CREATE USER IF NOT EXISTS 'masaisai_app'@'localhost' IDENTIFIED BY '$DB_PASS';
CREATE USER IF NOT EXISTS 'masaisai_app'@'127.0.0.1' IDENTIFIED BY '$DB_PASS';
ALTER USER 'masaisai_app'@'localhost' IDENTIFIED BY '$DB_PASS';
ALTER USER 'masaisai_app'@'127.0.0.1' IDENTIFIED BY '$DB_PASS';
GRANT ALL PRIVILEGES ON masaisai.* TO 'masaisai_app'@'localhost';
GRANT ALL PRIVILEGES ON masaisai.* TO 'masaisai_app'@'127.0.0.1';
FLUSH PRIVILEGES;
EOF

echo "== 7/8 systemd services =="
cp "$DEPLOY_SRC/masaisai-ingest.service" /etc/systemd/system/
cp "$DEPLOY_SRC/masaisai-dashboard.service" /etc/systemd/system/
systemctl daemon-reload
systemctl enable --now masaisai-ingest masaisai-dashboard > /dev/null
systemctl restart masaisai-ingest masaisai-dashboard

echo "== 8/8 Firewall =="
if command -v ufw > /dev/null && ufw status | grep -q "Status: active"; then
  ufw allow 1883/tcp > /dev/null
  ufw allow 8501/tcp > /dev/null
  echo "   ufw: opened 1883, 8501"
else
  echo "   ufw inactive/absent -- no firewall change"
fi

echo
echo "======================================================"
echo " MASAISAI Phase-1 deployed."
echo "   MQTT broker : $(hostname -I | awk '{print $1}'):1883 (user masaisai_node)"
echo "   MQTT pass   : $MQTT_PASS"
echo "   Dashboard   : http://$(hostname -I | awk '{print $1}'):8501"
echo "   Services    : masaisai-ingest, masaisai-dashboard (enabled at boot)"
echo "======================================================"
