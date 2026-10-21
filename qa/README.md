# QA: Independent Review and Sign-Off

This folder is for a **human reviewer** who independently checks the study and signs off on it. The review has three parts:

1. **Re-run** the whole study on your own computer, with full date-stamped logs.
2. **Review the code** to confirm that every key assumption is implemented as the study describes it.
3. **Check the results**: confirm that every number reported in the README files, manuscript, one-page summary and abstract matches the re-run's outputs.

You record your work in a checklist workbook, store the evidence in a dated folder, and sign a short attestation form. Anyone can then see **who** validated the study, **what** they checked, **when** they checked it, and **what tools** they used.

You do not need programming experience to complete the re-run and the results checks. The code review (checklist section C) asks you to read short SQL and Python files and compare them with the manuscript. Each checklist row names the exact file to open and what to look for.

## What is in this folder

| File or folder | What it is | What you do with it |
|---|---|---|
| `README.md` | These instructions | Read first |
| `QA_Checklist.xlsx` | The checklist workbook: every task, each assumption to check, a run log, an issues log, and a summary | Copy it into your re-run folder and fill in the yellow cells |
| `QA_Signoff_Template.docx` | The sign-off form (Microsoft Word) | Copy it into your re-run folder, complete it, and sign it |
| `collect_rerun.py` | Copies your re-run's logs and results into a dated folder | Run it once, after the re-run (step 5) |
| `reruns/` | The holding space: one folder per re-run, named `<date>_<initials>` | Your evidence goes here |
| `scripts/` | The scripts that build the checklist and the sign-off form | Nothing (for maintainers) |

## Time required

| Step | Hands-on time | Waiting time |
|---|---|---|
| 1-4. Set up and start the re-run | 45 minutes | 3½ to 4 hours (computer runs on its own) |
| 5. Collect the re-run | 5 minutes | |
| 6. Code review (section C) | 3 to 5 hours | |
| 7. Results and other checks (sections D-G) | 2 to 3 hours | |
| 8-9. Issues, sign-off and submission | 30 minutes | |

You can do the code review while the re-run is running.

## Before you start

- You need your own computer (Windows, macOS or Linux) with at least 8 GB of memory and 3 GB of free disk space.
- You need **Microsoft Excel** (or LibreOffice Calc) and **Microsoft Word** (or LibreOffice Writer).
- For reading code, any text editor works. [Visual Studio Code](https://code.visualstudio.com/) (free) shows SQL and Python with colors and line numbers. You can also read every file on the GitHub website.
- **Commands** in this guide are written for macOS and Linux. **On Windows**, replace `.venv/bin/python` with `.venv\Scripts\python`, and use backslashes (`\`) in file paths.

---

## Step 1. Get a fresh copy of the project

Do the review in a **new, empty folder on your own computer**, not in a copy that someone else has already run. This is what makes the re-run independent.

Follow [`start-here/README.md`](../start-here/README.md), **steps 1 to 5** (check your computer, install Python, download the project, open a terminal in the project folder, and set up the project). All later commands are typed in that terminal, in the project folder.

## Step 2. Start your checklist

1. Open `qa/QA_Checklist.xlsx` in Excel.
2. Read the **How to use** sheet.
3. Fill in the **Reviewer** sheet: your name, initials, role, organization, any relationship to the study, and the review start date. (You will copy your computer and software details from `environment.txt` after step 3.)
4. Save the workbook somewhere outside the project folder for now (for example your Desktop) as `QA_Checklist_<date>_<initials>.xlsx`, for example `QA_Checklist_2026-10-21_JD.xlsx`. You will move it into your re-run folder in step 5.

Work through checklist **section A** (setup and independence) now.

## Step 3. Re-run the study with date-stamped logs

This is checklist **section B**.

1. Run the quick trial (about 5 minutes):

   ```bash
   .venv/bin/python start-here/run_all.py --quick
   ```

   It should end with `Your setup works.`

2. Start the full re-run (3½ to 4 hours):

   ```bash
   .venv/bin/python start-here/run_all.py
   ```

   Keep the computer awake and plugged in. If the run is interrupted, continue it with `--from` and the stage number shown in the terminal (for example `.venv/bin/python start-here/run_all.py --from 3`). The checklist accepts a resumed run as long as every stage finishes once.

**The logs are created automatically.** Every run writes a date-stamped folder `start-here/logs/run_<date>_<time>/` containing:

- `environment.txt`: the date and time, your computer's name, operating system, processor cores and memory, the Python and package versions, and the project version (Git commit). This is the record of **what tools** were used.
- `run_log.txt`: every stage and command with the date and time it started and how long it took. This is the record of **when** the work was done.
- one `.log` file per command (for example `stage2_02_part_d_ipm_estimation_config.log`), with the command's complete output and every line date-stamped.

Do not edit these files.

3. When the run finishes, the terminal shows a **RESULT CHECK**. Note the conclusion: `REPRODUCED EXACTLY`, `REPRODUCED` or `NOT REPRODUCED` (see [`start-here/README.md`](../start-here/README.md), step 8, for what each means).

4. Fill in the **Run log** sheet: one row per run folder (start, finish, outcome, result check), and the time of each stage from `run_log.txt` ("Stage N finished in ..."). The sheet shows the published stage times for comparison.

## Step 4. Record your computer and software

Open `start-here/logs/run_<date>_<time>/environment.txt` (the full run's folder) and copy the operating system, processor cores, memory, Python version and package versions into the **Reviewer** sheet. Add the tools you are using for the review (Excel version, text editor, terminal).

## Step 5. Collect the re-run into the holding space

Type, with your own name and initials:

```bash
.venv/bin/python qa/collect_rerun.py --reviewer "Jane Doe" --initials JD
```

This creates `qa/reruns/<today's date>_<initials>/`, for example `qa/reruns/2026-10-21_JD/`, containing:

- `RERUN_SUMMARY.md`: a one-page summary (who, when, computer and software, run times, result check)
- `logs/`: copies of every date-stamped run folder
- `results/`: the re-run's output files, in the same folders as in the project
- `verification/verify_check.txt` and `verification/file_inventory.csv`: the result check, and every file's fingerprint compared with the published file
- `review/`: an empty folder for your checklist, sign-off form and notes

Now **move your checklist workbook** into the `review/` folder. Everything you write from here on goes in `review/`. See [`reruns/README.md`](reruns/README.md) for the full folder layout.

Complete the remaining rows of checklist section B (they ask you to look at these files).

## Step 6. Review the code (checklist section C)

Section C lists **each key assumption of the study as its own row**. These include:

- assumptions common to every program: perfect review, one audit per year, errors independent of selection, Neyman allocation, netting, calibration, random numbers, scale factors, interval formulas, regression, the bootstrap simulation and scoring;
- assumptions specific to each program: population, errors, calibration targets, benefit rules and audit design for Part C, Part D (including the pre-IRA reference), PERM, EIPM and CERT.

For each row:

1. Open the file named in **Where to look**. Each SQL and Python file begins with a comment block that explains what it does and every probability or formula it uses; start there.
2. Find the value or formula described in **How to check**, and compare it with **Expected result** (which also names the manuscript section that describes it).
3. Set **Status** to Pass, Fail or N/A. Enter the date, your initials, and in **Evidence** the file and line number you checked (for example `shared/ipsim/simulation.py, lines 120-140`).
4. If it does not match, set **Status** to Fail, add the problem to the **Issues log** sheet, and put its issue ID (for example I-02) in the **Issue ID** column.

One known discrepancy is already listed as an example on the Issues log (row C21: a description in the Part C configuration that does not match the audit size actually used). Confirm or reject it as part of your review.

## Step 7. Check the results and complete sections D to G

- **Section D, results represented correctly.** Compare every reported number with the re-run's outputs in your `results/` folder: the README tables with `shared/results/report/by_scenario.csv`, the manuscript tables with `manuscripts/generated/tables.md`, and the text, figures, one-page summary and abstract with those tables. Open CSV files in Excel. One row asks you to recompute a median and a coverage count by hand from `by_audit_year.csv`.
- **Section E, tests and independent checks.** Confirm the automated tests passed. Re-run one program with a single processor thread to confirm that the results do not depend on the computer's thread count, and spot-check one interval by hand.
- **Section F, data security and disclosure.** Confirm the study uses only synthetic data and public sources, and that disclosures are complete.
- **Section G, documentation.** Record anything in the instructions that was unclear or did not work on your computer.

For anything that fails, add a row to the **Issues log** with a severity:

| Severity | Meaning |
|---|---|
| Critical | A reported result is wrong or cannot be reproduced |
| Major | An assumption or method differs from its description in a way that could change a result |
| Minor | A documentation or labeling error with no effect on results |
| Note | A suggestion |

## Step 8. Close out and sign

1. Complete checklist **section H**. The **Summary** sheet shows how many tasks are done and, at the bottom, **READY TO SIGN?** It reads "YES" when every task has a status, no Critical or Major issue is open, and every Fail has an issue ID.
2. Copy `qa/QA_Signoff_Template.docx` into your `review/` folder as `QA_Signoff_<date>_<initials>.docx`.
3. Open it in Word and complete every yellow box. Copy the details from `RERUN_SUMMARY.md`, `environment.txt` and the checklist's Summary sheet. Section by section, the form records:
   - **1. Who validated** (name, role, organization, independence)
   - **2. What was reviewed** (project version, re-run folder, and the result of each checklist section)
   - **3. When** (review dates; re-run start and finish times)
   - **4. What tools** (computer, operating system, Python and package versions, review software)
   - **5. Re-run outcome** (the result check and tests)
   - **6. Findings** (issues by severity, and a summary of any open items)
   - **7. Attestation** (your decision, and your signature)
4. Choose a decision: **Approved**, **Approved with conditions**, or **Not approved**.
5. Sign it, by hand on a printed copy that you then scan, or electronically, and save the signed copy as `QA_Signoff_<date>_<initials>.pdf` in `review/`.

## Step 9. Submit the review

Your re-run folder, `qa/reruns/<date>_<initials>/`, now holds all the evidence: logs, results, verification, the completed checklist, and the signed form. Submit it in one of two ways:

- **GitHub:** commit the folder on a new branch and open a pull request titled `QA review <date> <initials>`.
- **Email:** compress the folder into a ZIP file (Windows: right-click → **Send to → Compressed (zipped) folder**; macOS: right-click → **Compress**) and send it to the study author.

Record the submission date in checklist row H5.

---

## Questions

**The result check says `REPRODUCED`, not `REPRODUCED EXACTLY`. Is that a failure?** No, if the explanation holds: every number in the results tables matches, but some stored files differ in their last digits, usually because of a different operating system or library version. Mark row B9 as Pass and explain it in Notes. `NOT REPRODUCED` is a Critical issue.

**Can I review someone else's re-run instead of doing my own?** No. The attestation states that you personally re-ran the study. You can, however, compare your re-run folder with an earlier one in `reruns/`.

**I found an error after signing.** Add it to the Issues log, update the form, and sign and date a new copy. Keep the earlier copy and add `_superseded` to its file name.

**Where do I check what a column in an output file means?** In [`shared/data_dictionary.md`](../shared/data_dictionary.md).

**How were the checklist and form made?** By `qa/scripts/build_checklist.py` and `qa/scripts/build_signoff.js`. To change a checklist row, edit the script and rebuild the workbook, rather than editing the workbook directly, so the checklist stays traceable.
