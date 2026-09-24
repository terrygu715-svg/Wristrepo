# T16 Storage Verification Ledger

Measured 24 September 2026 on the local APFS data volume. This ledger is
evidence for the storage portion of E04; it does not authorize cache creation.

| Measurement | Value | Command / source |
|---|---:|---|
| Dataset files | 23,613,965,440 bytes (about 22.0 GiB) | `outputs/kaggle_manifest.json` |
| Dataset directory usage | 22G | `du -sh Kaggledata` |
| Files | 80 `.npy` nights plus `patients.csv` | `outputs/kaggle_manifest.json` |
| Volume capacity | 228 GiB | `df -h .` |
| Free space before any T16 work | 8.2 GiB | `df -h .` |
| T02 reserve at inspection | 4 GiB for OS/browser; 8–10 GiB usable job budget | `environment_report.json` |

## Decision

The source dataset is present and accounted for, but the current 8.2 GiB
free-space measurement is below the documented 16 GiB unified-memory/storage
operating budget and leaves no safe working margin for a cache or temporary
artifacts. No download, cache generation, or signal materialization was run.

T16 remains blocked by E04. Remediation is required before T15/T23: reclaim or
externalize storage, then repeat this ledger with before/after `df` measurements
and a bounded streaming-cache pilot. The 16-channel files remain quarantined;
this ledger does not resolve T09/U02/U03.
