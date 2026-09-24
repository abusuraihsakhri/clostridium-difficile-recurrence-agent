import { evaluateCDI } from "./cdiff.mjs";

const form = document.querySelector("#assessment-form");
const themeButton = document.querySelector("#theme-toggle");
const resetButton = document.querySelector("#reset-button");
const statusBox = document.querySelector("#status-box");
const severityValue = document.querySelector("#severity-value");
const riskValue = document.querySelector("#risk-value");
const riskMeta = document.querySelector("#risk-meta");
const severitySummary = document.querySelector("#severity-summary");
const primaryPlan = document.querySelector("#primary-plan");
const alternativePlan = document.querySelector("#alternative-plan");
const adjunctPlan = document.querySelector("#adjunct-plan");
const fmtPlan = document.querySelector("#fmt-plan");
const factorList = document.querySelector("#factor-list");
const errorBox = document.querySelector("#error-box");

function field(id) {
  return document.getElementById(id);
}

function checked(id) {
  return field(id).checked;
}

function optionalValue(id) {
  return field(id).value.trim() === "" ? null : field(id).value;
}

function readInput() {
  return {
    age: field("age").value,
    wbcCount: field("wbc").value,
    serumCreatinine: field("creatinine").value,
    priorEpisodes: field("prior-episodes").value,
    concomitantAntibiotics: checked("concomitant-abx"),
    immunocompromised: checked("immunocompromised"),
    ppiUse: checked("ppi"),
    albumin: optionalValue("albumin"),
    chronicKidneyDisease: checked("ckd"),
    inpatient: checked("inpatient"),
    hypotensionOrShock: checked("shock"),
    ileus: checked("ileus"),
    toxicMegacolon: checked("megacolon"),
    lactate: optionalValue("lactate"),
    heartFailureHistory: checked("chf"),
    priorRegimen: field("prior-regimen").value || null,
  };
}

function setFactors(factors) {
  factorList.replaceChildren();
  if (!factors.length) {
    const item = document.createElement("li");
    item.textContent = "No heuristic risk factors selected.";
    factorList.append(item);
    return;
  }
  for (const factor of factors) {
    const item = document.createElement("li");
    item.textContent = `+${factor.points.toFixed(1)} — ${factor.label}`;
    factorList.append(item);
  }
}

function render(report) {
  errorBox.hidden = true;
  statusBox.dataset.state = report.severity.isFulminant ? "urgent" : "ready";
  statusBox.textContent = report.severity.isFulminant
    ? "Fulminant criteria present — urgent clinical review"
    : "Assessment complete";

  severityValue.textContent = report.severity.grade.replace("_", " ");
  severitySummary.textContent = report.severity.summary;

  riskValue.textContent = report.risk.category.replace("_", " ");
  riskMeta.textContent =
    `Heuristic score ${report.risk.score.toFixed(1)} · legacy numeric estimate ${(report.risk.probability * 100).toFixed(1)}%. ${report.risk.modelNotice}`;

  primaryPlan.textContent = report.treatment.primary;
  alternativePlan.textContent = report.treatment.alternative;

  adjunctPlan.textContent = report.treatment.considerBezlotoxumab
    ? "Bezlotoxumab may be considered as an adjunct in a high-recurrence-risk patient. " +
      (report.treatment.bezlotoxumabWarning || "No CHF warning flag was selected.")
    : "No automated bezlotoxumab consideration flag from the selected inputs.";

  fmtPlan.textContent = report.treatment.fmtNote;
  setFactors(report.risk.factors);
}

function analyze(event) {
  event?.preventDefault();
  try {
    render(evaluateCDI(readInput()));
  } catch (error) {
    errorBox.hidden = false;
    errorBox.textContent = error instanceof Error ? error.message : String(error);
    statusBox.dataset.state = "error";
    statusBox.textContent = "Check input";
  }
}

function applyTheme(theme) {
  document.documentElement.dataset.theme = theme;
  themeButton.setAttribute("aria-pressed", String(theme === "dark"));
  themeButton.textContent = theme === "dark" ? "Light mode" : "Dark mode";
  try {
    localStorage.setItem("cdiff-theme", theme);
  } catch {
    // Theme persistence is optional.
  }
}

themeButton.addEventListener("click", () => {
  applyTheme(document.documentElement.dataset.theme === "dark" ? "light" : "dark");
});

form.addEventListener("submit", analyze);
resetButton.addEventListener("click", () => {
  form.reset();
  field("age").value = "65";
  field("wbc").value = "12.0";
  field("creatinine").value = "1.2";
  field("prior-episodes").value = "0";
  analyze();
});

let initialTheme = "light";
try {
  initialTheme = localStorage.getItem("cdiff-theme") || "light";
} catch {
  initialTheme = "light";
}
applyTheme(initialTheme === "dark" ? "dark" : "light");
analyze();
