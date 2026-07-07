# MASAISAI

**Teaching Zimbabwe's airwaves to run themselves.**

Submitted to the POTRAZ AI for Impact (AI4I) Challenge 2026 -- Development Track.

## Problem

Spectrum in Zimbabwe is allocated in static blocks under POTRAZ's Zimbabwe National
Frequency Allocation Plan (ZNFAP). Zimbabwe's UHF digital terrestrial television (DTT) band
(DVB-T2, licensed under Statutory Instrument 26 of 2020) leaves significant "white space"
unused across much of the day and most of the country, at the same time rural Zimbabwe
remains underserved by broadband. TV white space broadband is a proven global category
(Microsoft Airband ran the world's largest pilot in northern Namibia), but nobody has built
the piece that makes it safe for a regulator to actually turn on: a system that can prove,
continuously and verifiably, that a channel is genuinely idle before opening it, and vacate
it the instant a licensed broadcaster reappears.

## Solution

MASAISAI is a network of low-cost RF sensing nodes feeding an ML occupancy-forecasting
model and a POTRAZ-rules constraint engine that has final veto over every access decision.
See `docs/architecture.png` and the full written proposal
(`../MASAISAI_AI4I_Proposal_Development.pdf`) for the complete case.

## Demo

This repository is a **working simulated prototype** -- no real RTL-SDR hardware or POTRAZ
monitoring feed was available during proposal preparation (see
`data/DATASET_STATEMENT.md` for full disclosure). Synthetic sensing data drives real,
tested ML and constraint-engine logic end-to-end.

```bash
pip install -r requirements.txt
streamlit run src/dashboard_app.py
```

Or run the pipeline pieces directly:

```bash
python src/sensing_sim.py       # generate synthetic sensing data
python src/occupancy_model.py   # train model, print ML-vs-baseline comparison
python src/constraint_engine.py # example access decisions
```

## Architecture

Six layers: Sensing -> Data -> ML Occupancy Engine -> Rules/Constraint Layer -> Access
Layer -> Dashboard/Audit Layer. **The rules layer always overrides the ML layer** -- see
`docs/architecture.png` and `src/constraint_engine.py`.

## Data

100% synthetic, generator-documented, methodology disclosed in full in
`data/DATASET_STATEMENT.md`. Small sample at `data/sample_occupancy.csv`.

## AI Method

RandomForestClassifier forecasting *next-window* channel occupancy (not same-window
classification, which would be trivial energy detection -- see the docstring in
`src/occupancy_model.py` for why that distinction matters). Benchmarked against a
fixed-schedule baseline on a held-out period containing unannounced schedule
irregularities; see `docs/ai_usage_note.md` and
`tests/test_occupancy_model.py::test_ml_model_beats_fixed_schedule_baseline_on_held_out_period`
for the reproducible result (ML ~71% accuracy vs. baseline ~64% on this synthetic
benchmark -- a real, moderate, non-inflated gap, not a suspiciously perfect score).

## Setup

Requires Python 3.11+.

```bash
pip install -r requirements.txt
pytest tests/ -v
```

## Environment Variables

Not required for the current simulated prototype. See `.env.example` for the variables
the Phase 1 real-hardware pilot will need (MQTT broker, ZCHPC CCE endpoint).

## Tests

```bash
pytest tests/ -v
```

10 tests covering: constraint-engine rule-override behaviour (protected channels, exclusion
zones, fail-safe-off on low sensing confidence), ML model output validity, the ML-vs-baseline
forecasting comparison, and edge deployment budget verification (model size, inference
latency).

## Deployment

See `docs/deployment_plan.md`.

## Known Limitations

- No real SDR hardware has been tested; sensing is fully simulated (disclosed throughout,
  not hidden).
- `data/znfap_rules_PLACEHOLDER.json` is an illustrative structure, not POTRAZ's real
  channel-protection table -- POTRAZ has not published one to this team.
- Geographic exclusion zones (around real transmitter/aviation/emergency-services sites)
  are not modelled; no site-coordinate dataset was available.
- The ML-vs-baseline comparison is on synthetic data designed to be neither trivially easy
  nor unrealistically hard; real-world numbers will differ once live sensing data exists.

## Team

- Arnold (GRIWD) -- RF/transmission engineering background; NUST Telecommunications
  Engineering (Level 4.2). Sensing-node hardware, RF signal processing, ML occupancy model.
- Adrianny Jaliele -- NUST Telecommunications/Engineering. [specialisation to confirm].
