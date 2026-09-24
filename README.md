# C. difficile Recurrence & Severity Tool

A deterministic decision-support tool for adult *Clostridioides difficile* infection (CDI). It classifies disease severity using the IDSA/SHEA adult framework, summarizes guideline-referenced treatment options, and reports a repository-specific recurrence-risk heuristic.

> **Clinical scope:** adults aged 18 years or older. This software is for educational, research, and decision-support use. It does not diagnose CDI, replace clinician assessment, or provide patient-specific prescribing advice.

## Features

- IDSA/SHEA-compatible adult severity classification:
  - non-severe: WBC ≤15,000/µL and serum creatinine <1.5 mg/dL
  - severe: WBC >15,000/µL or serum creatinine ≥1.5 mg/dL
  - fulminant: hypotension/shock, ileus, or toxic megacolon
- Recurrence-risk factor summary and a legacy numeric heuristic retained for compatibility
- Guideline-referenced options for initial CDI, first recurrence, and multiple recurrences
- Bezlotoxumab consideration with the FDA heart-failure warning/precaution
- Fecal microbiota-based therapy triage for recurrent CDI
- Interactive command-line assessment and CSV batch processing
- Static browser interface suitable for GitHub Pages
- Light theme by default with optional dark mode
- No server-side processing and no runtime Python dependencies

## Browser application

Open `index.html` locally in a modern browser, or use the GitHub Pages deployment after it has been enabled for this repository.

The browser implementation uses small ES modules rather than Pyodide. The underlying algorithm is deterministic and uses only standard arithmetic and rules, so a JavaScript mirror avoids the large WebAssembly/Python runtime download while preserving the same classification thresholds and decision-support logic. Browser-engine smoke tests run in CI.

All browser calculations occur locally. The page does not send entered case data to a server. Theme preference is the only value written to browser storage.

## Command-line usage

Python 3.10 or newer is required.

```bash
python cli.py \
  --age 72 \
  --wbc 16.8 \
  --creatinine 1.7 \
  --prior-episodes 1
```

Use `--help` to see all optional clinical-context flags.

### Batch CSV

```bash
python cli.py batch -i sample.csv -o results.csv
```

Required CSV columns are:

```text
patient_id,age,wbc_count,serum_creatinine
```

Optional columns include prior CDI episodes, concomitant antibiotics, immune status, PPI exposure, albumin, CKD, inpatient/LTCF exposure, fulminant criteria, lactate, CHF history, and prior CDI regimen. Boolean fields accept `true/false`, `yes/no`, or `1/0`.

## Recurrence-risk heuristic

The recurrence score and its legacy logistic numeric estimate are **not a validated or calibrated clinical prediction model**. They are retained for backward compatibility and transparent exploration of selected risk factors. Do not interpret the numeric estimate as a patient-specific probability of recurrence.

The tool separates this heuristic from guideline-based severity classification and labels the limitation in CLI/JSON and browser output.

## Development and verification

Install test/build dependencies:

```bash
python -m pip install -e ".[test]"
```

Run the Python suite:

```bash
python -m pytest -p no:zarr -v
```

Run the browser-engine smoke tests:

```bash
node tests/web_engine.test.mjs
```

Build and test the installed console entry point:

```bash
python -m build
python -m pip install --force-reinstall dist/*.whl
clostridium-difficile-recurrence-engine --help
```

CI runs on Python 3.10, 3.11, and 3.12 and performs compilation, tests, package build/install, CLI batch smoke testing, and browser-engine smoke testing.

## Privacy and data handling

The browser app performs calculations entirely on-device and makes no API requests. The CLI processes local arguments/files only. Do not place identifiable patient information in repositories, committed sample files, issue reports, or other shared artifacts.

## Clinical references

- Johnson S, et al. IDSA/SHEA 2021 Focused Update Guidelines on Management of *Clostridioides difficile* Infection in Adults. <https://www.idsociety.org/practice-guideline/clostridioides-difficile-2021-focused-update/>
- McDonald LC, et al. IDSA/SHEA 2017 Clinical Practice Guidelines for *Clostridium difficile* Infection. <https://www.idsociety.org/practice-guideline/clostridium-difficile/>
- Kelly CR, et al. ACG Clinical Guidelines: Prevention, Diagnosis, and Treatment of *Clostridioides difficile* Infections. *Am J Gastroenterol.* 2021;116:1124-1147. <https://pubmed.ncbi.nlm.nih.gov/34003176/>
- American Gastroenterological Association. Fecal microbiota-based therapies for select gastrointestinal diseases. 2024. <https://gastro.org/clinical-guidance/fecal-microbiota-based-therapies-for-select-gastrointestinal-diseases/>
- DailyMed. ZINPLAVA (bezlotoxumab) current U.S. prescribing information. <https://dailymed.nlm.nih.gov/dailymed/drugInfo.cfm?setid=8f479bfe-2bfa-4cc5-9aee-1357364480b0>

## Technology

- Python standard library for the clinical engine and CLI
- Vanilla HTML, CSS, and JavaScript ES modules for the browser interface
- GitHub Actions for test/build verification and GitHub Pages deployment
- No third-party runtime JavaScript packages or remote web assets

Tested CI targets are Python 3.10–3.12. The browser interface targets current Chrome, Firefox, Safari, and Edge.

## License

MIT. See [LICENSE](LICENSE).
