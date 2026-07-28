# MASAISAI Phase 1 — Live Demo (Wokwi node + VPS backend)

The bootcamp demo architecture, exactly as promised in proposal Section 2.2:

```
Wokwi ESP32 sensing node  --MQTT-->  Mosquitto (VPS:1883, auth)
  (simulates 10 nodes off                |
   one board -- see wokwi-vscode/)  ingest_service.py (systemd)
                                     trains the fusion model at boot, fuses every node
                                     currently reporting on a channel, constraint engine
                                     classifies VERIFIED IDLE / FLAGGED
                                        |
                                   MySQL (VPS)
                                        |
                              live_dashboard.py (systemd, :8501)
```

## Wokwi node (`wokwi-vscode/` — this is the current, actively maintained version)

`wokwi/` (browser-only sketch) is an old, abandoned single-node variant kept for reference
only — do not use it, it predates the 10-node fusion demo and will not match the trained
model's expectations. Use `wokwi-vscode/` (local VS Code + PlatformIO + Wokwi extension):

1. Open the `phase1/wokwi-vscode/` folder in VS Code (requires the PlatformIO and Wokwi
   Simulator extensions installed).
2. Set the real MQTT password in `wokwi-vscode/src/main.cpp`'s `MQTT_PASSW` constant — it
   ships as the placeholder `CHANGE_ME_NODE_PASSWORD` and is **never committed** with the
   real value (see `.gitignore`/local-only convention below). Get the real password from
   whoever last ran the VPS deploy, or from `C:\masaisai\.env` on the VPS itself
   (`MQTT_PASS=...`).
3. `F1` → **"Wokwi: Start Simulator"**.
4. Slide the potentiometer = simulated broadcaster TX power, applied across all 10
   simulated nodes at their own fixed per-node attenuation:
   - Slide UP → strong signal → nodes report OCCUPIED → fused verdict flips to **FLAGGED**.
   - Slide DOWN → weak signal → nodes report IDLE → fused verdict flips to **VERIFIED IDLE**
     (if the rules layer also clears it).
5. Watch it land in the live dashboard within a few seconds:
   http://38.247.146.172:8501

**Never commit the real MQTT password.** `main.cpp` with the real value baked in is a
local-only, uncommitted change on the machine actually running the demo — check
`git status` before committing anything in `wokwi-vscode/` and make sure `MQTT_PASSW` is
back to the placeholder if you do need to commit something else in that file.

## VPS

Currently deployed on a Windows Server VPS (`38.247.146.172`) via `phase1/vps/deploy.ps1`
(idempotent, safe to re-run) — installs Mosquitto, MySQL schema + app user, and registers
`masaisai-ingest` + `masaisai-dashboard` as NSSM services (auto-start, auto-restart on
crash). `deploy.sh` (systemd) is the equivalent for a future Linux target (e.g. the ZCHPC
Cloud Compute Environment named in the proposal) — not yet used in practice.

To push a code update to the already-deployed VPS (not a fresh install):
```
scp -i ~/.ssh/zesa_vps src/occupancy_model.py src/sensing_sim.py src/constraint_engine.py \
    Administrator@38.247.146.172:C:/masaisai/src/
scp -i ~/.ssh/zesa_vps phase1/vps/ingest_service.py phase1/vps/live_dashboard.py \
    Administrator@38.247.146.172:C:/masaisai/
ssh -i ~/.ssh/zesa_vps Administrator@38.247.146.172 \
    "powershell -Command \"Remove-Item -Recurse -Force C:\masaisai\__pycache__, C:\masaisai\src\__pycache__ -ErrorAction SilentlyContinue; Restart-Service masaisai-ingest; Restart-Service masaisai-dashboard\""
```

Dashboard: http://38.247.146.172:8501
