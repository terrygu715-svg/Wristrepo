# T16 Storage Verification Ledger

Measured 24 September 2026 on the local APFS data volume. This ledger is
evidence for the storage portion of E04; it does not authorize cache creation.

| Measurement | Value | Command / source |
|---|---:|---|
| Original dataset files | 23,613,965,440 bytes (about 22.0 GiB) | `outputs/kaggle_manifest.json` provenance |
| Reduced working directory usage | 5.4G | `du -sh Kaggledata` after trim |
| Local working files | 20 `.npy` nights plus `patients.csv` | `docs/working_set.md` |
| Volume capacity | 228 GiB | `df -h .` |
| Free space before trim | 7.9 GiB | `df -h .`, 24 Sep 2026 |
| Free space after trim | 24 GiB | `df -h .`, 24 Sep 2026 |
| T02 reserve at inspection | 4 GiB for OS/browser; 8–10 GiB usable job budget | `environment_report.json` |
| Streaming pilot | 20 files, 1 MiB chunks, 716,916,000 samples, 22.29 s wall time | read-only mmap/chunked pilot, 24 Sep 2026 |
| Pilot peak RSS | 337,117,184 bytes (~322 MiB) | `/usr/bin/time -l` |
| Pilot cache/output writes | None | pilot result |

## Decision

The local working set now fits the documented 16 GiB operating budget: 24 GiB is
free after removing 60 unselected recordings. No cache generation or signal
materialization was run. The original 80-file manifest remains provenance and
must not be used as a claim that all source files remain local.

The storage portion of T16 is cleared: the bounded read-only pilot stayed within
the storage/RAM budget, completed across all 20 retained files, and wrote no
cache or derived signal artifacts. E04 capacity is cleared for this measured
CPU streaming policy; neural/backend-specific work still requires its own pilot.
The 16-channel file remains quarantined; this ledger does not resolve T09/U02/U03.
