# Gap Review and Corrections

Review date: 17 September 2026. Baseline before review: 85 passing tests.
After the original corrections: 102 passing tests. Latest seam correction pass:
24 September 2026, 116 passing tests. This review is about correctness and test
confidence, not a claim that the research pipeline is complete.

## Issues Fixed

- **T08 integrity was incomplete.** The sample builder calculated new hashes
  but did not compare them with the canonical T07 manifest, and it did not
  prove the sample IDs joined to `patients.csv`. It now rejects manifest
  size/hash mismatches, path traversal, duplicate selections, invalid names,
  and missing label rows. Real output: `outputs/sample_manifest.json` has
  `source_manifest_verified: true`.
- **T09 did not produce all stated statistics.** The audit claimed standard
  deviation but emitted none. It now emits population standard deviation,
  extreme-value counts, bytes, and SHA-256, while retaining mmap/chunked
  reads. Non-6-channel files remain quarantined, not silently treated as the
  six-channel contract.
- **T10 silently overwrote duplicate rows.** Label loading now rejects
  duplicate user/night rows, blank IDs, non-finite numbers, and invalid
  boundaries. One-night exclusions are participant-level (20 excluded
  participants) while all 40 missing source rows remain available in
  `excluded_source_rows` for audit.
- **Full/Reduced comparison did not verify pairing identity.** T25 now rejects
  participant or true-label mismatches for a shared recording ID and rejects
  extra strata participants. A matching recording ID alone is insufficient.
- **T26 allowed unusable object arrays and lacked nested-parent handling.**
  Object arrays are rejected before persistence, arrays are loaded with an
  explicit non-pickle context, and missing bundle parents are created.
- **T34 could strand an interrupted job.** The ledger now records the owner
  PID, recovers dead-owner lock files, creates missing parents, rejects
  non-JSON artifact-hash payloads, and requeues jobs left `running` on resume.
- **CLI import side effect.** `python -m sleep_apnea.data.ingest` no longer
  preloads its own module and emits a runpy warning.
- **Versioned artifact validators were incomplete.** Contract validators now
  reject non-object and unversioned documents, enforce required metric/config
  fields, reject non-finite or boolean numeric values, and reconcile metric
  sample counts with the confusion matrix. T24/T25 producers emit versioned
  outputs that validate against their own contracts.
- **S05 evidence could be opaque.** A motion proxy now requires a non-empty
  source plus quantified overlap coverage and maximum offset; malformed or
  unquantified evidence takes the documented omission path. Boolean channel
  indices and channel-count values are rejected.

## Remaining Critical Gaps

- **T05/E02:** AHI scoring rule, sleep-time denominator, subtype coverage, and
  exact category boundary evidence are still not sourced. The current 5/15/30
  values are explicit provisional defaults, not a cleared scientific gate.
- **T09/T12:** Both 16-channel files are fully audited and quarantined, but
  their extra channels are not identified. Sampling rate and per-channel
  identities remain open.
 - **T11/T14:** T11 now has a documented omit-motion decision and E03 is cleared
   for alignment. No synchronization map or artifact/coverage mask implementation
   exists; S05 has decision/audit tests, while T14 quality-mask implementation
   remains pending.
- **C04/E05/T18:** The one-night labelled cohort has 20 participants with
  class counts normal 1, mild 2, moderate 7, severe 10. C04 now documents
  participant-level leave-one-participant-out outer folds; no split manifest
  may be created until T18 implements and tests that redesign.
- **S03:** The test suite has a synthetic cross-split tripwire, but no real
  participant-disjoint split implementation or inspection-ID enforcement.
- **S06/T15:** No window cache exists; cache boundary, provenance-hash, and
  no-global-normalization tests are still pending.
- **S08/T21/T23:** Prediction comparison now verifies row identity, but no
  feature-matrix builder proves Full is a superset of Reduced. No annotation
  exclusion scan exists.
- **S12/T27/T33:** No training harness exists to prove fit-on-test rejection,
  inner stopping/outer scoring separation, or neural epoch isolation.
- **S13/T31/T32:** No neural loader/model exists; padding/mask invariance and
  measured RAM/backend fit are untested.
- **T02/E04/T16:** The local dump is ~22 GiB; the T16 ledger measured 7.9 GiB
  free on 24 September, below the documented operating budget. No cache or
  training job should start until storage is reclaimed or externalized and a
  bounded streaming storage/RAM budget is measured again.

## Stop Rules

1. Do not close T12 while any E02/E03/E04/E05 item above is unresolved.
2. Do not run T18 or any model training before the C04 split redesign is
   documented and its participant-disjointness tests pass.
3. Do not treat T08/T09 sample outputs as empirical model results.
4. Do not claim S06/S08/S12/S13 coverage from the current 116-test count;
   their owning implementations and seam tests are absent.
