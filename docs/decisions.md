# Scope and Experiment Decisions (T01)

- Status: Done (planning snapshot)
- Version: 1.0 — 17 September 2026
- Source input: `Sleep_Apnea_Implementation_Tickets.docx` v1.0 (based on merged specification v2.0)
- Ticket: T01 — Record scope and experiment decisions (60 min, Planning, Ready, Depends on None)
- Deliverable: `docs/decisions.md` (this file)
- Note: The merged spec v2.0 document itself is not present in this repo. Decisions below are
  transcribed from the Implementation Tickets v1.0 plan. Anything not evidenced in a ticket,
  sample, or cited release doc is marked `UNVERIFIED` and assigned an owner + required evidence.
  This file unblocks T03. It does not implement models, schemas, or data access.

## 1. Experiment framing (adopted, not pending)

These are defaults carried forward from the tickets plan. They do not change without a
versioned config revision (see T12 / T18 / T40 protocol gates).

1. **Task:** Predict one of **four night-level severity categories** per night (one row per night).
2. **Awake retention:** Retain awake inputs. No sleep filtering / no sleep-stage-gated exclusion
   in the core baseline.
3. **Reference label:** Reference AHI per **sleep hour** (not recording hour, not event counts).
   Category boundaries map from that reference AHI variable once E02 clears.
4. **Participant disjointness:** All splits/folds are participant-disjoint. 80/20 participant split
   + five development folds when counts permit (T18). Sample records inspected for debugging in
   T08–T17 are reserved for development in T18. No test-score computation during feature building (T23).
5. **Full vs Reduced pairing:** Reduced is a **true subset** of Full. Full/Reduced rows share
   identical IDs/labels (T23). Full-only features must never appear in Reduced (T21).
6. **Motion naming:** If motion is used, it enters only as a **named actigraphy proxy**.
   Body position, activity counts, and six-axis IMU are not conflated (T11).
7. **Leakage prohibitions:** Sleep-stage annotations and outcome labels never enter predictors.
   No globally fitted normalization cached (T15). Fitted transforms learn parameters only from
   passed training IDs (T19). Inner stopping and outer scoring are distinct (T27);
   epoch/round selection never reads outer scoring or test labels (T33, T36).
8. **Windowing:** Per-recording 30-second blocks + longer-context references, masks, provenance;
   labels stored separately; suitable per-channel rates preserved (T15).
9. **Evaluation (frozen intent):** From saved predictions compute macro/weighted F1, accuracy,
   macro precision/recall, per-class scores, and both confusion matrices (T24). Paired comparison
   is 2,000 seeded participant resamples within reference strata, draws reused per Full/Reduced
   pair, conditioning on fitted models and class composition stated (T25).
10. **Scale of core baseline:** CV = 40 fold/input jobs (4 models × 5 folds × 2 inputs).
    Final fitting = 8 bundles (LR/GBT/SVM × Full/Reduced = 6 + 2 neural) (T37–T42).
    Repeated seeds multiply those counts and require a declared budget.
11. **Reproducibility:** Separate source vs generated-output directories; manifest-based acquisition
    with integrity checks (T07); immutable manifests, run metadata, checkpoint bundles with ordered
    channels/features, class mapping, provenance, atomic writes (T26); single coordinator writer
    for shared ledgers (T34).

## 2. Pending choices — owner + evidence needed (T01 Done criterion)

Every row below must be resolved with cited evidence before its downstream gate clears.
`Owner` uses the role assignments from the tickets plan (not actual delegated agents).

| # | Pending choice | Owner | Evidence needed to close | Blocks |
|---|----------------|-------|--------------------------|--------|
| P01 | MESA access path: actual requirements, eligible applicant, institutional contact, receipt/approval | Project lead (E01 owner) | Access status note without credentials (T04 deliverable); authorized access + usable download capability clears E01. T04 submission alone does NOT clear E01. | T08 and all real-data descendants |
| P02 | Reference AHI variable: exact summary variable name, release/table, scoring rule, subtype coverage | Data reviewer (E02 owner) | `labels.py` + label audit (T10); sample IDs reconcile with documented values; boundary + missing-label tests pass. If summaries inadequate, open C01 before closing T10. | T10, T12, T17 + training descendants |
| P03 | Event/scoring definition if AHI must be reconstructed | Data reviewer (E02 owner) | Verified event taxonomy + reconciliation fixture (C01, 90-min bounded session, separately estimated parser/continuation). No generic event summation. | T10 stays blocked until reconciled |
| P04 | Sleep-time denominator for AHI | Data reviewer (E02 owner) | Documented sleep-time definition + category-boundary record in T10/T12; reconciliation if reconstructed | T12, T17 |
| P05 | Four-class category boundaries (exact cut points, inclusivity) | Project lead + Data reviewer | Signed-off config revision + channel manifest (T12); boundary-case tests in T10 | T12, T18, all training |
| P06 | Motion representation: which actigraphy field(s), overlap with PSG, offsets, missing coverage; proxy vs omission | Data reviewer (E03 owner) | `alignment_feasibility.json` (T11): quantified offsets/coverage on samples, field-meaning docs, or explicit omit-motion decision. Documented no-motion result CAN complete T11. | T11–T12 when proxy selected; T14 quality masks |
| P07 | Alignment map trust (if a supplied map is claimed) | Data reviewer (E03 owner) | Evaluated evidence for map on samples (T11); else C02 bounded 120-min diagnosis → validated mapping or omit-motion recommendation | T14, T15 |
| P08 | Primary Reduced set + Full superset channel lists, aliases allowed | Project lead (T12 gate) + Data reviewer | Frozen config revision + channel manifest (T12); explicit per-modality handling (T22); actigraphy enters both sets if selected | T13–T23, T31–T32 |
| P09 | Common interval rules, minimum coverage, deterministic one-night-per-participant selection policy | Project lead (T12 gate) | Same T12 signed-off revision; cohort flow report shows each included participant has one valid label + eligible inputs (T17) | T17, T18 |
| P10 | Laptop/GPU capacity: OS, Python, CPU, RAM, free disk, GPU type, backend (do NOT assume CUDA), allocation check, memory/storage budget | Environment implementer (E04 owner) | `environment_report.json` (T02) + bounded pilot demonstrating fit (T31 neural loader batch test, T16 ledger with actual bytes/remaining storage). CPU path may clear E04 with revised elapsed-time expectations. | T16, T31–T33, long-running jobs |
| P11 | Cohort support for 80/20 + 5-fold + inner stopping subsets; handling of inspection-record constraint | Data reviewer (E05 owner) | Split manifests with disjoint-ID check + class-support report (T18); Full/Reduced share hashes. Insufficient support → documented protocol revision (C04 bounded 90-min redesign), never silent class merging. | T18 and downstream evaluation |
| P12 | Signal I/O aliases, units, rates, mandatory-channel failure policy | Environment implementer + Data reviewer | `data/readers.py` (T13) + sample inventory from `audit_dataset.py` (T09) distinguishing raw vs derived, modality vs channel count | T13, T14 |
| P13 | Artifact/coverage/quality-mask rules (gap representation, exclusion reasons, no zero-fill for absent signal) | Project lead (T12 gate) | `data/quality.py` (T14); synthetic offset/gap checks + sample review; Full/Reduced follow common policy | T14, T15 |
| P14 | Feature scope: HR/SpO2 shared features + Full-only ECG/airflow/effort + EEG/EOG/EMG/position bounds, channel permissions, missingness rules | Project lead (T12 gate) | `features/cardiorespiratory.py` (T20), `features/full_respiratory.py` (T21), `features/other_signals.py` (T22); no expert annotation read; units/context recorded | T20–T23 |
| P15 | Final freeze: model settings, final rounds/epochs, seed policy, preprocessing/split hashes, bootstrap settings, test-inference policy | Project lead (T40 gate) | `release_manifest.json` + freeze review (T40); every pair has reviewed CV evidence (T37–T39); no unresolved label/leakage issue | T41–T43 |

UNVERIFIED as of this commit: P02–P05 (no MESA release doc in repo), P06–P07 (no sample inspected),
P08–P09 (no T12 sign-off yet), P10 (no `environment_report.json` yet — see T02), P11 (no cohort manifest yet).
T05 (`docs/mesa_evidence.md`) is the designated place to convert P02/P06 unknowns into sourced claims.

## 3. Explicitly out of scope for the core baseline (T01 Done criterion)

No AHI-denominator change, event-count shortcut, or automation work enters scope:

- No change of AHI denominator (e.g., per-recording-hour) without a new config revision.
- No event-counting / event-detection model as a substitute for night-level four-class prediction.
- No wristband transfer, on-device automation, or closed-loop work (deferred).
- No sleep-filtered variant as the primary result.
- No multi-night-per-participant modeling in core; one-night rule stands until versioned revision.
- No silent class merging if support is thin (see C04).
- No indefinite motion-repair loop (see C02: one bounded session, then omit or remap).
- Core excludes hyperparameter tuning as a separate experiment (equal Full/Reduced budgets required first),
  extra-seed replication without declared budget, learned attention pooling / Mamba, and any test-driven
  model selection or stopping. Optional research extensions are outside the 78.5-hour / 45-ticket core estimate.

Conditional work (C01–C04) is triggered only on stated evidence and estimated separately;
it is never silently required to close T10/T12/T18.

## 4. Gates carried forward

- **External/evidence gates:** E01 Access, E02 Label definition, E03 Motion alignment, E04 Capacity,
  E05 Cohort support — per table in §2. Gate owners: project lead owns E01 + protocol choices;
  data reviewer owns E02/E03/E05; environment implementer owns E04.
- **Protocol gates (evidence gates):** T12 freezes data meaning + eligibility; T18 freezes paired cohort
  partitions; T36 first real end-to-end pair on development data (GBT, does not wait for neural);
  T40 freezes final experiment; T43 first final-test scoring. Changes after a gate require a new
  configuration revision and invalidate affected downstream artifacts.
- **Contamination rule:** Full-cohort eligibility and label counts follow predefined rules; avoid
  exploratory signal inspection of the eventual test set.

## 5. Sequencing note (for T03 and later)

Wave 0 is T01 (this file), T02, T04, T05, then T03. T03 becomes Ready after T01 (this commit).
After T03, fixture/interface work (T06, T19, T24–T26, T34–T35) can proceed without real data while
access waits. Recommended first sessions: start T04, then complete T01 + T02; run T05 alongside
when a second contributor is available; continue with T03, T06, T07.

Controlling chain (not a schedule): T04+T07 → E01 → T08 → audit/labels → T12 → T13/T14+T16 →
T17 → T18 → feature/trainer or neural path → T36 → slowest of T37/T38/T39 → T40 →
slowest of T41/T42 → T43 → T44 → T45.

## 6. Acceptance check for T01

- [x] Each pending choice (§2, P01–P15) has an owner and evidence needed.
- [x] Four night-level classes + awake input retained (§1.1–1.2).
- [x] No AHI denominator change, event-count shortcut, or automation work in scope (§3).
- [x] Deliverable path is `docs/decisions.md`.
- [x] Next ready ticket: T03 (per plan: “T03 becomes ready after T01”); T02/T04/T05 were already Ready
  and remain Ready. Recalculate readiness after each completion.

## 7. Handoff

- Implementation commit: this commit adding `docs/decisions.md` (see git log).
- Configuration/split hash: N/A (no config or splits in T01).
- Acceptance evidence: this file’s §6 checklist + §2 owner/evidence table + §3 exclusions.
- Unresolved issues: all P-items UNVERIFIED pending T02/T04/T05 evidence; merged spec v2.0 source
  file absent — inputs transcribed from tickets v1.0 only.
- Active time: ~60 min planning allowance.
- Newly ready ticket IDs: T03 (unblocked by T01). T02, T04, T05 remain Ready.
