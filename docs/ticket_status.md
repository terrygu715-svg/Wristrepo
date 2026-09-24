# Active Ticket Status

This ledger supersedes the status wording in the original
`Sleep_Apnea_Implementation_Tickets.docx`. The original `.docx` remains an
immutable planning input; this file is the
active implementation board.

Status vocabulary: `Done`, `Review`, `Blocked`, `Ready`, `Not applicable`.
`Done` means the implementation evidence and the ticket-specific tests are
present. It does not clear a later scientific or protocol gate.

## Progress Snapshot

Last verified 24 September 2026:

- `main` includes seam correction commit `c97b91d`; this documentation sync
  records its verification state.
- GitHub tracker: 14 issues closed (T01–T04, T06–T08, T19, T24–T26,
  T34–T35, and C01); 35 issues remain open because they are review,
  provisional, blocked, or pending.
- Verification: 116/116 tests pass; Python compilation passes.
- Data integrity: `outputs/kaggle_manifest.json` verifies `Kaggledata/` with
  the original 80-file manifest remains provenance; the reduced working set is
  documented in `docs/working_set.md`. The latest T16 ledger measured 24 GiB
  free after trim.
- Generated evidence: `outputs/sample_manifest.json` is source-manifest and
  `patients.csv` verified; `outputs/sample_inventory.json` quarantines the
  16-channel anomaly; `outputs/label_table.json` contains 20 selected labels,
  20 excluded participants, and 40 excluded source rows.
- The original ticket `.docx` is unchanged; this ledger is the active board.

## Gates

| Gate | Status | Evidence / blocker |
|---|---|---|
| E01 Access | Cleared locally | `docs/kaggle_access.md`, original manifest provenance, and reduced working-set record. |
| E02 Label definition | Open | Kaggle AHI scoring rule, denominator, subtype coverage, and exact boundaries are not sourced. |
| E03 Motion/alignment | Cleared for omit-motion | `docs/alignment_feasibility.md` documents absent motion/HR/SpO2 time series and the explicit omit decision; T12 still freezes the resulting channel/feature contract. |
| E04 Capacity | Cleared for bounded CPU streaming | T16 ledger records 24 GiB free and a 20-file, 1 MiB-chunk pilot at ~322 MiB peak RSS; neural/backend-specific pilot remains separate. |
| E05 Cohort support | Open | One-night cohort has 20 participants with class counts normal 1, mild 2, moderate 7, severe 10. C04 redesign is complete; T18 manifests/support tests remain. |

## Tickets

| Ticket | Status | Evidence / next action |
|---|---|---|
| T01 | Done | `docs/decisions.md`; Kaggle amendment supersedes MESA rows. |
| T02 | Done | `environment_report.json`; CPU verified, CUDA unavailable. |
| T03 | Done | Contracts/scaffold committed in `c79d223`; 14 contract tests pass. |
| T04 | Done | `docs/kaggle_access.md`; URL, local provenance, manifest, and integrity verification. License remains open for sharing. |
| T05 | Done | `docs/kaggle_evidence.md`; Kaggle API claims, local measurements, anomalies, discrepancies, and remaining unknowns are recorded. E02 remains open; E03 is cleared for the documented omit-motion decision. |
| T06 | Done | Deterministic SYNTH_ fixtures, boundary/missingness/leakage tripwires; tested. |
| T07 | Done | Original local Kaggle manifest, streaming hashes, verify CLI, and secret guard; reduced working-set policy is documented separately. |
| T08 | Done | `outputs/sample_manifest.json`; two pre-registered files match T07 and `patients.csv`, reserved for development. |
| T09 | Done | `outputs/sample_inventory.json`; all audited files have complete stats, byte counts, hashes, and per-channel values. Both 16-channel files are quarantined and excluded from the six-channel contract; no remap is inferred. Sampling/channel semantics remain documented unknowns for T12. |
| T10 | Done/Blocked E02 | Real-header/first-row, comma-decimal, boundary, duplicate, and missing-label tests pass. The label table contains 20 selected participants, 20 participant exclusions, and 40 retained source-row exclusions; AHI semantics remain an E02 gate. |
| T11 | Done | `docs/alignment_feasibility.md`; source review confirms no motion/HR/SpO2 time series or channel map. Omit-motion is explicit for both Full and Reduced, with helper regression tests. T12 still must freeze channel/feature scope. |
| T12 | Blocked | E02/E04/E05 evidence and the channel/quality contract are not frozen. E03 is cleared for omit-motion. |
| T13 | Blocked by T12 | Canonical `.npy` signal reader not started. |
| T14 | Blocked by T12 | Quality masks and no-zero-fill policy not implemented. |
| T15 | Blocked by T14/E04 | Window cache and cache-hash tests not implemented. |
| T16 | Done | `docs/storage_ledger.md` records before/after trim measurements and the completed 20-file bounded streaming pilot: 24 GiB free, ~322 MiB peak RSS, no cache writes. |
| T17 | Blocked by T12/T14/T16 | Full paired cohort audit not frozen. |
| T18 | Blocked by E05/T12 | `docs/cohort_redesign.md` replaces the unsupported 80/20 + five-fold design with 20 participant-level leave-one-participant-out outer folds; versioned split manifests and support tests are still required. |
| T19 | Done | Train-only fitted transforms with held-out sentinel/order tests. |
| T20 | Blocked by T12/T15 | Feature scope conflicts with unresolved Kaggle channel map and no HR/SpO2 time series. |
| T21 | Blocked by T12/T15 | Full respiratory feature module not started. |
| T22 | Blocked by T12/T15 | Remaining signal feature module not started. |
| T23 | Blocked by T18/T20–T22 | Paired matrices and Full-superset proof not started. |
| T24 | Done | Metrics implementation with hand-computed score tests. |
| T25 | Done | 2,000 seeded paired bootstrap with participant/label identity checks. |
| T26 | Done | Versioned atomic checkpoint bundles and serialization rejection tests. |
| T27 | Blocked by T18/T23 | Generic training harness not started. |
| T28 | Blocked by T27 | Boosted-tree adapter not started. |
| T29 | Blocked by T27 | Logistic adapter not started. |
| T30 | Blocked by T27 | SVM adapter not started. |
| T31 | Blocked by T02/T15/T18/E04 | Neural loader and measured batch-fit pilot not started. |
| T32 | Blocked by T26/T31 | Neural architecture not started. |
| T33 | Blocked by T27/T32/E04 | Neural training integration not started. |
| T34 | Done | Dependency ledger, failure visibility, stale/running recovery, lock tests. |
| T35 | Done | Deterministic fixture report generation; no training during regeneration. |
| T36 | Blocked by T24/T28/T34 | First real development GBT pair not started. |
| T37 | Blocked by T36 | GBT development CV not started. |
| T38 | Blocked by T29/T30/T36 | LR/SVM development CV not started. |
| T39 | Blocked by T33/T36/E04 | Neural development CV not started. |
| T40 | Blocked by T25/T35/T37–T39 | Final experiment freeze not started. |
| T41 | Blocked by T40 | Six conventional final bundles not started. |
| T42 | Blocked by T40/E04 | Two neural final bundles not started. |
| T43 | Blocked by T24/T40–T42 | Held-out scoring is intentionally unopened. |
| T44 | Blocked by T25/T35/T43 | Final comparison report not started. |
| T45 | Blocked by T34/T44 | Reproducibility package not started. |

## Conditional Work

| Item | Status | Decision |
|---|---|---|
| C01 XML/event label reconstruction | Not applicable | Kaggle provides summary AHI in `patients.csv`; no XML source is present. Reopen only if that summary is disproven. |
| C02 Motion repair | Not triggered | No motion representation has been established. One bounded repair session only if a source map later identifies motion. |
| C03 Compute adjustment | Pending | Trigger only if the measured pilot exceeds RAM/disk/runtime budget. |
| C04 Cohort redesign | Done | `docs/cohort_redesign.md` selects 20 participant-level leave-one-participant-out outer folds with fixed a priori settings; T18 must build and test the manifests. |

## Current Stop Point

The next executable work is T12 contract freeze preparation and T18
implementation of the C04 fold manifests. T16 storage verification is complete
for bounded CPU streaming. The full layered execution order is in
`docs/epics_and_testing_seams.md §5`. No split,
feature extraction, cache generation, model training, CV, or held-out scoring
may begin before the corresponding status changes here and the tests listed in
`docs/epics_and_testing_seams.md` pass.
