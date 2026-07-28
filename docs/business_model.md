# Business Model Summary (Annex A template)

**Updated 28 Jul 2026** to match the current positioning: MASAISAI verifies band idle-status
and flags anomalies for review — it does not itself grant spectrum access or make a final
call. Full pricing/IP depth lives in the pitch-prep materials
(`Pitching and Presenting/11_BUSINESS_MODEL_PRICING_IP.md`); this is the repo-resident
summary judges can find without leaving the codebase. See `business_model_diagram.png` for
the same content as a one-page visual.

| Field | Response |
|---|---|
| Problem | Rural Zimbabwe lacks affordable broadband; meanwhile UHF DTT spectrum sits idle most of the day across most of the country, and POTRAZ has no verifiable way to prove just how idle it is. |
| Primary user | POTRAZ (the regulator, sole buyer) — not rural ISPs or communities directly. |
| Beneficiary (downstream, Phase 2, not the pilot ask) | Rural residents, schools, and clinics who could eventually gain broadband access once POTRAZ separately decides to act on the verified data; POTRAZ itself gains continuous AI-verified spectrum visibility instead of a static allocation table alone. |
| Customer or payer | Sole buyer: POTRAZ. Pilot funding: one-time cost-recovery (~$80k, AI4I milestone-based support model, itemised in the proposal). No consumer sale, no separate "customer" beyond POTRAZ. |
| Value proposition | Continuous, verifiable spectrum-utilization intelligence POTRAZ cannot get today from a static ZNFAP table — proves idle-ness, flags anomalies, without requiring any change to how the band is licensed or allocated. |
| Revenue or funding model | Three separate lines, not one number: (1) ~$80k one-time pilot cost-recovery; (2) hardware sold cost-plus, ~$190-230/site delivered against a ~$100-150 bare-BOM cost (covers calibration, warranty, field support); (3) recurring managed-service fee, ~$50-80/site/year (hosting, retraining, incident response) — priced against what one VSAT/Starlink terminal already costs a rural site monthly, forever. |
| Cost drivers | Sensing-node hardware and maintenance, edge/cloud compute for the fusion model, pilot-site connectivity build-out, field verification/compliance testing, personnel. See `../MASAISAI_AI4I_Proposal_Development.pdf` Section 5 for the itemised estimate. |
| IP | Codebase deliberately MIT-licensed — an auditable algorithm is a trust requirement for a regulator, not a giveaway. What's actually owned: trained model weights/calibration on real data, deployment/integration know-how, the brand, and any real utilization dataset collected during the pilot. No patent/trademark filed yet, disclosed honestly as a pre-pilot task. |
| Partnerships | POTRAZ (regulator, rules source, monitoring-pilot partner), NUST (institutional home, technical supervision), a pilot site (illustrative example: Chivhu-area anchor institution, see `physical_deployment_example.png` — not yet confirmed), ZCHPC (compute environment per proposal Section 3, not yet a confirmed relationship — flagged as an open question from the Day-3 technical clinics). |
| Pilot market | Single underserved rural community, one band (UHF TVWS) — deliberately not multi-band, per direct technical-clinic feedback. |
| Adoption risks | POTRAZ's own decision timeline to act on a monitoring partnership; sensing-hardware sourcing/import lead times; the real, disclosed technical gap that today's RSSI-only sensing can't yet distinguish a specific broadcaster from another transmitter on the same frequency (see `constraints_diagram.png`); ZCHPC relationship not yet confirmed. See `risk_compliance_checklist.md` for the full table. |
| Success metrics | 30 days: sensing nodes deployed on one band, dashboard live with real (not simulated) utilization data. 60 days: fusion model classifying real readings, a real utilization/anomaly dataset accumulating, zero missed-flag incidents against known ground truth. 90 days: a real utilization/compliance case reviewed with POTRAZ, scale plan agreed for additional sites — **not** "anchor institution connected," since that outcome depends on POTRAZ's own separate decision, not on MASAISAI directly. |

## Long-term revenue, both sides named separately

- **For the team**: the hardware/integration markup, the recurring service contract, and —
  contingent on this pilot succeeding — the same open-core package resold to a second African
  regulator at lower marginal cost, since the hard engineering is already built.
- **For POTRAZ**: a previously-idle asset gains a coordination/visibility capability it
  didn't have before, plus first-mover standing as (to our knowledge) Africa's first
  AI-governed spectrum-utilization authority against its own National AI Strategy
  commitments — a reputational and strategic asset, not just a technical one.
