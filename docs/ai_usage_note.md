# Data and AI Usage Note

**Reworked 27 Jul 2026** from a next-window forecasting task to a multi-node sensor fusion
task -- the forecasting framing only ever existed to feed a grant/deny access decision this
project no longer makes (see `Pitching and Presenting/04_ANTICIPATED_QUESTIONS.md` section 1
for the full reasoning and the honest note on how this differs from the submitted proposal).

## Why AI, specifically

The task MASAISAI's ML component solves is **fusing** several independently noisy,
confidence-scored sensing nodes into one verified, current-window verdict on whether a
channel is genuinely idle.

A single sensor's own RSSI threshold reading can be wrong on its own -- multipath fade,
transient interference, or just standing somewhere with poor signal geometry
(`src/sensing_sim.py` deliberately injects exactly this kind of independent per-node noise).
That alone is ordinary energy detection, no ML needed, and the constraint engine
(`src/constraint_engine.py`) still uses exactly that, directly, per sensor. An unweighted
majority vote across several nodes is the obvious next step, and it is the baseline this
project benchmarks against (`predict_naive_vote_baseline`) -- it helps, but treats every
node's vote equally regardless of how trustworthy that particular reading actually is.
Framing a single sensor's own reading as "AI" would be exactly the "sledgehammer to crack a
nut" pattern the AI4I rubric penalizes; an earlier version of this project's forecasting
model made precisely that mistake once, caught because it hit a suspicious 100% accuracy
(a red flag for data leakage). The current fusion result was checked for the same failure
mode directly (feature importances are well-distributed, no single feature dominates) before
being trusted.

The fusion task is genuinely harder than a vote: the model learns which patterns of
multi-node disagreement, confidence spread, and recent channel history actually correlate
with true occupancy, correcting exactly the cases where a plain vote gets outvoted by
degraded sensors.

## Method

- **Model**: `sklearn.ensemble.RandomForestClassifier`, deliberately small (40 estimators,
  max depth 6) to stay within the edge deployment budget (<256MB, <100ms/prediction on this
  host -- both verified, not just asserted, in
  `tests/test_occupancy_model.py::test_model_stays_within_edge_deployment_budget`).
- **Features**: for every (channel, hour) window, aggregated across every node reporting on
  it -- mean/min/max/std RSSI, mean/min/max sensing confidence, the naive per-node vote
  fraction, a confidence-weighted vote, channel identity, hour/day-of-week, and a 3-window
  rolling idle-rate for that channel. All computed from the current window plus history, no
  future information.
- **Baseline**: an unweighted majority vote of single-node energy-detection flags (each
  node's own RSSI against the same threshold the sensing firmware uses,
  `occupancy_model.ENERGY_DETECTION_THRESHOLD_DBM`) -- the alternative simpler approach this
  project explicitly benchmarks against, per the AI4I rubric's "AI necessity" requirement.

## Validation

`tests/test_occupancy_model.py::test_ml_fusion_beats_naive_vote_baseline_on_held_out_period`
trains both approaches on the same data and evaluates both on a held-out period. On this
synthetic benchmark: fusion model ~100% accuracy/F1 vs. naive-vote baseline ~98% accuracy
(recall ~95-97%, precision 100%) -- a real, small, reproducible gap, and specifically a
safety-relevant one: the baseline's errors are concentrated in *missed* occupancy, the
dangerous direction for incumbent protection, not false alarms (see
`data/DATASET_STATEMENT.md` for exactly how the benchmark dataset is constructed, including
the independent per-node fade noise that makes fusion meaningfully different from a vote).

## Limitations and human oversight

- Benchmark numbers are on synthetic data (see `data/DATASET_STATEMENT.md`); real-world
  performance will differ once live sensing data exists and must be re-validated then.
- Current sensing (RSSI threshold) cannot distinguish a specific broadcaster's signal from
  another transmitter on the same frequency -- that needs real signal classification on
  proper SDR hardware, not yet built or tested. The model fuses readings into a triage signal
  for POTRAZ's own certified equipment to verify, not an autonomous verdict.
- The model's classification is only ever one input to a decision -- the rules layer in
  `constraint_engine.py` can flag it for review unconditionally, and POTRAZ retains a
  standing manual override. The ML model never has unchecked authority.
- Failure mode if the model is wrong in the unsafe direction (verifies idle when actually
  occupied) is bounded by the sensing-confidence fail-safe, not by trusting the model
  indefinitely.
