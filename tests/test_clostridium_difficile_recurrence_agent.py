"""
Pytest Test Suite for Clostridium Difficile Recurrence Agent.
"""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

import pytest
from cdiff_recurrence import (
    CDiffRecurrenceEngine,
    PatientInput,
    SeverityAssessment,
    RecurrenceRiskAssessment,
)


def test_severity_classification():
    p_non_sev = PatientInput(patient_id="T1", wbc_count=9.0, serum_creatinine=1.0)
    sev1 = CDiffRecurrenceEngine.assess_severity(p_non_sev)
    assert sev1.severity_grade == "NON_SEVERE"

    p_sev = PatientInput(patient_id="T2", wbc_count=18.0, serum_creatinine=1.2)
    sev2 = CDiffRecurrenceEngine.assess_severity(p_sev)
    assert sev2.severity_grade == "SEVERE"

    p_ful = PatientInput(patient_id="T3", wbc_count=22.0, serum_creatinine=2.0, hypotension_or_shock=True)
    sev3 = CDiffRecurrenceEngine.assess_severity(p_ful)
    assert sev3.severity_grade == "FULMINANT"


def test_treatment_recommendations():
    p1 = PatientInput(patient_id="T4", age=68, prior_cdi_episodes=0)
    rep1 = CDiffRecurrenceEngine.evaluate(p1)
    assert "Fidaxomicin" in rep1.treatment.primary_regimen
    assert rep1.treatment.bezlotoxumab_indicated is True

    p2 = PatientInput(patient_id="T5", age=70, prior_cdi_episodes=2)
    rep2 = CDiffRecurrenceEngine.evaluate(p2)
    assert rep2.treatment.fmt_candidacy is True
