# Clostridium Difficile Recurrence Agent

> **Domain:** Clinical Decision Support & Biomedical Computing  
> **Reference Guidelines & Standards:** `Standard Clinical Formulations & ISO/IEC Quality Frameworks`

<div align="center">

[![License: MIT](https://img.shields.io/badge/License-MIT-blue.svg)](LICENSE)
![Python](https://img.shields.io/badge/Python-3.10%20%7C%203.11%20%7C%203.12-3776AB.svg?logo=python&logoColor=white)
![FastAPI](https://img.shields.io/badge/FastAPI-0.111-009688.svg?logo=fastapi&logoColor=white)
![Audit Trail](https://img.shields.io/badge/Audit-HMAC--SHA256_Tamper--Evident-brightgreen.svg)
![Zero-PHI Guard](https://img.shields.io/badge/Guard-Zero--PHI_Outbound-blue.svg)
![Docker](https://img.shields.io/badge/Docker-Ready-2496ED.svg?logo=docker&logoColor=white)

</div>

---

## 📖 What It Does

**Clostridium Difficile Recurrence Agent** is an advanced analytical and computational platform implementing SHEA/IDSA Staging, Fidaxomicin & FMT Candidate Evaluator.

---

## ⚙️ Key Capabilities & Algorithmic Modules

### 🔬 Core Algorithmic & Evaluation Engines

- **`PatientInput`**: Input clinical parameters for C. difficile assessment.
- **`SeverityAssessment`**: Clinical severity classification per IDSA/SHEA & ACG criteria.
- **`RecurrenceRiskAssessment`**: Multivariable risk score and statistical probability of recurrence.
- **`TreatmentGuidelineRecommendation`**: Evidence-based clinical therapeutics and regimen options.
- **`AssessmentReport`**: Unified comprehensive CDI clinical report.
- **`CDiffRecurrenceEngine`**: Core algorithmic engine for C. difficile severity classification,
recurrence risk calculation, and guideline-adherent therapeutic mapping.

---

## 📐 Mathematical Formulation & Logic

```text
  score = 0.0
  Calculate logistic probability
  risk = cls.calculate_recurrence_risk(patient, sev)
```

---

## 💻 CLI Quickstart & Usage

### 1. Guided Interactive Mode
```bash
python cli.py
```

### 2. Direct Parameterized Evaluation
```bash
python cli.py --- <value> --interactive <value> --json <value> --csv <value>
```

### Parameter Reference
- `---`: Specifies input measurement or parameter value.
- `--interactive`: Specifies input measurement or parameter value.
- `--json`: Specifies input measurement or parameter value.
- `--csv`: Specifies input measurement or parameter value.
- `--patient-id`: Specifies input measurement or parameter value.
- `--age`: Specifies input measurement or parameter value.
- `--wbc`: Specifies input measurement or parameter value.
- `--creatinine`: Specifies input measurement or parameter value.
- `--baseline-creatinine`: Specifies input measurement or parameter value.
- `--prior-episodes`: Specifies input measurement or parameter value.

### Input Data Schema

| Field | Description | Requirement |
|:------|:------------|:------------|
| `patient_id` | Parameter / observation metric | Required |
| `age` | Parameter / observation metric | Required |
| `wbc_count` | Parameter / observation metric | Required |
| `serum_creatinine` | Parameter / observation metric | Required |
| `baseline_creatinine` | Parameter / observation metric | Required |
| `prior_cdi_episodes` | Parameter / observation metric | Required |
| `concomitant_antibiotics` | Parameter / observation metric | Required |
| `immunocompromised` | Parameter / observation metric | Required |

---

## 🛡️ Security & Enterprise Architecture

* **Zero-PHI Outbound Interceptor:** Active AST and regex inspection blocking SSNs, MRNs, phone numbers, and patient identifiers.
* **Tamper-Evident HMAC-SHA256 Audit Trail:** Chained, cryptographically signed logs for every evaluation and state transition.
* **Air-Gapped LLM Reasoning Adapter:** Agnostic integration for local Ollama instances (`llama3`, `mistral`), Claude 3.5 Sonnet, GPT-4o, and deterministic test mocks.
* **Active Learning Bayesian Calibration:** Dynamic tracker updating worker reliability weights and monitoring Brier calibration drift.
* **FastAPI & Prometheus Telemetry:** Exposes OpenAPI 3.1 REST endpoints and operational Prometheus metrics (`/metrics`).

---

## 🧪 Testing & Verification

Run the automated test suite:

```bash
pytest -v
```

Execute high-throughput batch simulation benchmarks:

```bash
python simulator.py --tasks 1000 --concurrency 8
```

---

## 🐳 Container Deployment

```bash
docker build -t clostridium-difficile-recurrence-agent .
docker run -p 8000:8000 clostridium-difficile-recurrence-agent
```
