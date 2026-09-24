# Reduced Local Working Set

Measured 24 September 2026 after storage remediation.

- The original 80-file Kaggle inventory remains recorded in
  `outputs/kaggle_manifest.json` as provenance, but the local signal directory
  is intentionally reduced.
- Retained files: the 20 `User-<labelled-user>-Night-1.npy` recordings selected
  by `outputs/label_table.json`, including the quarantined 16-channel anomaly
  for `User-8-Night-1.npy`.
- Removed from the local working copy: the other 60 `.npy` recordings. They are
  not treated as missing labels or silently substituted; the original manifest
  records their prior hashes and sizes.
- `patients.csv` is retained unchanged.
- Retained signal bytes: `5,735,330,560` (`5.34 GiB`).

This is a storage reduction, not a new scientific cohort definition. The
one-night labelled cohort and T17/C04 policy remain unchanged. T07's original
80-file integrity verification is historical provenance; any local-file check
must target this reduced working-set policy until the full source is restored.
