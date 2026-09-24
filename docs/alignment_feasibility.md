# T11 Alignment Feasibility

- Status: Done (omit-motion path; E03 cleared for this decision)
- Decision date: 24 September 2026
- Source: Kaggle `yfrite/polysom`, dataset page/API checked for T05, plus the
  local `Kaggledata/` inventory and `patients.csv`.

## Evidence

- The publisher documents six EEG rows: `Fp1-M2`, `C3-M2`, `O1-M2`, `Fp2-M1`,
  `C4-M1`, and `O2-M1`.
- The publisher does not document a motion/actigraphy channel, and the local
  six-channel files have no source channel map beyond positional rows.
- `patients.csv` contains per-night pulse and blood-pressure attributes, not
  HR or SpO2 time series. No motion, HR, SpO2, synchronization markers, or
  overlap stream is present in this source.
- The two 16-channel files are quarantined by T09. Their extra rows are
  unmapped and cannot be used as a motion proxy.

## Decision

Use `assess(6, False)` and omit motion from both Full and Reduced inputs. Do
not infer a motion channel from positional EEG rows or from the quarantined
16-channel files. The T11 helper returns `decision=omit` with reasons covering
the missing channel map and missing motion representation.

This clears the T11/E03 alignment decision only. T12 must still freeze the
verified channel contract and document the resulting feature scope; E02 AHI
semantics, E04 capacity, and E05 cohort support remain independent blockers.
