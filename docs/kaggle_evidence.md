# Kaggle Evidence Audit (T05, Kaggle rescoping per §7)

- Status: Done (measured half) / Blocked (source-doc half)
- Ticket: T05 — Audit Kaggle documentation + record measured evidence (90 min)
- Deliverable: this file (successor to the `.docx` `docs/mesa_evidence.md` path;
  kept under a Kaggle name so the handoff trail is explicit).

## Sourced claims (measured 17 Sep 2026, conda Python)

| # | Claim | Evidence |
|---|-------|----------|
| M01 | 80 nights, 40 users × 2, float64 `.npy` | `outputs/kaggle_manifest.json`, verify OK |
| M02 | 78 files 6-ch (~5.19–6.94M samples); 2 files 16-ch (`User-8-Night-1`, `User-14-Night-2`) | header census in manifest |
| M09 | Dataset page https://www.kaggle.com/datasets/yfrite/polysom, publisher yfrite, updated 2024-06-12; described as "6 EEG channels for apnoea/hypopnoea prediction" | dataset mirror (selectdataset), file dates |
| M03 | `patients.csv` columns: user_id, night_id, age, sex, height, weight, pulse, BPsys/BPdia, ODI, NAp, NHyp, AI, HI, AHI | file header |
| M04 | Decimals are commas (`17,7`); naive float() parse fails | probed 17 Sep 2026 |
| M05 | AHI present for 20/40 users, both nights or neither | parsed with comma handling |
| M06 | Labelled-night classes at 5/15/30: severe 20, moderate 15, mild 4, normal 1 | same parse |
| M07 | One probed night spans −3541…+3395 (artifact vs unit TBD) | `User-1-Night-1.npy` mmap probe |
| M08 | File durations ≈ 7.2–9.6 h at assumed 200 Hz | sample counts ÷ 200 |

## Explicit unknowns (each blocks its gate until sourced)

| # | Unknown | Blocks |
|---|---------|--------|
| U01 | License/redistribution terms (page + publisher confirmed M09; license needs logged-in check) | sharing only (see T04) |
| U02 | Sampling rate (200 Hz is an assumption from durations) | T09, T12, T15 |
| U03 | Per-channel identities/order (described as 6 EEG; map, rate, and the extra 10 channels in 16-ch files still unknown) | T11 (E03), T12 |
| U04 | AHI definition: scoring rule, subtype coverage, sleep-time denominator | T10 (E02), T12 |
| U05 | Meaning of AI/HI/ODI/NAp/NHyp columns; BP/pulse provenance | T10, T20 |
| U06 | Why 20 users lack AHI (withheld vs unmeasured) | T17 exclusion rationale |
| U07 | Origin of extreme values (M07): artifact, unit, or sensor saturation | T09, T14 |

## Handoff

- Acceptance evidence: M01–M08 table above; U01–U07 each named with owner
  (data reviewer) and blocking ticket.
- Unresolved: U01 (license half) + U02–U07; source-doc half of T05 stays
  open until the license is confirmed. Measured half is Done and unblocks
  T09–T11 fieldwork.
- Active time: ~90 min planning allowance.
- Newly ready: T09 fieldwork (header/value audit) can proceed on measured data.
