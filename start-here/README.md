# Start Here: Replicating the Study

This guide explains how to reproduce every result in this study on your own computer, from an empty machine to the final tables. No programming experience is needed. You will install two free programs, download the project, and type a handful of commands that are given below exactly as you should type them.

Replication takes about **20 to 30 minutes** of hands-on setup and about **3½ to 4 hours** of unattended computing (measured on a computer with 2 processor cores and 8 GB of memory; a computer with more cores will finish sooner). At the end, a check script compares your results with the published results and reports whether they match.

| Step | What you do | Time |
|---|---|---|
| [1. Check your computer](#1-check-your-computer) | Confirm memory, disk space, and operating system | 2 minutes |
| [2. Install the software](#2-install-the-software) | Install Python (required), plus optional tools | 10 minutes |
| [3. Download the project](#3-download-the-project) | Download and unzip the project folder | 2 minutes |
| [4. Open a terminal in the project folder](#4-open-a-terminal-in-the-project-folder) | Open the window where you type commands | 2 minutes |
| [5. Set up the project](#5-set-up-the-project) | Create a private Python environment and install the packages | 5 minutes |
| [6. Run a trial](#6-run-a-trial) | Confirm that everything works | 5 minutes |
| [7. Run the full replication](#7-run-the-full-replication) | Reproduce every result | 3½ to 4 hours |
| [8. Check and view your results](#8-check-and-view-your-results) | Compare your results with the published results | 5 minutes |

If something goes wrong at any point, see [Troubleshooting](#troubleshooting).

---

## 1. Check your computer

You need:

- **Operating system:** Windows 10 or 11, macOS 12 (Monterey) or later, or a recent Linux distribution.
- **Memory (RAM):** at least 8 GB. Close other large programs (for example, web browsers with many tabs) during the full run.
- **Free disk space:** at least 3 GB.
- **Internet connection:** only for steps 2, 3, and 5 (downloading the software and packages). The replication itself runs offline.
- **Permission to install software.** On a work computer, you may need your IT department's help.

To check memory and disk space:

- **Windows:** Open **Settings → System → About** for memory ("Installed RAM"), and **File Explorer → This PC** for free space on the C: drive.
- **macOS:** Open the **Apple menu → About This Mac** for memory, and **Apple menu → System Settings → General → Storage** for free space.

The full run takes several hours. Set your computer so that it does not go to sleep while plugged in (Windows: **Settings → System → Power**; macOS: **System Settings → Battery** or **Energy Saver**), and keep it plugged in.

---

## 2. Install the software

### 2.1 Python (required)

Python is the free programming language the study is written in. The study requires **Python 3.11, 3.12, or 3.13**. The published results were produced with Python 3.13, which is recommended.

**Windows**

1. Go to <https://www.python.org/downloads/windows/>.
2. Under "Stable Releases," find the newest **Python 3.13** release and click **Download Windows installer (64-bit)**.
3. Open the downloaded file.
4. On the first screen, **check the box "Add python.exe to PATH"** at the bottom. This box is easy to miss and matters.
5. Click **Install Now** and wait for "Setup was successful," then click **Close**.

**macOS**

1. Go to <https://www.python.org/downloads/macos/>.
2. Find the newest **Python 3.13** release and click **Download macOS 64-bit universal2 installer**.
3. Open the downloaded `.pkg` file and click **Continue** through the screens, then **Install**. Enter your Mac password when asked.
4. When the installer finishes, a Finder window opens. Double-click **Install Certificates.command** in that window (this lets Python download packages securely).

**Linux (Ubuntu or Debian)**

Open a terminal and type:

```bash
sudo apt update
sudo apt install python3 python3-venv python3-pip
```

Check that the version shown by `python3 --version` is 3.11 or later.

### 2.2 Git (optional)

Git is a tool for downloading and tracking versions of projects. You do **not** need it: step 3 shows how to download the project as a ZIP file instead. If you prefer Git, install it from <https://git-scm.com/downloads> using the default options.

### 2.3 Pandoc and wkhtmltopdf (optional)

These two programs turn the manuscript's text files into PDF and Word documents. You need them only if you want to rebuild those documents yourself ([step 9](#9-optional-rebuild-the-pdf-and-word-documents)). The results, tables, and checks in steps 6 to 8 do not need them.

- Pandoc: <https://pandoc.org/installing.html>
- wkhtmltopdf: <https://wkhtmltopdf.org/downloads.html>

---

## 3. Download the project

**Option A: Download a ZIP file (no Git needed)**

1. Go to <https://github.com/andrewcistola/improper-payment-estimation-accuracy>.
2. Click the green **Code** button, then **Download ZIP**.
3. Find the downloaded file (usually in your **Downloads** folder) and unzip it:
   - **Windows:** right-click the file, choose **Extract All…**, then **Extract**.
   - **macOS:** double-click the file.
4. You now have a folder named `improper-payment-estimation-accuracy-main`. Move it somewhere easy to find, such as your **Documents** folder. Avoid folders synced by OneDrive, iCloud, or Dropbox, which can slow the run or interfere with its files.

**Option B: Use Git**

```bash
git clone https://github.com/andrewcistola/improper-payment-estimation-accuracy.git
```

In the rest of this guide, **"the project folder"** means this folder: the one that contains `README.md`, `pyproject.toml`, and the `start-here` folder.

---

## 4. Open a terminal in the project folder

A terminal is a window where you type commands and press **Enter** to run them. Every command in this guide is typed in a terminal that is "in" the project folder.

**Windows**

1. Open the project folder in **File Explorer**.
2. Click once in the **address bar** at the top of the window (where the folder path is shown), type `powershell`, and press **Enter**.
3. A blue or black window opens. Its prompt ends with the project folder's path, for example `PS C:\Users\you\Documents\improper-payment-estimation-accuracy-main>`.

**macOS**

1. Open the **Terminal** app (press **Command + Space**, type `Terminal`, and press **Enter**).
2. Type `cd ` (the letters c and d, then a space). Do not press Enter yet.
3. Drag the project folder from Finder into the Terminal window. Its path appears after `cd `.
4. Press **Enter**.

**Linux**

Open a terminal and use `cd` to move to the project folder, for example `cd ~/Documents/improper-payment-estimation-accuracy`.

**Check that you are in the right place.** Type the command below and press Enter. You should see `README.md`, `pyproject.toml`, and `start-here` among the names listed.

- Windows: `dir`
- macOS and Linux: `ls`

---

## 5. Set up the project

This step creates a private Python environment (a folder named `.venv` inside the project folder) and installs the packages the study uses into it. Nothing outside the project folder is changed. The packages and their versions are listed in `pyproject.toml` and `requirements.txt`; DuckDB is pinned to version 1.5.6 because the random draws depend on it.

Type these two commands, one at a time, pressing **Enter** after each. The second command downloads about 200 MB and takes a few minutes; wait until the prompt returns.

**Windows (PowerShell)**

```powershell
py -3.13 -m venv .venv
.venv\Scripts\python -m pip install -e ".[all]"
```

**macOS and Linux**

```bash
python3 -m venv .venv
.venv/bin/python -m pip install -e ".[all]"
```

(On macOS, if you installed Python 3.13 from python.org but `python3` points to an older version, use `python3.13` in place of `python3` in the first command.)

The setup has worked if the last line printed begins with `Successfully installed`. A notice that "a new release of pip is available" is harmless.

**In every command from here on**, the start of the command is the private environment's Python:

- Windows: `.venv\Scripts\python`
- macOS and Linux: `.venv/bin/python`

The commands below are written the macOS and Linux way. **On Windows, replace `.venv/bin/python` with `.venv\Scripts\python`.**

---

## 6. Run a trial

The trial runs every part of the study on a much smaller scale (3 audit years and 100 iterations, instead of 25 audit years and 1,000 iterations). It confirms that the software is installed correctly before you start the long run. It takes about 5 minutes. It builds the synthetic populations exactly as the full run does and writes its trial estimates to `start-here/_quick/`, leaving the published estimates untouched. Before it starts, it saves a copy of the published results to `start-here/_reference/` for the check in step 8.

```bash
.venv/bin/python start-here/run_all.py --quick
```

The terminal shows each step as it runs. The trial has worked if the last line reads:

```
Your setup works. Start the full replication with:  python start-here/run_all.py
```

---

## 7. Run the full replication

```bash
.venv/bin/python start-here/run_all.py
```

This one command runs the whole study, in eight stages. Leave the terminal window open and the computer awake until it finishes. You can use the computer for light tasks in the meantime.

| Stage | What it does | Files it writes | Time |
|---|---|---|---|
| 1 | Builds the five synthetic populations with their fabricated errors (and the Part D population under the pre-IRA benefit), and checks each against the public figures it is calibrated to | `*/errors/output*/` | 1 minute |
| 2 | Draws 25 audit years for each program and estimates improper payments with expansion, ratio, regression, and bootstrap simulation with parametric rates | `*/estimation/results/` | 1 hour 10 minutes |
| 3 | Repeats stage 2 on the same audits with fixed-rate bootstrap simulation (the comparison in the manuscript) | `*/estimation/results_fixed/` | 1 hour 15 minutes |
| 4 | Repeats Part D under the pre-IRA benefit design (the robustness reference) | `part-d-ipm/estimation/results_pre_ira*/`, `part-d-ipm/pre-ira-reference.md` | 1 hour 10 minutes |
| 5 | Joins every estimate to the true value | `shared/results/` (the README tables come from `shared/results/report/by_scenario.csv`) | under 1 minute |
| 6 | Builds the manuscript's tables and figures | `manuscripts/generated/`, `manuscripts/manuscript.md` | under 1 minute |
| 7 | Runs the automated tests of the estimators and payment functions | none | 1 minute |
| 8 | Compares your results with the published results | none | seconds |

Each stage's run time is recorded in `start-here/run_log.txt`.

If the trial has not already done so, the script first copies the published results into `start-here/_reference/`, so that stage 8 can compare them with what your run produces. Your run then overwrites the result files in the project folder with the files it computes.

**If the run is interrupted** (for example, the computer restarted), you do not have to start over. Open a terminal in the project folder again and continue from the stage that was running, for example stage 3:

```bash
.venv/bin/python start-here/run_all.py --from 3
```

To see every command each stage runs, without running anything, type `.venv/bin/python start-here/run_all.py --list`.

---

## 8. Check and view your results

### The check

Stage 8 prints a section headed `RESULT CHECK`, which ends with one of three conclusions:

- **`REPRODUCED EXACTLY`:** every output file is byte-for-byte identical to the published files. Each file's SHA-256 fingerprint, recorded in the `manifest.json` files throughout the project, matches.
- **`REPRODUCED`:** every number in the results tables matches the published results, but some stored files differ in their last digits. This can happen on a different operating system or library version, which may round the final digit of a floating-point number differently. No reported finding changes.
- **`NOT REPRODUCED`:** some numbers differ. See [Troubleshooting](#troubleshooting).

To run the check again at any time:

```bash
.venv/bin/python start-here/verify.py check
```

### Where the findings are

| Finding | File | How to open it |
|---|---|---|
| Gross improper payments by program and method (the tables in the main README) | `shared/results/report/by_scenario.csv` | Excel, Numbers, or Google Sheets. The README uses the rows where `domain` ends in `gross` and the columns `median_estimate`, `median_lower`, `median_upper` (and their `_usd` versions) |
| Every table in the manuscript (Tables 2 to 5 and C1) | `manuscripts/generated/tables.md` | Any text editor, or view it on GitHub |
| Every program, measure, and method in one table | `manuscripts/generated/results_long.csv` | Excel, Numbers, or Google Sheets |
| Figures 1 and 2 | `manuscripts/generated/fig1_width.png`, `fig2_coverage.png` | Any image viewer. The check does not compare the figures, because text in an image is drawn slightly differently by different library builds; the values they show come from `results_long.csv`, which is compared |
| Part D under the pre-IRA benefit | `part-d-ipm/pre-ira-reference.md` | Any text editor |
| Each program's detailed results | `*/estimation/results/*/metrics.json` and `estimates.parquet` | Described in [`shared/data_dictionary.md`](../shared/data_dictionary.md) |

---

## 9. Optional: rebuild the PDF and Word documents

If you installed Pandoc and wkhtmltopdf ([step 2.3](#23-pandoc-and-wkhtmltopdf-optional)), you can rebuild the manuscript, one-page summary, conference abstract, and literature review from the regenerated tables. On macOS and Linux:

```bash
bash manuscripts/scripts/render.sh
```

On Windows, run the commands listed inside `manuscripts/scripts/render.sh` one at a time, or use Windows Subsystem for Linux. The rebuilt PDFs can differ slightly in appearance from the published ones (fonts and page breaks depend on the computer), but their numbers are the same.

---

## Troubleshooting

**"python" or "py" is not recognized (Windows).** Python was installed without the "Add python.exe to PATH" box checked. Run the Python installer again, choose **Modify** (or uninstall and reinstall), and check that box. Then close the terminal and open a new one.

**`python3: command not found` (macOS).** Install Python from python.org as described in step 2.1, then open a new Terminal window.

**`No module named venv` or `ensurepip is not available` (Linux).** Install the venv package: `sudo apt install python3-venv` (or `python3.13-venv` for a specific version).

**Running scripts is disabled on this system (Windows).** This message appears only if you try to "activate" the environment. This guide never activates it: type the full `.venv\Scripts\python` at the start of each command instead.

**The package installation (step 5) fails.** Check the Python version with `.venv/bin/python --version` (Windows: `.venv\Scripts\python --version`). It must be 3.11 to 3.13. Newer versions of Python can be released before every package supports them. If it is outside that range, delete the `.venv` folder, install Python 3.13 (step 2.1), and repeat step 5. Also check that you are connected to the internet and, on a work network, that your organization allows downloads from pypi.org.

**`SSL: CERTIFICATE_VERIFY_FAILED` (macOS).** Run **Install Certificates.command** from the **Applications → Python 3.13** folder, then repeat step 5.

**`Run this from the repository's top folder`.** The terminal is not in the project folder. Repeat step 4 and check with `dir` or `ls`.

**The run stops with `FAILED`.** The lines just above `FAILED` describe the problem, and the last line tells you how to continue once it is fixed. The most common causes are:

- *Out of memory* (`Out of Memory Error`, `MemoryError`, or the computer becoming very slow): close other programs and continue with `--from` the stage that failed.
- *Out of disk space* (`No space left on device`): free at least 3 GB and continue.

**Stage 8 reports `NOT REPRODUCED`.** First make sure every stage ran to completion (`start-here/run_log.txt` should end with "All stages finished"). If it did, check that DuckDB is version 1.5.6: `.venv/bin/python -c "import duckdb; print(duckdb.__version__)"`. The random draws depend on DuckDB's hash function, so a different version produces different (equally valid) synthetic data, and therefore different numbers. If the versions are correct and the results still differ, please open an issue at <https://github.com/andrewcistola/improper-payment-estimation-accuracy/issues> and attach `start-here/run_log.txt` and the printed `RESULT CHECK`.

**The computer went to sleep, or the terminal was closed.** Open a terminal in the project folder (step 4) and continue with `--from` the stage that was running (shown in `start-here/run_log.txt`).

---

## How the replication works

Every number in the study comes from synthetic data. Each population is built from stated probability distributions, and every random draw is a fixed function of a seed, so the same software produces the same data and the same results on every run. No real or non-public data are used, and nothing needs to be downloaded besides the project and its packages. The main [README](../README.md) describes the study and its design, and each program's folder (`part-c-ipm`, `part-d-ipm`, `perm-cert`, `eipm`) has a README describing its population, audit, and methods. The commands that `run_all.py` runs are the same commands listed in the main README's **Run** section and in [`manuscripts/README.md`](../manuscripts/README.md), so an experienced user can also run each step by hand.

This replication package was tested by downloading the project into an empty folder, installing the packages into a new environment exactly as in step 5, and running steps 6 to 8 on Linux with Python 3.13. The run reproduced all 183 published output files byte for byte (`REPRODUCED EXACTLY`) in 3 hours 32 minutes. The scripts use only Python and are written to run unchanged on Windows and macOS.
