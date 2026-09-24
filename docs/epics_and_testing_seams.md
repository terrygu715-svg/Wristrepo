# Epics, Critical Testing Seams, and STOP-AND-TEST Updates

- Source: `Sleep_Apnea_Implementation_Tickets.docx` v1.0, 17 Sep 2026 (merged spec v2.0), 45 core tickets, 78.5 h planning allowance.
- This file is the epic organization + test-seam index + ticket Done amendments. It does not edit the `.docx`; amendments in §4 override/augment the `.docx` Done criteria until the `.docx` is reissued.
- §7 records the Kaggle-source amendment, which supersedes all MESA assumptions in the `.docx` and in `docs/decisions.md` P01/P02/P06/P08/P10/P11. Where §7 conflicts with §1–§6, §7 wins.
- Plan rule applied throughout: tests target leakage, pairing, serialization, alignment, and score correctness, not code mirrors.

## 0. Repo reality check (recalculated frontier)

- T01 Done: `docs/decisions.md` exists with P01–P15 owners/evidence (MESA-framed; see §7 supersession).
- T02 Done: `environment_report.json` exists. Verified backend = CPU. No CUDA (Apple M4, no torch/TF). The latest T16 ledger measured 7.9 GiB free while `Kaggledata/` (~22 GB) sits on that disk. E04 stays open; T16 requires remediation, not a download.
- Data present locally (git-ignored): `Kaggledata/patients.csv` (80 rows) + `Kaggledata/polysomnographics/` (80 `.npy`, 40 users × 2 nights). Profiled in §7.
- T03 Done: scaffold committed in `c79d223`; the status note was recorded in `e8fafdc`. The §4 gate is closed.
- T04 Done (Kaggle rescoping): `docs/kaggle_access.md` — URL and publisher recorded; manifest 80 files / 23,613,965,440 bytes, verify OK. License remains UNVERIFIED (blocks sharing only).
- T05 Done: `docs/kaggle_evidence.md` records M01–M09 and U01–U07 with Kaggle API evidence and explicit unknowns. E02 and remaining source-data questions stay open.
- E-B Done: implementation committed in `c79d223`; test-strengthening committed in `bbe49d9`; current suite is 116 tests. Local source ingestion is covered; network retry is explicitly Not applicable for the local Kaggle copy.
- GitHub progress: 14 finished/not-applicable issues are closed; all review, provisional, blocked, and pending issues remain open. Seam correction commit `c97b91d` is the current implementation head.
- T08 Done: `outputs/sample_manifest.json` verifies two pre-registered inspection files against the canonical manifest and `patients.csv`; IDs are development-only.
- T09 Done: `outputs/sample_inventory.json` records value statistics for the registered samples and both 16-channel anomalies (`User-8-Night-1.npy`, `User-14-Night-2.npy`). The anomalies are quarantined and excluded from the six-channel contract; their extra rows are unmapped and are not remapped or zero-filled.
- T10 Done/Blocked at E02: labels parse comma decimals, apply tested provisional lower-inclusive boundaries, and produce 20 labelled participants plus 20 participant-level exclusions (40 source rows). AHI semantics and scientific boundary sign-off remain unverified.
- T11 Done: `docs/alignment_feasibility.md` records the source review and explicit omit-motion decision for both inputs. Unmapped channel semantics remain a T12 contract concern, not a motion claim.
- Next hard stop: T12 cannot close, and T18 cannot generate manifests until its C04 leave-one-participant-out redesign is implemented and tested; the one-night cohort has only 20 participants with class support normal 1, mild 2, moderate 7, severe 10.
- Full ticket ledger: `docs/ticket_status.md` (active statuses for T01–T45 and C01–C04).
- `random_forest.py` (iris demo) is out of scope for all epics. `docs/decisions.md §3` exclusions stand.

## 1. Epics (waves → epics, with gates)

| Epic | Wave | Tickets | Exit / gate |
|------|------|---------|-------------|
| E-A Foundation & governance | 0 Start | T01, T02, T04, T05 → T03 | T03 Done (schema rejects missing IDs + ambiguous order; example config marks UNVERIFIED; src/outputs distinct). Unlocks synthetic work. |
| E-B Synthetic + infra (no real data) | 1 Setup | T06, T07, T19, T24, T25, T26, T34, T35 | Each ticket's fixture/interface test passes on SYNTH_ data only. Never counted as results. Can overlap access wait. |
| E-C Real-data audit + protocol freeze | 2 Data | T08 → T09, T10, T11 → T12 → T13–T18 | T12 freezes input/quality contract; T18 freezes paired cohort partitions. E01–E05 evidence required. |
| E-D Features + neural loading | 3 Features | T20, T21, T22 → T23; T31 → T32 | T23 development matrices with identical Full/Reduced IDs/labels; T32 shape/gradient + padding-invariance pass. No test scoring. |
| E-E Training + first pair | 4 First pair | T27 → T28, T29, T30; T27+T32 → T33; → T36 | T36: reloaded GBT dev pair reproduces scores with matched IDs. Does not wait for neural. No test opened. |
| E-F Development CV + freeze | 5 CV | T37, T38, T39 → T40 | T40 `release_manifest.json` freeze review; every pair has reviewed CV evidence. |
| E-G Final release | 6 Final | T41, T42 → T43 → T44 → T45 | T43 first test scoring (coverage validated before scoring); T45 clean reload/report regeneration reproduces results. |

Controlling chain (not a schedule): T04+T07 → E01 → T08 → audit/labels → T12 → T13/T14+T16 → T17 → T18 → feature/trainer or neural path → T36 → slowest of T37/T38/T39 → T40 → slowest of T41/T42 → T43 → T44 → T45.

Parallel rules: one schema integrator after T03; separate module owners after T12 (T20/T21/T22); one GPU job + bounded CPU workers; separate run dirs; single coordinator writer.

## 2. Critical testing seams (where to stop and test)

| Seam | Boundary | What must be tested (not a code mirror) | Primary ticket(s) | Failure if missed |
|------|----------|------------------------------------------|-------------------|-------------------|
| S01 Contract/ID integrity | schemas ↔ all manifests/predictions | Missing/empty/duplicate IDs rejected; class_order length-4 unique; object/version/numeric consistency enforced | T03, T06 | Silent ID drops corrupt every downstream join |
| S02 Acquisition integrity | local source ↔ manifest | For Kaggle: selected files match canonical size/hash, missing/corrupt files fail, logs contain no secret; network resume is Not applicable | T07, T08, T16 | Partial/replaced local files treated as complete; credential leak |
| S03 Participant disjointness | splits ↔ everything | Dev/test/fold IDs disjoint; inspection IDs (T08–T17) forced to development; Full/Reduced share split hashes | T18, T23, T27 | Test contamination; inflated scores |
| S04 Label boundaries | labels ↔ cohort | Exact AHI cut-point inclusivity (e.g. 5/15/30 ±ε), participant-level missing-label exclusion, duplicate-row rejection, summary-vs-reconstruction reconciliation | T10 (+C01) | Off-by-one class shift; invented AHI |
| S05 Alignment/quality | raw signals ↔ masks | Quantified proxy evidence or documented omission; synthetic offset/gap recovery; absent signal ≠ zero activity; Full/Reduced share common policy | T11, T14 (+C02) | Motion misalignment becomes fake signal |
| S06 Cache determinism | preprocessing ↔ cache | No participant boundary crossed; hash changes with preprocessing; no globally fitted norm cached | T15 | Cache hides config change; leakage via normalization |
| S07 Train-only fitting | splits ↔ transforms | Held-out sentinel values don't move fitted params; feature order deterministic; missing-feature fail | T19 | Scaler/imputer fitted on test |
| S08 Full/Reduced pairing | channels ↔ features ↔ rows | Full-only channels absent in Reduced (channel-permission test); rows share identical IDs/labels | T21, T23, T28 | Reduced sees Full-only signal; comparison invalid |
| S09 Score correctness | predictions ↔ metrics | Known synthetic confusion matrices → expected macro/weighted F1; duplicate/missing IDs + class-order errors fail | T24 | Wrong metric implementation ships to final |
| S10 Comparison validity | metrics ↔ report | Identical predictions → zero gap; row reorder harmless; unmatched IDs fail; n_bootstrap=2000; strata-conditioned statement present | T25, T44 | Unpaired bootstrap; overstated significance |
| S11 Bundle serialization | training ↔ inference | Round-trip inference matches within tolerance; wrong feature/config version rejected; atomic writes | T26, T32 | Stale bundle scored as current release |
| S12 Harness separation | training ↔ scoring | Dummy baseline runs on dev; inner stopping ≠ outer scoring; fit-on-test rejected; epoch selection never reads test | T27, T33 | Test-driven stopping/selection |
| S13 Neural masking | cache ↔ loader ↔ head | One target per night; padded/missing blocks masked; masked padding doesn't change output; batch fits measured budget | T31, T32 | Padding leaks into prediction; OOM mid-CV |
| S14 Orchestration/reporting | coordinator ↔ ledger ↔ report | Failed jobs stay visible; resume rejects stale hashes; distinct worker outputs; single ledger writer; report regen does no training | T34, T35, T45 | Lost failures; report regenerates different numbers |

## 3. Seam → test-file map (target layout)

Current test files:

- `tests/test_contracts.py` — S01 contract rejection and schema/config parity.
- `tests/test_acquisition.py` — S02 local manifest/hash/secret guard.
- `tests/test_audit_sample.py` — S02/T08 sample join; S05 audit and omit/proxy branches.
- `tests/test_labels.py` — S04 parsing, boundaries, duplicate rows, participant exclusions.
- `tests/test_fixtures.py` — T06 deterministic synthetic data and fixture-level S03 tripwire.
- `tests/test_metrics_compare.py` — S09/S10 hand-computed metrics, identity pairing, bootstrap.
- `tests/test_artifacts.py` — S11 bundle round-trip, schema/version, object-array and atomic-failure guards.
- `tests/test_preprocessing.py` — S07 train-only sentinel/order/math.
- `tests/test_coordinator.py` — S14 dependency, failure, stale/running recovery, lock, report behavior.

Future test files, blocked by their owning tickets: `tests/test_quality.py` (S05/T14),
`tests/test_cache.py` (S06/T15), `tests/test_pairing.py` (S03/S08/T18/T21/T23),
`tests/test_harness.py` (S12/T27/T33), and `tests/test_neural_loading.py`
(S13/T31/T32).

All synthetic IDs use `SYNTH_` prefix. No empirical numbers in these files.

Coverage audit 24 Sep 2026 (116 tests): S01/S02/S04/S07/S09/S10/S11/S14
have meaningful unit/failure-path coverage. S05 has audit/decision coverage,
but not real synchronization or T14 masking. S03 is fixture-only. S06/S08/S12/S13
are not implemented and have no placeholder tests. Full details and the
remaining risks are in `docs/gap_review.md`.

## 4. STOP-AND-TEST ticket updates (amendments to .docx Done criteria)

Notation: STOP = do not start listed downstream work until the test passes. Only tickets needing strengthening are listed; unlisted tickets keep their .docx Done as-is.

- T03 — STOP T06/T19/T24/T26/T34 until `tests/test_contracts.py` (21 tests) passes AND a commit hash is recorded. This gate is now cleared by `c79d223`.
- T06 — STOP T13/T15/T19 until new `tests/test_fixtures.py` proves: class-boundary rows exist, missing-block rows exist, repeated-participant rows exist, and a leakage-check fixture fails when a participant spans splits. Amendment: fixture manifest must validate via `validate_manifest`.
- T07 — STOP T08 until `tests/test_acquisition.py` proves the local manifest catches missing/corrupt files and the secret scan passes. Network interrupt/resume is Not applicable for this already-local Kaggle source; the handoff must say so.
- T08 — STOP T09/T10/T11 downstream interpretation until the sample manifest verifies selected file hashes against T07 and joins every inspection ID to `patients.csv`; inspection IDs are development-only.
- T09 — STOP T11/T12 until the 16-channel anomaly has a disposition and the audit records channel count, dtype, finite-value range, NaN/Inf fractions, standard deviation, extreme count, bytes, and hash.
- T10 — STOP T12/T17 until `tests/test_labels.py` proves boundary inclusivity at every cut point (±ε both sides), comma-decimal parsing, duplicate-row rejection, participant-level missing-label exclusions, and sample IDs reconcile. AHI semantics and boundaries still require E02 evidence. If summary AHI is inadequate: STOP and open C01; T10 stays Blocked (no generic event summation).
- T11 — STOP T12 (when proxy selected) until offsets + missing coverage are quantified on samples. The documented no-motion decision in `docs/alignment_feasibility.md` completes T11. If alignment is later found inconsistent: STOP and open C02 (one 120-min session, then map or omit — no repair loop).
- T14 — STOP T15 until `tests/test_alignment_quality.py` proves absent signal is masked (never zero-filled as zero activity) and Full/Reduced use the common policy on a synthetic offset/gap case.
- T15 — STOP T20–T22/T31 until `tests/test_preprocessing.py` proves: no cross-participant windows, cache hash changes when preprocessing changes, labels stored separately. Amendment: record cache hash in handoff.
- T18 — PROTOCOL GATE. STOP all of T23/T27/T31/T36 until split manifests prove IDs disjoint, class support reported, Full/Reduced share hashes, and T08–T17 inspection IDs are all in development. If counts cannot support 80/20 + 5-fold, use the documented C04 revision; never silently merge classes.
- T19 — STOP T27 until sentinel test proves held-out values don't move fitted params + feature-order determinism. Amendment: test must use SYNTH_ features only.
- T21/T22 — STOP T23 until `tests/test_pairing.py` proves Full-only channels cannot appear in Reduced and every modality has documented handling; annotations provably unread (import/scan check).
- T23 — STOP T27 until paired matrices prove identical IDs/labels across Full/Reduced and feature→channel provenance declared. Amendment: record row counts + manifest hash; no test-score computation allowed in this ticket.
- T27 — STOP T28/T29/T30/T33 until dummy/simple baseline runs on dev data, inner-stopping vs outer-scoring separation demonstrated, and fit-on-test raises. Amendment: record stopping policy in run metadata.
- T31 — E04 sub-gate. STOP T33/T39 until measured batch fits the T02 budget (16 GiB unified, ~25 GiB disk) on this laptop; record batch size, RAM high-water, backend string (CPU, or MPS only if a torch pilot proves it — never assume CUDA).
- T32 — STOP T33 until shapes/gradients pass, masked-padding invariance holds, bundle round-trip works, and no window carries an event label.
- T34 — STOP T37–T39 job submission until `tests/test_coordinator.py` proves failed jobs visible, resume rejects stale hashes, workers write distinct outputs, single ledger writer enforced.
- T36 — INTEGRATION GATE. STOP T37/T38/T39 until reloaded GBT dev predictions reproduce scores with matched IDs; defect list has bounded follow-ups; confirm no test partition was opened.
- T37/T38/T39 — STOP T40 until ALL fold/input jobs succeed AND are reviewed on development results only (10 / 20 / 10 jobs respectively). Any unresolved job → ticket stays Blocked; SVM over-budget → split continuation, never retune on test.
- T40 — RELEASE GATE. STOP T41/T42 until `release_manifest.json` freeze review confirms: every pair has CV evidence, no unresolved label/leakage issue, seed/preprocessing/split/bootstrap hashes pinned, baseline-vs-tuned scope explicit.
- T43 — FIRST TEST SCORING. STOP T44 until coverage validation (all 8 bundles, matched IDs/labels) passes BEFORE scoring; any pipeline failure gets documented repair, never selective exclusion.
- T44 — STOP T45 until numbers reconcile with saved predictions, bootstrap gaps state model/class conditioning, no equivalence claim or invented AHI present, failed runs prominent.
- Conditional C01/C02/C03/C04 are never silently required; each is a separately estimated bounded session triggered only on the evidence stated in the .docx.

## 5. Recommended next sessions (unchanged order, with stop tests inserted)

1. T12: freeze the channel, omit-motion, label, and quality contract after E02/E04 evidence review.
2. T16: resolve storage capacity and repeat the E04 ledger before cache work.
3. T18: implement the C04 fold manifests and support/disjointness tests.
4. T12 freeze, then implement T13–T18 with S05–S07 stop tests.

## 6. Acceptance check for this organization

- [x] All 45 core tickets placed in exactly one epic (§1); C01–C04 and E01–E05 carried as gates, not tickets.
- [x] Every Definition-of-Done test target (leakage, pairing, serialization, alignment, score correctness) mapped to ≥1 seam (§2) and ≥1 test file (§3).
- [x] Every protocol gate (T12/T18/T36/T40/T43) and every ticket that must halt downstream work has an explicit STOP rule (§4).
- [x] No synthetic scores presented as results; no test partition opened before T43; no scope change without config revision.
- [x] Kaggle amendment (§7) profiles measured data, rescopes MESA tickets, and forces the C04 cohort redesign before T18 closes.

## 7. Kaggle-source amendment (supersedes MESA assumptions)

Measured profile (conda Python, read 17 Sep 2026; sampling rate still UNVERIFIED):

- `Kaggledata/polysomnographics/`: 80 `.npy`, float64. 78 files are `(6, ~5.19–6.94M)` samples ≈ 7.2–9.6 h at an assumed 200 Hz. 2 anomalies with **16 channels**: `User-8-Night-1.npy`, `User-14-Night-2.npy`. One probed file spans −3541…+3395 with per-channel means near 0 — extreme values need T09 explanation (artifact vs unit), not silent clipping.
- `Kaggledata/patients.csv`: 80 rows (40 users × nights 1–2). Decimals use **commas** (`17,7`). Only **20 of 40 users have any AHI** (both nights labelled or neither). Labelled nights = 40, class split at 5/15/30: severe 20, moderate 15, mild 4, normal 1.
- One-night-per-participant rule → at most **20 labelled nights**. 80/20 + 5-fold over ~16 dev participants with 1 normal total is indefensible — **C04 triggers by measurement, not opinion** (see T17/T18 below).
- `Kaggledata/` is git-ignored and lives on the disk measured at 7.9 GiB free by T16. Storage, not download, is the T16 risk.

Ticket/gate remap (MESA → Kaggle). Unlisted tickets keep their `.docx` Done:

- E01 Access: clears on local availability + provenance/license note, not external approval. T04 rescoped to "verify Kaggle provenance, license/redistribution terms, and record a local inventory (80 files, sizes, header census)". T04 submission + inventory clears E01. No credentials exist; the no-secrets test in T07 stands as a guard, not a credential flow.
- T05 rescoped to "audit the Kaggle dataset page/docs": signal layout, channel identities/order, sampling rate, AHI definition and sleep-time denominator, meaning of AI/HI/ODI/NAp/NHyp columns. Every §7 anomaly (16-ch files, comma decimals, 50% label missingness, extreme values) must appear as a sourced claim or explicit unknown in `docs/kaggle_evidence.md`.
- T07: `acquire_*.py` becomes local ingestion — manifest of all 80 files with byte sizes + hashes, header census, integrity re-check. Network resume/retry is Not applicable (record why); manifest + integrity + secret-scan stay.
- T08: sample from local files (no transfer wait). Reserve inspected records for development; record IDs for T18 exclusion from test.
- T09: EDF/annotation audit becomes `.npy` header + value audit — per-file shape/dtype census, inferred-vs-documented sampling rate, the two 16-channel files quarantined/excluded, value-range/artifact report, and channel-identity evidence (or explicit unknown going into T12).
- T10 Done/Blocked E02: `labels.py` parses the real `patients.csv` header/first rows with comma-decimal handling (`17,7` → 17.7), lower-inclusive provisional boundaries, duplicate rejection, and explicit missing-AHI exclusions. The output retains 20 labelled participants, 20 participant exclusions, and 40 excluded source rows. C01 (XML reconstruction) is Not applicable because no XML/event source is present; AHI scoring semantics still block E02.
- T11 Done: six EEG channels are documented, with no motion/HR/SpO2 time series or overlap evidence. The documented omit-motion path is selected for both inputs and E03 clears for alignment; T12 still freezes the channel/feature contract.
- T12: Reduced/Full sets are chosen from the verified Kaggle channels (≤6 + resolution of 16-ch anomalies), not MESA montages. T13–T15 read `.npy`, not EDF.
- T16: no download. Deliverable becomes a storage-verification ledger: `df` before/after, 22 GB accounted, free-space remediation (clean or externalize) if below the T02 budget. Latest check is 7.9 GiB free, so T16 remains blocked and no cache generation (T15/T23) is allowed until E04 clears.
- T17: eligible cohort is at most the 20 labelled participants (one night each). Cohort flow report must show the 20 unlabelled users excluded by rule and class support per split/fold plan.
- T18: STOP — E05 cannot clear on the original 80/20 + 5-fold design (normal n=1). C04 selects 20 participant-level leave-one-participant-out outer folds with fixed a priori settings; T18 must produce versioned manifests and disjointness/support tests before any downstream CV.
- T23 scale note: development matrices are ~16 nights (post-C04), not a MESA-scale cohort. Pairing tests (S08) are unchanged and matter more at this n.
- T31/E04: batch-fit pilot is also a RAM pilot for float64 `.npy` windows (6 × ~6M float64 ≈ 275 MB per night in memory) — stream, don't load nights whole. T33/T39 inherit the measured policy.

New STOP-AND-TEST additions from §7 (append to §4):

- T05 STOP T10/T12 until the evidence doc records the sampling rate, channel identities (or unknown), AHI definition/denominator, and all four §7 anomalies with sources.
- T09 STOP is cleared for T11–T14 regarding anomaly disposition: both 16-channel files are quarantined/excluded and the regression test asserts the finalized reason. T11 is complete via omit-motion; T12 remains gated by unresolved channel semantics and E02/E04/E05 evidence.
- T10 STOP is cleared for T12/T17 regarding parser mechanics: comma-decimal parsing, boundary inclusivity, and missing-label exclusion tests pass on the real `patients.csv` header/first rows. E02 AHI semantics and denominator remain a separate stop.
- T16 STOP T15/T23 cache work until the storage ledger shows fit within the T02 budget.
- T18 STOP T23 and everything downstream until `docs/cohort_redesign.md` is implemented as split manifests that pass disjointness + support tests.
