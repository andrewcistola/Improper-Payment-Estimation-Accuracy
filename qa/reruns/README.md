# QA re-runs (holding space)

Each independent re-run of the study is stored here in its own folder, named by date and reviewer initials:

```
qa/reruns/
└── 2026-10-21_JD/                      <date>_<reviewer initials>
    ├── RERUN_SUMMARY.md                who, when, computer and software, run times, result check
    ├── logs/                           date-stamped run folders, copied from start-here/logs/
    │   ├── run_2026-10-21_093000_quick/
    │   ├── run_2026-10-21_094500/
    │   │   ├── environment.txt         date, computer, operating system, Python and package versions, project version
    │   │   ├── run_log.txt             every stage and command with its start time and run time
    │   │   └── stage1_01_part_c_ipm_errors_config.log ...   full output of each command, every line date-stamped
    │   └── run_log_all_runs.txt
    ├── results/                        the re-run's outputs, in the same folders as in the project
    │   ├── part-c-ipm/  part-d-ipm/  eipm/  perm/  cert/     errors/output*/ (truth, checks, manifests), estimation/results*/
    │   ├── shared/results/             report/by_scenario.csv (README tables), by_audit_year.*
    │   └── manuscripts/generated/      tables.md, results_long.csv, figures
    ├── verification/
    │   ├── verify_check.txt            output of start-here/verify.py check
    │   └── file_inventory.csv          every file with its SHA-256 fingerprint and whether it matches the published file
    └── review/
        ├── QA_Checklist_2026-10-21_JD.xlsx     the completed checklist
        ├── QA_Signoff_2026-10-21_JD.docx       the completed sign-off form
        ├── QA_Signoff_2026-10-21_JD.pdf        the signed copy
        └── (notes, screenshots)
```

The first completed review (2026-10-21) is kept in [`qa/Claude/`](../Claude/) rather than here, at the author's request. A re-run folder is created by `qa/collect_rerun.py` (see [`qa/README.md`](../README.md), step 5). Do not edit the files in `logs/`, `results/` or `verification/`; they are the evidence of the re-run. Put everything you write yourself in `review/`.

A completed folder is about 15 MB and contains synthetic data only, so it can be committed to the repository. To find a result in a re-run, use the same path as in the project under `results/`: for example, the project's `part-c-ipm/estimation/results/base/metrics.json` is `results/part-c-ipm/estimation/results/base/metrics.json` here.
