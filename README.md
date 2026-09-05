# MedLens — AI-Powered Clinical Intelligence & Healthcare Portal

An enterprise-grade, full-stack AI healthcare platform that combines:
1. **Patient Information Intake & Clinical History**
2. **Medical Laboratory Report Processing (PDF & Text) with Strict Reference-Range Awareness & Source Provenance**
3. **AI Patient-Friendly Summaries** with clinical safety guardrails (zero definitive diagnoses or unauthorized prescriptions)
4. **User Authentication & Role-Based Access Control** (Patient, Doctor, Admin with 1-click demo accounts)
5. **Integrated Booking System** (Online Teleconsultations with encrypted WebRTC video rooms & In-Person clinic appointments)
6. **Emergency Ambulance Dispatch & Real-Time Telemetry Tracker** (Live GPS ETA, ACLS unit telemetry, paramedic contact, and 911/112 hotline)
7. **AI Symptom-to-Disease Agent & Triage Engine** (60+ clinical conditions, body-system selector, triage urgency indicators)
8. **Automatic Medication Detection & Online Pharmacy Redirection** (Detects tablet/medicine queries in AI chat, provides drug guidance, and automatically redirects to the integrated pharmacy to order)
9. **Clinician Human Verification, Multi-Report Trend Comparison, and Drug-Allergy Conflict Detection**

---

## 🚀 Quick Start

### 1. Requirements
- Python 3.10+ (Verified on Python 3.14 / 3.13)
- No Node.js required! Delivered via FastAPI and high-performance vanilla JavaScript with Tailwind CSS.

### 2. Run the Server
```bash
python app.py
```
Or simply double-click:
`start_app.bat`

Then open your browser at:
**[http://127.0.0.1:8000](http://127.0.0.1:8000)**

---

## 🔑 Demo Accounts (Instant 1-Click Login)

| Role | Email | Password | Linked Demo Profile |
| :--- | :--- | :--- | :--- |
| **Patient** | `patient@medlens.health` | `patient123` | Eleanor Vance (Type 2 Diabetes & Metabolic Panel) |
| **Doctor** | `doctor@medlens.health` | `doctor123` | Dr. Evelyn Reed, MD (Consultant Cardiologist) |
| **Admin** | `admin@medlens.health` | `admin123` | MedLens Clinical Administrator |

*Tip*: You can also switch roles instantly using the **`🩺 Demo Dr.`** and **`👤 Demo Pt.`** buttons in the top navigation header!

---

## 🌟 Core Feature Breakdown

### 1. Structured Clinical Record & Lab Dossier
- **Strict Reference-Range Awareness**: Evaluates `LOW`, `NORMAL`, or `HIGH` strictly using intervals printed in the document. If no reference range is provided in the source report, the status is marked `UNSPECIFIED` (**no standard ranges are ever invented**).
- **Source & Provenance**: Interactive color-coded badges tracing every datum to `User Provided`, `Extracted from Report: [Filename]` (with line snippet), or `AI Generated`.
- **Human Verification & Editing**: Attending clinicians can review and mark lab results as `Verified by Clinician` with audit notes and timestamps.
- **Multi-Report Comparison**: Side-by-side historical comparison view showing baseline vs latest values, delta %, and directional trends (`INCREASED`, `DECREASED`, `STABLE`).
- **Conflict & Inconsistency Detection**: Flags drug-allergy interactions (e.g. Penicillin vs Amoxicillin, Aspirin vs NSAIDs) and critical lab elevations.

### 2. AI Symptom-to-Disease Agent & Clinical Chat
- Evaluates symptoms against a knowledge base of 60+ medical conditions.
- Body-System Interactive Symptom Picker (Head & Brain, Chest & Heart, Abdomen, Muscles & Joints, Systemic).
- 1-Click Clinical Demo Scenarios (Influenza, Suspected Cardiac Emergency, Severe Migraine, Type 2 Diabetes, UTI).
- Multi-turn doctor-agent chat with triage urgency classifications (`ROUTINE`, `MODERATE`, `EMERGENCY RED-FLAG`).

### 3. Automatic Medication Detection & Online Pharmacy Redirection
- When a user asks about tablets or medications (e.g., *Paracetamol*, *Metformin*, *Atorvastatin*, *Amoxicillin*, *Ibuprofen*, *Aspirin*, *Cetirizine*, *Omeprazole*, etc.):
  1. The AI Agent explains indications, standard dosage form, precautions, and prescription requirements.
  2. Renders an interactive **MedLens Pharmacy Card** directly in the chat with 1-click Add-to-Cart.
  3. Displays a floating countdown banner (*"Identified medication: [Name]. Redirecting you to MedLens Online Pharmacy in 2 seconds..."*).
  4. Automatically transitions the UI tab to the **Online Pharmacy**, scrolls to and highlights the target medication with an animated glow ring, and opens the purchase drawer!
- Complete Online Pharmacy store with search, category filtering, cart management, and 1-click checkout with order tracking numbers.

### 4. Integrated Healthcare Booking System
- **Online Teleconsultations**: Directory of 5 specialist doctors (Cardiologist, Endocrinologist, General Physician, Pulmonologist, Neurologist). Generates an encrypted WebRTC video call room link (`https://telehealth.medlens.health/room/BK-XXXXX`) with an interactive video consultation simulator.
- **In-Person Appointments**: Select clinic branch / hospital suite, doctor, date/time slot, and generate appointment passes.
- **My Appointments**: Active bookings manager with cancellation support.

### 5. Emergency Ambulance Dispatch & Live Telemetry Tracker
- High-priority ACLS ambulance request by emergency condition (Cardiac Chest Pain, Severe Respiratory Distress, Stroke, Trauma).
- Pickup address with **"📍 Auto-Fill Current Location"** GPS coordinate pinpointing.
- Real-time dispatch telemetry panel with progress tracker (`1. Dispatched` ➔ `2. En Route` ➔ `3. Arrived`), live ETA countdown, vehicle unit telemetry, paramedic team contact, and direct **911 / 112 hotline** speed dial.

---

## 🧪 Running Automated Tests

Run the complete 24-test automated test suite:

```bash
python -m unittest -v test_app.py test_platform.py
```

### Validation Output:
```
Ran 24 tests in 0.342s
OK (100% Passed)
```

---

## 📁 Repository Structure

```
Medical AI Agent/
├── app.py                     # Unified FastAPI REST backend & static asset server
├── models.py                  # Pydantic schemas (Patient, LabResult, User, Bookings, Ambulance, Pharmacy)
├── pharmacy.py                # Medication catalog, intent parser & auto-redirection engine
├── extractor.py               # PDF parser (pypdf), regex clinical NLP, ref-range evaluator
├── summarizer.py              # Patient-friendly summary generator with clinical safety guardrails
├── storage.py                 # Persistent JSON store with preloaded cases, users, and orders
├── samples.py                 # Synthetic clinical datasets & sample lab reports
├── test_app.py                # Core intake & lab parser test suite (8 tests)
├── test_platform.py           # Integration test suite: Auth, Bookings, Ambulance, Pharmacy (16 tests)
├── start_app.bat              # 1-Click Windows launch script
├── requirements.txt           # Python dependencies
├── data/                      # Persistent storage JSON records
├── sample_reports/            # Ready-to-use sample lab PDF documents
│   ├── Metabolic_Panel_Vance.pdf
│   ├── Cardio_Lipid_Panel_Thorne.pdf
│   └── CBC_Iron_Study_Chen.pdf
└── static/
    ├── index.html             # Responsive clinical portal UI (Tailwind CSS, Lucide Icons)
    ├── app.js                 # Frontend state, chat triage, pharmacy redirect & booking logic
    └── style.css              # Custom styling, siren animations, provenance badges, print styles
```
