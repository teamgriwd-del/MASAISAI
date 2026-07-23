# MASAISAI — Project Memory / Progress Log

A running log of major project milestones, so anyone joining (or judging) the
project can reconstruct where it is and how it got here.

## Status at a glance

| Item | State |
|---|---|
| AI4I 2026 track | Development (Track 3) |
| Proposal | Submitted 12 July 2026 |
| **Shortlist (30 teams)** | **SHORTLISTED — 21 July 2026** |
| Bootcamp | Mutare, 27 July – 1 August 2026 |
| Prototype demo (synthetic) | https://masaisai-ehlxdm2nqy8hozzgesh9qg.streamlit.app/ |
| Phase-1 live demo (hardware-in-the-loop) | Built — Wokwi ESP32 node → VPS backend |
| Team | Adrianny Jaliele (lead) · Arnold T Mapindu |

## Milestone log

### July 2026 — Proposal & submission
- Working simulated prototype completed: synthetic RF sensing generator,
  RandomForest next-window occupancy forecaster, POTRAZ-rules constraint
  engine with absolute veto, Streamlit console, 10-test pytest suite.
- ML-vs-baseline benchmark locked: ~71% vs ~64% accuracy on a held-out
  period with unannounced schedule irregularities (the "why AI" evidence).
- Edge budget verified by test: 0.38 MB model, ~36 ms inference.
- Public demo deployed to Streamlit Community Cloud.
- Proposal PDF finalised (cover: lead innovator, team, date) and submitted
  ahead of the 14 July deadline, with Git link + live demo URL.

### 21 July 2026 — Shortlisted
- MASAISAI selected into the 30-team AI4I shortlist (Development track).

### 23 July 2026 — Phase-1 live pipeline built (bootcamp demo)
This is the architecture the proposal promised for the real pilot, now
running end-to-end with a simulated hardware node:

```
Wokwi ESP32 sensing node (VS Code simulation, slide-pot = broadcaster TX)
      → MQTT (auth) → Mosquitto broker on Windows Server VPS
      → masaisai-ingest service: same trained model + same constraint engine
        as the prototype, scoring every live reading
      → MySQL (sensing_readings + access_decisions audit trail, schema per
        proposal Section 2.3)
      → live Streamlit console on :8501 (auto-refresh, full audit log)
```

- `phase1/wokwi/` — browser-Wokwi version of the sensing node
  (ESP32 + SSD1306 OLED + slide potentiometer + occupancy LEDs).
- `phase1/wokwi-vscode/` — local VS Code simulation: PlatformIO project,
  compiled firmware (784 KB flash / 14% RAM), `wokwi.toml` wiring.
- `phase1/vps/` — Windows Server deployment: `deploy.ps1` installs
  Mosquitto (auth required), Python venv, MySQL schema + least-privilege
  app user, and registers `masaisai-ingest` + `masaisai-dashboard` as
  auto-start / auto-restart services (NSSM), so the backend survives
  reboots unattended. Linux (systemd) variants included for the future
  ZCHPC CCE deployment.
- Demo storyline: slide the potentiometer up → node reports the channel
  OCCUPIED → constraint engine denies within seconds. Slide down → verified
  idle → bounded GRANT. Incumbent protection, made visible.

## Next steps
- Bake per-deployment MQTT credentials into the node firmware (never
  committed — credentials live only on the VPS and in the local build).
- Rehearse the bootcamp demo run-of-show.
- Regulatory-sandbox conversation with POTRAZ during bootcamp week.
- Phase 1 proper: replace Wokwi node with real RTL-SDR + Raspberry Pi
  hardware; re-validate the ML benchmark on real sensing data.
