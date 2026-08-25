#!/usr/bin/env python3
"""
Comprehensive Unit Test Suite for C. difficile Recurrence & Severity Engine
Tests severity classifications, multivariable recurrence modeling, IDSA/SHEA
guideline mapping, Bezlotoxumab rules, FMT candidacy, and CSV batch processing.
"""

import unittest
import json
import math
from cdiff_recurrence import (
    CDiffRecurrenceEngine,
    PatientInput,
    SeverityAssessment,
    RecurrenceRiskAssessment,
    TreatmentGuidelineRecommendation,
    AssessmentReport,
)


class TestCDiffSeverityAssessment(unittest.TestCase):
    """Test clinical severity grading according to IDSA/SHEA and ACG criteria."""

    def test_non_severe_baseline(self):
        patient = PatientInput(
            patient_id="PT-01",
            age=50,
            wbc_count=8.5,
            serum_creatinine=0.9,
            hypotension_or_shock=False,
            ileus_present=False,
            toxic_megacolon=False
        )
        sev = CDiffRecurrenceEngine.assess_severity(patient)
        self.assertEqual(sev.severity_grade, "NON_SEVERE")
        self.assertFalse(sev.is_severe)
        self.assertFalse(sev.is_fulminant)
        self.assertFalse(sev.wbc_threshold_exceeded)
        self.assertFalse(sev.creatinine_threshold_exceeded)

    def test_severe_by_wbc_cutoff(self):
        # WBC exactly 15.0 or above
        patient = PatientInput(
            patient_id="PT-02",
            age=55,
            wbc_count=15.0,
            serum_creatinine=1.1
        )
        sev = CDiffRecurrenceEngine.assess_severity(patient)
        self.assertEqual(sev.severity_grade, "SEVERE")
        self.assertTrue(sev.is_severe)
        self.assertFalse(sev.is_fulminant)
        self.assertTrue(sev.wbc_threshold_exceeded)
        self.assertFalse(sev.creatinine_threshold_exceeded)

    def test_severe_by_high_wbc(self):
        patient = PatientInput(
            patient_id="PT-03",
            age=60,
            wbc_count=24.5,
            serum_creatinine=1.2
        )
        sev = CDiffRecurrenceEngine.assess_severity(patient)
        self.assertEqual(sev.severity_grade, "SEVERE")
        self.assertTrue(sev.is_severe)

    def test_severe_by_creatinine_cutoff(self):
        patient = PatientInput(
            patient_id="PT-04",
            age=58,
            wbc_count=11.0,
            serum_creatinine=1.5
        )
        sev = CDiffRecurrenceEngine.assess_severity(patient)
        self.assertEqual(sev.severity_grade, "SEVERE")
        self.assertTrue(sev.is_severe)
        self.assertTrue(sev.creatinine_threshold_exceeded)

    def test_severe_by_baseline_creatinine_multiplier(self):
        # Baseline 0.8 -> 1.3 is > 1.5x baseline (0.8 * 1.5 = 1.2)
        patient = PatientInput(
            patient_id="PT-05",
            age=45,
            wbc_count=10.0,
            serum_creatinine=1.3,
            baseline_creatinine=0.8
        )
        sev = CDiffRecurrenceEngine.assess_severity(patient)
        self.assertEqual(sev.severity_grade, "SEVERE")
        self.assertTrue(sev.creatinine_threshold_exceeded)

    def test_fulminant_by_shock(self):
        patient = PatientInput(
            patient_id="PT-06",
            age=70,
            wbc_count=28.0,
            serum_creatinine=2.4,
            hypotension_or_shock=True
        )
        sev = CDiffRecurrenceEngine.assess_severity(patient)
        self.assertEqual(sev.severity_grade, "FULMINANT")
        self.assertTrue(sev.is_fulminant)
        self.assertTrue(sev.is_severe)
        self.assertIn("Systemic hypotension or vasopressor-dependent septic shock", sev.fulminant_criteria)

    def test_fulminant_by_ileus(self):
        patient = PatientInput(
            patient_id="PT-07",
            age=68,
            wbc_count=18.0,
            serum_creatinine=1.8,
            ileus_present=True
        )
        sev = CDiffRecurrenceEngine.assess_severity(patient)
        self.assertEqual(sev.severity_grade, "FULMINANT")
        self.assertTrue(sev.is_fulminant)
        self.assertIn("Paralytic ileus documented clinically or radiographically", sev.fulminant_criteria)

    def test_fulminant_by_megacolon(self):
        patient = PatientInput(
            patient_id="PT-08",
            age=62,
            wbc_count=32.0,
            serum_creatinine=2.1,
            toxic_megacolon=True
        )
        sev = CDiffRecurrenceEngine.assess_severity(patient)
        self.assertEqual(sev.severity_grade, "FULMINANT")
        self.assertTrue(sev.is_fulminant)

    def test_fulminant_by_lactate(self):
        patient = PatientInput(
            patient_id="PT-09",
            age=75,
            wbc_count=16.0,
            serum_creatinine=1.6,
            serum_lactate=5.4
        )
        sev = CDiffRecurrenceEngine.assess_severity(patient)
        self.assertEqual(sev.severity_grade, "FULMINANT")
        self.assertTrue(sev.is_fulminant)


class TestCDiffRecurrenceRiskModel(unittest.TestCase):
    """Test multivariable recurrence modeling and risk categorization."""

    def test_young_low_risk_outpatient(self):
        patient = PatientInput(
            patient_id="PT-LOW",
            age=32,
            wbc_count=7.5,
            serum_creatinine=0.8,
            prior_cdi_episodes=0,
            concomitant_antibiotics=False,
            immunocompromised=False,
            ppi_use=False,
            serum_albumin=4.2,
            chronic_kidney_disease=False,
            inpatient_or_nursing_home=False
        )
        sev = CDiffRecurrenceEngine.assess_severity(patient)
        risk = CDiffRecurrenceEngine.calculate_recurrence_risk(patient, sev)
        
        self.assertEqual(risk.risk_score, 0.0)
        self.assertEqual(risk.risk_category, "LOW")
        # Baseline probability: 1 / (1 + exp(2.20)) ~ 0.0998
        self.assertAlmostEqual(risk.predicted_recurrence_probability, 0.0998, delta=0.01)

    def test_moderate_risk_elderly_inpatient(self):
        # Age >= 65 (+1.5), Inpatient (+1.0), PPI (+1.0) -> Score 3.5
        patient = PatientInput(
            patient_id="PT-MOD",
            age=68,
            wbc_count=9.0,
            serum_creatinine=1.1,
            prior_cdi_episodes=0,
            concomitant_antibiotics=False,
            immunocompromised=False,
            ppi_use=True,
            inpatient_or_nursing_home=True
        )
        sev = CDiffRecurrenceEngine.assess_severity(patient)
        risk = CDiffRecurrenceEngine.calculate_recurrence_risk(patient, sev)

        self.assertEqual(risk.risk_score, 3.5)
        self.assertEqual(risk.risk_category, "MODERATE")
        self.assertTrue(0.20 <= risk.predicted_recurrence_probability < 0.35)

    def test_high_risk_first_recurrence_with_abx(self):
        # Age 70 (+1.5), 1st recurrence (+2.5), Inpatient (+1.0) -> Score 5.0
        patient = PatientInput(
            patient_id="PT-HIGH",
            age=70,
            wbc_count=12.0,
            serum_creatinine=1.2,
            prior_cdi_episodes=1,
            concomitant_antibiotics=False,
            inpatient_or_nursing_home=True
        )
        sev = CDiffRecurrenceEngine.assess_severity(patient)
        risk = CDiffRecurrenceEngine.calculate_recurrence_risk(patient, sev)

        self.assertEqual(risk.risk_score, 5.0)
        self.assertEqual(risk.risk_category, "HIGH")
        self.assertEqual(risk.recurrent_episode_type, "FIRST_RECURRENCE")
        self.assertTrue(0.35 <= risk.predicted_recurrence_probability < 0.55)

    def test_very_high_risk_polymorbid_multiple_recurrence(self):
        # Age 78 (+1.5), Multiple prior (+4.0), Concomitant Abx (+2.0), Severe index (+1.5),
        # Immunocompromised (+2.0), PPI (+1.0), Albumin 2.4 (+1.0), CKD (+1.0), Inpatient (+1.0) -> Score 15.0
        patient = PatientInput(
            patient_id="PT-VHIGH",
            age=78,
            wbc_count=17.5,
            serum_creatinine=1.9,
            prior_cdi_episodes=2,
            concomitant_antibiotics=True,
            immunocompromised=True,
            ppi_use=True,
            serum_albumin=2.4,
            chronic_kidney_disease=True,
            inpatient_or_nursing_home=True
        )
        sev = CDiffRecurrenceEngine.assess_severity(patient)
        risk = CDiffRecurrenceEngine.calculate_recurrence_risk(patient, sev)

        self.assertEqual(risk.risk_score, 15.0)
        self.assertEqual(risk.risk_category, "VERY_HIGH")
        self.assertEqual(risk.recurrent_episode_type, "MULTIPLE_RECURRENCE")
        self.assertTrue(risk.predicted_recurrence_probability > 0.85)


class TestCDiffTreatmentRecommendations(unittest.TestCase):
    """Test guideline-compliant therapeutic regimens and biologic indications."""

    def test_primary_non_severe_preferred_fidaxomicin(self):
        patient = PatientInput(
            patient_id="PT-TX-1",
            age=40,
            wbc_count=9.0,
            serum_creatinine=1.0,
            prior_cdi_episodes=0
        )
        report = CDiffRecurrenceEngine.evaluate(patient)
        tx = report.treatment

        self.assertIn("Fidaxomicin", tx.primary_regimen)
        self.assertIn("200 mg orally twice daily", tx.primary_dosage)
        self.assertIn("Oral Vancomycin", tx.alternative_regimen)
        self.assertFalse(tx.fmt_candidacy)

    def test_primary_fulminant_dual_regimen(self):
        patient = PatientInput(
            patient_id="PT-TX-2",
            age=67,
            wbc_count=26.0,
            serum_creatinine=2.5,
            hypotension_or_shock=True,
            ileus_present=True
        )
        report = CDiffRecurrenceEngine.evaluate(patient)
        tx = report.treatment

        self.assertIn("Oral Vancomycin PLUS Intravenous Metronidazole", tx.primary_regimen)
        self.assertIn("500 mg orally/nasogastrically", tx.primary_dosage)
        self.assertIn("Vancomycin Retention Enema", tx.alternative_regimen)

    def test_first_recurrence_prior_vancomycin_uses_fidaxomicin(self):
        patient = PatientInput(
            patient_id="PT-TX-3",
            age=62,
            wbc_count=11.0,
            serum_creatinine=1.1,
            prior_cdi_episodes=1,
            prior_treatment_regimen="vancomycin"
        )
        report = CDiffRecurrenceEngine.evaluate(patient)
        tx = report.treatment

        self.assertIn("Fidaxomicin", tx.primary_regimen)
        self.assertIn("Vancomycin Tapered and Pulsed", tx.alternative_regimen)

    def test_first_recurrence_prior_fidaxomicin_uses_vanco_taper(self):
        patient = PatientInput(
            patient_id="PT-TX-4",
            age=64,
            wbc_count=10.0,
            serum_creatinine=1.0,
            prior_cdi_episodes=1,
            prior_treatment_regimen="fidaxomicin"
        )
        report = CDiffRecurrenceEngine.evaluate(patient)
        tx = report.treatment

        self.assertIn("Vancomycin Tapered and Pulsed Regimen", tx.primary_regimen)

    def test_multiple_recurrence_fmt_candidacy(self):
        patient = PatientInput(
            patient_id="PT-TX-5",
            age=71,
            wbc_count=12.0,
            serum_creatinine=1.2,
            prior_cdi_episodes=2
        )
        report = CDiffRecurrenceEngine.evaluate(patient)
        tx = report.treatment

        self.assertTrue(tx.fmt_candidacy)
        self.assertIn("FMT / LBP restores microbial diversity", tx.fmt_rationale)
        self.assertTrue(len(tx.live_biotherapeutic_options) >= 2)
        self.assertTrue(any("VOWST" in opt for opt in tx.live_biotherapeutic_options))
        self.assertTrue(any("REBYOTA" in opt for opt in tx.live_biotherapeutic_options))

    def test_bezlotoxumab_indicated_for_elderly_high_risk(self):
        patient = PatientInput(
            patient_id="PT-BEZLO-1",
            age=72,
            wbc_count=11.0,
            serum_creatinine=1.0,
            prior_cdi_episodes=0,
            history_congestive_heart_failure=False
        )
        report = CDiffRecurrenceEngine.evaluate(patient)
        tx = report.treatment

        self.assertTrue(tx.bezlotoxumab_indicated)
        self.assertIn("Age >= 65", tx.bezlotoxumab_rationale)
        self.assertIsNone(tx.bezlotoxumab_warning)

    def test_bezlotoxumab_heart_failure_black_box_warning(self):
        patient = PatientInput(
            patient_id="PT-BEZLO-2",
            age=74,
            wbc_count=16.0,
            serum_creatinine=1.6,
            prior_cdi_episodes=1,
            history_congestive_heart_failure=True
        )
        report = CDiffRecurrenceEngine.evaluate(patient)
        tx = report.treatment

        self.assertTrue(tx.bezlotoxumab_indicated)
        self.assertIsNotNone(tx.bezlotoxumab_warning)
        self.assertIn("BLACK BOX WARNING", tx.bezlotoxumab_warning)


class TestCDiffSerializationAndBatch(unittest.TestCase):
    """Test report serialization, dictionary export, and CSV batch processing."""

    def test_json_and_dict_serialization(self):
        patient = PatientInput(
            patient_id="PT-SER-01",
            age=66,
            wbc_count=14.2,
            serum_creatinine=1.4
        )
        report = CDiffRecurrenceEngine.evaluate(patient)
        d = report.to_dict()
        self.assertEqual(d["patient_id"], "PT-SER-01")
        self.assertIn("severity", d)
        self.assertIn("recurrence_risk", d)
        self.assertIn("treatment", d)

        json_str = report.to_json()
        parsed = json.loads(json_str)
        self.assertEqual(parsed["patient_id"], "PT-SER-01")
        self.assertEqual(parsed["severity"]["severity_grade"], "NON_SEVERE")

    def test_batch_csv_evaluation(self):
        csv_sample = (
            "patient_id,age,wbc_count,serum_creatinine,prior_cdi_episodes,concomitant_antibiotics,immunocompromised,ppi_use\n"
            "P-101,45,8.2,0.9,0,false,false,false\n"
            "P-102,72,16.5,1.7,0,true,false,true\n"
            "P-103,68,11.0,1.2,2,false,true,false\n"
        )
        reports = CDiffRecurrenceEngine.evaluate_batch_csv(csv_sample)
        self.assertEqual(len(reports), 3)
        self.assertEqual(reports[0].patient_id, "P-101")
        self.assertEqual(reports[0].severity.severity_grade, "NON_SEVERE")
        self.assertEqual(reports[1].patient_id, "P-102")
        self.assertEqual(reports[1].severity.severity_grade, "SEVERE")
        self.assertEqual(reports[2].patient_id, "P-103")
        self.assertTrue(reports[2].treatment.fmt_candidacy)

    def test_edge_case_zero_and_none_values(self):
        patient = PatientInput(
            patient_id="PT-ZERO",
            age=0,
            wbc_count=0.0,
            serum_creatinine=0.0,
            baseline_creatinine=None,
            prior_cdi_episodes=0,
            serum_albumin=None,
            serum_lactate=None,
            inpatient_or_nursing_home=False
        )
        report = CDiffRecurrenceEngine.evaluate(patient)
        self.assertEqual(report.severity.severity_grade, "NON_SEVERE")
        self.assertEqual(report.recurrence_risk.risk_score, 0.0)

    def test_hypoalbuminemia_and_ckd_factors(self):
        patient = PatientInput(
            patient_id="PT-ALB-CKD",
            age=50,
            wbc_count=8.0,
            serum_creatinine=1.1,
            serum_albumin=2.6,
            chronic_kidney_disease=True,
            inpatient_or_nursing_home=False
        )
        report = CDiffRecurrenceEngine.evaluate(patient)
        self.assertEqual(report.recurrence_risk.risk_score, 2.0)
        self.assertEqual(len(report.recurrence_risk.contributing_risk_factors), 2)

    def test_concomitant_antibiotics_factor_alone(self):
        patient = PatientInput(
            patient_id="PT-ABX",
            age=40,
            wbc_count=7.0,
            serum_creatinine=0.8,
            concomitant_antibiotics=True,
            inpatient_or_nursing_home=False
        )
        report = CDiffRecurrenceEngine.evaluate(patient)
        self.assertEqual(report.recurrence_risk.risk_score, 2.0)
        factors = [f["factor"] for f in report.recurrence_risk.contributing_risk_factors]
        self.assertIn("Concomitant Systemic Antibiotic Therapy", factors)

    def test_infection_control_and_supportive_recommendations(self):
        patient = PatientInput(patient_id="PT-IC", age=65)
        report = CDiffRecurrenceEngine.evaluate(patient)
        tx = report.treatment
        self.assertTrue(len(tx.infection_control_measures) >= 4)
        self.assertTrue(any("SOAP AND WATER" in ic for ic in tx.infection_control_measures))
        self.assertTrue(any("anti-motility" in sc for sc in tx.supportive_care))

    def test_format_report_text_output(self):
        from cli import format_report_text
        patient = PatientInput(patient_id="PT-FMT-TEST", age=72, prior_cdi_episodes=2)
        report = CDiffRecurrenceEngine.evaluate(patient)
        txt = format_report_text(report)
        self.assertIn("CLOSTRIDIOIDES DIFFICILE CLINICAL DECISION SUPPORT REPORT", txt)
        self.assertIn("QUALIFIED CANDIDATE", txt)
        self.assertIn("VOWST", txt)


if __name__ == "__main__":
    unittest.main()
