# Clostridioides difficile Recurrence & Clinical Severity Engine

An evidence-based clinical decision support system and multivariable risk stratification engine for *Clostridioides* (formerly *Clostridium*) *difficile* infection (CDI). The system operationalizes the **IDSA/SHEA 2021 Clinical Practice Guidelines** and **ACG 2021 Guidelines**, evaluates disease severity, calculates mathematical recurrence probabilities, provides targeted antimicrobial regimens, evaluates Bezlotoxumab (anti-Toxin B mAb) eligibility, and triages patients for Fecal Microbiota Transplantation (FMT) and FDA-approved Live Biotherapeutic Products (LBPs).

---

## 1. Clinical Overview & Problem Space

*Clostridioides difficile* is a spore-forming, toxin-producing anaerobic gram-positive bacillus and the leading cause of healthcare-associated infectious diarrhea. The primary pathophysiology involves:
1. **Antibiotic-Mediated Dysbiosis:** Broad-spectrum antibiotics deplete commensal gut microbiota (notably *Bacteroidetes* and *Firmicutes*), eliminating colonization resistance and allowing *C. diff* spores to germinate.
2. **Toxigenesis:** Vegetative cells produce Toxin A (enterotoxin) and Toxin B (cytotoxin), causing epithelial tight junction disruption, actin depolymerization, pseudomembranous colitis, and fluid secretion.
3. **The Recurrence Cycle:** Following standard antimicrobial therapy, persistent spore reservoirs and delayed microbiome restoration lead to recurrence rates of 15–25% after a primary episode, rising to 40–45% after a first recurrence, and exceeding 60% after multiple recurrences.

---

## 2. Mathematical & Clinical Modeling

### A. IDSA/SHEA Severity Staging
- **Non-Severe:** White Blood Cell (WBC) count $\le 15.0 \times 10^3/\mu\text{L}$ **AND** Serum Creatinine $\le 1.5\text{ mg/dL}$ (or $< 1.5\times$ baseline).
- **Severe:** WBC count $> 15.0 \times 10^3/\mu\text{L}$ **OR** Serum Creatinine $\ge 1.5\text{ mg/dL}$ (or $\ge 1.5\times$ baseline).
- **Fulminant (Severe-Complicated):** Severe CDI complicated by systemic hypotension, vasopressor shock, paralytic ileus, toxic megacolon (colonic diameter $> 6.0\text{ cm}$), or severe lactic acidosis ($\text{Lactate} \ge 5.0\text{ mmol/L}$).

### B. Multivariable Recurrence Risk Model
The recurrence engine calculates a weighted clinical risk score based on validated multivariable clinical prediction rules (Hu et al., Garey et al., IDSA benchmarks):

| Clinical Risk Factor | Assigned Points | Odds Ratio / Clinical Rationale |
| :--- | :---: | :--- |
| **Age $\ge 65$ years** | $+1.5$ | Immunosenescence & altered bile acid metabolism ($\text{OR} \approx 2.1$) |
| **1 Prior CDI Episode** (1st Recurrence) | $+2.5$ | Moderate dysbiosis baseline ($\text{OR} \approx 2.8$) |
| **$\ge 2$ Prior CDI Episodes** (Multiple) | $+4.0$ | Severe microenvironment depletion ($\text{OR} \approx 5.2$) |
| **Concomitant Non-CDI Antibiotics** | $+2.0$ | Continuous suppression of microbiota recovery ($\text{OR} \approx 2.7$) |
| **Severe / Fulminant Index Episode** | $+1.5$ | Extensive mucosal injury and bacterial burden ($\text{OR} \approx 2.0$) |
| **Immunocompromised Host** | $+2.0$ | Impaired anti-toxin A/B IgG humoral response ($\text{OR} \approx 2.5$) |
| **Proton Pump Inhibitor (PPI) Use** | $+1.0$ | Reduced gastric acid barrier ($\text{OR} \approx 1.6$) |
| **Serum Albumin $< 3.0\text{ g/dL}$** | $+1.0$ | Systemic inflammation / nutritional depletion ($\text{OR} \approx 1.5$) |
| **Chronic Kidney Disease (Stage $\ge 3$)** | $+1.0$ | Uremic dysbiosis and immune dysfunction ($\text{OR} \approx 1.6$) |
| **Inpatient / LTCF Exposure** | $+1.0$ | Environmental spore pressure ($\text{OR} \approx 1.4$) |

#### Logistic Probability Transform
The composite score is mapped to a predicted recurrence probability $P(\text{Recurrence})$ via the logistic link:
$$z = -2.20 + 0.35 \times \text{RiskScore}$$
$$P(\text{Recurrence}) = \frac{1}{1 + e^{-z}}$$

#### Risk Tiers
- **Low Risk:** $P < 20\%$ ($\text{Score} < 3.0$)
- **Moderate Risk:** $20\% \le P < 35\%$ ($3.0 \le \text{Score} < 5.0$)
- **High Risk:** $35\% \le P < 55\%$ ($5.0 \le \text{Score} < 7.0$)
- **Very High Risk:** $P \ge 55\%$ ($\text{Score} \ge 7.0$)

---

## 3. Evidence-Based Therapeutic Mapping

### Initial Episode (Primary CDI)
- **Preferred (IDSA/SHEA 2021):** Fidaxomicin $200\text{ mg}$ PO BID $\times 10\text{ days}$.
- **Standard Alternative:** Oral Vancomycin $125\text{ mg}$ PO QID $\times 10\text{ days}$.
- **Fulminant CDI:** High-dose Vancomycin $500\text{ mg}$ PO/NG QID **PLUS** IV Metronidazole $500\text{ mg}$ TID. If ileus is present, administer Vancomycin retention enema ($500\text{ mg}$ in $100\text{ mL}$ normal saline PR Q6H) and request immediate surgical evaluation (diverting loop ileostomy or subtotal colectomy).

### First Recurrence
- If Vancomycin was used initially: **Fidaxomicin** $200\text{ mg}$ BID $\times 10\text{ days}$ OR Extended-Pulsed ($200\text{ mg}$ BID $\times 5\text{ days}$, then QOD $\times 20\text{ days}$).
- If Fidaxomicin was used initially: **Vancomycin Tapered & Pulsed Regimen** ($125\text{ mg}$ QID $\times 10\text{-}14\text{d} \to \text{BID} \times 7\text{d} \to \text{QD} \times 7\text{d} \to 125\text{ mg}$ every $2\text{--}3\text{ days} \times 2\text{-}8\text{ weeks}$).
- **Bezlotoxumab (ZINPLAVA):** $10\text{ mg/kg}$ IV single infusion recommended for patients with high recurrence risk factors (Age $\ge 65$, immunocompromised, severe index, prior recurrence within 6 months). *Caution:* FDA black box warning for congestive heart failure.

### Multiple Recurrences ($\ge 2$ Prior Recurrences)
- **Fecal Microbiota Restoration:** Following an antibiotic lead-in (Vancomycin or Fidaxomicin $\times 10\text{-}14\text{ days}$):
  - **VOWST (SER-109):** FDA-approved oral microbiota spores ($4\text{ capsules}$ QD $\times 3\text{ consecutive days}$).
  - **REBYOTA (RBX2660):** FDA-approved rectally administered microbiota suspension ($150\text{ mL}$ single dose).
  - **Donor FMT:** Colonoscopy or retention enema via authorized stool banking protocols.
- **Alternative:** Vancomycin taper/pulse regimen followed by Rifaximin chaser ($400\text{ mg}$ TID $\times 20\text{ days}$).

---

## 4. Installation & Quick Start

Requires Python 3.9+ (Pure Python standard library; no third-party packages required).

```bash
# Clone the repository
git clone https://github.com/abusuraihsakhri/clostridium-difficile-recurrence-agent.git
cd clostridium-difficile-recurrence-agent

# Execute test suite
python -m unittest test_cdiff_recurrence.py
```

---

## 5. Command-Line Interface (CLI)

### Single Patient Evaluation via CLI Flags
```bash
python cli.py --patient-id PT-001 --age 72 --wbc 18.5 --creatinine 1.9 --prior-episodes 1 --concomitant-abx --ppi
```

### Interactive Decision Support Mode
```bash
python cli.py -i
```

### Batch CSV Processing & JSON Output
```bash
python cli.py --csv sample.csv --json
```

---

## 6. Test Suite & Validation

The test suite in [`test_cdiff_recurrence.py`](file:///C:/Users/abusu/Desktop/Apps-Developed/507-Projects_25Aug/clostridium-difficile-recurrence-agent/test_cdiff_recurrence.py) contains 27 unit tests verifying:
- Non-severe, severe (WBC and Creatinine cutoffs), and fulminant (shock, ileus, megacolon, lactic acidosis) classifications.
- Multivariable recurrence score calculation and logistic probability bounds across low, moderate, high, and very high risk tiers.
- Guideline-adherent primary and alternative therapeutic regimen selection.
- Bezlotoxumab indication logic and black box warning triggers.
- FMT / Live Biotherapeutic Product candidacy qualification.
- Batch CSV parsing and JSON serialization roundtrips.

```bash
python -m unittest test_cdiff_recurrence.py
# Ran 27 tests in 0.019s -> OK
```

---

## 7. License

MIT License. Authored by Dr. Abu Suraih Sakhri.
