# MediSync AI — Clinical Record & Report Processing System

An AI-powered, full-stack clinical intelligence application that collects patient information, ingests diagnostic laboratory reports (PDF or text), organizes findings into a structured medical record with strict reference-range awareness, tracks provenance, and generates patient-friendly clinical summaries without diagnostic or prescribing claims.

---

## 🚀 Quick Start Guide

### 1. Requirements
- Python 3.10+ (Tested and verified on Python 3.14 / 3.13)
- No Node.js required! The single-page frontend is delivered directly by FastAPI.

### 2. Run the Application
In your terminal, navigate to the project root and execute:

```bash
python app.py
```

Then open your browser and navigate to:
**[http://127.0.0.1:8000](http://127.0.0.1:8000)**

---

## 🎯 Core Requirements & Implementation Highlights

| Requirement | Implementation in MediSync AI |
| :--- | :--- |
| **1. Patient Information Intake** | Multi-section intake form capturing demographics (Name, Age, Sex, DOB, Blood Type, Contact, Emergency Contact), dynamic symptoms (Severity, Duration, Notes), active medications, allergies with reactions, conditions, and surgeries. |
| **2. Medical Report Processing** | Ingests PDF or raw clinical text reports. Extracts test names, values, units, reference intervals, collection dates, and observations using dual-engine parser (Clinical NLP regex or Google Gemini AI). |
| **3. Structured Medical Record** | Unified patient dossier categorizing tests into clinical domains (Hematology, Metabolic, Lipids, Renal, Hepatic, etc.), alongside clinical intake data and out-of-range critical alerts. |
| **4. Reference-Range Awareness** | **Strict Guarantee**: The system strictly uses reference ranges printed in the source report. It evaluates `LOW`, `NORMAL`, `HIGH`. If no range exists in the document, it explicitly flags `Not specified in report` (Status: `UNSPECIFIED`) and **never invents standard ranges**. |
| **5. Source & Provenance** | Interactive color-coded badges and citation modal: <br>• 👤 `User Provided` (Intake fields)<br>• 📄 `Extracted from Report: [Filename]` (with exact raw line snippet and page number)<br>• 🤖 `AI Generated` (Summary narrative) |
| **6. AI-Powered Summary** | Synthesizes patient-friendly narrative, key highlights, lay explanations of out-of-range findings, and suggested questions to discuss with their physician. Follows strict safety guardrails: **zero medical diagnosis or prescriptive advice**. |

---

## 🧪 Preloaded Clinical Demo Cases & Sample PDFs

For instant 1-click evaluation, the application includes 3 realistic preloaded cases accessible via the **"Demo Cases"** button in the top navigation:

1. **Case 1: Eleanor Vance (54F)** — *Type 2 Diabetes & Comprehensive Metabolic Panel*
   - Elevated Glucose (142 mg/dL) and HbA1c (7.4%).
   - Demonstrates reference-range awareness via an un-ranged Urine Protein test (marked `Not specified in report`).
2. **Case 2: Marcus Thorne (47M)** — *Cardiovascular & Lipid Risk Assessment*
   - Elevated Total Cholesterol, high LDL, low HDL, elevated hs-CRP, normal Troponin I.
3. **Case 3: Sarah Chen (29F)** — *Hematology & Iron Deficiency Profile*
   - Microcytic hypochromic indices (low Hemoglobin 9.8 g/dL, low Hematocrit, low Ferritin 8 ng/mL, high TIBC).

### Testing PDF Upload:
Realistic PDF lab reports are pre-generated in the `sample_reports/` directory:
- `sample_reports/Metabolic_Panel_Vance.pdf`
- `sample_reports/Cardio_Lipid_Panel_Thorne.pdf`
- `sample_reports/CBC_Iron_Study_Chen.pdf`

You can drag and drop any of these directly onto the **"Upload & Process Report"** tab!

---

## ⚙️ Architecture & File Structure

```
Medical ai agent/
├── app.py                     # FastAPI REST API, report endpoints, static file mounting
├── models.py                  # Pydantic schemas (Patient, LabResult, StructuredRecord, Provenance)
├── extractor.py               # PDF parser (pypdf), regex clinical NLP, ref-range evaluator, Gemini API
├── summarizer.py              # Patient-friendly summary generator with clinical safety guardrails
├── storage.py                 # Persistent JSON store with preloaded sample records
├── samples.py                 # Synthetic clinical datasets & sample lab reports
├── create_sample_pdfs.py      # Utility script to generate sample clinical PDFs
├── test_app.py                # Automated test suite (8 unit & integration tests)
├── requirements.txt           # Python dependencies
├── sample_reports/            # Ready-to-use sample lab PDF documents
│   ├── Metabolic_Panel_Vance.pdf
│   ├── Cardio_Lipid_Panel_Thorne.pdf
│   └── CBC_Iron_Study_Chen.pdf
└── static/
    ├── index.html             # Responsive clinical dashboard UI (Tailwind CSS, Lucide Icons)
    ├── app.js                 # Reactive frontend logic, state management, API calls
    └── style.css              # Custom styling, provenance badges, print styles
```

---

## 🛡️ Optional Google Gemini AI Integration

The application works 100% offline out-of-the-box using the built-in deterministic clinical NLP parser.

If you wish to enable Google Gemini AI:
1. Click the **Settings (gear icon)** in the top navigation bar.
2. Enter your **Google Gemini API Key**.
3. The system will use Gemini 2.5 Flash for advanced structured extraction and summary synthesis while strictly maintaining source reference range validation and provenance citations.

---

## 🧪 Running Automated Tests

Run the automated test suite with:

```bash
python -m unittest test_app.py -v
```
