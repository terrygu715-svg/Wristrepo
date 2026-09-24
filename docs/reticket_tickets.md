# Implementation tickets 0–7 — simplified flight (docs only, no code)

> Branch: `reticket/simplified-flight`. Dataset assumed local:
> https://www.kaggle.com/datasets/yfrite/polysom. No downloads, no installs, no code.
> Spec refs = `Sleep_Apnea_Implementation_Tickets.docx` v1.0; evidence refs = `docs/` on `main`.

## Ticket 0 — Environment + dependency assess

- Epic: A — Foundation. Depends on: none. Spec: T02 (adapt Windows/local; backend stated, never assumed).
- Purpose: record whether the machine can run tickets 1–7.
- Inputs: local machine; `pyproject.toml` dep list + XGB/CNN backends.
- Plan: (a) OS/CPU/RAM/disk + free space vs ~22 GiB dump; (b) Python version + numpy /
  sklearn / scipy / xgboost / torch presence + versions; (c) backend statement
  (CPU/CUDA/MPS — verify, don't assume); (d) batch-fit budget note per T31/S13.
- Deliverable (docs only): dependency checklist with pass/missing list + budget note.
- Done when: every dep has present/missing + version; backend stated with evidence;
  disk/RAM vs dataset size recorded; no install or code run in this ticket.
- Out: installs, downloads, training.

## Ticket 1 — Data audit + freeze (derive labels + split inputs)

- Epic: B. Depends on: 0. Spec: T09 + T10 + T11 + T12; evidence: `kaggle_evidence.md`,
  `alignment_feasibility.md`, `cohort_redesign.md`.
- Purpose: freeze the channel/label/cohort contract; derive the label table and the
  participant list ticket 2 will split.
- Inputs: local `Kaggledata/` (80 `.npy` + `patients.csv`); Kaggle page for provenance.
- Plan: (a) per-file shape/dtype/value census + 16-ch disposition (quarantine expected);
  (b) `patients.csv` header/row probe, comma-decimal parse, AHI → 4 classes at
  provisional 5/15/30 with boundary + duplicate + missing-label rules; (c) channel
  freeze: Full set vs partial = HR + SpO₂ only (T20) vs omit-motion (T11);
  (d) one-night-per-participant rule + exclusion list; (e) DELETION: join PSG file list
  to label/actigraphy availability and drop null columns/rows missing the actigraphy
  required for the partial path; log dropped IDs + reclaimed bytes (no signing);
  (f) emit label table draft (selected / excluded / class counts) for ticket 2.
- Deliverable (docs only): audit + freeze note with file census, label table, channel
  manifest, deletion log, open unknowns (AHI scoring/denominator per E02;
  HR/SpO₂ presence flag).
- Done when: counts reconcile (files ↔ labels ↔ exclusions ↔ deletions); 16-ch disposition
  stated; dropped-null list + reclaimed bytes recorded; HR/SpO₂ availability
  confirmed or refuted in writing; boundaries + rules recorded.
- Gate: if HR/SpO₂ time series absent, tickets 3–6 proceed only under a written
  deviation (no silent remap).

## Ticket 2 — Train/eval/test split

- Epic: C. Depends on: 1. Spec: T18 (80/20 participant split + five dev folds).
- Purpose: persist the one frozen split every later ticket uses.
- Inputs: ticket-1 label table + exclusion list.
- Plan: (a) participant-disjoint train/eval/test with versioned manifests + hashes;
  (b) class-support report per split (normal 1 total expected — state the handling,
  never silently merge); (c) inspection IDs (if any) pinned to non-test;
  (d) Full/Reduced share split hashes.
- Deliverable (docs only): split manifest spec (paths, hash method, support table).
- Done when: disjointness + support + reuse rule stated; no re-roll policy declared.

## Ticket 3 — Single XGBoost on full-data labels (setup)

- Epic: D. Depends on: 1, 2. Spec: T23 + T27 + T28 (GBT branch of legacy ML plan).
- Purpose: define the one baseline pipeline (4-class XGB, full feature set) on train data.
- Inputs: ticket-1 channel manifest (full set), ticket-2 train split.
- Do-not-start (from legacy plan, adapted): ticket-1 freeze + ticket-2 manifests closed;
  train-only transforms scoped; capacity note from ticket 0 current (no stale budget).
- Plan: (a) feature list for full set with feature→channel provenance (Reduced ⊂ Full);
  (b) fixed-config XGB, multinomial 4-class, on standardized inputs; fixed rounds or
  dev-only early stopping; class-weight + seed policy recorded;
  (c) fit/transform scoped to passed train IDs only; feature-order validated, unknown /
  reordered features rejected; (d) `fit / predict / save / reload` through versioned
  atomic bundles; wrong feature/config version rejected on load;
  (e) file ownership (for implementer): harness `train_model.py` /
  `src/sleep_apnea/train_model.py`, adapter `src/sleep_apnea/models/gbt.py`,
  harness tests `tests/test_harness.py` (S12: dummy baseline runs, inner-stop ≠
  outer-score, fit-on-test raises), pairing tests `tests/test_pairing.py` (S08).
  Do not touch contracts/metrics/compare/coordinator except to import.
- Standing prohibitions: no test data until ticket 7 policy allows; no tuning sweep
  (equal Full/partial budgets); no zero-fill for absent signal; no sleep-stage or
  label features in predictors; no `outputs/` ↔ source mixing.
- Deliverable (docs only): pipeline spec wired end-to-end on paper (no code).
- Done when: every stage (features → fit → checkpoint → predict) has inputs/outputs
  named; train-only fitting + ID discipline stated.
- IMPLEMENTER QA CHECKLIST (ticket 3 half — complete before Epic E; most important gate):
  - [ ] Each feature traces to a frozen ticket-1 channel; Reduced ⊂ Full stated.
  - [ ] XGB config + rounds/stopping + weights + seeds pinned in writing.
  - [ ] Train-only scoping holds on paper (held-out values can't move fitted params).
  - [ ] Checkpoint + run-metadata fields enumerated (config/split hash, row counts).

## Ticket 4 — Train single XGB + record metrics (+ QA gate)

- Epic: D. Depends on: 3. Spec: T24 (metrics) + T36 (first-pair gate, adapted to single XGB).
- Purpose: define the scored record for the baseline.
- Inputs: ticket-3 pipeline + frozen split.
- Plan: (a) train on train split; (b) predict eval (+ test policy: closed until ticket 7
  or stated otherwise); (c) record accuracy + F-measure (macro/weighted) + confusion
  matrix + per-class scores from saved predictions; (d) save predictions + run metadata;
  (e) reload check: reloaded predictions reproduce scores with matched IDs; no test
  partition opened; defect list with bounded follow-ups.
- Deliverable (docs only): metrics-record template (what is stored, how reload-match is checked).
- Done when: metric set + CM layout + reload check + test policy all written.
- IMPLEMENTER QA CHECKLIST (most important manual gate — complete all before tickets 5–6):
  - [ ] Split reuse exact: ticket-02 hash match, no re-roll.
  - [ ] IDs/labels identical across Full/partial rows for shared nights.
  - [ ] No excluded-channel leakage into partial (Full-only features absent).
  - [ ] Reloaded predictions reproduce scores with matched IDs.
  - [ ] CM rows/columns reconcile with reported accuracy/F.
  - [ ] Failures/drops explicit (no selective exclusion).
  - [ ] Handoff fields filled: config hash / split hash, job IDs + states, acceptance
    evidence, stopping/weight/seed policy, unresolved issues, newly ready IDs.
  No-go on any box returns to ticket 3/4; Epic E never starts on a no-go.

## Ticket 5 — Remaining 4-class XGB + CNN setup

- Epic: E. Depends on: 1, 2 + Epic-D implementer QA checklist complete.
  Spec: T20 + T21 + T22 + T31 + T32 (neural branch of legacy ML plan).
  No Epic E work starts with an open QA box.
- Purpose: define the other pipelines: XGB variant(s) on partial + CNN classifiers.
- Inputs: partial (HR + SpO₂ only, T20) + full (T21/T22 additions) manifests; split.
- Plan: (a) partial vs full feature lists with provenance (Reduced ⊂ Full);
  (b) XGB configs per input (same fixed-config discipline as ticket 3);
  (c) CNN loader `src/sleep_apnea/data/night_dataset.py`: streaming 30-s blocks grouped
  by night, one target/night, padding/missing masks, recorded sampling policy; stream
  windows, never whole nights; measured batch (size + RAM high-water + backend string);
  (d) CNN arch `src/sleep_apnea/models/cnn_night.py`: compact channel/group window
  encoders → masked mean over valid windows → 4-class head; keep small (no attention /
  Mamba / tuning sweeps); shape/gradient pass, masked-padding invariance, bundle
  round-trip, no window-level event label; (e) neural tests
  `tests/test_neural_loading.py` (S13); (f) checkpoint formats per run.
- Standing prohibitions: no torch/TF dep before the batch pilot justifies it;
  no pre-trained/downloaded weights; no fine-tuning.
- Deliverable (docs only): matrix build spec with batching rules.
- Done when: partial/full lists frozen; CNN loader + arch + batch policy written;
  batching mandatory and sized (never whole-night loads).

## Ticket 6 — Train all 4 checkpoints (partial/full × XGB/CNN)

- Epic: E. Depends on: 2, 5 (+ Epic-D QA complete). Spec: T27/T28/T33 + T37/T39
  (adapted to the frozen split) + T34 run-tracking intent.
- Purpose: define the 4 training runs with batches and checkpoints.
- Matrix: (partial-XGB, full-XGB, partial-CNN, full-CNN) — all on ticket-02 train split.
- Plan: (a) per-run config + seeds; (b) batched training with inner-stopping on dev
  only (never test; epoch selection isolated from outer/test); mini smoke runs first
  (complete → save → reload, finite losses); (c) checkpoint save + provenance per run;
  (d) run ledger: pending/running/succeeded/failed visible, resume rejects stale hashes,
  workers write distinct outputs; (e) backend: CPU verified path; one 6 × ~6M float64
  night ≈ 275 MB — stream, don't load whole.
- Deliverable (docs only): run matrix sheet (4 rows × config/seed/checkpoint/metric target).
- Done when: all 4 runs specified with batch + stopping + checkpoint rules; same-split
  discipline stated.

## Ticket 7 — Peak accuracies + F + CM per checkpoint, same split

- Epic: F. Depends on: 6. Spec: T24/T25 (reduced to same-split peak reporting).
- Purpose: define the comparison record.
- Inputs: 4 saved checkpoints + frozen split.
- Plan: (a) peak-checkpoint selection on eval only; (b) per-checkpoint accuracy +
  F-measure + confusion matrix; (c) side-by-side table (partial/full × XGB/CNN);
  (d) conditioning + limitation notes (20-participant cohort, provisional boundaries,
  HR/SpO₂ deviation if any).
- Deliverable (docs only): comparison-report template.
- Done when: peak rule + metric set + CM layout + no-re-roll rule written.
