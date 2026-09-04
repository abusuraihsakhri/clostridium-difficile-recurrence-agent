#!/usr/bin/env python3
"""
Command-Line Interface for Clostridioides difficile Recurrence & Severity Engine
Supports interactive queries, direct CLI arguments, batch CSV evaluation, and JSON output.
"""

import argparse
import json
import sys
import os
import csv
from pathlib import Path
from typing import Optional, Dict, Any, List

# Add parent directory to path if needed
sys.path.insert(0, str(Path(__file__).parent.resolve()))

from cdiff_recurrence import CDiffRecurrenceEngine, PatientInput, AssessmentReport


def format_report_text(report: AssessmentReport) -> str:
    """Format AssessmentReport into a human-readable clinical consultation summary."""
    p = report.patient_input
    s = report.severity
    r = report.recurrence_risk
    t = report.treatment

    lines = []
    lines.append("=" * 80)
    lines.append(f"CLOSTRIDIOIDES DIFFICILE CLINICAL DECISION SUPPORT REPORT")
    lines.append(f"Patient ID: {report.patient_id:<20} Timestamp UTC: {report.timestamp_utc}")
    lines.append("=" * 80)

    # 1. Input Parameters
    lines.append("\n[1] CLINICAL PROFILE & LABORATORY VALUES")
    lines.append(f"  * Age: {p.age} years | Inpatient/LTCF: {'Yes' if p.inpatient_or_nursing_home else 'No'}")
    lines.append(f"  * WBC Count: {p.wbc_count:.1f} x 10^3/uL | Serum Creatinine: {p.serum_creatinine:.2f} mg/dL (Baseline: {p.baseline_creatinine if p.baseline_creatinine else 'N/A'})")
    lines.append(f"  * Prior CDI Episodes: {p.prior_cdi_episodes} ({r.recurrent_episode_type.replace('_', ' ')})")
    lines.append(f"  * Immunocompromised: {'Yes' if p.immunocompromised else 'No'} | Concomitant Antibiotics: {'Yes' if p.concomitant_antibiotics else 'No'}")
    lines.append(f"  * PPI Use: {'Yes' if p.ppi_use else 'No'} | Albumin: {f'{p.serum_albumin:.1f} g/dL' if p.serum_albumin else 'N/A'} | CKD: {'Yes' if p.chronic_kidney_disease else 'No'}")
    if p.hypotension_or_shock or p.ileus_present or p.toxic_megacolon or p.serum_lactate:
        lines.append(f"  * Critical Signs: Shock={'Yes' if p.hypotension_or_shock else 'No'}, Ileus={'Yes' if p.ileus_present else 'No'}, Megacolon={'Yes' if p.toxic_megacolon else 'No'}, Lactate={p.serum_lactate if p.serum_lactate else 'N/A'}")

    # 2. Severity Staging
    lines.append("\n[2] IDSA / SHEA 2021 SEVERITY CLASSIFICATION")
    lines.append(f"  * Severity Grade: >>> {s.severity_grade} <<<")
    lines.append(f"  * Summary: {s.clinical_summary}")
    if s.fulminant_criteria:
        lines.append("  * Fulminant Criteria Present:")
        for crit in s.fulminant_criteria:
            lines.append(f"    - {crit}")

    # 3. Recurrence Risk Stratification
    lines.append("\n[3] RECURRENCE RISK STRATIFICATION (Multivariable Model)")
    lines.append(f"  * Recurrence Risk Category: >>> {r.risk_category} RISK <<<")
    lines.append(f"  * Multivariable Risk Score: {r.risk_score:.2f} points")
    lines.append(f"  * Estimated Probability of Subsequent Recurrence: {r.predicted_recurrence_probability * 100:.1f}%")
    if r.contributing_risk_factors:
        lines.append("  * Contributing Risk Factors:")
        for factor in r.contributing_risk_factors:
            lines.append(f"    - (+{factor['points']:.1f} pts) {factor['factor']}: {factor['detail']}")

    # 4. Treatment Recommendations
    lines.append("\n[4] EVIDENCE-BASED THERAPEUTIC REGIMEN")
    lines.append(f"  * Primary Regimen:     {t.primary_regimen}")
    lines.append(f"    Dosage:              {t.primary_dosage}")
    lines.append(f"    Duration:            {t.primary_duration}")
    if t.alternative_regimen:
        lines.append(f"  * Alternative Regimen: {t.alternative_regimen}")
        lines.append(f"    Dosage:              {t.alternative_dosage}")
        lines.append(f"    Duration:            {t.alternative_duration}")

    # 5. Bezlotoxumab and FMT
    lines.append("\n[5] ADJUNCTIVE BIOLOGICS & MICROBIOTA RESTORATION")
    lines.append(f"  * Bezlotoxumab (ZINPLAVA) Indicated: {'YES' if t.bezlotoxumab_indicated else 'NO'}")
    if t.bezlotoxumab_rationale:
        lines.append(f"    Rationale: {t.bezlotoxumab_rationale}")
    if t.bezlotoxumab_warning:
        lines.append(f"    WARNING:   {t.bezlotoxumab_warning}")

    lines.append(f"  * FMT / Live Biotherapeutic Product Candidacy: {'QUALIFIED CANDIDATE' if t.fmt_candidacy else 'NOT CANDIDATE AT PRESENT'}")
    if t.fmt_rationale:
        lines.append(f"    Rationale: {t.fmt_rationale}")
    if t.live_biotherapeutic_options:
        lines.append("    Approved Live Biotherapeutic Options:")
        for opt in t.live_biotherapeutic_options:
            lines.append(f"      • {opt}")

    # 6. Infection Control & Supportive
    lines.append("\n[6] INFECTION CONTROL & STEWARDSHIP")
    for ic in t.infection_control_measures:
        lines.append(f"  * [ISOLATION] {ic}")
    for sc in t.supportive_care:
        lines.append(f"  * [SUPPORT]   {sc}")

    lines.append("=" * 80)
    return "\n".join(lines)


def run_interactive_mode() -> PatientInput:
    """Prompt user interactively for clinical parameters."""
    print("\n--- Interactive C. difficile Recurrence & Severity Assessment ---")
    
    def ask_str(prompt: str, default: str) -> str:
        val = input(f"{prompt} [{default}]: ").strip()
        return val if val else default

    def ask_int(prompt: str, default: int) -> int:
        val = input(f"{prompt} [{default}]: ").strip()
        try:
            return int(val) if val else default
        except ValueError:
            return default

    def ask_float(prompt: str, default: float) -> float:
        val = input(f"{prompt} [{default}]: ").strip()
        try:
            return float(val) if val else default
        except ValueError:
            return default

    def ask_opt_float(prompt: str) -> Optional[float]:
        val = input(f"{prompt} (or enter to skip): ").strip()
        if not val:
            return None
        try:
            return float(val)
        except ValueError:
            return None

    def ask_bool(prompt: str, default: bool = False) -> bool:
        def_str = "Y/n" if default else "y/N"
        val = input(f"{prompt} ({def_str}): ").strip().lower()
        if not val:
            return default
        return val in ["y", "yes", "true", "1"]

    pid = ask_str("Patient Identifier", "PT-INTERACTIVE")
    age = ask_int("Patient Age (years)", 68)
    wbc = ask_float("WBC Count (x 10^3/uL)", 16.5)
    cr = ask_float("Serum Creatinine (mg/dL)", 1.7)
    base_cr = ask_opt_float("Baseline Serum Creatinine (mg/dL)")
    prior_eps = ask_int("Number of prior CDI episodes (0=primary, 1=1st recurrence, >=2=multiple)", 0)
    abx = ask_bool("Concomitant non-CDI systemic antibiotics?", False)
    immuno = ask_bool("Immunocompromised host (chemo/transplant/steroids)?", False)
    ppi = ask_bool("Ongoing PPI / acid suppressive therapy?", True)
    alb = ask_opt_float("Serum Albumin (g/dL)")
    ckd = ask_bool("Chronic Kidney Disease (Stage >= 3)?", False)
    ltcf = ask_bool("Inpatient or Long-term Care Facility?", True)
    shock = ask_bool("Hypotension or vasopressor requirement?", False)
    ileus = ask_bool("Paralytic ileus present?", False)
    mega = ask_bool("Toxic megacolon present?", False)
    lactate = ask_opt_float("Serum Lactate (mmol/L)")
    chf = ask_bool("History of Congestive Heart Failure?", False)
    prior_reg = ask_str("Prior treatment regimen (vancomycin/fidaxomicin/none)", "none")
    if prior_reg == "none":
        prior_reg = None

    return PatientInput(
        patient_id=pid,
        age=age,
        wbc_count=wbc,
        serum_creatinine=cr,
        baseline_creatinine=base_cr,
        prior_cdi_episodes=prior_eps,
        concomitant_antibiotics=abx,
        immunocompromised=immuno,
        ppi_use=ppi,
        serum_albumin=alb,
        chronic_kidney_disease=ckd,
        inpatient_or_nursing_home=ltcf,
        hypotension_or_shock=shock,
        ileus_present=ileus,
        toxic_megacolon=mega,
        serum_lactate=lactate,
        history_congestive_heart_failure=chf,
        prior_treatment_regimen=prior_reg
    )


def run_batch_evaluation(input_path: str, output_path: Optional[str] = None, json_output: bool = False):
    """Execute batch evaluation from CSV and write optional CSV or print results."""
    if not os.path.exists(input_path):
        print(f"Error: CSV file '{input_path}' not found.", file=sys.stderr)
        sys.exit(1)

    with open(input_path, "r", encoding="utf-8") as f:
        csv_text = f.read()

    reports = CDiffRecurrenceEngine.evaluate_batch_csv(csv_text)

    if output_path:
        # Write batch output CSV
        fieldnames = [
            "patient_id",
            "age",
            "wbc_count",
            "serum_creatinine",
            "prior_cdi_episodes",
            "severity_grade",
            "is_severe",
            "is_fulminant",
            "risk_category",
            "risk_score",
            "predicted_recurrence_probability",
            "recurrent_episode_type",
            "primary_regimen",
            "primary_dosage",
            "primary_duration",
            "bezlotoxumab_indicated",
            "fmt_candidacy"
        ]
        with open(output_path, "w", newline="", encoding="utf-8") as f_out:
            writer = csv.DictWriter(f_out, fieldnames=fieldnames)
            writer.writeheader()
            for rep in reports:
                writer.writerow({
                    "patient_id": rep.patient_id,
                    "age": rep.patient_input.age,
                    "wbc_count": rep.patient_input.wbc_count,
                    "serum_creatinine": rep.patient_input.serum_creatinine,
                    "prior_cdi_episodes": rep.patient_input.prior_cdi_episodes,
                    "severity_grade": rep.severity.severity_grade,
                    "is_severe": rep.severity.is_severe,
                    "is_fulminant": rep.severity.is_fulminant,
                    "risk_category": rep.recurrence_risk.risk_category,
                    "risk_score": rep.recurrence_risk.risk_score,
                    "predicted_recurrence_probability": rep.recurrence_risk.predicted_recurrence_probability,
                    "recurrent_episode_type": rep.recurrence_risk.recurrent_episode_type,
                    "primary_regimen": rep.treatment.primary_regimen,
                    "primary_dosage": rep.treatment.primary_dosage,
                    "primary_duration": rep.treatment.primary_duration,
                    "bezlotoxumab_indicated": rep.treatment.bezlotoxumab_indicated,
                    "fmt_candidacy": rep.treatment.fmt_candidacy
                })
        print(f"Batch evaluation completed successfully. Results saved to {output_path} ({len(reports)} records).")
    elif json_output:
        print(json.dumps([r.to_dict() for r in reports], indent=2))
    else:
        for rep in reports:
            print(format_report_text(rep))
            print("\n")


def main():
    parser = argparse.ArgumentParser(
        description="Clostridioides difficile Recurrence Risk & Clinical Severity Evaluation Agent",
        formatter_class=argparse.RawDescriptionHelpFormatter
    )

    subparsers = parser.add_subparsers(dest="command", help="Sub-commands")

    # Batch subcommand
    batch_parser = subparsers.add_parser("batch", help="Batch process patient records from CSV")
    batch_parser.add_argument("-i", "--input", "--csv", dest="input_file", required=True, help="Input CSV file path")
    batch_parser.add_argument("-o", "--output", dest="output_file", default=None, help="Output CSV file path (optional)")
    batch_parser.add_argument("--json", action="store_true", help="Output results in structured JSON format")

    # Single evaluation / root flags
    parser.add_argument("-i", "--interactive", action="store_true", help="Launch interactive clinical question mode")
    parser.add_argument("--json", action="store_true", help="Output results in structured JSON format")
    parser.add_argument("--csv", type=str, help="Path to batch CSV file containing patient records")
    parser.add_argument("-o", "--output", dest="output_file", default=None, help="Output CSV file path for batch mode")

    # Direct Clinical Arguments
    parser.add_argument("--patient-id", type=str, default="PATIENT-001", help="Patient Identifier")
    parser.add_argument("--age", type=int, default=65, help="Patient age in years")
    parser.add_argument("--wbc", type=float, default=12.0, help="White blood cell count (x10^3/uL)")
    parser.add_argument("--creatinine", type=float, default=1.2, help="Serum creatinine (mg/dL)")
    parser.add_argument("--baseline-creatinine", type=float, default=None, help="Baseline serum creatinine (mg/dL)")
    parser.add_argument("--prior-episodes", type=int, default=0, help="Number of prior CDI episodes (0=primary, 1=first recurrence, 2+=multiple)")
    parser.add_argument("--concomitant-abx", action="store_true", help="Flag: Receiving concurrent non-CDI systemic antibiotics")
    parser.add_argument("--immunocompromised", action="store_true", help="Flag: Immunocompromised patient")
    parser.add_argument("--ppi", action="store_true", help="Flag: Ongoing Proton Pump Inhibitor usage")
    parser.add_argument("--albumin", type=float, default=None, help="Serum albumin (g/dL)")
    parser.add_argument("--ckd", action="store_true", help="Flag: Chronic kidney disease stage >= 3")
    parser.add_argument("--inpatient", action="store_true", default=True, help="Flag: Hospital inpatient or nursing home resident")
    parser.add_argument("--hypotension", action="store_true", help="Flag: Hypotension / vasopressor shock")
    parser.add_argument("--ileus", action="store_true", help="Flag: Paralytic ileus present")
    parser.add_argument("--megacolon", action="store_true", help="Flag: Toxic megacolon present")
    parser.add_argument("--lactate", type=float, default=None, help="Serum lactate level (mmol/L)")
    parser.add_argument("--chf", action="store_true", help="Flag: History of congestive heart failure")
    parser.add_argument("--prior-regimen", type=str, default=None, choices=["vancomycin", "fidaxomicin", "metronidazole"], help="Prior antibiotic used for previous episode")

    args = parser.parse_args()

    if args.command == "batch":
        run_batch_evaluation(args.input_file, args.output_file, json_output=args.json)
        return

    if args.csv:
        run_batch_evaluation(args.csv, getattr(args, "output_file", None), json_output=args.json)
        return

    if args.interactive:
        patient = run_interactive_mode()
    else:
        patient = PatientInput(
            patient_id=args.patient_id,
            age=args.age,
            wbc_count=args.wbc,
            serum_creatinine=args.creatinine,
            baseline_creatinine=args.baseline_creatinine,
            prior_cdi_episodes=args.prior_episodes,
            concomitant_antibiotics=args.concomitant_abx,
            immunocompromised=args.immunocompromised,
            ppi_use=args.ppi,
            serum_albumin=args.albumin,
            chronic_kidney_disease=args.ckd,
            inpatient_or_nursing_home=args.inpatient,
            hypotension_or_shock=args.hypotension,
            ileus_present=args.ileus,
            toxic_megacolon=args.megacolon,
            serum_lactate=args.lactate,
            history_congestive_heart_failure=args.chf,
            prior_treatment_regimen=args.prior_regimen
        )

    report = CDiffRecurrenceEngine.evaluate(patient)

    if args.json:
        print(report.to_json())
    else:
        print(format_report_text(report))


if __name__ == "__main__":
    main()
