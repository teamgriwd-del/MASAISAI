# System Architecture

One consolidated reference, organized exactly around what the AI4I Track 3 evidence
checklist asks for: "User interface, application/API layer, database/storage, AI
model/service, integrations, hosting/device environment and failure paths." Every diagram
referenced here lives in this same `docs/` folder.

## The most important thing to understand first: what's local vs. what's live on the VPS

This repo contains **two separate, independently-runnable things**, and mixing them up is
the single most common confusion point for a reviewer:

| | Runs where | What it shows |
|---|---|---|
| **Synthetic prototype** (`src/dashboard_app.py`) | Your own machine, `streamlit run src/dashboard_app.py` | The full AI pipeline against generated synthetic data — no network calls, no external dependencies, works completely offline. |
| **Phase-1 live pipeline** (`phase1/`) | A Wokwi simulator on your machine (or VS Code) **publishing over the internet to a hosted VPS** at `38.247.146.172` | The same AI pipeline, but fed by real MQTT messages, with a real MySQL database and a real live dashboard, both **hosted on the VPS, not on your machine**. |

**To see live data flowing** (not the synthetic demo), you must: (1) go into `phase1/`, (2)
follow `phase1/README.md` to run the Wokwi simulator, which (3) publishes to the
already-running, already-hosted backend on the VPS — you do not need to set up or run
anything backend-side yourself, it's already deployed and running. The database
(`sensing_readings` + `access_decisions` tables) lives **only on the VPS's MySQL instance**;
there is no local database file in this repo to inspect directly. Live dashboard, no login
required: **http://38.247.146.172:8501**

## User interface

Two dashboards, deliberately different in scope:
- `src/dashboard_app.py` — Streamlit, synthetic data, runs locally, no network needed.
- `phase1/vps/live_dashboard.py` — Streamlit, real MQTT-fed data, runs on the VPS only
  (`http://38.247.146.172:8501`), auto-refreshes every 5s.

Both read from the same underlying model/rules logic in `src/`; they differ only in where
the data comes from (generated vs. real).

## Application / API layer

There is no REST API — the interface contract is MQTT. See `phase1/README.md`'s "Interface
contract" section for the exact topic (`masaisai/sensing/<node_id>`) and JSON payload schema.
`phase1/vps/ingest_service.py` is the application layer: subscribes to that topic, fuses
readings, runs the rules engine, writes to MySQL.

## Database / storage

MySQL, hosted on the VPS only (`38.247.146.172`, see `phase1/vps/schema.sql` for the full
DDL). Two tables: `sensing_readings` (raw, append-only, one row per real MQTT message) and
`access_decisions` (one row per fused per-channel classification). No local database exists
in this repo — the synthetic prototype (`src/dashboard_app.py`) computes everything
in-memory on each run instead of persisting to a database at all.

## AI model / service

`src/occupancy_model.py` — a RandomForestClassifier fusing multi-node RSSI/confidence
readings into one occupancy probability. See `ai_solution_diagram.png` for the literal
inputs → model → output picture, with real, freshly-computed benchmark numbers (this AI:
100%, naive-vote baseline: 98.6%, single sensor: 80%). Full method writeup:
`ai_usage_note.md`. Trained fresh at service startup in both the local prototype and the
live VPS ingest service — not a pre-serialized model file shipped in the repo.

## Integrations

- **MQTT** (Mosquitto) — sensing nodes to ingest service, authenticated.
- **MySQL** — ingest service to dashboard (VPS only).
- No third-party APIs, no external AI services — the model is self-trained and self-hosted.

## Hosting / device environment

- **Today**: VPS = Windows Server, `38.247.146.172`, hosting Mosquitto + ingest service +
  MySQL + live dashboard, all co-located on one box (see `deployment_plan.md` for why this
  is a temporary consolidation, not the target production topology). Sensing node = Wokwi-
  simulated ESP32 (simulates 10 nodes off one board) running on whoever's demoing it.
- **Target Phase-1**: RTL-SDR + Raspberry-Pi-class hosts, physically distributed across one
  rural community — see `physical_deployment_example.png` for an illustrative (not yet
  confirmed) concrete example with real place names, and why the placement is non-collinear
  and distance-diverse on purpose, not evenly spaced.
- Full network topology (logical data/protocol flow + physical today-vs-target layout, one
  diagram): `network_topology.png`.

## Failure paths

- **MQTT broker unreachable**: client auto-retries (`paho-mqtt`'s `retry_first_connection`);
  no silent data loss, readings simply resume once reconnected.
- **MySQL unreachable**: caught and logged per-message, doesn't crash the ingest service —
  see `phase1/README.md`'s "Reliability" section for the known gap (no retry queue yet).
- **A sensing node going offline**: not a failure at all by design — fusion uses whichever
  nodes are currently reporting; one dropping out just means fewer inputs to that channel's
  fused verdict.
- **Low sensing confidence**: the rules layer fails *safe* (flags for review), never silently
  assumes "all clear" — see `src/constraint_engine.py` and `test_constraint_engine.py`.
- **Protected channel or excluded node**: rules layer vetoes unconditionally, before the AI
  is even consulted — the AI's output is never able to override this.

## Hardware and data constraints (the two things judges specifically asked to see)

One combined visual: `constraints_diagram.png` — today's ESP32 stand-in vs. the RTL-SDR/
Raspberry-Pi production target, the verified edge budget (<0.05MB, <40ms, against a 256MB/
100ms budget), the 100%-synthetic data disclosure, and what specifically changes once real
sensing data exists. Both panels name the honest, currently-open gaps directly rather than
implying they're solved.

## Business model

`business_model.md` (table) and `business_model_diagram.png` (one-page visual) — one buyer
(POTRAZ), three separate revenue lines, named risks, both sides' long-term earnings.
