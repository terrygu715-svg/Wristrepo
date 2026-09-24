# Kaggle Evidence Audit (T05, Kaggle rescoping per §7)

- Status: Done (documentation and measured audit; E02/E03 gates remain open)
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

## Dataset-page claims (Kaggle API, checked 24 Sep 2026)

Source: <https://www.kaggle.com/api/v1/datasets/view/yfrite/polysom> (dataset
page: <https://www.kaggle.com/datasets/yfrite/polysom>), publisher `YFrite`,
dataset version 3, last updated 2024-06-12.

| # | Claim | Evidence / qualification |
|---|---|---|
| P01 | The publisher documents a 200 Hz sampling rate for all channels. | Kaggle API description; this resolves the former rate assumption for the six-channel contract. |
| P02 | The documented six rows are `Fp1-M2`, `C3-M2`, `O1-M2`, `Fp2-M1`, `C4-M1`, and `O2-M1`, in that order. | Kaggle API description; row order is documented, but the two local 16-channel files remain unexplained. |
| P03 | `AI = NAp / TimeOfRecordInHours`, `HI = NHyp / TimeOfRecordInHours`, and `AHI = (NAp + NHyp) / TimeOfRecordInHours`. | Kaggle API attribute information. `TimeOfRecordInHours` is not defined as sleep time, so the E02 denominator remains unresolved. |
| P04 | The page describes ODI as the oxygen desaturation index, and NAp/NHyp as counts of apnoea/hypopnoea events; healthy-patient values may be absent. | Kaggle API attribute information. Event scoring rules and subtype coverage are not supplied. |
| P05 | The listed license is `Database: Open Database, Contents: © Original Authors`. | Kaggle API metadata. The exact redistribution obligations and original-author terms still require a license/legal check; do not infer unrestricted sharing. |

## Reconciled anomalies and remaining unknowns

- **16 channels:** local header census found `User-8-Night-1` and
  `User-14-Night-2` with 16 rows, while the publisher documents six EEG rows.
  The extra rows have no source mapping; rows 6-15 are zero-valued in both
  audited files. T09 disposition is **quarantine and exclude both files from
  the six-channel contract**. No remapping, zero-fill, or channel identity is
  inferred. The inventory records this disposition with bytes, hashes, and
  per-channel statistics.
- **Comma decimals:** the local `patients.csv` uses values such as `17,7`;
  this is a file-format observation and is handled by T10 parsing. The API page
  does not specify the delimiter/decimal convention.
- **50% missing AHI:** local parsing finds AHI for 20 of 40 users (both nights
  or neither). The API says healthy-patient values may be absent but does not
  explain whether missingness means withheld, unmeasured, or healthy; U06 stays
  open.
- **Extreme values:** the local probe spans -3541 to +3395 in one night. The
  API documentation gives no units, scaling, or saturation guidance; U07 stays
  open and no clipping is permitted.

## T10 label audit

The real `Kaggledata/patients.csv` header and first three rows were read
read-only and match the expected 14-column layout, including `user_id`,
`night_id`, and `AHI`. The parser accepts both dot and comma decimals (the
real file contains comma-decimal values such as `17,7`), applies lower-
inclusive provisional boundaries `[5, 15, 30]`, rejects duplicate user/night
rows and invalid numeric/boundary values, and never substitutes night 2 when
selected night 1 is unlabelled.

The generated label table contains 20 selected night-1 participants and 20
participant-level exclusions, with all 40 missing-AHI source rows retained for
audit. XML/event reconstruction is not applicable because this source provides
the summary AHI field but no XML or event annotations. The exact AHI scoring
and denominator remain an E02 unknown, so these labels are operationally
parsed but not yet scientifically cleared.

## Explicit unknowns (each blocks its gate until sourced)

| # | Unknown | Blocks |
|---|---------|--------|
| U01 | Exact redistribution obligations under the page's `Open Database` / original-author license label | sharing only (see T04) |
| U02 | None for the documented six-channel files: page states 200 Hz; whether the 16-channel files use the same rate is not established | T09 disposition, T12 |
| U03 | The six-channel row order is documented, but the extra 10 rows in each 16-channel file remain unidentified | T09/T11 (E03), T12 |
| U04 | AHI event scoring rule, subtype coverage, and whether `TimeOfRecordInHours` is sleep time | T10 (E02), T12 |
| U05 | ODI/NAp/NHyp labels have page-level meanings; their scoring/provenance and BP/pulse provenance remain unspecified | T10, T20 |
| U06 | Why 20 users lack AHI (withheld vs unmeasured) | T17 exclusion rationale |
| U07 | Origin of extreme values (M07): artifact, unit, or sensor saturation | T09, T14 |

## Handoff

- Acceptance evidence: M01–M09 table above; U01–U07 each named with owner
  (data reviewer) and blocking ticket.
- Unresolved: U01 and U03–U07. The source audit is complete, but these
  scientific/legal unknowns continue to block their respective gates. The
  measured half unblocks T09–T11 fieldwork; it does not authorize remapping or
  clinical interpretation.
- Active time: ~90 min planning allowance.
- Newly ready: T09 fieldwork (header/value audit) can proceed on measured data.
