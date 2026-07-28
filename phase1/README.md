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

## Interface contract (this system's "API" — no REST endpoint, MQTT is the interface)

Every sensing node publishes one MQTT message per channel per tick. This is the entire
contract between hardware and backend — `ingest_service.py`'s `on_message` parses exactly
this shape, nothing else is accepted.

- **Topic**: `masaisai/sensing/<node_id>` (e.g. `masaisai/sensing/wokwi-node-05`)
- **Payload** (JSON):
  ```json
  {"node_id": "wokwi-node-05", "channel": 27, "rssi_dbm": -84.3,
   "occupied": 0, "sensing_confidence": 0.91, "seq": 1042}
  ```
- **Auth**: username/password on the Mosquitto connection itself (`MQTT_USER`/`MQTT_PASS`),
  not per-message.
- **Database read/write surface**: `sensing_readings` (one row per raw MQTT message,
  append-only) and `access_decisions` (one row per fused classification, `node_id="FUSED"`)
  — see `phase1/vps/schema.sql` for the full schema. `live_dashboard.py` only ever reads
  these two tables; it has no write access.

## Reliability: dependency failure behaviour and known bugs

- **MQTT broker unreachable**: `ingest_service.py`'s underlying `paho-mqtt` client retries
  the connection automatically (`loop_forever(retry_first_connection=True)`); no readings are
  lost silently, they simply don't arrive until reconnected.
- **MySQL unreachable**: `on_message` catches and logs the exception per-message
  (`except Exception: log.exception(...)`) rather than crashing the whole service — one
  failed insert doesn't take down the ingest pipeline, though that reading's audit trail is
  lost. This is a known gap, not hidden: no retry/dead-letter queue exists yet for failed
  DB writes.
- **A single sensing node going offline**: handled by design, not a failure — fusion uses
  whichever nodes are currently reporting on a channel; one node dropping out just means one
  fewer input to the fusion model for that channel, not a service interruption.
- **Known bugs**: none currently open beyond the limitations already disclosed in
  `01_PROJECT_KNOWLEDGE_BRIEF.md` / `README.md` (100% synthetic training data, RF
  differentiation gap, no authentication layer yet). Two bugs found and fixed during
  development are recorded in project history for transparency: a field-node-to-training-node
  identity mismatch (fixed 27 Jul, see git log) and a `live_dashboard.py` function-ordering
  bug caught immediately after a live VPS deploy (fixed same night).

## Third-party dependency licences

Checked directly via `pip show`, not assumed: pandas (BSD-3-Clause), numpy (BSD-3-Clause,
plus a few vendored BSD/MIT/Zlib/CC0 bits), scikit-learn (BSD-3-Clause), streamlit (Apache-
2.0), plotly (MIT), PyMySQL (MIT) — all permissive. `paho-mqtt` is the one exception worth
naming precisely rather than lumping in: it's dual-licensed under the Eclipse Public
License v2.0 **or** the Eclipse Distribution License v1.0 (a BSD-style permissive license) —
as a library dependency used unmodified, this project takes it under the EDL option, so no
copyleft obligation applies, but it's not simply "MIT/BSD" and shouldn't be described that
way. No GPL dependencies anywhere in the stack. This project's own code is MIT-licensed (see
`LICENSE`) — a deliberate choice, not an oversight, so a regulator auditing an AI spectrum-
safety system can read every line.

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
