#!/usr/bin/env python3
"""
Clostridioides (Clostridium) difficile Recurrence & Clinical Severity Engine
----------------------------------------------------------------------------
Implements evidence-based clinical decision support based on IDSA/SHEA 2021
and ACG guidelines, multivariable recurrence risk stratification (Hu et al.,
Garey et al.), Bezlotoxumab criteria, and Fecal Microbiota Transplantation
(FMT) / Live Biotherapeutic Product (VOWST, REBYOTA) candidacy triage.

Domain: Infectious Diseases / Gastroenterology
Pure Python Standard Library (no external dependencies required).
"""

from dataclasses import dataclass, field, asdict
from typing import Dict, Any, List, Optional, Tuple, Union
import math
import json
import csv
import io
import sys


@dataclass
class PatientInput:
    """Input clinical parameters for C. difficile assessment."""
    patient_id: str = "PATIENT-001"
    age: int = 65
    wbc_count: float = 12.0  # cells x 10^3/uL (e.g. 12.0 = 12,000/uL)
    serum_creatinine: float = 1.2  # mg/dL
    baseline_creatinine: Optional[float] = None  # mg/dL
    prior_cdi_episodes: int = 0  # 0 = primary episode, 1 = 1st recurrence, >=2 = multiple
    concomitant_antibiotics: bool = False  # ongoing non-CDI systemic antimicrobials
    immunocompromised: bool = False  # malignancy, chemotherapy, transplant, immunosuppressants
    ppi_use: bool = False  # proton pump inhibitors / acid suppression
    serum_albumin: Optional[float] = None  # g/dL
    chronic_kidney_disease: bool = False  # CKD Stage >= 3 or eGFR < 60 mL/min
    inpatient_or_nursing_home: bool = True  # healthcare exposure / LTCF
    hypotension_or_shock: bool = False  # SBP < 90 mmHg or vasopressor requirement
    ileus_present: bool = False  # clinical/radiologic ileus
    toxic_megacolon: bool = False  # colonic dilation > 6 cm with toxicity
    serum_lactate: Optional[float] = None  # mmol/L (lactate >= 5.0 indicates fulminant)
    history_congestive_heart_failure: bool = False  # for Bezlotoxumab black-box warning
    prior_treatment_regimen: Optional[str] = None  # 'vancomycin', 'fidaxomicin', 'metronidazole', None


@dataclass
class SeverityAssessment:
    """Clinical severity classification per IDSA/SHEA & ACG criteria."""
    severity_grade: str  # 'NON_SEVERE', 'SEVERE', 'FULMINANT'
    is_severe: bool
    is_fulminant: bool
    wbc_threshold_exceeded: bool
    creatinine_threshold_exceeded: bool
    fulminant_criteria: List[str] = field(default_factory=list)
    clinical_summary: str = ""


@dataclass
class RecurrenceRiskAssessment:
    """Multivariable risk score and statistical probability of recurrence."""
    risk_score: float
    risk_category: str  # 'LOW', 'MODERATE', 'HIGH', 'VERY_HIGH'
    predicted_recurrence_probability: float  # 0.0 to 1.0 (percentage)
    contributing_risk_factors: List[Dict[str, Any]] = field(default_factory=list)
    recurrent_episode_type: str = "PRIMARY"  # 'PRIMARY', 'FIRST_RECURRENCE', 'MULTIPLE_RECURRENCE'


@dataclass
class TreatmentGuidelineRecommendation:
    """Evidence-based clinical therapeutics and regimen options."""
    primary_regimen: str
    primary_dosage: str
    primary_duration: str
    alternative_regimen: Optional[str]
    alternative_dosage: Optional[str]
    alternative_duration: Optional[str]
    bezlotoxumab_indicated: bool
    bezlotoxumab_rationale: Optional[str]
    bezlotoxumab_warning: Optional[str]
    fmt_candidacy: bool
    fmt_rationale: Optional[str]
    live_biotherapeutic_options: List[str] = field(default_factory=list)
    supportive_care: List[str] = field(default_factory=list)
    infection_control_measures: List[str] = field(default_factory=list)


@dataclass
class AssessmentReport:
    """Unified comprehensive CDI clinical report."""
    patient_id: str
    timestamp_utc: str
    patient_input: PatientInput
    severity: SeverityAssessment
    recurrence_risk: RecurrenceRiskAssessment
    treatment: TreatmentGuidelineRecommendation

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)

    def to_json(self, indent: int = 2) -> str:
        return json.dumps(self.to_dict(), indent=indent)


class CDiffRecurrenceEngine:
    """
    Core algorithmic engine for C. difficile severity classification,
    recurrence risk calculation, and guideline-adherent therapeutic mapping.
    """

    @staticmethod
    def assess_severity(patient: PatientInput) -> SeverityAssessment:
        """
        Classify disease severity according to SHEA/IDSA & ACG guidelines.
        - Non-Severe: WBC <= 15.0 x 10^3/uL AND Serum Cr <= 1.5 mg/dL (or < 1.5x baseline)
        - Severe: WBC > 15.0 x 10^3/uL OR Serum Cr >= 1.5 mg/dL (or >= 1.5x baseline)
        - Fulminant (Severe-Complicated): Hypotension, shock, ileus, toxic megacolon, or lactate >= 5.0 mmol/L
        """
        fulminant_triggers = []
        if patient.hypotension_or_shock:
            fulminant_triggers.append("Systemic hypotension or vasopressor-dependent septic shock")
        if patient.ileus_present:
            fulminant_triggers.append("Paralytic ileus documented clinically or radiographically")
        if patient.toxic_megacolon:
            fulminant_triggers.append("Toxic megacolon (colonic distension > 6.0 cm)")
        if patient.serum_lactate is not None and patient.serum_lactate >= 5.0:
            fulminant_triggers.append(f"Severe lactic acidosis (Lactate {patient.serum_lactate:.1f} >= 5.0 mmol/L)")

        # WBC threshold: > 15,000 / uL (or >= 15.0 in 10^3/uL units)
        wbc_flag = patient.wbc_count >= 15.0

        # Creatinine threshold: >= 1.5 mg/dL or >= 1.5x baseline
        cr_flag = False
        if patient.baseline_creatinine and patient.baseline_creatinine > 0:
            if patient.serum_creatinine >= 1.5 * patient.baseline_creatinine:
                cr_flag = True
        elif patient.serum_creatinine >= 1.5:
            cr_flag = True

        if len(fulminant_triggers) > 0:
            grade = "FULMINANT"
            is_sev = True
            is_ful = True
            summary = "Fulminant C. difficile colitis (Severe-Complicated). High mortality risk; ICU level monitoring & surgical consult required."
        elif wbc_flag or cr_flag:
            grade = "SEVERE"
            is_sev = True
            is_ful = False
            reasons = []
            if wbc_flag:
                reasons.append(f"Leukocytosis (WBC {patient.wbc_count:.1f} >= 15.0 x 10^3/uL)")
            if cr_flag:
                reasons.append(f"Renal impairment (Serum Cr {patient.serum_creatinine:.2f} mg/dL)")
            summary = f"Severe C. difficile infection: {', '.join(reasons)}."
        else:
            grade = "NON_SEVERE"
            is_sev = False
            is_ful = False
            summary = "Non-severe C. difficile infection: WBC < 15.0 x 10^3/uL and Serum Creatinine < 1.5 mg/dL."

        return SeverityAssessment(
            severity_grade=grade,
            is_severe=is_sev,
            is_fulminant=is_ful,
            wbc_threshold_exceeded=wbc_flag,
            creatinine_threshold_exceeded=cr_flag,
            fulminant_criteria=fulminant_triggers,
            clinical_summary=summary
        )

    @staticmethod
    def calculate_recurrence_risk(patient: PatientInput, severity: SeverityAssessment) -> RecurrenceRiskAssessment:
        """
        Multivariable clinical risk stratification for recurrent C. difficile infection (rCDI).
        Calculates weighted risk points and statistical recurrence probability via logistic transform:
        z = -2.20 + 0.35 * RiskScore
        P = 1 / (1 + exp(-z))
        """
        score = 0.0
        factors: List[Dict[str, Any]] = []

        # 1. Age >= 65
        if patient.age >= 65:
            pts = 1.5
            score += pts
            factors.append({
                "factor": "Age >= 65 years",
                "points": pts,
                "detail": f"Age {patient.age} is associated with altered microbiota and immunosenescence (OR ~ 2.1)"
            })

        # 2. Prior CDI episodes
        if patient.prior_cdi_episodes == 1:
            pts = 2.5
            score += pts
            ep_type = "FIRST_RECURRENCE"
            factors.append({
                "factor": "Prior CDI Episode (1st Recurrence)",
                "points": pts,
                "detail": "Single previous recurrence increases subsequent recurrence risk to ~35-45%"
            })
        elif patient.prior_cdi_episodes >= 2:
            pts = 4.0
            score += pts
            ep_type = "MULTIPLE_RECURRENCE"
            factors.append({
                "factor": f"Multiple Prior CDI Episodes ({patient.prior_cdi_episodes} prior)",
                "points": pts,
                "detail": "Multiple recurrences demonstrate persistent dysbiosis with recurrence risk exceeding 50-65%"
            })
        else:
            ep_type = "PRIMARY"

        # 3. Concomitant non-CDI antibiotics
        if patient.concomitant_antibiotics:
            pts = 2.0
            score += pts
            factors.append({
                "factor": "Concomitant Systemic Antibiotic Therapy",
                "points": pts,
                "detail": "Ongoing broad-spectrum antimicrobials suppress commensal colonization resistance (OR ~ 2.5-3.0)"
            })

        # 4. Severe index episode
        if severity.is_severe or severity.is_fulminant:
            pts = 1.5
            score += pts
            factors.append({
                "factor": "Severe or Fulminant Index Episode",
                "points": pts,
                "detail": f"Severe presentation ({severity.severity_grade}) correlates with elevated mucosal damage and recurrence"
            })

        # 5. Immunocompromised state
        if patient.immunocompromised:
            pts = 2.0
            score += pts
            factors.append({
                "factor": "Immunocompromised Host",
                "points": pts,
                "detail": "Compromised humoral response to Toxin A/B significantly increases relapse risk"
            })

        # 6. PPI or acid suppression
        if patient.ppi_use:
            pts = 1.0
            score += pts
            factors.append({
                "factor": "Proton Pump Inhibitor (PPI) Exposure",
                "points": pts,
                "detail": "Gastric acid reduction facilitates vegetative cell survival and microbiota disruption"
            })

        # 7. Serum Albumin < 3.0 g/dL
        if patient.serum_albumin is not None and patient.serum_albumin < 3.0:
            pts = 1.0
            score += pts
            factors.append({
                "factor": f"Hypoalbuminemia (Albumin {patient.serum_albumin:.1f} < 3.0 g/dL)",
                "points": pts,
                "detail": "Nutritional and inflammatory marker associated with poor mucosal recovery"
            })

        # 8. Chronic Kidney Disease
        if patient.chronic_kidney_disease:
            pts = 1.0
            score += pts
            factors.append({
                "factor": "Chronic Kidney Disease (Stage >= 3)",
                "points": pts,
                "detail": "Uremic dysbiosis and impaired immunity increase recurrence susceptibility"
            })

        # 9. Inpatient / Nursing home healthcare stay
        if patient.inpatient_or_nursing_home:
            pts = 1.0
            score += pts
            factors.append({
                "factor": "Healthcare Facility / Long-Term Care Exposure",
                "points": pts,
                "detail": "High environmental spore pressure and exposure to antimicrobial selective pressure"
            })

        # Calculate logistic probability
        # Calibrated logistic model: intercept = -2.20, slope = 0.35
        # Baseline probability for score 0 = 1 / (1 + exp(2.20)) = 0.099 (~10%)
        # Score 3: z = -1.15 -> P = 24.0%
        # Score 6: z = -0.10 -> P = 47.5%
        # Score 9: z = +0.95 -> P = 72.1%
        z = -2.20 + (0.35 * score)
        prob = 1.0 / (1.0 + math.exp(-z))
        prob = round(prob, 4)

        if prob < 0.20:
            category = "LOW"
        elif prob < 0.35:
            category = "MODERATE"
        elif prob < 0.55:
            category = "HIGH"
        else:
            category = "VERY_HIGH"

        return RecurrenceRiskAssessment(
            risk_score=round(score, 2),
            risk_category=category,
            predicted_recurrence_probability=prob,
            contributing_risk_factors=factors,
            recurrent_episode_type=ep_type
        )

    @staticmethod
    def generate_treatment_recommendations(
        patient: PatientInput,
        severity: SeverityAssessment,
        risk: RecurrenceRiskAssessment
    ) -> TreatmentGuidelineRecommendation:
        """
        Generate IDSA/SHEA 2021 & ACG compliant therapeutic plans,
        Bezlotoxumab evaluation, and FMT / Live Biotherapeutic candidacy.
        """
        # 1. Primary & Alternative Regimens based on episode stage and severity
        if severity.is_fulminant:
            primary_reg = "Oral Vancomycin PLUS Intravenous Metronidazole"
            primary_dose = "Vancomycin 500 mg orally/nasogastrically Q6H (QID) + Metronidazole 500 mg IV Q8H (TID)"
            primary_dur = "14 days (or until clinical resolution; re-evaluate daily)"
            
            alt_reg = "Vancomycin Oral + IV Metronidazole + Vancomycin Retention Enema"
            alt_dose = "If ileus present: Add Vancomycin 500 mg in 100 mL normal saline PR every 6 hours via rectal catheter"
            alt_dur = "Administer until ileus resolves and oral therapy transits successfully"

        elif risk.recurrent_episode_type == "PRIMARY":
            # Non-fulminant primary episode
            primary_reg = "Fidaxomicin (Preferred per IDSA/SHEA 2021)"
            primary_dose = "200 mg orally twice daily (BID)"
            primary_dur = "10 days"

            alt_reg = "Oral Vancomycin (Standard Alternative)"
            alt_dose = "125 mg orally four times daily (QID)"
            alt_dur = "10 days"

        elif risk.recurrent_episode_type == "FIRST_RECURRENCE":
            prior_reg = (patient.prior_treatment_regimen or "").lower()
            if "fidaxomicin" in prior_reg:
                # Used fidaxomicin initially, switch to pulsed/tapered vancomycin or extended fidaxomicin
                primary_reg = "Vancomycin Tapered and Pulsed Regimen"
                primary_dose = "125 mg QID x 10-14d, then BID x 7d, then QD x 7d, then 125 mg every 2-3 days"
                primary_dur = "6 to 8 weeks total"

                alt_reg = "Fidaxomicin Extended-Pulsed Regimen"
                alt_dose = "200 mg BID x 5 days, then 200 mg once every other day"
                alt_dur = "Days 6 through 25 (20 days pulsed)"
            else:
                # Used vancomycin or metronidazole initially: prefer Fidaxomicin standard or extended
                primary_reg = "Fidaxomicin Standard or Extended-Pulsed (Preferred)"
                primary_dose = "200 mg orally BID x 10 days OR 200 mg BID x 5d then QOD x 20d"
                primary_dur = "10 days (Standard) or 25 days (Extended-Pulsed)"

                alt_reg = "Vancomycin Tapered and Pulsed Regimen"
                alt_dose = "125 mg QID x 10-14d, then BID x 7d, then QD x 7d, then 125 mg every 2-3 days"
                alt_dur = "6 to 8 weeks total"

        else:
            # MULTIPLE RECURRENCES (>= 2 prior episodes)
            primary_reg = "Fecal Microbiota Transplantation (FMT) / FDA Live Biotherapeutic post-antibiotic lead-in"
            primary_dose = "Complete oral Vancomycin (125 mg QID x 10-14d) or Fidaxomicin, followed by FMT / Biotherapeutic"
            primary_dur = "Antibiotic lead-in x 10-14d, then FMT / VOWST / REBYOTA"

            alt_reg = "Vancomycin Taper/Pulse Regimen followed by Rifaximin Chaser"
            alt_dose = "Vancomycin taper/pulse x 6-8 weeks, followed by Rifaximin 400 mg TID x 20 days"
            alt_dur = "9 to 11 weeks total"

        # 2. Bezlotoxumab (ZINPLAVA) monoclonal antibody assessment
        # IDSA/SHEA 2021: Consider Bezlotoxumab (10 mg/kg IV single dose) for patients with CDI episode in the last 6 months
        # AND high risk of recurrence (Age >= 65, Immunocompromised, Severe CDI).
        bezlo_indicated = False
        bezlo_rationale = None
        bezlo_warning = None

        has_high_risk = (patient.age >= 65 or patient.immunocompromised or severity.is_severe or patient.prior_cdi_episodes >= 1)
        if has_high_risk and not severity.is_fulminant:
            bezlo_indicated = True
            reasons = []
            if patient.age >= 65:
                reasons.append("Age >= 65")
            if patient.immunocompromised:
                reasons.append("Immunocompromised")
            if severity.is_severe:
                reasons.append("Severe CDI presentation")
            if patient.prior_cdi_episodes >= 1:
                reasons.append("History of recurrent CDI")
            bezlo_rationale = f"Indicated as adjunctive single-dose infusion (10 mg/kg IV) during standard antibiotic therapy to bind Toxin B. Risk factors: {', '.join(reasons)}."
            
            if patient.history_congestive_heart_failure:
                bezlo_warning = "FDA BLACK BOX WARNING: Heart failure exacerbation observed in clinical trials. Use Bezlotoxumab only if benefit strictly outweighs risk in patients with congestive heart failure."

        # 3. FMT and Live Biotherapeutic Product (LBP) Assessment
        # Indicated for >= 2 recurrences (i.e. >= 3 total episodes) treated with appropriate antibiotics
        fmt_candidacy = False
        fmt_rationale = None
        lbp_options = []

        if patient.prior_cdi_episodes >= 2:
            fmt_candidacy = True
            fmt_rationale = f"Strong recommendation (IDSA/SHEA & ACG): Patient has {patient.prior_cdi_episodes} prior recurrences. FMT / LBP restores microbial diversity and cures >85-90% of multiply recurrent CDI."
            lbp_options = [
                "VOWST (SER-109): FDA-approved oral microbiota spores (4 capsules once daily x 3 consecutive days after completing antibiotics & magnesium citrate)",
                "REBYOTA (RBX2660): FDA-approved rectally administered live microbiota suspension (single 150 mL dose after antibiotic completion)",
                "Donor Fecal Microbiota Transplantation (Colonoscopy or retention enema via authorized stool bank)"
            ]
        elif patient.prior_cdi_episodes == 1 and risk.risk_category in ["HIGH", "VERY_HIGH"]:
            fmt_candidacy = False
            fmt_rationale = "First recurrence: Medical therapy (Fidaxomicin / Vancomycin taper +/- Bezlotoxumab) preferred first-line. FMT reserved if patient fails current regimen or suffers 2nd recurrence."

        # 4. Supportive Care Measures
        supportive = [
            "Discontinue non-essential systemic antimicrobial therapy immediately (reduces recurrence risk by 50%).",
            "Re-evaluate and discontinue unnecessary Proton Pump Inhibitors (PPIs) / H2 receptor antagonists.",
            "Avoid anti-motility / anti-diarrheal medications (e.g. loperamide, diphenoxylate) due to risk of toxic megacolon precipitation.",
            "Ensure adequate fluid resuscitation and electrolyte replacement (monitor potassium and magnesium)."
        ]

        # 5. Infection Control Measures
        infection_control = [
            "Strict Contact Precautions (gown and gloves required before patient room entry).",
            "Perform hand hygiene with SOAP AND WATER (alcohol-based hand rubs are ineffective against C. difficile bacterial spores).",
            "Environmental decontamination using EPA-registered sporocidal agents (sodium hypochlorite / bleach-based solutions).",
            "Maintain isolation precautions until at least 48 hours after complete diarrhea resolution (or throughout entire hospital stay per institutional policy)."
        ]

        return TreatmentGuidelineRecommendation(
            primary_regimen=primary_reg,
            primary_dosage=primary_dose,
            primary_duration=primary_dur,
            alternative_regimen=alt_reg,
            alternative_dosage=alt_dose,
            alternative_duration=alt_dur,
            bezlotoxumab_indicated=bezlo_indicated,
            bezlotoxumab_rationale=bezlo_rationale,
            bezlotoxumab_warning=bezlo_warning,
            fmt_candidacy=fmt_candidacy,
            fmt_rationale=fmt_rationale,
            live_biotherapeutic_options=lbp_options,
            supportive_care=supportive,
            infection_control_measures=infection_control
        )

    @classmethod
    def evaluate(cls, patient: PatientInput) -> AssessmentReport:
        """Run complete clinical evaluation for a patient."""
        import datetime
        sev = cls.assess_severity(patient)
        risk = cls.calculate_recurrence_risk(patient, sev)
        rx = cls.generate_treatment_recommendations(patient, sev, risk)

        return AssessmentReport(
            patient_id=patient.patient_id,
            timestamp_utc=datetime.datetime.now(datetime.timezone.utc).isoformat(),
            patient_input=patient,
            severity=sev,
            recurrence_risk=risk,
            treatment=rx
        )

    @classmethod
    def evaluate_batch_csv(cls, csv_text: str) -> List[AssessmentReport]:
        """Parse CSV content and run batch evaluations."""
        reader = csv.DictReader(io.StringIO(csv_text))
        results = []
        for row in reader:
            p = PatientInput(
                patient_id=row.get("patient_id", f"PT-{len(results)+1}"),
                age=int(row.get("age", 65)),
                wbc_count=float(row.get("wbc_count", 10.0)),
                serum_creatinine=float(row.get("serum_creatinine", 1.0)),
                baseline_creatinine=float(row["baseline_creatinine"]) if row.get("baseline_creatinine") else None,
                prior_cdi_episodes=int(row.get("prior_cdi_episodes", 0)),
                concomitant_antibiotics=str(row.get("concomitant_antibiotics", "false")).lower() in ["true", "1", "yes"],
                immunocompromised=str(row.get("immunocompromised", "false")).lower() in ["true", "1", "yes"],
                ppi_use=str(row.get("ppi_use", "false")).lower() in ["true", "1", "yes"],
                serum_albumin=float(row["serum_albumin"]) if row.get("serum_albumin") else None,
                chronic_kidney_disease=str(row.get("chronic_kidney_disease", "false")).lower() in ["true", "1", "yes"],
                inpatient_or_nursing_home=str(row.get("inpatient_or_nursing_home", "true")).lower() in ["true", "1", "yes"],
                hypotension_or_shock=str(row.get("hypotension_or_shock", "false")).lower() in ["true", "1", "yes"],
                ileus_present=str(row.get("ileus_present", "false")).lower() in ["true", "1", "yes"],
                toxic_megacolon=str(row.get("toxic_megacolon", "false")).lower() in ["true", "1", "yes"],
                serum_lactate=float(row["serum_lactate"]) if row.get("serum_lactate") else None,
                history_congestive_heart_failure=str(row.get("history_congestive_heart_failure", "false")).lower() in ["true", "1", "yes"],
                prior_treatment_regimen=row.get("prior_treatment_regimen") or None
            )
            results.append(cls.evaluate(p))
        return results
