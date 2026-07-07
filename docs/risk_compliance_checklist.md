# Risk and Compliance Checklist

| Safeguard | Status / How addressed |
|---|---|
| Data minimisation | System collects only RF energy-detection readings (RSSI, timestamp, node/channel ID) -- no personal data of any kind. |
| Consent | Not applicable to the sensing layer (no personal data). Anchor-institution pilot participation will follow standard institutional consent/agreement processes. |
| Access control | Dashboard/audit access restricted to POTRAZ and the operating team; role separation planned for the real pilot (admin vs. read-only regulator view). |
| Authentication | Not yet implemented in the simulated prototype (no external users in the demo); required before any real pilot deployment -- documented as a pre-pilot task, not glossed over. |
| Secrets management | No credentials committed to this repository; `.env.example` documents required variables without values. |
| Encryption | Real-pilot data-in-transit (sensing node -> ZCHPC CCE) will use TLS; not applicable to the current fully-local synthetic demo. |
| Auditability | Every access decision is logged with its full justification (`src/constraint_engine.py::Decision.to_dict`) -- see the dashboard's audit log expander. |
| Human oversight | POTRAZ retains a manual override/kill-switch over any node, channel, or the whole network at all times (proposal Section 5); the rules layer is human-authored and human-editable, not learned. |
| Misuse risk | Primary misuse risk is interference with licensed broadcasters if the constraint engine's veto were bypassed -- mitigated architecturally (rules layer checked first, unconditionally, before ML is consulted; see `test_constraint_engine.py`). |
| Bias and fairness | Not applicable to this system's core function (spectrum occupancy is a physical measurement, not a decision about people); the equity dimension that matters is *which communities* get pilot access first -- addressed by anchor-institution selection criteria to be agreed with POTRAZ, not left to the algorithm. |
| Data Protection Act [Chapter 12:07] | No personal data processed by the current system; if future phases add user-facing accounts (e.g. community network subscriber management), those components will be designed for compliance with the Act before launch, not retrofitted after. |
| Cybersecurity | Model/rules-config files are version-controlled (reviewable, revertible); no network-exposed write access to the constraint engine's rules file is implemented in the current prototype. |
| Known limitations disclosed | Yes -- see README.md "Known Limitations" and `data/DATASET_STATEMENT.md`. |
