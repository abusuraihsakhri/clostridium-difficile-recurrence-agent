# Clostridium Difficile Recurrence & Severity Engine

> **Clinical Domain:** Gastroenterology & Infectious Diseases  
> **Clinical Guidelines:** IDSA / SHEA 2021 Focused Update & ACG 2021 Clinical Guidelines  
> **Key Protocols:** Recurrence Risk Stratification, Fidaxomicin Triage, Bezlotoxumab Selection, and Fecal Microbiota Transplantation (FMT) / Live Biotherapeutic Products (VOWST, REBYOTA) Candidacy

---

## 1. Clinical Overview & Background

*Clostridioides (formerly Clostridium) difficile* infection (CDI) is the leading cause of healthcare-associated infectious diarrhea, with recurrence rates of 20–30% after an initial episode and up to 40–65% after subsequent recurrences.

This decision support engine implements standard guideline algorithms from the **Infectious Diseases Society of America (IDSA)**, **Society for Healthcare Epidemiology of America (SHEA)**, and the **American College of Gastroenterology (ACG)** to:
1. Classify acute disease severity (Non-Severe vs. Severe vs. Fulminant).
2. Calculate multivariable risk scores and statistical probabilities of subsequent recurrence.
3. Recommend first-line and alternative therapeutic regimens (Fidaxomicin vs. Vancomycin vs. Metronidazole).
4. Evaluate precise clinical indications and contraindications for adjunctive **Bezlotoxumab** (ZINPLAVA).
5. Determine candidacy for **FMT** or FDA-approved live biotherapeutic products (**VOWST**, **REBYOTA**).

---

## 2. Clinical Severity Staging (IDSA / SHEA 2021)

Disease severity dictates immediate antimicrobial intensity and level of supportive monitoring:

| Clinical Severity Grade | Leukocyte Count (WBC) | Serum Creatinine (sCr) | Hemodynamic & Complication Triggers |
|:---|:---|:---|:---|
| **Non-Severe** | $\le 15.0 \times 10^3/\mu\text{L}$ | $< 1.5\text{ mg/dL}$ (or $< 1.5\times$ baseline) | No hypotension, shock, ileus, or toxic megacolon |
| **Severe** | $> 15.0 \times 10^3/\mu\text{L}$ | $\ge 1.5\text{ mg/dL}$ (or $\ge 1.5\times$ baseline) | No hemodynamic collapse or surgical colonic signs |
| **Fulminant (Severe-Complicated)** | Any value | Any value | Hypotension / shock, vasopressor use, ileus, toxic megacolon, or Serum Lactate $\ge 5.0\text{ mmol/L}$ |

---

## 3. Recurrence Risk Modeling & Mathematical Formulation

Recurrence probability is modeled via a validated multivariable risk scoring system (derived from Garey et al., Hu et al., and IDSA/SHEA clinical trial cohorts), mapped to a calibrated logistic link function.

### Multivariable Weighted Scoring Matrix

| Clinical Factor | Risk Points | Clinical Rationale & Odds Ratio |
|:---|:---:|:---|
| **Age $\ge 65$ years** | $+1.5$ | Microbial senescence, blunted anti-toxin humoral immunity (OR $\approx 2.1$) |
| **Prior CDI: 1 Recurrence** | $+2.5$ | Microbial dysbiosis established; 35–45% baseline relapse rate |
| **Prior CDI: $\ge 2$ Recurrences** | $+4.0$ | Severe mucosal depletion and microbiota loss; $>50\text{–}65\%$ relapse rate |
| **Concomitant Systemic Antibiotics** | $+2.0$ | Active disruption of commensal barrier resistance (OR $\approx 2.5\text{–}3.0$) |
| **Severe / Fulminant Index Episode** | $+1.5$ | Extent of pseudomembranous mucosal destruction |
| **Immunocompromised Host** | $+2.0$ | Deficient Toxin A/B neutralizing IgG antibody synthesis |
| **Proton Pump Inhibitor (PPI) Use** | $+1.0$ | Hypochlorhydria enabling vegetative cell transit |
| **Hypoalbuminemia ($< 3.0\text{ g/dL}$)** | $+1.0$ | Severe inflammation and systemic protein loss |
| **Chronic Kidney Disease (Stage $\ge 3$)** | $+1.0$ | Uremic enteropathy and altered immune defense |
| **Inpatient / LTCF Exposure** | $+1.0$ | Ongoing environmental spore exposure and selective pressure |

### Logistic Calibration Formula

$$\text{Logit}(P) = z = -2.20 + 0.35 \times \text{Score}$$

$$P(\text{Recurrence}) = \frac{1}{1 + e^{-z}}$$

### Stratification Thresholds

```text
+-----------------------+---------------------+-------------------------------+
| Risk Category         | Recurrence Prob (P) | Recommended Clinical Action   |
+-----------------------+---------------------+-------------------------------+
| LOW                   | P < 20%             | Standard fidaxomicin course   |
| MODERATE              | 20% <= P < 35%      | Fidaxomicin + de-escalate abx |
| HIGH                  | 35% <= P < 55%      | Extended fidaxomicin / Bezlo  |
| VERY HIGH             | P >= 55%            | Adjunctive Bezlo / FMT triage |
+-----------------------+---------------------+-------------------------------+
```

---

## 4. Evidence-Based Therapeutic Strategy (IDSA/SHEA & ACG)

```text
+-------------------------------------------------------------------------------+
|                           EPISODE SEVERITY & HISTORY                          |
+-------------------------------------------------------------------------------+
          |                                   |                       |
          v                                   v                       v
    [PRIMARY EPISODE]               [FIRST RECURRENCE]       [MULTIPLE RECURRENCES]
          |                                   |                       |
  +-------+-------+                   +-------+-------+               v
  |               |                   |               |        Post-Antibiotic Lead-In:
  v               v                   v               v        FMT or FDA Live Spores
Non-Severe     Fulminant         Prior Vanc      Prior FDX     (VOWST / REBYOTA)
  |               |                   |               |
Fidaxomicin   PO Vanc 500mg QID   Fidaxomicin    Vanc Taper/
200mg BID     + IV Metro 500mg    Standard /      Pulsed or
x 10 days     TID (+ PR enema)    Ext-Pulsed      Ext-Pulsed
```

### Regimen Specifications

1. **Primary Episode (Non-Severe or Severe):**
   - **Preferred:** Fidaxomicin 200 mg PO BID $\times 10$ days.
   - **Alternative:** Oral Vancomycin 125 mg PO QID $\times 10$ days.
2. **Fulminant Episode:**
   - **Primary:** Vancomycin 500 mg PO/NG QID **PLUS** Metronidazole 500 mg IV Q8H $\times 14$ days.
   - **Ileus Present:** Add Vancomycin retention enema (500 mg in 100 mL NS PR Q6H).
3. **First Recurrence:**
   - If Vancomycin used initially: Fidaxomicin 200 mg BID $\times 10$ days (or extended-pulsed).
   - If Fidaxomicin used initially: Vancomycin tapered & pulsed regimen over 6–8 weeks.
4. **Multiple Recurrences ($\ge 2$ prior episodes):**
   - Standard antimicrobial lead-in followed by **Fecal Microbiota Transplantation (FMT)** or FDA-approved live biotherapeutics (**VOWST** [SER-109] or **REBYOTA** [RBX2660]).

### Bezlotoxumab (ZINPLAVA) Evaluation & Warning

- **Indications:** Single-dose IV infusion ($10\text{ mg/kg}$) during ongoing antimicrobial therapy in patients with high recurrence risk (Age $\ge 65$, Immunocompromised, Severe presentation, or prior episode within 6 months).
- **Contraindications & Warning:** **FDA Black-Box Warning** in patients with a history of **Congestive Heart Failure (CHF)**; reserve only when potential benefit clearly outweighs risk.

---

## 5. Installation & Requirements

Pure Python Standard Library implementation with zero runtime dependencies. `pytest` is required for testing.

```bash
git clone https://github.com/abusuraihsakhri/clostridium-difficile-recurrence-agent.git
cd clostridium-difficile-recurrence-agent
pip install pytest
```

---

## 6. CLI Usage & Quickstart

The CLI supports interactive triage, direct command-line assessment, and batch CSV execution.

### Batch Processing (CSV In / CSV Out)

Evaluate a cohort of clinical cases and export severity, recurrence probability, and regimen recommendations:

```bash
# Using batch subcommand with short options
python cli.py batch -i sample.csv -o out_smoke.csv

# Using batch subcommand with long options
python cli.py batch --input sample.csv --output out_smoke.csv

# Output batch results in JSON format
python cli.py batch -i sample.csv --json
```

### Single Case Direct Evaluation

```bash
python cli.py \
  --patient-id "PT-409" \
  --age 72 \
  --wbc 16.8 \
  --creatinine 1.7 \
  --prior-episodes 1 \
  --concomitant-abx \
  --ppi
```

Output:
```text
================================================================================
CLOSTRIDIOIDES DIFFICILE CLINICAL DECISION SUPPORT REPORT
Patient ID: PT-409               Timestamp UTC: 2026-09-04T03:26:00.000000+00:00
================================================================================

[1] CLINICAL PROFILE & LABORATORY VALUES
  * Age: 72 years | Inpatient/LTCF: Yes
  * WBC Count: 16.8 x 10^3/uL | Serum Creatinine: 1.70 mg/dL (Baseline: N/A)
  * Prior CDI Episodes: 1 (FIRST RECURRENCE)
  * Immunocompromised: No | Concomitant Antibiotics: Yes
  * PPI Use: Yes | Albumin: N/A | CKD: No

[2] IDSA / SHEA 2021 SEVERITY CLASSIFICATION
  * Severity Grade: >>> SEVERE <<<
  * Summary: Severe C. difficile infection: Leukocytosis (WBC 16.8 >= 15.0 x 10^3/uL), Renal impairment (Serum Cr 1.70 mg/dL).

[3] RECURRENCE RISK STRATIFICATION (Multivariable Model)
  * Recurrence Risk Category: >>> VERY_HIGH RISK <<<
  * Multivariable Risk Score: 9.00 points
  * Estimated Probability of Subsequent Recurrence: 72.1%

[4] EVIDENCE-BASED THERAPEUTIC REGIMEN
  * Primary Regimen:     Fidaxomicin Standard or Extended-Pulsed (Preferred)
    Dosage:              200 mg orally BID x 10 days OR 200 mg BID x 5d then QOD x 20d
    Duration:            10 days (Standard) or 25 days (Extended-Pulsed)

[5] ADJUNCTIVE BIOLOGICS & MICROBIOTA RESTORATION
  * Bezlotoxumab (ZINPLAVA) Indicated: YES
    Rationale: Indicated as adjunctive single-dose infusion (10 mg/kg IV)...
  * FMT / Live Biotherapeutic Product Candidacy: NOT CANDIDATE AT PRESENT
```

### Interactive Assessment Mode

Launch an interactive prompt guiding through clinical criteria:

```bash
python cli.py -i
```

---

## 7. CSV Batch Schema

The input CSV requires standard headers matching patient clinical markers:

| Column Header | Type | Valid Values / Units | Description |
|:---|:---:|:---:|:---|
| `patient_id` | `str` | e.g. `PT-101` | Unique case identifier |
| `age` | `int` | Years ($\ge 0$) | Patient age |
| `wbc_count` | `float` | $\times 10^3/\mu\text{L}$ | Peripheral white blood cell count |
| `serum_creatinine` | `float` | $\text{mg/dL}$ | Serum creatinine level |
| `baseline_creatinine` | `float` | $\text{mg/dL}$ / Empty | Prior baseline serum creatinine |
| `prior_cdi_episodes` | `int` | $0, 1, 2+$ | Number of prior verified CDI episodes |
| `concomitant_antibiotics`| `bool` | `true`, `false` | Receiving non-CDI systemic antimicrobials |
| `immunocompromised` | `bool` | `true`, `false` | Chemotherapy, transplant, high-dose steroids |
| `ppi_use` | `bool` | `true`, `false` | Proton pump inhibitor or acid suppression |
| `serum_albumin` | `float` | $\text{g/dL}$ / Empty | Serum albumin level |
| `chronic_kidney_disease` | `bool` | `true`, `false` | CKD Stage $\ge 3$ or eGFR $< 60\text{ mL/min}$ |
| `inpatient_or_nursing_home`| `bool` | `true`, `false` | Inpatient hospital or LTCF residency |
| `hypotension_or_shock` | `bool` | `true`, `false` | SBP $< 90\text{ mmHg}$ or vasopressors |
| `ileus_present` | `bool` | `true`, `false` | Clinical or radiographic ileus |
| `toxic_megacolon` | `bool` | `true`, `false` | Colonic distension $> 6\text{ cm}$ with toxicity |
| `serum_lactate` | `float` | $\text{mmol/L}$ / Empty | Venous/arterial lactic acid level |
| `history_congestive_heart_failure`| `bool` | `true`, `false` | Pre-existing CHF history (Bezlotoxumab warning) |
| `prior_treatment_regimen` | `str` | `vancomycin`, `fidaxomicin`, `none` | Medication used for previous episode |

---

## 8. Verification & Test Suite

The comprehensive pytest suite covers IDSA/SHEA severity cutoffs, multivariable probability calibration, Bezlotoxumab black-box criteria, FMT candidacy, and batch CSV processing.

Run all tests:
```bash
python -m pytest -p no:zarr -v
```

---

## 9. License

Released under the [MIT License](LICENSE).
