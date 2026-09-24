const MODEL_NOTICE =
  "Heuristic educational estimate retained for backwards compatibility; it is not a validated or calibrated clinical prediction model.";

function finiteNumber(value, name) {
  const number = Number(value);
  if (!Number.isFinite(number)) throw new Error(`${name} must be a finite number`);
  return number;
}

function validate(input) {
  if (!Number.isInteger(input.age) || input.age < 18 || input.age > 130) {
    throw new Error("Age must be an integer from 18 to 130 years; this tool implements adult guidance.");
  }
  for (const [name, value] of [
    ["WBC", input.wbcCount],
    ["serum creatinine", input.serumCreatinine],
  ]) {
    if (value < 0) throw new Error(`${name} must be non-negative.`);
  }
  if (!Number.isInteger(input.priorEpisodes) || input.priorEpisodes < 0) {
    throw new Error("Prior CDI episodes must be a non-negative integer.");
  }
  if (input.albumin !== null && input.albumin <= 0) {
    throw new Error("Albumin must be greater than 0 when supplied.");
  }
  if (input.lactate !== null && input.lactate < 0) {
    throw new Error("Lactate must be non-negative when supplied.");
  }
}

export function normalizeInput(raw = {}) {
  const optionalNumber = (value, name) =>
    value === "" || value === null || value === undefined ? null : finiteNumber(value, name);

  const input = {
    age: finiteNumber(raw.age ?? 65, "age"),
    wbcCount: finiteNumber(raw.wbcCount ?? 12, "WBC"),
    serumCreatinine: finiteNumber(raw.serumCreatinine ?? 1.2, "serum creatinine"),
    priorEpisodes: finiteNumber(raw.priorEpisodes ?? 0, "prior CDI episodes"),
    concomitantAntibiotics: Boolean(raw.concomitantAntibiotics),
    immunocompromised: Boolean(raw.immunocompromised),
    ppiUse: Boolean(raw.ppiUse),
    albumin: optionalNumber(raw.albumin, "albumin"),
    chronicKidneyDisease: Boolean(raw.chronicKidneyDisease),
    inpatient: Boolean(raw.inpatient),
    hypotensionOrShock: Boolean(raw.hypotensionOrShock),
    ileus: Boolean(raw.ileus),
    toxicMegacolon: Boolean(raw.toxicMegacolon),
    lactate: optionalNumber(raw.lactate, "lactate"),
    heartFailureHistory: Boolean(raw.heartFailureHistory),
    priorRegimen: raw.priorRegimen ? String(raw.priorRegimen).toLowerCase() : null,
  };
  validate(input);
  return input;
}

export function assessSeverity(input) {
  const fulminantCriteria = [];
  if (input.hypotensionOrShock) fulminantCriteria.push("Hypotension or shock");
  if (input.ileus) fulminantCriteria.push("Ileus");
  if (input.toxicMegacolon) fulminantCriteria.push("Toxic megacolon");

  const wbcThresholdExceeded = input.wbcCount > 15;
  const creatinineThresholdExceeded = input.serumCreatinine >= 1.5;

  let grade;
  let summary;
  if (fulminantCriteria.length) {
    grade = "FULMINANT";
    summary = "Fulminant CDI criteria are present. Urgent clinician assessment is required.";
  } else if (wbcThresholdExceeded || creatinineThresholdExceeded) {
    grade = "SEVERE";
    const reasons = [];
    if (wbcThresholdExceeded) reasons.push(`WBC ${input.wbcCount.toFixed(1)} > 15.0 ×10³/µL`);
    if (creatinineThresholdExceeded) reasons.push(`serum creatinine ${input.serumCreatinine.toFixed(2)} ≥ 1.5 mg/dL`);
    summary = `Severe CDI supportive criteria: ${reasons.join("; ")}.`;
  } else {
    grade = "NON_SEVERE";
    summary = "Non-severe supportive criteria: WBC ≤ 15.0 ×10³/µL and serum creatinine < 1.5 mg/dL.";
  }

  if (input.lactate !== null && input.lactate >= 5) {
    summary += " Lactate ≥5 mmol/L is concerning but is not an IDSA/SHEA fulminant criterion.";
  }

  return {
    grade,
    isSevere: grade !== "NON_SEVERE",
    isFulminant: grade === "FULMINANT",
    wbcThresholdExceeded,
    creatinineThresholdExceeded,
    fulminantCriteria,
    summary,
  };
}

export function recurrenceRisk(input, severity) {
  let score = 0;
  const factors = [];
  const add = (points, label) => {
    score += points;
    factors.push({ points, label });
  };

  if (input.age >= 65) add(1.5, "Age ≥65 years");
  if (input.priorEpisodes === 1) add(2.5, "One prior CDI episode");
  if (input.priorEpisodes >= 2) add(4.0, "Multiple prior CDI episodes");
  if (input.concomitantAntibiotics) add(2.0, "Concomitant non-CDI antibiotics");
  if (severity.isSevere) add(1.5, "Severe or fulminant index episode");
  if (input.immunocompromised) add(2.0, "Immunocompromised host");
  if (input.ppiUse) add(1.0, "PPI exposure");
  if (input.albumin !== null && input.albumin < 3.0) add(1.0, "Albumin <3.0 g/dL");
  if (input.chronicKidneyDisease) add(1.0, "Chronic kidney disease");
  if (input.inpatient) add(1.0, "Inpatient/LTCF exposure");

  const probability = 1 / (1 + Math.exp(-(-2.2 + 0.35 * score)));
  const category =
    probability < 0.2 ? "LOW" :
    probability < 0.35 ? "MODERATE" :
    probability < 0.55 ? "HIGH" : "VERY_HIGH";

  const episodeType =
    input.priorEpisodes === 0 ? "PRIMARY" :
    input.priorEpisodes === 1 ? "FIRST_RECURRENCE" : "MULTIPLE_RECURRENCE";

  return {
    score: Math.round(score * 100) / 100,
    category,
    probability: Math.round(probability * 10000) / 10000,
    factors,
    episodeType,
    modelNotice: MODEL_NOTICE,
  };
}

export function treatmentOptions(input, severity, risk) {
  let primary;
  let alternative;

  if (severity.isFulminant) {
    primary = "Oral/NG vancomycin plus IV metronidazole; add rectal vancomycin when ileus prevents delivery, per current guideline/local protocol.";
    alternative = "Urgent escalation, supportive care, and surgical consultation as clinically indicated.";
  } else if (risk.episodeType === "PRIMARY") {
    primary = "Fidaxomicin is preferred by IDSA/SHEA 2021 when feasible.";
    alternative = "Oral vancomycin is an acceptable alternative.";
  } else if (risk.episodeType === "FIRST_RECURRENCE") {
    primary = "Fidaxomicin (standard or extended-pulsed) is preferred for recurrent CDI.";
    alternative = "A tapered/pulsed oral vancomycin regimen is an acceptable alternative in appropriate cases.";
  } else {
    primary = "Use a guideline-supported recurrent-CDI antibacterial regimen and evaluate microbiota-restoration options after antibacterial treatment.";
    alternative = "Options include vancomycin taper/pulse, vancomycin followed by rifaximin, fidaxomicin, and specialist-directed fecal microbiota-based therapy.";
  }

  const highRisk =
    input.age >= 65 ||
    input.immunocompromised ||
    severity.isSevere ||
    input.priorEpisodes >= 1;
  const considerBezlotoxumab = highRisk && !severity.isFulminant;
  const bezlotoxumabWarning = input.heartFailureHistory && considerBezlotoxumab
    ? "Heart-failure warning/precaution: reserve bezlotoxumab for use when benefit outweighs risk in patients with prior CHF."
    : null;

  const fmtCandidate = input.priorEpisodes >= 2;
  let fmtNote = fmtCandidate
    ? "Candidate for specialist evaluation for fecal microbiota-based therapy after standard-of-care antibacterial treatment."
    : "Not automatically selected by this rule; reassess if additional recurrence occurs or specialist criteria are met.";
  if (fmtCandidate && input.immunocompromised) {
    fmtNote += " Degree of immunocompromise matters; AGA 2024 distinguishes mild/moderate from severe immunocompromise.";
  }

  return {
    primary,
    alternative,
    considerBezlotoxumab,
    bezlotoxumabWarning,
    fmtCandidate,
    fmtNote,
  };
}

export function evaluateCDI(raw = {}) {
  const input = normalizeInput(raw);
  const severity = assessSeverity(input);
  const risk = recurrenceRisk(input, severity);
  const treatment = treatmentOptions(input, severity, risk);
  return { input, severity, risk, treatment };
}
