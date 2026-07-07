# Data and AI Usage Note

## Why AI, specifically

The task MASAISAI's ML component solves is **forecasting** whether a channel will be
occupied in the *next* sensing window, using only information available *before* that
window is sensed (current/recent readings, hour-of-day, per-channel/per-node history).

This is explicitly not the same as detecting *current* occupancy from a *current* RSSI
reading -- that is ordinary energy detection, a simple threshold rule handles it
adequately, and the constraint engine (`src/constraint_engine.py`) already uses it directly
for real-time grant/revoke decisions. Framing that as "AI" would be exactly the
"sledgehammer to crack a nut" pattern the AI4I rubric penalizes, and an earlier version of
this codebase made precisely that mistake (see the git history / `occupancy_model.py`
docstring) -- it was caught because the model hit a suspicious 100% accuracy, which is a
red flag for data leakage, not a result to be proud of.

The forecasting task is genuinely harder: a static, fixed hour-of-day schedule table (the
first-generation FCC/Ofcom TV white space database pattern, implemented here as
`predict_baseline`) cannot react to an unannounced schedule change until well after it has
already happened. The ML model can, because it also conditions on the *current* sensing
trend, letting it notice a departure from the historical pattern while it is still
happening.

## Method

- **Model**: `sklearn.ensemble.RandomForestClassifier`, deliberately small (40 estimators,
  max depth 6) to stay within the edge deployment budget (<256MB, <100ms/prediction on this
  host -- both verified, not just asserted, in
  `tests/test_occupancy_model.py::test_model_stays_within_edge_deployment_budget`).
- **Features**: next window's hour-of-day and day-of-week, current RSSI, current occupied
  state, and a 3-reading rolling occupancy rate. All information available strictly before
  the predicted window.
- **Baseline**: fixed per-(channel, hour-of-day) majority-vote table learned from training
  data only -- the alternative simpler approach this project explicitly benchmarks against,
  per the AI4I rubric's "AI necessity" requirement.

## Validation

`tests/test_occupancy_model.py::test_ml_model_beats_fixed_schedule_baseline_on_held_out_period`
trains both approaches on the same data and evaluates both on a held-out period containing
unannounced schedule irregularities the training data does not show. On this synthetic
benchmark: ML ~71% accuracy / ~0.72 F1 vs. baseline ~64% accuracy / ~0.72 F1 recall-heavy --
a real, moderate, reproducible gap (see `data/DATASET_STATEMENT.md` for exactly how that
benchmark is constructed, including the earlier leakage bug and how it was caught and fixed).

## Limitations and human oversight

- Benchmark numbers are on synthetic data (see `data/DATASET_STATEMENT.md`); real-world
  performance will differ once live sensing data exists and must be re-validated then.
- The model's prediction is only ever one input to an access decision -- the rules layer in
  `constraint_engine.py` can veto it unconditionally, and POTRAZ retains a standing manual
  override. The ML model never has unchecked authority over spectrum access.
- Failure mode if the model is wrong in the unsafe direction (predicts idle when actually
  occupied) is bounded by the sensing-confidence fail-safe and the short grant window
  (default 15 minutes, `constraint_engine.DEFAULT_GRANT_WINDOW_MINUTES`), not by trusting
  the model indefinitely.
