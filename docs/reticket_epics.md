# Epic specs — simplified flight (tickets 0–7)

> Branch: `reticket/simplified-flight`. Old Txx/Cxx/Exx flight frozen on `main`.
> Source spec: `Sleep_Apnea_Implementation_Tickets.docx` v1.0 + `docs/` measurements on `main`.
> Dataset: https://www.kaggle.com/datasets/yfrite/polysom (assumed already local; no download).

## Epic A — Foundation (ticket 0)

Goal: prove the machine can run the plan before touching data.
Spec parents: T02 (environment), T31/E04 batch-fit rule, T16 storage ledger.
Covers: Python + deps (numpy, scikit-learn, scipy, xgboost, torch/CNN backend),
CPU/CUDA/MPS backend statement, RAM/disk vs ~22 GiB local dump, missing-dep list.
Explicitly out: downloads, installs, code changes.

## Epic B — Data audit + freeze (ticket 1)

Goal: freeze what the local copy actually contains; derive labels + split inputs here.
Spec parents: T09 (channel inventory) + T10 (labels) + T11 (alignment) + T12 (contract).
Derive on the local copy: per-file shape/dtype census, 16-ch disposition, comma-decimal
AHI parse → label table (participants, exclusions, class counts at 5/15/30 provisional),
channel contract: Full set vs partial (HR + SpO₂ only per T20) vs omit-motion.
Known gap to resolve in this epic: prior audit measured 6 EEG rows only with no HR/SpO₂
time series (`docs/kaggle_evidence.md`, `docs/alignment_feasibility.md`) — ticket 1 must
confirm or refute HR/SpO₂ availability; tickets 3–6 cannot proceed as spec'd if absent.

## Epic C — Splits (ticket 2)

Goal: one frozen train/eval/test split reused by every later ticket.
Spec parent: T18 (80/20 participant split + five development folds; IDs disjoint;
inspection records to development; Full/Reduced share hashes).
Ticket 1 supplies the labelled participant list; ticket 2 persists versioned manifests
with support counts. No re-rolls after freeze.

## Epic D — Single-XGB baseline (tickets 3–4)

Goal: one working 4-class XGBoost on full-data labels, then its scored record.
Spec parents: T23 (paired matrices, one row/night) + T27/T28 (harness + XGB adapter)
+ T24 (metrics: accuracy, macro/weighted F, per-class scores, confusion matrices).
Ticket 3 wires the pipeline on the train split; ticket 4 trains and records
accuracy + F-measure + confusion matrix on the frozen split with saved predictions
and run metadata. Test-split policy stated, not consumed early.

## Epic E — 4-checkpoint matrix (tickets 5–6)

Goal: remaining 4-class XGB + CNN, then all 4 checkpoints trained with batches.
Spec parents: T20 (partial = HR + SpO₂ only) + T21/T22 (full additions) + T31/S13
(streaming night dataset, padding/masks, batch fits budget) + T32/T33 (CNN arch + training).
Matrix = partial/full × XGBoost/CNN = 4 checkpoints. Batching mandatory
(6 ch × ~6M float64 ≈ 275 MB/night — stream windows, never whole nights).
All runs use the ticket-02 train split; checkpoints saved with provenance.

## Epic F — Compare (ticket 7)

Goal: peak accuracy + F-measure + confusion matrix per checkpoint on the same split.
Spec parents: T24/T25 (metrics + paired bootstrap intent, reduced here to same-split
peak reporting) + T36 (matched-ID reload discipline).
Side-by-side CMs, no split re-rolls, no test-leak repairs.
