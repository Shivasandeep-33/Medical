"""
Sample medical cases and synthetic lab reports for 1-click demonstration.
Allows instant testing of patient intake, report processing, reference-range awareness,
provenance tracking, and AI summary generation.
"""

from typing import Dict, Any

SAMPLE_CASES: Dict[str, Dict[str, Any]] = {
    "case_1_diabetes": {
        "title": "Case 1: Type 2 Diabetes & Metabolic Follow-Up",
        "description": "54-year-old female with elevated fasting blood sugar, high HbA1c, and an un-ranged urine protein test illustrating strict reference-range awareness.",
        "patient": {
            "patient_id": "PT-10482",
            "full_name": "Eleanor Vance",
            "age": 54,
            "sex": "Female",
            "dob": "1972-04-18",
            "blood_type": "A+",
            "contact_phone": "+1 (555) 234-8901",
            "emergency_contact": "David Vance (Spouse) - +1 (555) 234-8902",
            "symptoms": [
                {"name": "Persistent daytime fatigue", "severity": "Moderate", "duration": "3 weeks", "notes": "Worse in late afternoons"},
                {"name": "Increased thirst (polydipsia)", "severity": "Mild", "duration": "1 month", "notes": "Drinking > 3L water daily"},
                {"name": "Mild blurred vision", "severity": "Mild", "duration": "10 days", "notes": "Occasional screen reading difficulty"}
            ],
            "existing_conditions": [
                {"condition_name": "Type 2 Diabetes Mellitus", "diagnosed_year_or_date": "2019", "status": "Active"},
                {"condition_name": "Essential Hypertension", "diagnosed_year_or_date": "2017", "status": "Active"}
            ],
            "allergies": [
                {"allergen": "Sulfa drugs", "reaction": "Cutaneous maculopapular rash", "severity": "Moderate"},
                {"allergen": "Latex", "reaction": "Contact dermatitis", "severity": "Mild"}
            ],
            "medications": [
                {"name": "Metformin", "dosage": "850 mg", "frequency": "Twice daily with meals", "purpose": "Glycemic control"},
                {"name": "Lisinopril", "dosage": "10 mg", "frequency": "Once daily in morning", "purpose": "Blood pressure management"},
                {"name": "Omega-3 Fish Oil", "dosage": "1000 mg", "frequency": "Once daily", "purpose": "General heart wellness"}
            ],
            "surgical_history": ["Laparoscopic cholecystectomy (2015)"],
            "lifestyle_notes": "Sedentary desk job, walks 20 minutes on weekends. Non-smoker, occasional social wine."
        },
        "report_filename": "Metabolic_Panel_Vance.txt",
        "report_text": """METROPOLITAN DIAGNOSTIC LABORATORIES
Clinical Chemistry & Endocrinology Division
Accredited CAP / CLIA # 99D0872134
Director: Arthur Pendelton, MD, FCAP

PATIENT INFORMATION:
Patient Name: Eleanor Vance
DOB: 04/18/1972 (Age: 54)     Sex: Female
MRN: 88471923               Date of Service: 09/02/2026
Ordering Physician: Dr. Marcus Sterling, MD (Endocrinology)

=========================================================================================
TEST NAME                    RESULT   UNITS      REFERENCE INTERVAL   STATUS / FLAG
=========================================================================================
Fasting Blood Glucose        142      mg/dL      70 - 99              HIGH
Hemoglobin A1c               7.4      %          4.0 - 5.6            HIGH
Serum Creatinine             0.9      mg/dL      0.6 - 1.2            Normal
Blood Urea Nitrogen (BUN)    16       mg/dL      7 - 20               Normal
eGFR Non-African American    88       mL/min     > 60                 Normal
Sodium                       139      mEq/L      135 - 145            Normal
Potassium                    4.4      mEq/L      3.5 - 5.1            Normal
Chloride                     102      mEq/L      96 - 106             Normal
Carbon Dioxide (CO2)         24       mEq/L      22 - 29              Normal
Serum Calcium                9.4      mg/dL      8.5 - 10.2           Normal
Total Protein                7.1      g/dL       6.0 - 8.3            Normal
Serum Albumin                4.3      g/dL       3.5 - 5.0            Normal
Total Bilirubin              0.7      mg/dL      0.2 - 1.2            Normal
Alkaline Phosphatase         78       U/L        44 - 121             Normal
ALT (SGPT)                   28       U/L        7 - 35               Normal
AST (SGOT)                   24       U/L        8 - 35               Normal
Random Urine Protein         18       mg/dL                           [Pending range verification]
=========================================================================================
CLINICAL INTERPRETATION NOTES:
- Glycemic parameters (Fasting Glucose and HbA1c) are above the source reference range.
- Renal panel (Creatinine, BUN, eGFR) and hepatic transaminases remain within normal reference limits.
- Urine protein test did not include an established laboratory reference range in this automated run.
"""
    },

    "case_2_cardiac": {
        "title": "Case 2: Cardiac & Lipid Risk Assessment",
        "description": "47-year-old male with borderline blood pressure, exertion chest tightness, elevated LDL cholesterol, and high triglycerides.",
        "patient": {
            "patient_id": "PT-20931",
            "full_name": "Marcus Thorne",
            "age": 47,
            "sex": "Male",
            "dob": "1979-11-03",
            "blood_type": "O+",
            "contact_phone": "+1 (555) 782-4412",
            "emergency_contact": "Elena Thorne (Sister) - +1 (555) 782-4419",
            "symptoms": [
                {"name": "Substernal chest tightness on stairs", "severity": "Moderate", "duration": "2 weeks", "notes": "Relieves upon resting within 3 minutes"},
                {"name": "Shortness of breath on brisk walking", "severity": "Mild", "duration": "1 month", "notes": "Gradually noticeable over the last month"}
            ],
            "existing_conditions": [
                {"condition_name": "Hypercholesterolemia", "diagnosed_year_or_date": "2021", "status": "Active"},
                {"condition_name": "Borderline Pre-hypertension", "diagnosed_year_or_date": "2023", "status": "Active"}
            ],
            "allergies": [
                {"allergen": "Penicillin", "reaction": "Hives and facial swelling (angioedema)", "severity": "Severe"}
            ],
            "medications": [
                {"name": "Atorvastatin", "dosage": "20 mg", "frequency": "Once daily at bedtime", "purpose": "Cholesterol reduction"},
                {"name": "Baby Aspirin", "dosage": "81 mg", "frequency": "Once daily with food", "purpose": "Cardiovascular prophylaxis"}
            ],
            "surgical_history": ["Right knee arthroscopy (2018)"],
            "lifestyle_notes": "High stress managerial role, travels frequently, diet contains frequent restaurant meals."
        },
        "report_filename": "Cardio_Lipid_Panel_Thorne.txt",
        "report_text": """APEX CARDIOLOGY & METABOLIC INSTITUTE
Division of Preventive Cardiology
Lab Accession: APX-994012    Date: 08/28/2026

PATIENT DETAILS:
Name: Marcus Thorne     Age: 47     Sex: Male
Referring Cardiologist: Dr. Helena Vance, MD, FACC

=========================================================================================
TEST NAME                    RESULT   UNITS      REFERENCE INTERVAL   STATUS / FLAG
=========================================================================================
Total Cholesterol            228      mg/dL      < 200                HIGH
Triglycerides                210      mg/dL      < 150                HIGH
HDL Cholesterol              38       mg/dL      > 40                 LOW
LDL Cholesterol (Calc)       148      mg/dL      < 100                HIGH
Non-HDL Cholesterol          190      mg/dL      < 130                HIGH
Cholesterol/HDL Ratio        6.0      ratio      < 5.0                HIGH
High Sensitivity CRP         3.8      mg/L       < 1.0                HIGH
Troponin I (High Sens)       0.01     ng/mL      < 0.04               Normal
Brain Natriuretic Peptide    42       pg/mL      < 100                Normal
Serum Potassium              4.1      mEq/L      3.5 - 5.0            Normal
=========================================================================================
LABORATORY REMARKS:
- Lipid profile demonstrates atherogenic dyslipidemia with elevated LDL, elevated Triglycerides, and sub-optimal HDL.
- High-sensitivity CRP is elevated above standard baseline threshold (< 1.0 mg/L).
- Cardiac necrosis marker (Troponin I) is within normal reference limits.
"""
    },

    "case_3_hematology": {
        "title": "Case 3: Hematology & Iron Deficiency Profile",
        "description": "29-year-old female presenting with severe fatigue, pale conjunctiva, low hemoglobin, and depleted ferritin stores.",
        "patient": {
            "patient_id": "PT-33019",
            "full_name": "Sarah Chen",
            "age": 29,
            "sex": "Female",
            "dob": "1997-07-22",
            "blood_type": "B+",
            "contact_phone": "+1 (555) 349-1120",
            "emergency_contact": "Kevin Chen (Brother) - +1 (555) 349-1122",
            "symptoms": [
                {"name": "Severe chronic fatigue", "severity": "Severe", "duration": "2 months", "notes": "Impacting ability to exercise or focus"},
                {"name": "Lightheadedness on standing", "severity": "Moderate", "duration": "3 weeks", "notes": "Postural dizziness"},
                {"name": "Cold extremities / Brittle nails", "severity": "Mild", "duration": "Ongoing", "notes": "Noticeable spooning appearance on fingernails"}
            ],
            "existing_conditions": [
                {"condition_name": "Heavy Menstrual Bleeding (Menorrhagia)", "diagnosed_year_or_date": "2022", "status": "Active"}
            ],
            "allergies": [
                {"allergen": "Ibuprofen / NSAIDs", "reaction": "Gastric pain and heartburn", "severity": "Moderate"}
            ],
            "medications": [
                {"name": "Women's Daily Multivitamin", "dosage": "1 tablet", "frequency": "Once daily", "purpose": "Nutritional supplement"}
            ],
            "surgical_history": ["Wisdom teeth extraction (2016)"],
            "lifestyle_notes": "Vegetarian diet for 5 years, desk worker, exercises occasionally."
        },
        "report_filename": "CBC_Iron_Study_Chen.txt",
        "report_text": """BIO-PATH DIAGNOSTICS LABORATORY
Comprehensive Hematology Section
Collection Date: 09/01/2026

PATIENT DEMOGRAPHICS:
Patient: Sarah Chen     Age: 29     Gender: Female
Specimen: Whole Blood EDTA / Serum     Accession: BPD-772183

=========================================================================================
TEST NAME                    RESULT   UNITS      REFERENCE INTERVAL   STATUS / FLAG
=========================================================================================
White Blood Count (WBC)      6.8      K/uL       4.0 - 11.0           Normal
Red Blood Count (RBC)        3.4      M/uL       4.0 - 5.2            LOW
Hemoglobin                   9.8      g/dL       12.0 - 15.5          LOW
Hematocrit                   30.5     %          36.0 - 46.0          LOW
MCV                          72       fL         80 - 100             LOW
MCH                          23.4     pg         27.0 - 33.0          LOW
MCHC                         30.2     g/dL       32.0 - 36.0          LOW
RDW                          17.2     %          11.5 - 14.5          HIGH
Platelet Count               285      K/uL       150 - 450            Normal
Serum Ferritin               8        ng/mL      15 - 150             LOW
Serum Iron                   28       mcg/dL     50 - 170             LOW
Total Iron Binding (TIBC)    440      mcg/dL     250 - 400            HIGH
Transferrin Saturation       6.4      %          15.0 - 50.0          LOW
Vitamin B12                  480      pg/mL      200 - 900            Normal
=========================================================================================
PATHOLOGIST OBSERVATIONS:
- Microcytic hypochromic red blood cell indices (low MCV, low MCH) consistent with marked iron depletion.
- Platelet count and leukocyte counts are within normal limits.
"""
    }
}
