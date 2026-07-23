# MASAISAI Phase 1 — Live Demo (Wokwi node + VPS backend)

The bootcamp demo architecture, exactly as promised in proposal Section 2.2:

```
Wokwi ESP32 sensing node  --MQTT-->  Mosquitto (VPS:1883, auth)
                                        |
                              ingest_service.py (systemd)
                              trains model at boot, scores each reading,
                              constraint engine decides GRANT/DENY
                                        |
                                   MySQL (VPS)
                                        |
                              live_dashboard.py (systemd, :8501)
```

## Wokwi (no install needed — runs in the browser)
1. Go to https://wokwi.com → New Project → ESP32.
2. Replace the default sketch with `wokwi/sketch.ino`.
3. Open the `diagram.json` tab and replace with `wokwi/diagram.json`.
4. Library Manager tab → add the three libraries in `wokwi/libraries.txt`.
5. Set `MQTT_PASSW` in the sketch to the node password printed by deploy.sh.
6. Start the sim. Slide the potentiometer = broadcaster TX power.
   - Slide UP → OCCUPIED (red LED) → dashboard DENIES the channel.
   - Slide DOWN → IDLE (green LED) → dashboard GRANTS (if rules allow).

## VPS deploy (one shot, idempotent)
```
scp -r phase1/vps root@38.247.146.172:/opt/masaisai-deploy
scp -r src data root@38.247.146.172:/opt/masaisai-deploy/
ssh root@38.247.146.172 "bash /opt/masaisai-deploy/deploy.sh"
```
Services `masaisai-ingest` + `masaisai-dashboard` are systemd-enabled:
they auto-start on boot and auto-restart on crash.

Dashboard: http://38.247.146.172:8501
