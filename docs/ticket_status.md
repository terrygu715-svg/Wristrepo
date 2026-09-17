# Active Ticket Status

This ledger supersedes the status wording in the original
The original `.docx` remains an immutable planning input; this file is the
active implementation board.

Status vocabulary: `Done`, `Review`, `Blocked`, `Ready`, `Not applicable`.
`Done` means the implementation evidence and the ticket-specific tests are
present. It does not clear a later scientific or protocol gate.

## Gates

| Gate | Status | Evidence / blocker |
|---|---|---|
| E01 Access | Cleared locally | `docs/kaggle_access.md`, `outputs/kaggle_manifest.json`, 80 files verified. |
| E02 Label definition | Open | Kaggle AHI scoring rule, denominator, subtype coverage, and exact boundaries are not sourced. |
| E03 Motion/alignment | Provisional | Omit-motion path is documented; channel map and alignment evidence remain unknown. |
| E04 Capacity | Open | CPU verified; current local disk can be as low as 17 GiB free; no bounded cache/neural pilot yet. |
| E05 Cohort support | Open | One-night cohort has 20 participants with class counts normal 1, mild 2, moderate 7, severe 10. C04 is mandatory. |

## Tickets

| Ticket | Status | Evidence / next action |
|---|---|---|
| T01 | Done | `docs/decisions.md`; Kaggle amendment supersedes MESA rows. |
| T02 | Done | `environment_report.json`; CPU verified, CUDA unavailable. |
| T03 | Done | Contracts/scaffold committed in `c79d223`; 14 contract tests pass. |
| T04 | Done | `docs/kaggle_access.md`; URL, local provenance, manifest, and integrity verification. License remains open for sharing. |
| T05 | Review | `docs/kaggle_evidence.md`; M01–M09 recorded, U01–U07 remain open. |
| T06 | Done | Deterministic SYNTH_ fixtures, boundary/missingness/leakage tripwires; tested. |
| T07 | Done | Local Kaggle manifest, streaming hashes, verify CLI, secret guard; network resume is Not applicable. |
| T08 | Done | `outputs/sample_manifest.json`; two pre-registered files match T07 and `patients.csv`, reserved for development. |
| T09 | Review/Blocked | `outputs/sample_inventory.json`; stats emitted and 16-channel file quarantined. Resolve rate/channel map/anomaly disposition. |
| T10 | Implemented/Blocked E02 | Comma decimals, boundaries, duplicate rejection, 20 labelled participants + 20 participant exclusions. Source AHI semantics still open. |
| T11 | Provisional/Blocked E03 | Omit-motion decision helper and tests. Need source/channel evidence or signed omission evidence before T12. |
| T12 | Blocked | E02/E03/E04/E05 evidence and channel/quality contract are not frozen. |
| T13 | Blocked by T12 | Canonical `.npy` signal reader not started. |
| T14 | Blocked by T12/T11 | Quality masks and no-zero-fill policy not implemented. |
| T15 | Blocked by T14/E04 | Window cache and cache-hash tests not implemented. |
| T16 | Blocked by E04 | Bulk acquisition is Not applicable; storage ledger/remediation still required before cache work. |
| T17 | Blocked by T12/T14/T16 | Full paired cohort audit not frozen. |
| T18 | Blocked by C04/E05 | Original 80/20 + five-fold design is unsupported; redesign required before splits. |
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
| C04 Cohort redesign | Mandatory | Original class support cannot justify 80/20 + five-fold evaluation. Must document revised folds/splits or a versioned scope change before T18. |

## Current Stop Point

The next executable work is T09 evidence resolution, T10/T11 gate closure,
and the bounded C04 redesign. T12 is the next protocol gate. No split,
feature extraction, cache generation, model training, CV, or held-out scoring
may begin before the corresponding status changes here and the tests listed
in `docs/epics_and_testing_seams.md` pass.
