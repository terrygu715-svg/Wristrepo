# Epics, Critical Testing Seams, and STOP-AND-TEST Updates

- Source: `Sleep_Apnea_Implementation_Tickets.docx` v1.0, 17 Sep 2026 (merged spec v2.0), 45 core tickets, 78.5 h planning allowance.
- This file is the epic organization + test-seam index + ticket Done amendments. It does not edit the `.docx`; amendments in §4 override/augment the `.docx` Done criteria until the `.docx` is reissued.
- §7 records the Kaggle-source amendment, which supersedes all MESA assumptions in the `.docx` and in `docs/decisions.md` P01/P02/P06/P08/P10/P11. Where §7 conflicts with §1–§6, §7 wins.
- Plan rule applied throughout: tests target leakage, pairing, serialization, alignment, and score correctness, not code mirrors.

## 0. Repo reality check (recalculated frontier)

- T01 Done: `docs/decisions.md` exists with P01–P15 owners/evidence (MESA-framed; see §7 supersession).
- T02 Done: `environment_report.json` exists. Verified backend = CPU. No CUDA (Apple M4, no torch/TF). ~25 GiB free at inspection — and `Kaggledata/` (~22 GB) now sits on that same disk. E04 stays open; T16 must start with a `df` check and free-space remediation, not a download.
- Data present locally (git-ignored): `Kaggledata/patients.csv` (80 rows) + `Kaggledata/polysomnographics/` (80 `.npy`, 40 users × 2 nights). Profiled in §7.
- T03 Review (not Done): scaffold exists in working tree but is uncommitted (`src/sleep_apnea/contracts.py`, `schemas/*.json`, `configs/example_config.json`, `tests/test_contracts.py`, 14 tests passing). Commit it before marking Done. Until then T06/T19/T24/T26/T34 stay Blocked.
- T04 Done (Kaggle rescoping): `docs/kaggle_access.md` — manifest 80 files / 23,613,965,440 bytes, verify OK; E01 clears for local work. License/URL still UNVERIFIED (blocks sharing only).
- T05 measured-half Done: `docs/kaggle_evidence.md` — M01–M08 sourced, U01–U07 open with owners. Source-doc half waits on the dataset link.
- E-B Done (implementation + tests, 17 Sep 2026, commit `c79d223`): T06 `data/fixtures.py`, T07 `data/ingest.py`, T19 `preprocessing/fitted.py`, T24 `evaluation/metrics.py`, T25 `evaluation/compare.py`, T26 `artifacts/checkpoints.py`, T34 `coordinator.py`, T35 `generate_report.py`; 54/54 tests pass (14 T03 + 40 new). T03 Done: scaffold committed in `c79d223`, closing the §4 gate — E-B is formally unblocked.
- Next: E-C fieldwork on measured data (T08 sample → T09 header/value audit → T10 comma-decimal labels → T11 channel identity) and the mandatory C04 redesign before T18.
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
| S01 Contract/ID integrity | schemas ↔ all manifests/predictions | Missing/empty/duplicate IDs rejected; class_order length-4 unique enforced | T03, T06 | Silent ID drops corrupt every downstream join |
| S02 Acquisition integrity | network ↔ manifest | Mock interrupt resumes; corrupt bytes fail; logs contain no secret (grep test) | T07, T16 | Partial downloads treated as complete; credential leak |
| S03 Participant disjointness | splits ↔ everything | Dev/test/fold IDs disjoint; inspection IDs (T08–T17) forced to development; Full/Reduced share split hashes | T18, T23, T27 | Test contamination; inflated scores |
| S04 Label boundaries | labels ↔ cohort | Exact AHI cut-point inclusivity (e.g. 5/15/30 ±ε), missing-label fail, summary-vs-reconstruction reconciliation | T10 (+C01) | Off-by-one class shift; invented AHI |
| S05 Alignment/quality | raw signals ↔ masks | Synthetic offset/gap recovery; absent signal ≠ zero activity; Full/Reduced share common policy | T11, T14 (+C02) | Motion misalignment becomes fake signal |
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

Existing: `tests/test_contracts.py` covers S01 (partial), S09/S10 (partial via schema checks).
Add as owners clear prerequisites (do not create before T03 is committed):

- `tests/test_fixtures.py` — S01, S03, S06 (T06, T15, T18 properties on SYNTH_ data)
- `tests/test_acquisition.py` — S02 (T07 mock resume/corrupt/secret-scan)
- `tests/test_labels.py` — S04 (T10 boundaries/missing; C01 reconciliation when triggered)
- `tests/test_alignment_quality.py` — S05 (T11/T14 offset/gap/no-zero-fill)
- `tests/test_audit_sample.py` — S02 (sample manifest, reserved IDs), S05 (shape/dtype records, NaN mapping, 16-ch quarantine, non-2D reject, omit/proxy/E03 branches)
- `tests/test_preprocessing.py` — S06, S07 (T15 hashes/boundaries; T19 sentinel/order)
- `tests/test_pairing.py` — S03, S08 (T21/T23 identical IDs, Full-only absence)
- `tests/test_metrics_compare.py` — S09, S10 (T24/T25 synthetic matrices, reorder, unmatched, n=2000)
- `tests/test_artifacts_harness.py` — S11, S12 (T26 round-trip/version/atomic; T27 test-fit reject, stopping separation)
- `tests/test_neural_loading.py` — S13 (T31/T32 one-target, mask, padding invariance, budget)
- `tests/test_coordinator.py` — S14 (T34 stale-hash reject, single writer; T35 regen-no-training)

All synthetic IDs use `SYNTH_` prefix. No empirical numbers in these files.

Coverage audit 17 Sep 2026 (85 tests): S01/S02/S04/S05/S07/S09/S10/S11/S14
fully covered incl. non-degenerate cases (directional bootstrap gap,
hand-computed weighted F1, bundle atomic-failure, fixture determinism).
S03 covered at fixture level only (T18/T23/T27 splits future). S06/S08/S12/S13
pending their owning tickets (T15/T21/T23/T27/T31–T33) — no placeholder tests
written for unimplemented code.

## 4. STOP-AND-TEST ticket updates (amendments to .docx Done criteria)

Notation: STOP = do not start listed downstream work until the test passes. Only tickets needing strengthening are listed; unlisted tickets keep their .docx Done as-is.

- T03 — STOP T06/T19/T24/T26/T34 until `tests/test_contracts.py` (14 tests) passes AND working tree is committed. Amendment: Done requires a commit hash recorded in the handoff note (currently uncommitted → stays in Review).
- T06 — STOP T13/T15/T19 until new `tests/test_fixtures.py` proves: class-boundary rows exist, missing-block rows exist, repeated-participant rows exist, and a leakage-check fixture fails when a participant spans splits. Amendment: fixture manifest must validate via `validate_manifest`.
- T07 — STOP T08 until `tests/test_acquisition.py` proves mock interrupt resumes, corrupt bytes fail integrity, and a secret-scan (credential pattern grep over logs + saved config) passes. Amendment: Done requires the scan log path in the handoff.
- T10 — STOP T12/T17 until `tests/test_labels.py` proves boundary inclusivity at every cut point (±ε both sides) and missing-label fail; sample IDs reconcile with the cited release doc. If summary AHI is inadequate: STOP and open C01; T10 stays Blocked (no generic event summation).
- T11 — STOP T12 (when proxy selected) until offsets + missing coverage are quantified on samples in `alignment_feasibility.json`. A documented no-motion (omit) decision with evidence MAY complete T11. If alignment inconsistent: STOP and open C02 (one 120-min session, then map or omit — no repair loop).
- T14 — STOP T15 until `tests/test_alignment_quality.py` proves absent signal is masked (never zero-filled as zero activity) and Full/Reduced use the common policy on a synthetic offset/gap case.
- T15 — STOP T20–T22/T31 until `tests/test_preprocessing.py` proves: no cross-participant windows, cache hash changes when preprocessing changes, labels stored separately. Amendment: record cache hash in handoff.
- T18 — PROTOCOL GATE. STOP all of T23/T27/T31/T36 until split manifests prove IDs disjoint, class support reported, Full/Reduced share hashes, and T08–T17 inspection IDs are all in development. If counts can't support 80/20 + 5-fold: STOP and open C04 (documented revision; never silent merge).
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

1. Commit T03 (record hash) → run T04 (access note) + T05 (evidence doc) in parallel if possible.
2. T06 fixtures + `test_fixtures.py`, then T07 + secret-scan test.
3. T24/T25/T26/T19/T34/T35 on SYNTH_ data while access waits (each with its §3 test file).
4. On E01 clear: T08 (reserve inspection IDs for dev) → T09/T10/T11 → T12 freeze → T13–T18 with S05–S07 stop tests.

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
- `Kaggledata/` is git-ignored and lives on the ~25 GiB-free disk from T02. Storage, not download, is the T16 risk.

Ticket/gate remap (MESA → Kaggle). Unlisted tickets keep their `.docx` Done:

- E01 Access: clears on local availability + provenance/license note, not external approval. T04 rescoped to "verify Kaggle provenance, license/redistribution terms, and record a local inventory (80 files, sizes, header census)". T04 submission + inventory clears E01. No credentials exist; the no-secrets test in T07 stands as a guard, not a credential flow.
- T05 rescoped to "audit the Kaggle dataset page/docs": signal layout, channel identities/order, sampling rate, AHI definition and sleep-time denominator, meaning of AI/HI/ODI/NAp/NHyp columns. Every §7 anomaly (16-ch files, comma decimals, 50% label missingness, extreme values) must appear as a sourced claim or explicit unknown in `docs/mesa_evidence.md` (rename or successor noted in handoff; do not strand the deliverable path).
- T07: `acquire_*.py` becomes local ingestion — manifest of all 80 files with byte sizes + hashes, header census, integrity re-check. Network resume/retry is Not applicable (record why); manifest + integrity + secret-scan stay.
- T08: sample from local files (no transfer wait). Reserve inspected records for development; record IDs for T18 exclusion from test.
- T09: EDF/annotation audit becomes `.npy` header + value audit — per-file shape/dtype census, inferred-vs-documented sampling rate, the two 16-channel files resolved (separate montage vs corrupt vs extra modalities), value-range/artifact report, channel-identity evidence (or explicit unknown going into T11).
- T10: `labels.py` parses `patients.csv` with comma-decimal handling (`17,7` → 17.7 must be a test case, S04). Missing AHI (20 users) → documented exclusion with reasons, never silent drop. C01 (XML reconstruction) is Not applicable to this source — record why instead of opening it.
- T11: 6 channels are currently unnamed. T11 must either identify a motion/actigraphy channel with overlap evidence or take the documented omit-motion (HR + SpO₂) path — a no-motion result still completes the ticket. E03 clears either way with evidence.
- T12: Reduced/Full sets are chosen from the verified Kaggle channels (≤6 + resolution of 16-ch anomalies), not MESA montages. T13–T15 read `.npy`, not EDF.
- T16: no download. Deliverable becomes a storage-verification ledger: `df` before/after, 22 GB accounted, free-space remediation (clean or externalize) if below the T02 budget. STOP: no cache generation (T15/T23) until E04 clears on measured free space.
- T17: eligible cohort is at most the 20 labelled participants (one night each). Cohort flow report must show the 20 unlabelled users excluded by rule and class support per split/fold plan.
- T18: STOP — E05 cannot clear on the original 80/20 + 5-fold design (normal n=1). Mandatory C04 redesign session first: defensible options include fewer folds, repeated stratified splits with a declared seed budget, or a versioned scope change (e.g. two nights per participant, severity regrouping — each with its own leakage/medical justification, never silent merging). CV job counts in T37–T39, the T40 freeze, and §1 estimates update to whatever C04 documents.
- T23 scale note: development matrices are ~16 nights (post-C04), not a MESA-scale cohort. Pairing tests (S08) are unchanged and matter more at this n.
- T31/E04: batch-fit pilot is also a RAM pilot for float64 `.npy` windows (6 × ~6M float64 ≈ 275 MB per night in memory) — stream, don't load nights whole. T33/T39 inherit the measured policy.

New STOP-AND-TEST additions from §7 (append to §4):

- T05 STOP T10/T12 until the evidence doc records the sampling rate, channel identities (or unknown), AHI definition/denominator, and all four §7 anomalies with sources.
- T09 STOP T11–T14 until the 16-channel anomaly has a disposition (quarantine, remap, or documented exclusion) covered by a regression test.
- T10 STOP T12/T17 until comma-decimal parsing, boundary inclusivity, and missing-label exclusion tests pass on the real `patients.csv` header/first-rows (read-only; no signal inspection beyond counts).
- T16 STOP T15/T23 cache work until the storage ledger shows fit within the T02 budget.
- T18 STOP T23 and everything downstream until the C04 redesign is documented and its split manifests pass disjointness + support tests.
