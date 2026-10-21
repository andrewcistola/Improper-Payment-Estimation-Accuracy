// Build qa/QA_Signoff_Template.docx, the reviewer's sign-off form.
// Run from the repository's top folder:  node qa/scripts/build_signoff.js
// (needs the docx package:  npm install docx). Edit this script, not the .docx.
const fs = require("fs");
const path = require("path");
const {
  Document, Packer, Paragraph, TextRun, Table, TableRow, TableCell, WidthType, ShadingType,
  BorderStyle, AlignmentType, HeadingLevel, Footer, PageNumber, TabStopType,
} = require("docx");

const OUT = path.join(__dirname, "..", "QA_Signoff_Template.docx");
const W = 9360; // content width, US Letter with 1" margins (DXA)
const FONT = "Arial";
const NAVY = "1F3864";
const FILL = "FFF2CC"; // yellow: reviewer fills in
const GREY = "F2F2F2";
const border = { style: BorderStyle.SINGLE, size: 4, color: "A6A6A6" };
const borders = { top: border, bottom: border, left: border, right: border };

const t = (text, o = {}) => new TextRun({ text, font: FONT, size: o.size || 20, bold: o.bold, italics: o.italics, color: o.color });
const p = (runs, o = {}) => new Paragraph({ children: Array.isArray(runs) ? runs : [runs], spacing: { after: o.after ?? 80, before: o.before ?? 0 }, alignment: o.align });
const h1 = (text) => new Paragraph({ heading: HeadingLevel.HEADING_1, children: [t(text, { size: 24, bold: true, color: NAVY })], spacing: { before: 240, after: 100 } });
const note = (text) => p(t(text, { size: 17, italics: true, color: "595959" }), { after: 100 });

function cell(content, width, o = {}) {
  const paras = (Array.isArray(content) ? content : [content]).map((c) => (typeof c === "string" ? p(t(c, { bold: o.bold, size: o.size, color: o.color }), { after: 0 }) : c));
  return new TableCell({
    borders, width: { size: width, type: WidthType.DXA },
    shading: o.fill ? { fill: o.fill, type: ShadingType.CLEAR, color: "auto" } : undefined,
    margins: { top: 70, bottom: 70, left: 110, right: 110 },
    columnSpan: o.span, children: paras,
  });
}

// two-column form: label | fill-in
function form(rows, w1 = 3600) {
  const w2 = W - w1;
  return new Table({
    width: { size: W, type: WidthType.DXA }, columnWidths: [w1, w2],
    rows: rows.map(([label, hint]) => new TableRow({
      children: [cell(label, w1, { fill: GREY, bold: true }),
        cell(hint ? [p(t(hint, { size: 16, italics: true, color: "7F7F7F" }), { after: 0 })] : "", w2, { fill: FILL })],
    })),
  });
}

function grid(head, rows, widths) {
  return new Table({
    width: { size: W, type: WidthType.DXA }, columnWidths: widths,
    rows: [
      new TableRow({ tableHeader: true, children: head.map((h, i) => cell(h, widths[i], { fill: NAVY, bold: true, color: "FFFFFF", size: 18 })) }),
      ...rows.map((r) => new TableRow({
        height: r[0] === "Signature" ? { value: 900, rule: "atLeast" } : undefined,
        children: r.map((v, i) => cell(v ?? "", widths[i], { fill: v === null ? FILL : undefined, size: 18 })),
      })),
    ],
  });
}

const box = "☐"; // ballot box
const children = [
  p(t("QA REVIEW SIGN-OFF", { size: 32, bold: true, color: NAVY }), { after: 40 }),
  p(t("Comparative Accuracy of Improper Payment Estimation Methods in Federal Health Programs: A Monte Carlo Evaluation of Analytic Estimators and Bootstrap Simulation", { size: 20, bold: true }), { after: 40 }),
  p(t("Repository: github.com/andrewcistola/improper-payment-estimation-accuracy", { size: 18, color: "595959" }), { after: 120 }),
  note("Complete every yellow box. Copy computer, software and run details from RERUN_SUMMARY.md and environment.txt in your re-run folder (qa/reruns/<date>_<initials>/). Instructions: qa/README.md, step 8. Save the completed form, and a signed PDF, in the review/ subfolder of your re-run folder."),

  h1("1. Who validated"),
  form([
    ["Full name", ""],
    ["Title / role", ""],
    ["Organization", ""],
    ["Email", ""],
    ["Relationship to the study or its authors", "For example: none; colleague; co-author"],
    ["Independent of the study's development?", `${box} Yes     ${box} No (explain in Section 6)`],
  ]),

  h1("2. What was reviewed"),
  form([
    ["Project version", "Git commit ID, or ZIP download date and time (environment.txt, 'Project version')"],
    ["How obtained", `${box} Git clone     ${box} ZIP download from GitHub`],
    ["Re-run folder", "qa/reruns/YYYY-MM-DD_INITIALS"],
    ["Completed checklist file", "review/QA_Checklist_YYYY-MM-DD_INITIALS.xlsx"],
  ]),
  p(t(" ", { size: 8 }), { after: 60 }),
  grid(["Checklist section", "Done?", "Tasks passed / total", "Summary of result"], [
    ["A. Setup and independence", `${box} Yes ${box} No`, null, null],
    ["B. Re-run with date-stamped logs", `${box} Yes ${box} No`, null, null],
    ["C. Code review: key assumptions", `${box} Yes ${box} No`, null, null],
    ["D. Results: represented correctly", `${box} Yes ${box} No`, null, null],
    ["E. Tests and independent checks", `${box} Yes ${box} No`, null, null],
    ["F. Data security and disclosure", `${box} Yes ${box} No`, null, null],
    ["G. Documentation and reproducibility", `${box} Yes ${box} No`, null, null],
    ["H. Close-out and sign-off", `${box} Yes ${box} No`, null, null],
  ], [3300, 1500, 1500, 3060]),
  note("Counts are on the checklist's Summary sheet."),

  h1("3. When it was checked"),
  form([
    ["Review start date", "YYYY-MM-DD"],
    ["Review end date", "YYYY-MM-DD"],
    ["Full re-run started", "YYYY-MM-DD HH:MM (first line of run_log.txt)"],
    ["Full re-run finished", "YYYY-MM-DD HH:MM (last line of run_log.txt)"],
    ["Total run time", "From RERUN_SUMMARY.md, for example 3h 32m"],
    ["Run folder name(s)", "start-here/logs/run_YYYY-MM-DD_HHMMSS (list every folder if the run was resumed)"],
  ]),

  h1("4. What tools were used"),
  form([
    ["Computer", "Make/model, or for example 'personal laptop'"],
    ["Operating system and version", ""],
    ["Processor cores / memory", "For example 8 cores / 16 GB"],
    ["Python version", ""],
    ["DuckDB version", "Must be 1.5.6"],
    ["Other package versions", "numpy, numba, pyarrow, scipy (or attach environment.txt)"],
    ["Spreadsheet software", "For example Microsoft Excel 365"],
    ["Code viewer / text editor", "For example VS Code, or the GitHub website"],
    ["Terminal", "For example PowerShell, macOS Terminal"],
    ["Other tools", ""],
  ]),

  h1("5. Re-run outcome"),
  form([
    ["Result check (verify_check.txt)", `${box} REPRODUCED EXACTLY     ${box} REPRODUCED     ${box} NOT REPRODUCED`],
    ["Output files identical to published", "For example 183 of 183"],
    ["Automated tests", "For example 38 passed, 0 failed"],
    ["Explanation (if not REPRODUCED EXACTLY)", ""],
  ]),

  h1("6. Findings"),
  grid(["Severity", "Total", "Open", "Resolved", "Accepted"], [
    ["Critical", null, null, null, null],
    ["Major", null, null, null, null],
    ["Minor", null, null, null, null],
    ["Note", null, null, null, null],
  ], [2560, 1700, 1700, 1700, 1700]),
  note("From the checklist's Summary sheet. Describe each open or accepted issue below, with its Issue ID."),
  new Table({
    width: { size: W, type: WidthType.DXA }, columnWidths: [3000, W - 3000],
    rows: [new TableRow({ children: [cell("Summary of findings and open items", 3000, { fill: GREY, bold: true }),
      cell([1, 2, 3, 4, 5].map(() => p(t(""), { after: 0 })), W - 3000, { fill: FILL })] })],
  }),

  h1("7. Attestation"),
  p(t("By signing below, I attest that:", { bold: true }), { after: 60 }),
  ...[
    "I personally re-ran the full study on the computer described in Section 4, following start-here/README.md, and the date-stamped logs in the re-run folder named in Section 2 are the unedited logs of that run.",
    "I reviewed each key assumption listed in Section C of the checklist against the code and configuration files, and recorded the result of every check.",
    "I compared the reported results (README, program READMEs, manuscript, one-page summary and conference abstract) with the outputs of my re-run, and recorded the result of every check.",
    "Every failed check is recorded on the Issues log, and the findings in Section 6 are complete and accurate.",
    "The information on this form and in the completed checklist is true and complete to the best of my knowledge.",
  ].map((s, i) => p([t(`${i + 1}.  `, { bold: true }), t(s)], { after: 60 })),
  p(t("Review decision (check one):", { bold: true }), { before: 120, after: 60 }),
  p(t(`${box}  Approved: the results are reproduced and represented correctly.`), { after: 40 }),
  p(t(`${box}  Approved with conditions: the issues listed in Section 6 must be resolved as described.`), { after: 40 }),
  p(t(`${box}  Not approved: see Section 6.`), { after: 160 }),
  grid(["", "Reviewer", "Second signer (optional: supervisor or study author acknowledging receipt)"], [
    ["Signature", null, null],
    ["Printed name", null, null],
    ["Title", null, null],
    ["Date signed", null, null],
  ], [1800, 3780, 3780]),
  note("Sign by hand on a printed copy and scan it, or sign electronically. Save the signed copy as QA_Signoff_YYYY-MM-DD_INITIALS.pdf in review/, alongside this .docx."),

  h1("8. Attachments (in the re-run folder)"),
  ...[
    "RERUN_SUMMARY.md: who, when, computer and software, run times, result check",
    "logs/: every date-stamped run folder (environment.txt, run_log.txt, one log per command)",
    "verification/verify_check.txt and verification/file_inventory.csv",
    "results/: the re-run's output files, in the same folders as in the project",
    "review/: this form (signed), the completed checklist, and any notes or screenshots",
  ].map((s) => p([t(`${box}  `), t(s)], { after: 40 })),
];

const doc = new Document({
  creator: "QA reviewer",
  title: "QA Review Sign-Off",
  styles: { default: { document: { run: { font: FONT, size: 20 } } } },
  sections: [{
    properties: { page: { size: { width: 12240, height: 15840 }, margin: { top: 1440, bottom: 1440, left: 1440, right: 1440 } } },
    footers: {
      default: new Footer({
        children: [new Paragraph({
          tabStops: [{ type: TabStopType.RIGHT, position: W }],
          children: [t("QA Review Sign-Off · Reviewer initials: ______", { size: 16, color: "7F7F7F" }),
            new TextRun({ children: ["\tPage ", PageNumber.CURRENT, " of ", PageNumber.TOTAL_PAGES], font: FONT, size: 16, color: "7F7F7F" })],
        })],
      }),
    },
    children,
  }],
});

Packer.toBuffer(doc).then((buf) => { fs.writeFileSync(OUT, buf); console.log("wrote", path.relative(process.cwd(), OUT)); });
