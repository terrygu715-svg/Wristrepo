# Simplified Re-ticket — v1.0 decisions (branch: `reticket/simplified-flight`)

> Status: v1.0 AGREED DIRECTION — 24 Sep 2026.
> Old flight (T01–T45 + C01–C04, E01–E05) is frozen on `main`; nothing here changes it.
> New flight: straight-numbered tickets grouped by epic specs. Same scope, user-guided path.

## 1. Why the old flight is too complex for what we're building

Carried from `docs/` on `main` (a9894ab). The old-flight source files below were removed
from this branch to avoid ambiguity — they remain on `main` for reference.

- **45 core tickets + 4 conditional (78.5 h plan)** across 7 epics (E-A…E-G), 14 testing seams
  (S01…S14), 14 STOP-AND-TEST gates, 5 evidence gates (E01–E05). Source:
  `docs/epics_and_testing_seams.md`, `docs/ticket_status.md`.
- **Hard stop at T12/T18 (L0 frontier):** only 20 labelled participants after one-night rule
  (normal 1 / mild 2 / moderate 7 / severe 10); 80/20 + 5-fold indefensible → C04 forces
  20-fold leave-one-participant-out. Source: `docs/cohort_redesign.md`.
- **Signal is thinner than the plan assumes:** 6 EEG rows only (`Fp1-M2…O2-M1`, 200 Hz per
  Kaggle API), no motion/HR/SpO2 time series → T11 omit-motion; 2× 16-ch files quarantined;
  extreme values (−3541…+3395) unexplained; sampling/channel semantics partly open.
  Source: `docs/kaggle_evidence.md`, `docs/alignment_feasibility.md`.
- **Label gate open:** AHI = (NAp+NHyp)/TimeOfRecordInHours per API, but scoring rule,
  subtype coverage, sleep-time denominator, exact 5/15/30 boundary sign-off all UNVERIFIED
  (E02). T10 parses comma decimals and emits 20 labels + 20 exclusions, but stays
  Done/Blocked E02. Source: `docs/kaggle_evidence.md` U04, `docs/decisions.md` P02–P05.
- **Capacity gate open:** ~22 GiB dataset on disk with 7.9 GiB free (T16 ledger); no cache/
  training allowed until storage remediated + streaming pilot measured. Source:
  `docs/storage_ledger.md`.
- **What still works:** E-B infra (116 tests: S01/S02/S04/S07/S09/S10/S11/S14), T07 local
  manifest verify OK (80 files), T08 sample manifest, T09 quarantine, T10 parser mechanics.
  Source: `docs/gap_review.md`, `docs/ticket_status.md`.

Verdict carried forward: the old flight is a full publication-grade Full-vs-Reduced
comparison with release gates (T36/T40/T43). If the actual goal is smaller (feasibility
demo / wrist-relevant subset / methods spike), we should not carry its gates.

## 2. Agreed scheme (v1.0, per user 24 Sep 2026)

- **Tickets:** straight numbers `01, 02, 03…` (no Txx/Cxx/Exx; old tags stay on `main` only).
- **Grouping:** epic specs group tickets. Epics are docs, tickets are work units.
- **Scope:** UNCHANGED — 4-class night-level severity (5/15/30 provisional), Full-vs-Reduced
  pairing, XGBoost + CNN deep-learning path, CPU baseline first. Simplification is in
  ticket count/gates, not in task or models.
- **Code mechanics:** blank rewrite on this branch. `src/sleep_apnea/*` (old E-B infra) stays
  as reference on `main` only; this branch will delete/replace `src/` once ticket 01 lands.
  No code deletion until epic/ticket v1.0 is frozen.
- **Dev path:** user-guided. No auto-build past documentation until user directs each epic.

## 3. Kept scope (explicit — simplification does NOT cut these)

- [x] 4-class night-level severity, awake retained, participant-disjoint splits
- [x] Full-vs-Reduced pairing (Reduced = true subset, shared IDs/labels)
- [x] XGBoost (conventional) + CNN (neural) paths
- [x] Known hard facts carried as inputs, not re-decided: 20 labelled participants
  (1/2/7/10), 6 EEG @200 Hz omit-motion, 2×16-ch quarantined, comma-decimal AHI parse,
  7.9 GiB free storage gate, 116-test E-B infra as reference
- [ ] Simplification target = fewer tickets, fewer STOP cascades, epic-grouped specs

## 4. Agreed implementation path (user direction, 24 Sep 2026 — supersedes 12-step draft)

Straight numbers `0–7`, grouped by epic specs. Old 12-step table in §5 is scrapped.

| # | Epic | Title | Done = |
|---|---|---|---|
| 0 | Epic A — Foundation | Environment + dependency assess (dataset assumed local) | `environment_report.json`-equivalent refreshed: Python/deps (numpy, sklearn, xgb, torch/CNN backend), CPU/CUDA/MPS, RAM/disk vs ~22 GiB local dump; missing-dep list; no downloads |
| 1 | Epic B — Data audit | Data audit + freeze (keep from old flight) | 6-EEG contract (omit-motion, quarantine 2×16-ch), comma-decimal AHI parse, 20 labels + exclusions, one-night rule frozen in a single config |
| 2 | Epic C — Splits | Train/eval/test split on local dataset | Versioned manifests, participant-disjoint, same split reused by all later tickets; support counts recorded |
| 3 | Epic D — Baseline | Single XGBoost on full-data labels | XGB 4-class pipeline wired to full feature set on downloaded data; trains without error on train split |
| 4 | Epic D — Baseline score | Train + record metrics (single XGB) | Accuracy + F-measure (macro/weighted) + confusion matrix on eval (and test policy stated); saved predictions + run metadata |
| 5 | Epic E — Full matrix | Remaining 4-class XGB + CNN setup | XGB variants + CNN classifier implemented with batched loading (stream windows, never whole nights; spec T31 batch-fit rule) |
| 6 | Epic E — Matrix train | All 4 checkpoints: partial/full × XGB/CNN | 4 runs (partial-XGB, full-XGB, partial-CNN, full-CNN) trained on ticket-02 train split with batching; checkpoints saved |
| 7 | Epic F — Compare | Peak acc + F + CM per checkpoint, same split | Peak-checkpoint metrics per run on the identical split; confusion matrices side-by-side; no split re-rolls |

Notes:
- Dataset: https://www.kaggle.com/datasets/yfrite/polysom (assumed local; no re-download).
- "Partial data" = HR + SpO₂ only, per spec T20 (`features/cardiorespiratory.py` — shared HR-level
  trends/variability + SpO₂ with context/missingness rules). "Full data" = partial + T21
  (ECG/airflow/effort) + T22 (EEG/EOG/EMG/position). Reduced stays a true subset (old S08).
- Ticket-02 split = spec T18: 80/20 participant split + five development folds, IDs disjoint,
  inspection records constrained to development, Full/Reduced share hashes. Exact counts are
  derived in ticket 1/2 implementation against the local copy (20 labelled participants expected
  per prior audit: 1/2/7/10 — insufficient for 80/20+5-fold without revision; ticket 1 must state
  the actual rule used).
- Labels = spec T10: verified summary AHI preferred, 4 classes, boundaries recorded; comma-decimal
  handling for this source.
- ⚠ Known gap carried in: this Kaggle source measured 6 EEG rows only with no HR/SpO₂ time series
  (see `docs/kaggle_evidence.md`, `docs/alignment_feasibility.md`). Ticket 1 must confirm or refute
  HR/SpO₂ availability on the local copy before tickets 3–6 can proceed as spec'd.

## 5. Scrapped: 12-step draft (kept for history, not active)

| # | Epic | Title (merges old) | Done = |
|---|---|---|---|
| 01 | Epic A — Contracts & fixtures | Schemas + SYNTH_ fixtures (old T03+T06) | `tests/test_contracts.py` + `test_fixtures.py` pass on SYNTH_ only |
| 02 | Epic A | Local ingestion manifest (old T07) | 80-file manifest + verify OK + secret guard; network N/A stated |
| 03 | Epic B — Data audit | Sample + value audit + quarantine (old T08+T09) | sample_manifest verified; 16-ch quarantined with stats/hash |
| 04 | Epic B | Labels + cohort rule (old T10+T17+C04) | 20 labels + 20 exclusions, comma-parse, boundary tests; one-night rule frozen |
| 05 | Epic B | Channel/quality contract (old T11+T12+T14) | omit-motion + 6-EEG contract + mask policy frozen in one config |
| 06 | Epic C — Windows/cache | Readers + window cache (old T13+T15) | `.npy` reader + cache hash/provenance tests; streaming rule for 7.9 GiB disk |
| 07 | Epic C | Splits (old T18) | 20-fold LOPO manifests + disjointness/support tests |
| 08 | Epic D — Features | Full/Reduced matrices (old T20–T23) | paired matrices, identical IDs/labels, Full-superset proof |
| 09 | Epic E — Training | Harness + XGBoost + CNN loader/arch (old T27–T33) | fit-on-test rejected, stopping/scoring separated, padding masked |
| 10 | Epic E | Dev CV (old T36–T39) | reloaded dev-pair reproduces scores; all folds reviewed |
| 11 | Epic F — Release | Freeze + final refits (old T40–T42) | `release_manifest.json` + 8 bundles |
| 12 | Epic F | Scoring + report + repro (old T43–T45) | coverage-before-scoring, bootstrap comparison, regen reproduces |

Old STOP-AND-TEST seams S01–S14 fold into the Done column above instead of 14 separate gates.
Storage ledger (old T16) becomes a pre-condition on 06, not a standalone ticket — confirm?

## 6. Ticket docs (active): `docs/reticket_epics.md` (Epics A–F) + `docs/reticket_tickets.md`
(tickets 0–7) + `docs/reticket_new_dataset.md` (rerun on a different dataset).
Docs only — no env work, no code, per user direction.
