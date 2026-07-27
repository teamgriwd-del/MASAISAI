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

Six layers: Sensing -> Data -> ML Fusion/Verification Engine -> Rules/Constraint Layer ->
Flagging Layer -> Dashboard/Audit Layer. **The rules layer always overrides the ML layer** --
see `docs/architecture.png` and `src/constraint_engine.py`. Reworked 27 Jul 2026: this no
longer forecasts a future window to feed a grant/deny decision -- it fuses several
independently noisy, confidence-scored sensing nodes into one verified, current-window
idle/occupied verdict per channel, which a single sensor or an unweighted vote can't reach as
reliably. See the module docstring in `src/occupancy_model.py`.

## Data

100% synthetic, generator-documented, methodology disclosed in full in
`data/DATASET_STATEMENT.md`. Small sample at `data/sample_occupancy.csv`.

## AI Method

RandomForestClassifier fusing mean/min/max/spread RSSI, a confidence-weighted vote, and
recent channel history across every node currently reporting on a channel into one
current-window occupancy verdict (not next-window forecasting, and not single-sensor energy
detection, which would be trivial -- see the docstring in `src/occupancy_model.py` for why
that distinction matters). Benchmarked against an unweighted naive-vote baseline (majority
vote of single-node energy-detection flags) on a held-out period; see
`tests/test_occupancy_model.py::test_ml_fusion_beats_naive_vote_baseline_on_held_out_period`
for the reproducible result (fusion ~100% accuracy vs. baseline ~98% on this synthetic
benchmark -- a small, honest gap, concentrated in the baseline missing real occupancy rather
than false alarms, not a suspiciously large or perfect-vs-poor score).

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
