# Kaggle Access Status (T04, Kaggle rescoping per §7)

- Status: Done (local source; no external review exists for this path)
- Ticket: T04 — Verify Kaggle provenance + record local inventory (60 min, Access, Ready)
- E01 Access clears on this note + the verified manifest below. No credentials
  exist for this path; the T07 secret-scan guard stands as a standing check.

## Provenance

- Source: https://www.kaggle.com/datasets/yfrite/polysom ("Polysomnographic
  sleep data", publisher yfrite, updated 2024-06-12 per dataset mirror —
  matches local file dates). Local copy `Kaggledata/` (git-ignored):
  `patients.csv` (80 rows) + `polysomnographics/` (80 `.npy`, 40 users ×
  nights 1–2).
- UNVERIFIED: license/redistribution terms (Kaggle pages require login to
  confirm; not confirmed 17 Sep 2026). Until confirmed, treat the data as
  all-rights-reserved local input — no redistribution, no upload of derived
  artifacts containing raw signal.

## Inventory (measured, not claimed)

- Manifest: `outputs/kaggle_manifest.json` (generated, git-ignored) —
  80 files, 23,613,965,440 bytes (~22.0 GiB), per-file SHA-256 + header census.
- Verification 17 Sep 2026: `ingest --verify` → OK (0 failures).
- Layout: 78 files `(6, ~5.19–6.94M)` float64; 2 sixteen-channel anomalies:
  `User-8-Night-1.npy (16, 5797800)`, `User-14-Night-2.npy (16, 5358600)`.
- `patients.csv`: present, 3692 bytes,
  sha256 `2e344d3…a3d0339` (full hash in manifest). Comma decimals; AHI
  present for 20/40 users (both nights or neither).
- Historical disk verification: 228 Gi total, 17 Gi avail. The latest T16
  ledger measured 8.2 GiB free. The dump fills the T02 budget; E04 stays open
  and T15/T23 streaming remains blocked pending remediation.

## Handoff

- Deliverable: this note (no credentials involved or stored).
- Acceptance evidence: manifest build + verify OK above; byte counts; anomaly list.
- Unresolved: license terms (blocks any sharing, not any local work).
- Active time: ~60 min planning allowance.
- Newly ready: E01 clears for local work; T08 Ready (sample locally, reserve IDs).
