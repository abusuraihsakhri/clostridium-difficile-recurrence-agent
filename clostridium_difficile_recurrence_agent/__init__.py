"""
Clostridioides difficile Recurrence & Severity Triage Package
"""
from cdiff_recurrence import (
    CDiffRecurrenceEngine,
    PatientInput,
    SeverityAssessment,
    RecurrenceRiskAssessment,
    TreatmentGuidelineRecommendation,
    AssessmentReport,
)

__version__ = "2.1.1"
__all__ = [
    "CDiffRecurrenceEngine",
    "PatientInput",
    "SeverityAssessment",
    "RecurrenceRiskAssessment",
    "TreatmentGuidelineRecommendation",
    "AssessmentReport",
]
