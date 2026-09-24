# Ticket 0 — Fresh-PC bootstrap prompt (paste into opencode on the new machine)

> Copy everything below the line into a fresh opencode session on the new PC.
> Docs only — the agent records evidence; it does not train models or download extra data.

---

You are setting up the full development environment for this repo from a bare machine.
Ticket: 0 (Epic A — Foundation) on branch `reticket/simplified-flight`.
Dataset (assumed local after setup): https://www.kaggle.com/datasets/yfrite/polysom (~22 GiB).
Spec parent: T02 (backend stated with evidence, never assumed). No installs skipped silently —
record every step and stop with a clear error if one fails.

Follow these steps in order. Do not skip ahead. Confirm each step before continuing.

## Step 1 — GitHub CLI + terminal + auth

1. Check whether GitHub CLI is installed: run `gh --version`.
2. If missing, install it:
   - Windows: `winget install --id GitHub.cli` (if winget is missing, tell me and stop).
   - macOS: `brew install gh`. Linux: use the system package manager (`apt install gh` or equivalent).
3. Open a terminal and authenticate: run `gh auth login`, choose GitHub.com, HTTPS, and
   complete the browser/device flow. Then run `gh auth status` and show me it passes.
4. Check git: `git --version`. If missing, install it (Windows: `winget install --id Git.Git`)
   and re-verify.

## Step 2 — Clone repo and check out this branch

1. Clone: `git clone https://github.com/terrygu715-svg/Wristrepo.git` (or
   `gh repo clone terrygu715-svg/Wristrepo`).
2. `cd Wristrepo`.
3. `git fetch origin` then `git checkout reticket/simplified-flight` (exact name).
4. Verify: `git branch --show-current` must print `reticket/simplified-flight`,
   and `git status --short` should be clean. Show me both.

## Step 3 — Download the Kaggle dataset (BLOCKING)

Do not continue past this step until the dataset is confirmed in the repository.

1. Check free disk first: you need >30 GiB free for the ~22 GiB dump plus working room.
   Windows: check via `Get-PSDrive C`; macOS/Linux: `df -h .`. Show me the number and stop
   if below 30 GiB free.
2. Install the Kaggle CLI if missing: `pip install kaggle` (or `pipx install kaggle`).
3. Set up Kaggle API credentials: download `kaggle.json` from kaggle.com → Account →
   Create New API Token, place it at `%USERPROFILE%\.kaggle\kaggle.json` (Windows) or
   `~/.kaggle/kaggle.json` (macOS/Linux). Then download:
   `kaggle datasets download -d yfrite/polysom -p Kaggledata --unzip`
   (large download, ~22 GiB — let it finish; retry/resume on failure).
4. Confirm ALL of the following and show me the outputs:
   - `Kaggledata/patients.csv` exists.
   - `Kaggledata/polysomnographics/` contains 80 `.npy` files (40 users × 2 nights).
   - Byte total ≈ 23.6 GB (compare with `outputs/kaggle_manifest.json` if present on this
     branch; if the manifest is absent, record per-file sizes instead).
5. If any file is missing or corrupt, stop here and report exactly which files.
   Tickets 1–7 are blocked until this confirmation passes.

## Step 4 — Python virtualenv + dependencies

1. Check Python: `python --version`. You need Python ≥3.10 (3.12 preferred).
   If missing, install Python 3.12 (Windows: `winget install --id Python.Python.3.12`)
   and re-verify.
2. From the repo root, create and activate a venv:
   - Windows: `python -m venv .venv` then `.venv\Scripts\Activate.ps1`
   - macOS/Linux: `python3 -m venv .venv` then `source .venv/bin/activate`
3. Upgrade pip: `python -m pip install --upgrade pip`.
4. Install project deps: `python -m pip install -e ".[dev]"` (reads `pyproject.toml`:
   numpy, scikit-learn, scipy, pytest).
5. Install the model backends: `python -m pip install xgboost` and GPU torch —
   Windows/Linux with NVIDIA: `python -m pip install torch --index-url https://download.pytorch.org/whl/cu121`
   (CUDA 12.1 build; pick the matching CUDA if yours differs — record which).
   macOS Apple Silicon: `python -m pip install torch` (MPS backend, no CUDA wheel).
   Verify with `python -c "import torch; print(torch.__version__, torch.cuda.is_available())"`.
   CPU-only torch is NOT acceptable here — if no GPU/MPS is present, stop and report.
6. Record versions: `python -c "import numpy, sklearn, scipy, xgboost, torch; ..."`.
   Save the full `python -m pip freeze` output to `ticket0_freeze.txt` (untracked scratch,
   do not commit it).

## Step 5 — Ticket-0 evidence record

1. Run and record: OS + CPU + RAM + GPU (`Get-ComputerInfo` on Windows,
   `sysctl`/`system_profiler` on macOS, `lscpu`/`free -h` on Linux);
   backend statement (CPU verified? CUDA/MPS present? — verify with
   `torch.cuda.is_available()`, never assume); disk free before/after dataset;
   Python + each dep version; pytest smoke: `python -m pytest -q` (record pass/fail —
   a fail here is evidence, fix nothing silently).
2. Write the results into a short `ticket0_evidence.md` (machine specs, backend, disk,
   dep table, dataset confirmation, pytest result, missing-dep list). Show it to me.
3. Stop and hand back: list what is Ready (ticket 1 unblocked?) and anything missing.
   Do not start ticket 1, do not install anything else, do not train anything.
