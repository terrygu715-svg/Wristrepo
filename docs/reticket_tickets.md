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
  (d) one-night-per-participant rule + exclusion list; (e) STORAGE GATE: list every
  patient/night missing the actigraphy required for the partial path, gate them out,
  delete their local copies (log hash + bytes reclaimed per file, keep the gate list);
  (f) emit label table draft (selected / excluded / class counts) for ticket 2.
- Deliverable (docs only): audit + freeze note with file census, label table, channel
  manifest, storage-gate deletion log, open unknowns (AHI scoring/denominator per E02;
  HR/SpO₂ presence flag).
- Done when: counts reconcile (files ↔ labels ↔ exclusions ↔ deletions); 16-ch disposition
  stated; gated-missing-actigraphy list + reclaimed bytes recorded; HR/SpO₂ availability
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

- Epic: D. Depends on: 1, 2. Spec: T23 + T27 + T28.
- Purpose: define the one baseline pipeline (4-class XGB, full feature set) on train data.
- Inputs: ticket-1 channel manifest (full set), ticket-2 train split.
- Plan: (a) feature list for full set with channel provenance; (b) XGB fixed config
  + class-weight + stopping policy (dev-only); (c) fit/transform scoping (train IDs only);
  (d) checkpoint + run-metadata format.
- Deliverable (docs only): pipeline spec wired end-to-end on paper (no code).
- Done when: every stage (features → fit → checkpoint → predict) has inputs/outputs
  named; train-only fitting + ID discipline stated.
- QA plan (ticket 3 half — reviewed by human before Epic E): (a) full feature list
  traces each feature to a frozen channel; Reduced ⊂ Full check stated;
  (b) XGB config + seeds + stopping/weighting policy pinned; (c) train-only
  fit/transform scoping provable on paper (held-out sentinel reasoning);
  (d) checkpoint + metadata fields enumerated.

## Ticket 4 — Train single XGB + record metrics (+ QA sign-off)

- Epic: D. Depends on: 3. Spec: T24 (metrics) + T36 (reload discipline).
- Purpose: define the scored record for the baseline.
- Inputs: ticket-3 pipeline + frozen split.
- Plan: (a) train on train split; (b) predict eval (+ test policy: closed until ticket 7
  or stated otherwise); (c) record accuracy + F-measure (macro/weighted) + confusion
  matrix + per-class scores from saved predictions; (d) save predictions + run metadata.
- Deliverable (docs only): metrics-record template (what is stored, how reload-match is checked).
- Done when: metric set + CM layout + reload check + test policy all written.
- MANUAL QA GATE (most important — human sign-off required before tickets 5–6):
  reviewer checks (1) split reuse exact (ticket-02 hash match, no re-roll);
  (2) IDs/labels identical across Full/partial rows; (3) no excluded-channel leakage
  into partial; (4) reloaded predictions reproduce scores with matched IDs;
  (5) CM rows/columns reconcile with reported accuracy/F; (6) failure/drop handling
  explicit. Sign with name + date + go/no-go. No-go returns to ticket 3/4;
  Epic E never starts on a no-go.

## Ticket 5 — Remaining 4-class XGB + CNN setup

- Epic: E. Depends on: 1, 2 + Epic-D QA sign-off (go). Spec: T20 + T21 + T22 + T31 + T32.
  No Epic E work starts on a no-go.
- Purpose: define the other pipelines: XGB variant(s) on partial + CNN classifiers.
- Inputs: partial (HR + SpO₂ only, T20) + full (T21/T22 additions) manifests; split.
- Plan: (a) partial vs full feature lists with provenance (Reduced ⊂ Full);
  (b) XGB configs per input; (c) CNN: streaming night dataset (30-s blocks,
  padding/masks, one target/night), compact arch (window encoders + masked
  aggregation + 4-class head), batch sizing per T31 budget; (d) checkpoint formats.
- Deliverable (docs only): matrix build spec with batching rules.
- Done when: partial/full lists frozen; CNN loader + arch + batch policy written;
  batching mandatory and sized (never whole-night loads).

## Ticket 6 — Train all 4 checkpoints (partial/full × XGB/CNN)

- Epic: E. Depends on: 2, 5. Spec: T27/T28/T33 + T37/T39 (CV intent, reduced here to
  the frozen split) + coordinator T34 intent (run tracking).
- Purpose: define the 4 training runs with batches and checkpoints.
- Matrix: (partial-XGB, full-XGB, partial-CNN, full-CNN) — all on ticket-02 train split.
- Plan: (a) per-run config + seeds; (b) batched training with inner-stopping on dev
  only (never test); (c) checkpoint save + provenance per run; (d) failure/visibility
  handling (failed runs stay visible, resume rejects stale hashes).
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
