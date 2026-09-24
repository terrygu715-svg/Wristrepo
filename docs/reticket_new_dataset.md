# Rerunning the pipeline on a different dataset

> Branch: `reticket/simplified-flight`. Companion to `docs/reticket_tickets.md` (tickets 0–7).
> Theory: a new dataset = a new data folder + a fresh pass through the data tickets,
> reusing the frozen model code. No changes to tickets 3/5 code paths.

## Principle

Model code (tickets 3, 5) is dataset-agnostic: it consumes a frozen channel manifest,
a versioned split, and normalized window batches. So a second dataset only redoes the
data-side tickets and the comparison, then trains 4 new checkpoints with the same code.

## Steps

1. **New folder.** Add a dataset folder next to the existing one (e.g.
   `Kaggledata/` → `Newdata/`), with the same layout contract: signal files +
   a `patients.csv`-equivalent (one row per subject/night with the AHI or label field).
   Record source URL + license the same way ticket 0 requires. Do not mix folders —
   one dataset per folder, never shared files.
2. **Redo ticket 1 (audit + freeze) for the new folder.** Per-file census, label parse
   (map the new label field to the same 4 classes at 5/15/30 provisional unless the new
   source justifies a recorded deviation), channel freeze (Full vs partial = HR + SpO₂
   only), one-night rule, and the join-and-drop-nulls deletion for nights missing
   required actigraphy. Output: a new label table + channel manifest versioned per
   dataset (e.g. `*_v2` hashes — never overwrite the original manifests).
3. **Redo ticket 2 (split) for the new folder.** Fresh participant-disjoint
   train/eval/test manifests from the new label table. Same rules (support report,
   no re-rolls after freeze). The new split is independent — never reuse ticket-02
   hashes across datasets.
4. **Reuse ticket 3/5 code unchanged.** Point the frozen XGB + CNN pipelines at the new
   manifests. Only the feature→channel provenance table is re-checked (new channel
   names must map to the same feature slots; any unmappable channel is a written
   deviation, never a silent remap). Preprocessing (ticket-5g) refits normalization on
   the NEW train IDs — never carry scalers across datasets. Resumability (ticket-5h)
   works as-is.
5. **Train 4 new checkpoints** (partial/full × XGB/CNN) on the new train split per
   ticket 6. Checkpoint names carry the dataset tag (e.g. `newdata-full-xgb`).
6. **Redo ticket 7 (compare) for the new dataset.** Peak accuracy + F + confusion matrix
   per new checkpoint on the new split. Report side-by-side with the original dataset
   only as separate tables — never pool splits or checkpoints across datasets.

## What is NOT redone

- Tickets 0 (environment), 3 (XGB setup), 5 (XGB+CNN setup): reused as-is.
- Ticket 4's QA checklist is re-executed against the new manifests (same boxes, new hashes).

## Done when

- [ ] New folder layout + source/license recorded.
- [ ] New label table + channel manifest versioned (no overwrite of originals).
- [ ] New split manifests frozen with support report.
- [ ] Provenance re-check signed (or deviation written).
- [ ] 4 new dataset-tagged checkpoints trained + ticket-7 comparison recorded.
