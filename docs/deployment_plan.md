# Deployment Plan (Annex B template)

| Field | Response |
|---|---|
| Deployment environment | Hybrid: edge (sensing nodes, Raspberry-Pi-class hosts running the occupancy model locally) + institutional/cloud (dashboard, audit log, model retraining) via the ZCHPC Cloud Compute Environment (CCE). |
| Hosting provider or site | ZCHPC CCE for the dashboard/audit/retraining layer (see proposal Section 3); sensing nodes physically hosted at the pilot site. |
| Operator | POTRAZ (system owner/operator of record), with the MASAISAI team (NUST) providing initial technical operation and handover during the pilot and incubation period. |
| Pilot site | Bootcamp demo: a single accessible test site (NUST campus or a reachable Harare-area site). Phase 1 pilot: one underserved rural community, anchor institution as first real connected user, per the proposal's phased rollout (Section 6). |
| Users to onboard | Bootcamp demo: judges/adjudicators (dashboard walkthrough). Phase 1: one anchor institution (school or clinic) and its immediate user base. |
| Training and support | Anchor-institution induction session (in person), a plain-language user guide, WhatsApp support channel for the pilot period -- matching the connectivity/support norms described in the Supporting Guidance. |
| Monitoring | Dashboard/audit layer logs every access decision with its justification (see `src/constraint_engine.py::Decision`); sensing-node uptime and confidence tracked per node; POTRAZ has standing read access and manual override at all times. |
| Backup and recovery | Time-series occupancy data and audit log backed up on a defined schedule; constraint-engine rules configuration (`data/znfap_rules_PLACEHOLDER.json` and its real-data successor) version-controlled so any change is reviewable and reversible. |
| Connectivity plan | Sensing nodes report over available local connectivity (Wi-Fi/cellular backhaul at the pilot site); designed to degrade safely (fail-safe-off, see `constraint_engine.py`) if a node loses connectivity rather than failing open. |
| Scale pathway | Phase 1 (single community, 6-10 nodes) -> Phase 2 (geographic expansion, ZNFAP-as-API published for reuse by other POTRAZ-approved tools) -> national coverage, per proposal Section 6. |
| Milestones | 0-30 days: sensing nodes deployed at pilot site, dashboard showing real (not simulated) data. 31-60 days: constraint engine live-deciding real access grants, anchor institution connected. 61-90 days: adoption case documented, scale plan refined with POTRAZ. |
