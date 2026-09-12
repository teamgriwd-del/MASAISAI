"""
Dashboard payload builder for the MASAISAI operations console.

This module is the single boundary between the existing MASAISAI backend and the redesigned
UI. It does not change any backend behaviour: it calls sensing_sim, occupancy_model and
constraint_engine exactly as the previous dashboard did, then shapes their outputs into one
JSON-serialisable dict the front end renders.

Every number the UI shows is derived from those modules, with one deliberate exception:
NODE_SITES. The simulator's eight nodes have no geography, so they are sited at real
Zimbabwean towns purely so the map has somewhere to draw them. That mapping is illustrative
and is labelled as such in the payload.

The ML layer is a multi-node *fusion* classifier -- it verifies the current window, it does not
forecast. The "outlook" series below is therefore split honestly into what the model measured
(past and now) and what the training-period hourly profile suggests (next six hours). The UI
labels the second part as an expectation, never as an ML forecast.
"""

from __future__ import annotations

from datetime import datetime

import numpy as np
import pandas as pd

from constraint_engine import (
    DEFAULT_CONFIDENCE_THRESHOLD,
    DEFAULT_GRANT_WINDOW_MINUTES,
    DEFAULT_OCCUPANCY_GRANT_THRESHOLD,
    decide_access,
    load_rules,
)
from occupancy_model import (
    ENERGY_DETECTION_THRESHOLD_DBM,
    build_fusion_frame,
    predict_model_proba,
    run_comparison,
)
from sensing_sim import CHANNELS, generate_dataset

BAND_LOW_MHZ = 470.0
BAND_HIGH_MHZ = 694.0
CHANNEL_BW_MHZ = 8.0

# Illustrative siting only -- the simulated nodes carry no coordinates. (town, lon, lat)
NODE_SITES = {
    "NODE1": ("Harare", 31.05, -17.83),
    "NODE2": ("Bulawayo", 28.58, -20.15),
    "NODE3": ("Gweru", 29.82, -19.45),
    "NODE4": ("Mutare", 32.67, -18.97),
    "NODE5": ("Masvingo", 30.83, -20.07),
    "NODE6": ("Victoria Falls", 25.85, -17.93),
    "NODE7": ("Kariba", 28.80, -16.52),
    "NODE8": ("Chinhoyi", 30.20, -17.36),
}

# Channels shown on the 24-hour heatmap, matching the operational view in the brief.
HEATMAP_CHANNELS = [f"CH{n}" for n in range(21, 31)]
RECENT_HOURS = 6
OUTLOOK_PAST_HOURS = 12
OUTLOOK_NEXT_HOURS = 6


def channel_centre_mhz(channel: str) -> float:
    n = int(channel[2:])
    return BAND_LOW_MHZ + (n - 21) * CHANNEL_BW_MHZ + CHANNEL_BW_MHZ / 2.0


def _f(x, nd=3):
    """JSON-safe float."""
    if x is None or (isinstance(x, float) and np.isnan(x)):
        return None
    return round(float(x), nd)


def _node_label(node_id: str) -> str:
    return "NODE-%02d" % int(node_id.replace("NODE", ""))


# ------------------------------------------------------------------ backend runs --

def run_backend(seed: int = 3) -> dict:
    """Exactly the pipeline the original dashboard ran, trained once."""
    raw = generate_dataset(n_days=14, test_period_days=4, seed=seed)
    fused = build_fusion_frame(raw)
    train_df = fused[fused["split"] == "train"]
    test_df = fused[fused["split"] == "test"].copy()
    comparison = run_comparison(train_df, test_df)
    model = comparison["model"]
    test_df["ml_probability"] = predict_model_proba(model, test_df)
    return {
        "raw": raw,
        "train_df": train_df,
        "test_df": test_df,
        "comparison": comparison,
        "rules": load_rules(),
    }


# ------------------------------------------------------------------- decisions --

def _classify_reason(reason: str) -> str:
    r = reason.lower()
    if "protected" in r:
        return "protected"
    if "exclusion" in r:
        return "excluded"
    if "confidence" in r:
        return "failsafe"
    if "occupancy probability" in r:
        return "occupied"
    return "verified"


def _humanise(kind: str, p_occ: float, conf: float) -> str:
    return {
        "verified": "Verified idle (P(idle) = %.2f)" % (1 - p_occ),
        "protected": "Protected channel -- incumbent list",
        "excluded": "Node inside exclusion zone",
        "failsafe": "Sensing confidence %.2f below fail-safe" % conf,
        "occupied": "Predicted occupied (P(occ) = %.2f)" % p_occ,
        "revoked": "Incumbent signal detected",
    }[kind]


def _decide_window(test_df, raw, rules, day, hour):
    """Run the constraint engine over every channel for one sensing window."""
    window = test_df[(test_df["day_index"] == day) & (test_df["hour"] == hour)]
    readings = raw[(raw["day_index"] == day) & (raw["hour"] == hour)]
    out = {}
    for row in window.itertuples():
        per_node = readings[readings["channel"] == row.channel]
        # The node that heard this channel most reliably is the reporting node; the rules
        # engine checks it against the exclusion list, which "FUSED" never could.
        best = per_node.loc[per_node["sensing_confidence"].idxmax()]
        node_id = best["node_id"]
        d = decide_access(node_id, row.channel, float(row.ml_probability),
                          float(row.max_confidence), rules)
        kind = "verified" if d.granted else _classify_reason(d.reason)
        out[row.channel] = {
            "channel": row.channel,
            "node_id": node_id,
            "granted": d.granted,
            "kind": kind,
            "p_occ": float(row.ml_probability),
            "confidence": float(row.max_confidence),
            "mean_rssi": float(row.mean_rssi_dbm),
            "naive_vote": float(row.naive_vote_frac),
            "engine_reason": d.reason,
        }
    return out


# ---------------------------------------------------------------------- payload --

def build_payload(backend: dict, now: datetime | None = None) -> dict:
    now = now or datetime.now()
    raw, test_df = backend["raw"], backend["test_df"]
    train_df, rules = backend["train_df"], backend["rules"]
    comparison = backend["comparison"]
    protected = set(rules.get("protected_channels", []))

    # The simulated test period's final day stands in for "today", aligned to the real
    # clock hour so the console reads as live. The data itself stays simulated.
    day = int(test_df["day_index"].max())
    hour = now.hour

    windows = {}
    for h in range(max(0, hour - RECENT_HOURS + 1), hour + 1):
        windows[h] = _decide_window(test_df, raw, rules, day, h)
    current = windows[hour]
    readings_now = raw[(raw["day_index"] == day) & (raw["hour"] == hour)]

    # ------------------------------------------------------------- nodes
    nodes = []
    for node_id in sorted(raw["node_id"].unique(), key=lambda n: int(n[4:])):
        town, lon, lat = NODE_SITES[node_id]
        r = readings_now[readings_now["node_id"] == node_id]
        conf = float(r["sensing_confidence"].median())
        idle_frac = float((r["rssi_dbm"] <= ENERGY_DETECTION_THRESHOLD_DBM).mean())
        # In the simulator, confidence falls with distance from the transmitter, so a low
        # value means a node hears less clearly -- not that it is failing. Online is simply
        # "reporting"; link quality is a separate, secondary attribute.
        reporting = bool((r["sensing_confidence"] > 0).any())
        status = "online" if reporting else "offline"
        quality = ("good" if conf >= DEFAULT_CONFIDENCE_THRESHOLD else
                   "fair" if conf >= 0.3 else "weak")
        availability = ("offline" if status == "offline" else
                        "high" if idle_frac >= 0.6 else
                        "moderate" if idle_frac >= 0.35 else "low")
        nodes.append({
            "id": node_id, "label": _node_label(node_id), "town": town,
            "lon": lon, "lat": lat, "status": status, "quality": quality,
            "confidence": _f(conf, 2), "idle_fraction": _f(idle_frac, 2),
            "availability": availability,
        })

    # ---------------------------------------------------------- channels
    channels = []
    for ch in CHANNELS:
        c = current[ch]
        kind = c["kind"]
        status = ("AVAILABLE" if c["granted"] else
                  "PROTECTED" if kind == "protected" else
                  "FLAGGED" if kind in ("failsafe", "excluded") else "OCCUPIED")
        channels.append({
            "channel": ch,
            "freq_mhz": channel_centre_mhz(ch),
            "mean_rssi": _f(c["mean_rssi"], 1),
            "naive_vote": _f(c["naive_vote"], 2),
            "naive_state": "OCCUPIED" if c["naive_vote"] >= 0.5 else "IDLE",
            "p_occ": _f(c["p_occ"]),
            "p_idle": _f(1 - c["p_occ"]),
            "ml_confidence": _f(max(c["p_occ"], 1 - c["p_occ"])),
            "sensing_confidence": _f(c["confidence"], 2),
            "protected": ch in protected,
            "status": status,
            "reason": _humanise(kind, c["p_occ"], c["confidence"]),
            "engine_reason": c["engine_reason"],
            "node": _node_label(c["node_id"]),
            "town": NODE_SITES[c["node_id"]][0],
        })
    by_ch = {c["channel"]: c for c in channels}

    # ------------------------------------------------------- per-node RF
    rf = {}
    for ch in CHANNELS:
        per = readings_now[readings_now["channel"] == ch].sort_values("node_id")
        rf[ch] = [{
            "node": _node_label(r.node_id), "town": NODE_SITES[r.node_id][0],
            "rssi": _f(r.rssi_dbm, 1), "confidence": _f(r.sensing_confidence, 2),
            "naive_occupied": bool(r.rssi_dbm > ENERGY_DETECTION_THRESHOLD_DBM),
        } for r in per.itertuples()]

    # ------------------------------------------------ decisions & audit
    events, audit = [], []
    prev = {}
    for h in sorted(windows):
        w = windows[h]
        stamp = "%02d:00" % h
        n_pass = sum(1 for c in w.values() if c["granted"])
        audit.append({"time": stamp + ":00", "kind": "ingest", "channel": None,
                      "text": "SENSING WINDOW INGESTED -- %d nodes x %d channels"
                              % (len(nodes), len(w))})
        audit.append({"time": stamp + ":00", "kind": "ml", "channel": None,
                      "text": "ML FUSION UPDATED -- %d channels verified" % len(w)})
        audit.append({"time": stamp + ":00", "kind": "rules", "channel": None,
                      "text": "POTRAZ RULE CHECK -- %d PASS / %d FLAGGED"
                              % (n_pass, len(w) - n_pass)})
        for ch in CHANNELS:
            c = w[ch]
            before = prev.get(ch)
            changed = before is None or before["granted"] != c["granted"] \
                or before["kind"] != c["kind"]
            if not changed:
                continue
            if c["granted"]:
                decision, kind = "Granted", "verified"
            elif before is not None and before["granted"] and c["kind"] == "occupied":
                decision, kind = "Revoked", "revoked"
            else:
                decision, kind = "Denied", c["kind"]
            events.append({
                "time": stamp, "hour": h, "channel": ch,
                "location": NODE_SITES[c["node_id"]][0],
                "node": _node_label(c["node_id"]), "decision": decision,
                "duration": "%d min" % DEFAULT_GRANT_WINDOW_MINUTES if c["granted"] else None,
                "reason": _humanise(kind, c["p_occ"], c["confidence"]),
            })
            if decision == "Revoked":
                audit.append({"time": stamp + ":00", "kind": "occupied", "channel": ch,
                              "text": "%s INCUMBENT DETECTED" % ch})
                audit.append({"time": stamp + ":00", "kind": "denied", "channel": ch,
                              "text": "%s ACCESS REVOKED" % ch})
            elif decision == "Granted":
                audit.append({"time": stamp + ":00", "kind": "granted", "channel": ch,
                              "text": "%s %s ACCESS GRANTED -- %d MIN WINDOW"
                                      % (ch, NODE_SITES[c["node_id"]][0].upper(),
                                         DEFAULT_GRANT_WINDOW_MINUTES)})
            elif c["kind"] == "protected" and before is None:
                audit.append({"time": stamp + ":00", "kind": "protected", "channel": ch,
                              "text": "%s FLAGGED -- PROTECTED CHANNEL" % ch})
        prev = w
    # Newest window first; within a window, revocations and denials lead -- an operator
    # needs the exceptions before the routine grants.
    priority = {"Revoked": 2, "Denied": 1, "Granted": 0}
    events.sort(key=lambda e: (e["hour"], priority[e["decision"]], e["channel"]), reverse=True)
    audit.reverse()

    # ------------------------------------------------------------- KPIs
    granted_now = [c for c in channels if c["status"] == "AVAILABLE"]
    grants_on_protected = sum(1 for c in granted_now if c["protected"])
    n_online = sum(1 for n in nodes if n["status"] == "online")
    n_degraded = sum(1 for n in nodes if n["quality"] == "weak")
    n_offline = sum(1 for n in nodes if n["status"] == "offline")
    usage = {
        "idle": len(granted_now),
        "occupied": sum(1 for c in channels if c["status"] == "OCCUPIED"),
        "protected": sum(1 for c in channels if c["status"] == "PROTECTED"),
        "flagged": sum(1 for c in channels if c["status"] == "FLAGGED"),
        "total": len(channels),
    }

    # ---------------------------------------------------------- heatmap
    day_df = test_df[test_df["day_index"] == day]
    heat = {ch: [_f(v) for v in day_df[day_df["channel"] == ch]
                 .sort_values("hour")["ml_probability"].tolist()] for ch in CHANNELS}

    # ---------------------------------------------------------- outlook
    candidates = sorted([c for c in channels if not c["protected"]],
                        key=lambda c: c["p_occ"])
    focus = [c["channel"] for c in candidates[:2]]
    profile = train_df.groupby(["channel", "hour"])["occupied"].mean()
    outlook = []
    for ch in focus:
        past = []
        for h in range(max(0, hour - OUTLOOK_PAST_HOURS + 1), hour + 1):
            p = day_df[(day_df["channel"] == ch) & (day_df["hour"] == h)]["ml_probability"]
            past.append({"hour": h, "p_idle": _f(1 - float(p.iloc[0]))})
        expected = [{"hour": (hour + k) % 24,
                     "p_idle": _f(1 - float(profile.loc[(ch, (hour + k) % 24)]))}
                    for k in range(1, OUTLOOK_NEXT_HOURS + 1)]
        outlook.append({"channel": ch, "measured": past, "expected": expected})

    # ---------------------------------------------------- live decision
    best = next((c for c in candidates if c["status"] == "AVAILABLE"), candidates[0])
    live = {
        "channel": best["channel"], "freq_mhz": best["freq_mhz"],
        "node": best["node"], "town": best["town"],
        "rssi": best["mean_rssi"], "naive_state": best["naive_state"],
        "naive_vote": best["naive_vote"], "p_idle": best["p_idle"],
        "sensing_confidence": best["sensing_confidence"],
        "granted": best["status"] == "AVAILABLE",
        "checks": _rule_checks(best, rules, nodes),
    }

    # -------------------------------------------------- RF attribution
    occupied = [c for c in channels if c["status"] in ("OCCUPIED", "PROTECTED")]
    focus_ch = "CH22" if by_ch.get("CH22", {}).get("status") == "OCCUPIED" else (
        max(occupied, key=lambda c: c["mean_rssi"])["channel"] if occupied else CHANNELS[0])
    n = int(focus_ch[2:])
    neighbours = [f"CH{k}" for k in (n + 1, n + 2) if f"CH{k}" in by_ch]

    ml = comparison["ml_score"]
    base = comparison["baseline_score"]
    hourly_util = (test_df.groupby("hour")["occupied"].mean() * 100).reindex(range(24), fill_value=0)

    return {
        "meta": {
            "product": "MASAISAI",
            "tagline": "Teaching Zimbabwe's Airwaves to Run Themselves",
            "description": "Real-time spectrum intelligence for a more connected Zimbabwe.",
            "context": "POTRAZ AI FOR IMPACT (AI4I)",
            "context_sub": "Dynamic Spectrum Access for Rural Broadband",
            "simulated": True,
            "data_notice": "Simulated demo -- synthetic sensing data. See data/DATASET_STATEMENT.md.",
            "site_notice": "Node sites are illustrative; the simulator's nodes carry no coordinates.",
            "rules_version": rules.get("version"),
            "rules_source": rules.get("source"),
            "snapshot_hour": hour,
            "snapshot_day": day,
            "band_monitored": "%s-%s" % (CHANNELS[0], CHANNELS[-1]),
            "band_mhz": "%.0f-%.0f MHz" % (BAND_LOW_MHZ, BAND_LOW_MHZ + len(CHANNELS) * CHANNEL_BW_MHZ),
        },
        "config": {
            "confidence_threshold": DEFAULT_CONFIDENCE_THRESHOLD,
            "occupancy_threshold": DEFAULT_OCCUPANCY_GRANT_THRESHOLD,
            "grant_window_min": DEFAULT_GRANT_WINDOW_MINUTES,
            "energy_threshold_dbm": ENERGY_DETECTION_THRESHOLD_DBM,
            "protected_channels": sorted(protected),
            "excluded_nodes": rules.get("excluded_nodes", []),
            "model": "Random Forest fusion (40 trees, depth 6)",
        },
        "kpis": {
            "nodes_total": len(nodes), "nodes_online": n_online,
            "nodes_degraded": n_degraded, "nodes_offline": n_offline,
            "channels_monitored": len(channels),
            "idle": len(granted_now),
            "idle_pct": round(100.0 * len(granted_now) / len(channels)),
            "active_grants": len(granted_now),
            "grants_on_protected": grants_on_protected,
        },
        "nodes": nodes,
        "channels": channels,
        "rf": rf,
        "rf_focus": {"channel": focus_ch, "neighbours": neighbours},
        "heatmap": {"channels": HEATMAP_CHANNELS, "all_channels": CHANNELS,
                    "hours": list(range(24)), "values": heat, "now_hour": hour},
        "outlook": outlook,
        "decisions": events,
        "audit": audit,
        "usage": usage,
        "live": live,
        "health": {
            "nodes": "%d/%d" % (n_online, len(nodes)),
            "readings": int(len(raw)),
            "ml_accuracy": _f(ml["accuracy"] * 100, 1),
            "ml_latency_ms": _f(comparison["latency_ms"], 2),
            "rules_version": rules.get("version"),
            "protected_count": len(protected),
            "active_grants": len(granted_now),
            "audit_events": len(audit),
        },
        "analytics": {
            "ml": ml, "baseline": base,
            "latency_ms": _f(comparison["latency_ms"], 2),
            "hourly_utilisation": [_f(v, 1) for v in hourly_util.tolist()],
            "train_windows": int(len(train_df)), "test_windows": int(len(test_df)),
        },
    }


def _rule_checks(ch: dict, rules: dict, nodes: list) -> list:
    """The checks the rules engine actually performs, plus the ones it honestly does not."""
    in_band = BAND_LOW_MHZ <= ch["freq_mhz"] <= BAND_HIGH_MHZ
    excluded = rules.get("excluded_nodes", [])
    node_id = "NODE%d" % int(ch["node"].split("-")[1])
    return [
        {"name": "Frequency Allocation", "state": "PASS" if in_band else "FAIL",
         "detail": "Within UHF TV white-space band 470-694 MHz"},
        {"name": "Incumbent Protection", "state": "FAIL" if ch["protected"] else "PASS",
         "detail": "Not on the protected/incumbent list" if not ch["protected"]
         else "Channel is on the protected/incumbent list"},
        {"name": "Geographic Restriction", "state": "FAIL" if node_id in excluded else "PASS",
         "detail": "Reporting node outside exclusion zones"},
        {"name": "Sensing Integrity", "state": "PASS"
         if ch["sensing_confidence"] >= DEFAULT_CONFIDENCE_THRESHOLD else "FAIL",
         "detail": "Best-node confidence %.2f vs fail-safe %.2f"
         % (ch["sensing_confidence"], DEFAULT_CONFIDENCE_THRESHOLD)},
        {"name": "Channel Availability", "state": "PASS"
         if ch["p_occ"] <= DEFAULT_OCCUPANCY_GRANT_THRESHOLD else "FAIL",
         "detail": "Fused P(occupied) %.2f vs threshold %.2f"
         % (ch["p_occ"], DEFAULT_OCCUPANCY_GRANT_THRESHOLD)},
        {"name": "Permitted Power", "state": "NOT MODELLED",
         "detail": "Requires POTRAZ EIRP limits -- not yet supplied"},
        {"name": "Regulatory Conditions", "state": "PLACEHOLDER",
         "detail": "Rules file %s is illustrative, pending ZNFAP extract"
         % rules.get("version")},
    ]


if __name__ == "__main__":
    import json
    p = build_payload(run_backend())
    print(json.dumps({k: p[k] for k in ("meta", "kpis", "usage", "live")}, indent=2)[:3000])
