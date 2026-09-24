#!/usr/bin/env python3
"""
Clostridioides (Clostridium) difficile Recurrence & Clinical Severity Engine
----------------------------------------------------------------------------
Implements adult CDI severity rules based on IDSA/SHEA guidance, a
repository-specific recurrence-risk heuristic, guideline-referenced treatment
option summaries, bezlotoxumab consideration, and fecal microbiota-based
therapy candidacy triage.

Domain: Infectious Diseases / Gastroenterology
Pure Python Standard Library (no external dependencies required).
"""

from dataclasses import dataclass, field, asdict
from typing import Dict, Any, List, Optional
import math
import json
import csv
import io


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
    inpatient_or_nursing_home: bool = False  # healthcare exposure / LTCF
    hypotension_or_shock: bool = False  # SBP < 90 mmHg or vasopressor requirement
    ileus_present: bool = False  # clinical/radiologic ileus
    toxic_megacolon: bool = False  # colonic dilation > 6 cm with toxicity
    serum_lactate: Optional[float] = None  # mmol/L; contextual severity marker
    history_congestive_heart_failure: bool = False  # for bezlotoxumab heart-failure precaution
    prior_treatment_regimen: Optional[str] = None  # 'vancomycin', 'fidaxomicin', 'metronidazole', None

    def __post_init__(self) -> None:
        """Validate inputs for the adult guideline scope used by this tool."""
        if not str(self.patient_id).strip():
            raise ValueError("patient_id must not be empty")
        if not 18 <= self.age <= 130:
            raise ValueError("age must be between 18 and 130 years; this tool implements adult guidance")
        if self.wbc_count < 0:
            raise ValueError("wbc_count must be non-negative")
        if self.serum_creatinine < 0:
            raise ValueError("serum_creatinine must be non-negative")
        if self.baseline_creatinine is not None and self.baseline_creatinine <= 0:
            raise ValueError("baseline_creatinine must be > 0 when supplied")
        if self.prior_cdi_episodes < 0:
            raise ValueError("prior_cdi_episodes must be non-negative")
        if self.serum_albumin is not None and self.serum_albumin <= 0:
            raise ValueError("serum_albumin must be > 0 when supplied")
        if self.serum_lactate is not None and self.serum_lactate < 0:
            raise ValueError("serum_lactate must be non-negative")
        if self.prior_treatment_regimen is not None:
            normalized = self.prior_treatment_regimen.strip().lower()
            if normalized in {"", "none"}:
                self.prior_treatment_regimen = None
            else:
                allowed = {"vancomycin", "fidaxomicin", "metronidazole"}
                if normalized not in allowed:
                    raise ValueError(
                        "prior_treatment_regimen must be one of: vancomycin, fidaxomicin, metronidazole, none"
                    )
                self.prior_treatment_regimen = normalized


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
    """Repository-specific recurrence-risk heuristic and legacy numeric estimate."""
    risk_score: float
    risk_category: str  # 'LOW', 'MODERATE', 'HIGH', 'VERY_HIGH'
    predicted_recurrence_probability: float  # legacy heuristic estimate from 0.0 to 1.0
    contributing_risk_factors: List[Dict[str, Any]] = field(default_factory=list)
    recurrent_episode_type: str = "PRIMARY"  # 'PRIMARY', 'FIRST_RECURRENCE', 'MULTIPLE_RECURRENCE'
    model_notice: str = (
        "Heuristic educational estimate retained for backwards compatibility; "
        "it is not a validated or calibrated clinical prediction model."
    )


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
    recurrence-risk heuristic calculation, and guideline-referenced therapeutic mapping.
    """

    @staticmethod
    def assess_severity(patient: PatientInput) -> SeverityAssessment:
        """
        Classify disease severity according to SHEA/IDSA & ACG guidelines.
        - Non-Severe: WBC <= 15.0 x 10^3/uL AND Serum Cr < 1.5 mg/dL
        - Severe: WBC > 15.0 x 10^3/uL OR Serum Cr >= 1.5 mg/dL
        - Fulminant: Hypotension/shock, ileus, or toxic megacolon
        Baseline creatinine and lactate may be clinically relevant, but they are not used here
        as IDSA/SHEA fulminant classification criteria.
        """
        fulminant_triggers = []
        if patient.hypotension_or_shock:
            fulminant_triggers.append("Systemic hypotension or vasopressor-dependent septic shock")
        if patient.ileus_present:
            fulminant_triggers.append("Paralytic ileus documented clinically or radiographically")
        if patient.toxic_megacolon:
            fulminant_triggers.append("Toxic megacolon")

        # IDSA/SHEA supportive severity thresholds for adults:
        # non-severe is WBC <= 15,000/uL and serum creatinine < 1.5 mg/dL.
        wbc_flag = patient.wbc_count > 15.0
        cr_flag = patient.serum_creatinine >= 1.5

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
                reasons.append(f"Leukocytosis (WBC {patient.wbc_count:.1f} > 15.0 x 10^3/uL)")
            if cr_flag:
                reasons.append(f"Renal impairment (Serum Cr {patient.serum_creatinine:.2f} mg/dL)")
            summary = f"Severe C. difficile infection: {', '.join(reasons)}."
        else:
            grade = "NON_SEVERE"
            is_sev = False
            is_ful = False
            summary = "Non-severe C. difficile infection: WBC <= 15.0 x 10^3/uL and Serum Creatinine < 1.5 mg/dL."

        if patient.serum_lactate is not None and patient.serum_lactate >= 5.0:
            summary += (
                " Lactate >= 5.0 mmol/L is a concerning severity marker, "
                "but it is not an IDSA/SHEA fulminant criterion."
            )

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
        Repository-specific heuristic risk stratification for recurrent C. difficile infection (rCDI).
        The legacy numeric estimate is retained for backwards compatibility and must not be
        interpreted as a validated patient-specific probability. It uses the transform:
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
                "detail": f"Age {patient.age} is a guideline-recognized recurrence risk factor"
            })

        # 2. Prior CDI episodes
        if patient.prior_cdi_episodes == 1:
            pts = 2.5
            score += pts
            ep_type = "FIRST_RECURRENCE"
            factors.append({
                "factor": "Prior CDI Episode (1st Recurrence)",
                "points": pts,
                "detail": "A prior CDI episode increases the risk of an additional recurrence"
            })
        elif patient.prior_cdi_episodes >= 2:
            pts = 4.0
            score += pts
            ep_type = "MULTIPLE_RECURRENCE"
            factors.append({
                "factor": f"Multiple Prior CDI Episodes ({patient.prior_cdi_episodes} prior)",
                "points": pts,
                "detail": "Multiple prior episodes are associated with a high risk of additional recurrence"
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
                "detail": "Ongoing non-CDI antimicrobials can disrupt colonization resistance"
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
        # Legacy heuristic mapping: these coefficients are not externally validated/calibrated.
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
        Generate guideline-referenced therapeutic option summaries,
        bezlotoxumab consideration, and fecal microbiota-based therapy candidacy.
        """
        # 1. Primary & Alternative Regimens based on episode stage and severity
        if severity.is_fulminant:
            primary_reg = "Oral Vancomycin PLUS Intravenous Metronidazole"
            primary_dose = "Vancomycin 500 mg orally/nasogastrically Q6H (QID) + Metronidazole 500 mg IV Q8H (TID)"
            primary_dur = "Duration should follow current guideline/local protocol and clinical response"
            
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
            # IDSA/SHEA 2021 prefers fidaxomicin (standard or extended-pulsed)
            # over a standard course of vancomycin for recurrent CDI.
            primary_reg = "Fidaxomicin Standard or Extended-Pulsed (Preferred)"
            primary_dose = "200 mg orally BID x 10 days OR 200 mg BID x 5 days then every other day x 20 days"
            primary_dur = "10 days (standard) or 25 days (extended-pulsed)"

            alt_reg = "Vancomycin Tapered and Pulsed Regimen"
            alt_dose = "Use a guideline-consistent tapered/pulsed oral vancomycin regimen"
            alt_dur = "Regimen-specific; follow current guideline and local protocol"

        else:
            # MULTIPLE RECURRENCES (>= 2 prior episodes)
            primary_reg = "Multiple-recurrence options: antibacterial therapy plus microbiota-restoration evaluation"
            primary_dose = (
                "Use a guideline-supported recurrent-CDI antibacterial regimen; after completion, "
                "evaluate for FDA-approved fecal microbiota products or conventional FMT as appropriate"
            )
            primary_dur = "Regimen-specific; follow current guideline, product labeling, and specialist protocol"

            alt_reg = "Vancomycin tapered/pulsed regimen or vancomycin followed by rifaximin"
            alt_dose = "Use a guideline-consistent regimen selected for the individual clinical context"
            alt_dur = "Regimen-specific"

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
            bezlo_rationale = (
                "Consider adjunctive bezlotoxumab (10 mg/kg IV once during antibacterial treatment) "
                f"in a patient at high risk for recurrence. Risk factors present: {', '.join(reasons)}. "
                "This flag is decision support, not an automatic treatment recommendation."
            )
            
            if patient.history_congestive_heart_failure:
                bezlo_warning = (
                    "FDA WARNING/PRECAUTION: heart failure occurred more often in patients with prior CHF; "
                    "reserve bezlotoxumab for use when the benefit outweighs the risk."
                )

        # 3. FMT and Live Biotherapeutic Product (LBP) Assessment
        # Indicated for >= 2 recurrences (i.e. >= 3 total episodes) treated with appropriate antibiotics
        fmt_candidacy = False
        fmt_rationale = None
        lbp_options = []

        if patient.prior_cdi_episodes >= 2:
            fmt_candidacy = True
            fmt_rationale = (
                f"Patient has {patient.prior_cdi_episodes} prior recurrences and may be evaluated for "
                "fecal microbiota-based therapy after standard-of-care antibacterial treatment. "
                "Selection depends on immune status, product eligibility, availability, and specialist assessment."
            )
            if patient.immunocompromised:
                fmt_rationale += (
                    " AGA 2024 guidance distinguishes mild/moderate from severe immunocompromise; "
                    "this binary input cannot make that distinction, so specialist review is required."
                )
            lbp_options = [
                "VOWST (fecal microbiota spores, live-brpk): FDA-approved to prevent recurrence after antibacterial treatment for recurrent CDI; follow current labeling",
                "REBYOTA (fecal microbiota, live-jslm): FDA-approved to prevent recurrence after antibiotic treatment for recurrent CDI; follow current labeling",
                "Conventional donor FMT: use only within applicable regulatory, donor-screening, and institutional requirements"
            ]
        elif patient.prior_cdi_episodes == 1 and risk.risk_category in ["HIGH", "VERY_HIGH"]:
            fmt_candidacy = False
            fmt_rationale = "First recurrence: Medical therapy (Fidaxomicin / Vancomycin taper +/- Bezlotoxumab) preferred first-line. FMT reserved if patient fails current regimen or suffers 2nd recurrence."

        # 4. Supportive Care Measures
        supportive = [
            "Review and discontinue non-essential systemic antimicrobial therapy when clinically appropriate.",
            "Re-evaluate and discontinue unnecessary Proton Pump Inhibitors (PPIs) / H2 receptor antagonists.",
            "Avoid routine anti-motility therapy during active severe disease unless the treating clinician determines it is appropriate.",
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

    @staticmethod
    def _parse_csv_bool(value: Optional[str], field_name: str, default: bool = False) -> bool:
        """Parse common CSV boolean forms without silently accepting invalid values."""
        if value is None or str(value).strip() == "":
            return default
        normalized = str(value).strip().lower()
        if normalized in {"true", "1", "yes", "y"}:
            return True
        if normalized in {"false", "0", "no", "n"}:
            return False
        raise ValueError(
            f"Invalid boolean value for {field_name!r}: {value!r}; "
            "use true/false, yes/no, or 1/0"
        )

    @classmethod
    def evaluate_batch_csv(cls, csv_text: str) -> List[AssessmentReport]:
        """Parse a CSV cohort and run validated adult CDI assessments."""
        reader = csv.DictReader(io.StringIO(csv_text))
        if reader.fieldnames is None:
            raise ValueError("CSV input is missing a header row")

        required = {"patient_id", "age", "wbc_count", "serum_creatinine"}
        missing = sorted(required.difference(reader.fieldnames))
        if missing:
            raise ValueError(f"CSV input is missing required columns: {', '.join(missing)}")

        results: List[AssessmentReport] = []
        for line_number, row in enumerate(reader, start=2):
            try:
                patient = PatientInput(
                    patient_id=(row.get("patient_id") or "").strip(),
                    age=int(row["age"]),
                    wbc_count=float(row["wbc_count"]),
                    serum_creatinine=float(row["serum_creatinine"]),
                    baseline_creatinine=float(row["baseline_creatinine"]) if row.get("baseline_creatinine") else None,
                    prior_cdi_episodes=int(row.get("prior_cdi_episodes") or 0),
                    concomitant_antibiotics=cls._parse_csv_bool(row.get("concomitant_antibiotics"), "concomitant_antibiotics"),
                    immunocompromised=cls._parse_csv_bool(row.get("immunocompromised"), "immunocompromised"),
                    ppi_use=cls._parse_csv_bool(row.get("ppi_use"), "ppi_use"),
                    serum_albumin=float(row["serum_albumin"]) if row.get("serum_albumin") else None,
                    chronic_kidney_disease=cls._parse_csv_bool(row.get("chronic_kidney_disease"), "chronic_kidney_disease"),
                    inpatient_or_nursing_home=cls._parse_csv_bool(row.get("inpatient_or_nursing_home"), "inpatient_or_nursing_home"),
                    hypotension_or_shock=cls._parse_csv_bool(row.get("hypotension_or_shock"), "hypotension_or_shock"),
                    ileus_present=cls._parse_csv_bool(row.get("ileus_present"), "ileus_present"),
                    toxic_megacolon=cls._parse_csv_bool(row.get("toxic_megacolon"), "toxic_megacolon"),
                    serum_lactate=float(row["serum_lactate"]) if row.get("serum_lactate") else None,
                    history_congestive_heart_failure=cls._parse_csv_bool(
                        row.get("history_congestive_heart_failure"),
                        "history_congestive_heart_failure",
                    ),
                    prior_treatment_regimen=(row.get("prior_treatment_regimen") or "").strip() or None,
                )
                results.append(cls.evaluate(patient))
            except (TypeError, ValueError) as exc:
                raise ValueError(f"Invalid CSV data on line {line_number}: {exc}") from exc

        return results
