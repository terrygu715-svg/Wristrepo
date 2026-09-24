# C04 Cohort Redesign

- Status: Done (design decision; T18 remains blocked until manifests are built
  and tested)
- Decision date: 24 September 2026
- Source artifact: `outputs/label_table.json`

## Measured cohort

The one-night policy selects 20 labelled participants. Class support is:

| Class | Participants |
|---|---:|
| normal | 1 |
| mild | 2 |
| moderate | 7 |
| severe | 10 |

The other 20 participants are excluded because AHI is absent; all 40 missing
source rows remain in the label audit. Participant IDs, not nights, are the
unit of every future split.

## Decision

Replace the unsupported 80/20 split plus five-fold CV with **20 participant-
level leave-one-participant-out outer folds**. Each fold has one held-out
participant and 19 development participants. This is the only selected outer
scheme that preserves every participant for evaluation without pretending that
the single normal participant supports a stratified test split.

- No participant appears in both train/development and held-out data.
- Hyperparameters and preprocessing policy must be fixed a priori; no inner CV
  is authorized by this redesign.
- Per-class metrics are reported only when the aggregate held-out predictions
  contain that class; normal-class sensitivity has one observation and must be
  labelled descriptive.
- The 20 inspection recordings from T08 remain development-only and cannot be
  used as held-out evidence.
- No split manifest is created by C04. T18 must generate versioned manifests,
  prove disjointness, and record the exact fold membership before training.

This redesign changes downstream CV planning from 5 folds to 20 outer folds;
job counts and estimates remain provisional until T18 freezes the manifests.
