import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src"))

import pytest  # noqa: E402

from occupancy_model import (  # noqa: E402
    MAX_LATENCY_MS,
    MAX_MODEL_SIZE_MB,
    build_fusion_frame,
    measure_latency_ms,
    predict_model_proba,
    predict_naive_vote_baseline,
    run_comparison,
    save_model,
    train_model,
)
from sensing_sim import generate_dataset  # noqa: E402


@pytest.fixture(scope="module")
def fused_data():
    raw = generate_dataset(n_days=14, test_period_days=4, seed=11)
    fused = build_fusion_frame(raw)
    train_df = fused[fused["split"] == "train"]
    test_df = fused[fused["split"] == "test"]
    return train_df, test_df


def test_model_predictions_are_valid_probabilities(fused_data):
    train_df, test_df = fused_data
    model = train_model(train_df)
    probs = predict_model_proba(model, test_df)
    assert (probs >= 0).all() and (probs <= 1).all()
    assert len(probs) == len(test_df)


def test_ml_fusion_beats_naive_vote_baseline_on_held_out_period(fused_data):
    """The core AI-justification claim: fusing several nodes' RSSI/confidence readings
    (mean/min/max/std, confidence-weighted vote, recent history) should classify a channel's
    true occupancy at least as accurately as an unweighted majority vote of single-node
    energy-detection flags -- the 'simple rule' a non-ML system would run. This is the
    evidence for 'why AI beats a simpler rule' required by the Development track rubric."""
    train_df, test_df = fused_data
    result = run_comparison(train_df, test_df)
    assert result["ml_score"]["accuracy"] >= result["baseline_score"]["accuracy"]
    assert result["ml_score"]["f1"] >= result["baseline_score"]["f1"]


def test_model_stays_within_edge_deployment_budget(fused_data, tmp_path):
    """Verifies (not just claims) the edge feasibility numbers required by
    rubric C4: model file size under 256MB, single-prediction latency
    under 100ms on this host."""
    train_df, test_df = fused_data
    model = train_model(train_df)

    path = save_model(model, tmp_path / "model.joblib")
    size_mb = path.stat().st_size / (1024 * 1024)
    assert size_mb < MAX_MODEL_SIZE_MB

    latency_ms = measure_latency_ms(model, test_df)
    assert latency_ms < MAX_LATENCY_MS


def test_naive_vote_baseline_uses_only_the_vote_fraction(fused_data):
    """Sanity check that the baseline is a genuine simple rule (deterministic function of
    naive_vote_frac alone), not accidentally smuggling in the richer fusion features
    (confidence, spread, history) the ML model gets."""
    train_df, test_df = fused_data
    preds = predict_naive_vote_baseline(test_df)
    expected = (test_df["naive_vote_frac"] >= 0.5).astype(int).to_numpy()
    assert (preds == expected).all()
