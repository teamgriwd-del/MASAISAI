"""
ML occupancy-verification model for MASAISAI, plus the naive-vote baseline it is
benchmarked against.

Reframed 27 Jul 2026 from a next-window *forecasting* task to a multi-node sensor *fusion*
task -- see `Pitching and Presenting/04_ANTICIPATED_QUESTIONS.md` section 1. "Forecast the
next window" only ever existed to feed a grant/deny access decision that this project no
longer makes; the deliverable is now proving, verifiably, that a band is idle.

Why AI instead of a simple vote: a single sensor's RSSI threshold reading can be wrong on its
own -- multipath fade, transient interference, or just standing somewhere with poor signal
geometry (sensing_sim.py deliberately injects exactly this kind of noise). An unweighted
majority vote across several nodes helps, but treats every node's vote equally regardless of
how trustworthy that particular reading actually is. `predict_naive_vote_baseline` is that
unweighted vote -- the "simple rule" this has to beat. The ML model instead learns which
patterns of multi-node disagreement, confidence spread, and recent channel history actually
correlate with true occupancy, producing a single, more accurate, fully auditable verdict a
plain vote can't reach on its own.

`run_comparison()` trains both on the same data and scores both on a held-out period, to give
a real, reproducible number for "why AI was necessary" rather than an assertion.
"""

from __future__ import annotations

import time
from pathlib import Path

import joblib
import numpy as np
import pandas as pd
from sklearn.ensemble import RandomForestClassifier
from sklearn.metrics import accuracy_score, f1_score, precision_score, recall_score

# Matches the firmware's own single-node energy-detection cutoff
# (phase1/wokwi-vscode/src/main.cpp, OCCUPIED_THRESHOLD_DBM) -- kept identical so the naive
# per-node vote this baseline is built from is the same simple rule a real node already runs,
# not a strawman.
ENERGY_DETECTION_THRESHOLD_DBM = -75.0

FEATURE_COLUMNS = [
    "hour", "dow", "channel_code",
    "mean_rssi_dbm", "min_rssi_dbm", "max_rssi_dbm", "std_rssi_dbm",
    "mean_confidence", "min_confidence", "max_confidence",
    "naive_vote_frac", "confidence_weighted_vote",
    "rolling_occupancy_rate",
]
TARGET_COLUMN = "occupied"
MODEL_PATH = Path(__file__).resolve().parent.parent / "data" / "occupancy_model.joblib"

# Edge deployment budget this model is designed against (see proposal Section 2 / rubric C4):
# quantized/serialized model must stay well under 256MB and single-prediction latency under
# 100ms on a Raspberry-Pi-class edge host. Verified in tests/test_occupancy_model.py, not just
# claimed.
MAX_MODEL_SIZE_MB = 256
MAX_LATENCY_MS = 100


def build_fusion_frame(df: pd.DataFrame) -> pd.DataFrame:
    """Pivots sensing_sim's long-format rows (one per day/hour/channel/node) into one row per
    (day_index, hour, channel), fusing that hour's per-node readings into aggregate features.
    Target is the real, un-shifted ground-truth `occupied` for that window -- there is no
    "next" here, this verifies the current window, using every node reporting on it."""
    naive_flag = (df["rssi_dbm"] > ENERGY_DETECTION_THRESHOLD_DBM).astype(int)

    grouped = df.assign(_naive_flag=naive_flag).groupby(
        ["day_index", "hour", "channel", "split"], as_index=False
    ).agg(
        dow=("dow", "first"),
        occupied=("occupied", "first"),
        mean_rssi_dbm=("rssi_dbm", "mean"),
        min_rssi_dbm=("rssi_dbm", "min"),
        max_rssi_dbm=("rssi_dbm", "max"),
        std_rssi_dbm=("rssi_dbm", "std"),
        mean_confidence=("sensing_confidence", "mean"),
        min_confidence=("sensing_confidence", "min"),
        max_confidence=("sensing_confidence", "max"),
        naive_vote_frac=("_naive_flag", "mean"),
        _confidence_sum=("sensing_confidence", "sum"),
    )
    grouped["std_rssi_dbm"] = grouped["std_rssi_dbm"].fillna(0.0)

    # Confidence-weighted vote: nodes with higher sensing confidence count for more --
    # computed separately since it needs both the flag and the confidence per row together.
    weighted = df.assign(_naive_flag=naive_flag, _weighted=naive_flag * df["sensing_confidence"])
    weighted_sum = weighted.groupby(["day_index", "hour", "channel", "split"], as_index=False)[
        "_weighted"
    ].sum()
    grouped = grouped.merge(weighted_sum, on=["day_index", "hour", "channel", "split"])
    grouped["confidence_weighted_vote"] = (
        grouped["_weighted"] / grouped["_confidence_sum"].replace(0, np.nan)
    ).fillna(0.5)
    grouped = grouped.drop(columns=["_weighted", "_confidence_sum"])

    grouped["channel_code"] = grouped["channel"].astype("category").cat.codes

    grouped = grouped.sort_values(["channel", "day_index", "hour"])
    grp = grouped.groupby("channel", group_keys=False)
    # Rolling idle-rate over the previous 3 windows for this channel (not including the
    # current one) -- the "recent trend" signal a one-shot reading doesn't have.
    grouped["rolling_occupancy_rate"] = grp[TARGET_COLUMN].transform(
        lambda s: s.shift(1).rolling(3, min_periods=1).mean()
    ).fillna(0.5)

    return grouped.reset_index(drop=True)


def train_model(train_df: pd.DataFrame, n_estimators: int = 40, max_depth: int = 6) -> RandomForestClassifier:
    """Small, edge-deployable RandomForest -- kept shallow/narrow on purpose
    to satisfy the edge size/latency budget, not just for speed."""
    X = train_df[FEATURE_COLUMNS]
    y = train_df[TARGET_COLUMN]
    model = RandomForestClassifier(
        n_estimators=n_estimators, max_depth=max_depth, random_state=7, n_jobs=-1
    )
    model.fit(X, y)
    return model


def predict_model(model: RandomForestClassifier, df: pd.DataFrame) -> np.ndarray:
    return model.predict(df[FEATURE_COLUMNS])


def predict_model_proba(model: RandomForestClassifier, df: pd.DataFrame) -> np.ndarray:
    return model.predict_proba(df[FEATURE_COLUMNS])[:, 1]


def predict_naive_vote_baseline(df: pd.DataFrame) -> np.ndarray:
    """The simple rule this has to beat: an unweighted majority vote of single-node
    energy-detection flags (each node's own RSSI against ENERGY_DETECTION_THRESHOLD_DBM).
    Uses only `naive_vote_frac` -- no confidence weighting, no history, no cross-channel
    learning -- exactly what a network of nodes would do with no ML layer at all."""
    return (df["naive_vote_frac"] >= 0.5).astype(int).to_numpy()


def score(y_true, y_pred) -> dict:
    return {
        "accuracy": round(accuracy_score(y_true, y_pred), 4),
        "f1": round(f1_score(y_true, y_pred, zero_division=0), 4),
        "precision": round(precision_score(y_true, y_pred, zero_division=0), 4),
        "recall": round(recall_score(y_true, y_pred, zero_division=0), 4),
    }


def save_model(model, path: Path = MODEL_PATH) -> Path:
    path.parent.mkdir(parents=True, exist_ok=True)
    joblib.dump(model, path)
    return path


def load_model(path: Path = MODEL_PATH):
    return joblib.load(path)


def measure_latency_ms(model, df: pd.DataFrame, n_runs: int = 200) -> float:
    """Average single-row inference latency in milliseconds."""
    row = df[FEATURE_COLUMNS].iloc[[0]]
    start = time.perf_counter()
    for _ in range(n_runs):
        model.predict_proba(row)
    elapsed = time.perf_counter() - start
    return (elapsed / n_runs) * 1000


def run_comparison(train_df: pd.DataFrame, test_df: pd.DataFrame) -> dict:
    model = train_model(train_df)
    ml_preds = predict_model(model, test_df)
    baseline_preds = predict_naive_vote_baseline(test_df)

    return {
        "model": model,
        "ml_score": score(test_df[TARGET_COLUMN], ml_preds),
        "baseline_score": score(test_df[TARGET_COLUMN], baseline_preds),
        "latency_ms": round(measure_latency_ms(model, test_df), 3),
    }


if __name__ == "__main__":
    from sensing_sim import generate_dataset

    raw = generate_dataset()
    fused = build_fusion_frame(raw)
    train_df = fused[fused["split"] == "train"]
    test_df = fused[fused["split"] == "test"]

    result = run_comparison(train_df, test_df)
    print("ML model (fusion)  :", result["ml_score"])
    print("Naive-vote baseline:", result["baseline_score"])
    print(f"Latency  : {result['latency_ms']} ms/prediction (budget: {MAX_LATENCY_MS} ms)")

    path = save_model(result["model"])
    size_mb = path.stat().st_size / (1024 * 1024)
    print(f"Model size: {size_mb:.3f} MB (budget: {MAX_MODEL_SIZE_MB} MB)")
