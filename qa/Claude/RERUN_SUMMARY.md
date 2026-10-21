# QA re-run: 2026-10-21, Claude (Anthropic) (CLAUDE)

Collected 2026-10-21 19:05:34 EDT by `qa/collect_rerun.py`.

**Result check:** REPRODUCED EXACTLY: every output file is byte-for-byte identical to the published results.

## Runs

| Run folder (logs/) | Type | Started | Last entry | Outcome |
|---|---|---|---|---|
| `run_2026-10-21_145457_quick` | quick trial | 2026-10-21 14:54:57 | 2026-10-21 14:57:25 | finished |
| `run_2026-10-21_145729` | full replication | 2026-10-21 14:57:29 | 2026-10-21 16:42:20 | did not finish (interrupted) |
| `run_2026-10-21_165745` | full replication, stages 3 to 3 | 2026-10-21 16:57:45 | 2026-10-21 18:00:45 | finished |
| `run_2026-10-21_180449` | full replication, stages 4 to 8 | 2026-10-21 18:04:52 | 2026-10-21 19:04:22 | finished |

## Stage run times (full replication runs)

| Run folder | Stage | Time |
|---|---|---|
| `run_2026-10-21_145729` | 1 | 1m 17s |
| `run_2026-10-21_145729` | 2 | 1h 05m 15s |
| `run_2026-10-21_165745` | 3 | 1h 02m 59s |
| `run_2026-10-21_180449` | 4 | 58m 23s |
| `run_2026-10-21_180449` | 5 | 0m 01s |
| `run_2026-10-21_180449` | 6 | 0m 04s |
| `run_2026-10-21_180449` | 7 | 1m 00s |
| `run_2026-10-21_180449` | 8 | 0m 03s |

## Computer and software (latest run)

```
Run started:        2026-10-21 18:04:49 EDT (UTC-0400)
Run type:           full replication, stages 4 to 8
Command:            python start-here/run_all.py --from 4
Project folder:     /tmp/claude-0/-home-claude/42cb9023-b3be-56b3-ab9a-06a6ce4302a7/scratchpad/repo
Project version:    33c6c47068df10f5f7cb56c8bf3c00cdd210a50d
Computer name:      vm
Operating system:   Linux-6.18.44-fc-v139-x86_64-with-glibc2.39
Processor:          x86_64 x86_64
Processor cores:    2
Memory:             7.8 GB
Python:             3.13.16 (/tmp/claude-0/-home-claude/42cb9023-b3be-56b3-ab9a-06a6ce4302a7/scratchpad/repo/.venv/bin/python)
  duckdb            1.5.6
  pyarrow           26.0.0
  numpy             2.5.4
  numba             0.68.0
  pyyaml            6.0.3
  scipy             1.18.1
  pandas            3.0.6
  matplotlib        3.11.2
  pytest            9.1.1
```

## Contents

- `logs/`: the date-stamped run folders from `start-here/logs/` (environment, run log, one log per command)
- `results/`: the re-run's output files, in the same folders as in the project
- `verification/verify_check.txt`: the result check
- `verification/file_inventory.csv`: every file with its fingerprint and whether it matches the published file
- `review/`: the completed checklist, the signed sign-off form, and any notes or screenshots
