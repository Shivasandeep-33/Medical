"""
Utility script to generate sample clinical laboratory PDF reports.
Creates sample PDF files in sample_reports/ directory for drag-and-drop testing.
"""

import os
from reportlab.lib.pagesizes import letter
from reportlab.pdfgen import canvas
from samples import SAMPLE_CASES


def generate_pdf_report(filename: str, title: str, patient_name: str, mrn: str, tests: list, notes: str):
    os.makedirs("sample_reports", exist_ok=True)
    filepath = os.path.join("sample_reports", filename)
    c = canvas.Canvas(filepath, pagesize=letter)
    width, height = letter

    # Header
    c.setFont("Helvetica-Bold", 14)
    c.drawString(50, height - 50, "METROPOLITAN DIAGNOSTIC LABORATORIES")
    c.setFont("Helvetica", 9)
    c.drawString(50, height - 65, "Department of Pathology & Clinical Laboratory Medicine | CLIA # 99D0872134")
    c.drawString(50, height - 78, "Director: Arthur Pendelton, MD, FCAP | 500 Medical Plaza, Suite 400")

    # Divider
    c.setLineWidth(1)
    c.setStrokeColorRGB(0.2, 0.4, 0.6)
    c.line(50, height - 85, width - 50, height - 85)

    # Patient info box
    c.setFont("Helvetica-Bold", 10)
    c.drawString(50, height - 105, "PATIENT INFORMATION:")
    c.setFont("Helvetica", 9)
    c.drawString(50, height - 120, f"Patient Name: {patient_name}")
    c.drawString(240, height - 120, f"MRN: {mrn}")
    c.drawString(380, height - 120, "Date of Service: 09/02/2026")

    c.drawString(50, height - 135, f"Report Title: {title}")
    c.drawString(380, height - 135, "Ordering: Dr. Marcus Sterling, MD")

    # Table Header
    y = height - 165
    c.setFillColorRGB(0.93, 0.95, 0.98)
    c.rect(50, y - 5, width - 100, 18, fill=1, stroke=0)
    c.setFillColorRGB(0, 0, 0)
    c.setFont("Helvetica-Bold", 8.5)
    c.drawString(55, y, "TEST NAME")
    c.drawString(220, y, "RESULT")
    c.drawString(280, y, "UNITS")
    c.drawString(350, y, "REFERENCE RANGE")
    c.drawString(480, y, "FLAG")

    # Table Rows
    y -= 20
    c.setFont("Helvetica", 8.5)
    for t in tests:
        name, val, unit, ref_range, flag = t
        c.drawString(55, y, name)
        c.drawString(220, y, str(val))
        c.drawString(280, y, unit)
        c.drawString(350, y, ref_range)
        if flag:
            c.setFont("Helvetica-Bold", 8.5)
            c.drawString(480, y, flag)
            c.setFont("Helvetica", 8.5)
        y -= 16

    # Clinical notes
    y -= 15
    c.setStrokeColorRGB(0.8, 0.8, 0.8)
    c.line(50, y, width - 50, y)
    y -= 15
    c.setFont("Helvetica-Bold", 9)
    c.drawString(50, y, "CLINICAL INTERPRETATION NOTES:")
    y -= 14
    c.setFont("Helvetica", 8)
    for line in notes.split("\n"):
        if line.strip():
            c.drawString(50, y, line.strip())
            y -= 12

    # Footer
    c.setFont("Helvetica-Oblique", 7.5)
    c.drawString(50, 35, "Confidential Medical Document - Verified Electronic Pathology Signature")
    c.drawString(width - 120, 35, "Page 1 of 1")

    c.save()
    print(f"Generated PDF: {filepath}")


def create_all_sample_pdfs():
    # Case 1
    generate_pdf_report(
        filename="Metabolic_Panel_Vance.pdf",
        title="Comprehensive Metabolic Panel & Glycemic Assessment",
        patient_name="Eleanor Vance",
        mrn="PT-10482",
        tests=[
            ("Fasting Blood Glucose", "142", "mg/dL", "70 - 99", "HIGH"),
            ("Hemoglobin A1c", "7.4", "%", "4.0 - 5.6", "HIGH"),
            ("Serum Creatinine", "0.9", "mg/dL", "0.6 - 1.2", "Normal"),
            ("Blood Urea Nitrogen (BUN)", "16", "mg/dL", "7 - 20", "Normal"),
            ("eGFR Non-African American", "88", "mL/min", "> 60", "Normal"),
            ("Sodium", "139", "mEq/L", "135 - 145", "Normal"),
            ("Potassium", "4.4", "mEq/L", "3.5 - 5.1", "Normal"),
            ("Serum Calcium", "9.4", "mg/dL", "8.5 - 10.2", "Normal"),
            ("ALT (SGPT)", "28", "U/L", "7 - 35", "Normal"),
            ("AST (SGOT)", "24", "U/L", "8 - 35", "Normal"),
            ("Random Urine Protein", "18", "mg/dL", "", "Pending"),
        ],
        notes="Elevated glycemic parameters (Glucose, HbA1c) above source reference range.\nRenal indices and liver transaminases within normal reference limits.\nRandom urine protein has no reference interval assigned on this automated assay."
    )

    # Case 2
    generate_pdf_report(
        filename="Cardio_Lipid_Panel_Thorne.pdf",
        title="Preventive Cardiology Lipid & Inflammatory Profile",
        patient_name="Marcus Thorne",
        mrn="PT-20931",
        tests=[
            ("Total Cholesterol", "228", "mg/dL", "< 200", "HIGH"),
            ("Triglycerides", "210", "mg/dL", "< 150", "HIGH"),
            ("HDL Cholesterol", "38", "mg/dL", "> 40", "LOW"),
            ("LDL Cholesterol (Calc)", "148", "mg/dL", "< 100", "HIGH"),
            ("High Sensitivity CRP", "3.8", "mg/L", "< 1.0", "HIGH"),
            ("Troponin I (High Sens)", "0.01", "ng/mL", "< 0.04", "Normal"),
            ("Serum Potassium", "4.1", "mEq/L", "3.5 - 5.0", "Normal"),
        ],
        notes="Lipid profile demonstrates atherogenic dyslipidemia with elevated LDL and triglycerides.\nHigh sensitivity CRP indicates elevated systemic inflammation above < 1.0 mg/L baseline.\nTroponin I marker within normal baseline threshold."
    )

    # Case 3
    generate_pdf_report(
        filename="CBC_Iron_Study_Chen.pdf",
        title="Complete Blood Count & Iron Deficiency Studies",
        patient_name="Sarah Chen",
        mrn="PT-33019",
        tests=[
            ("White Blood Count (WBC)", "6.8", "K/uL", "4.0 - 11.0", "Normal"),
            ("Red Blood Count (RBC)", "3.4", "M/uL", "4.0 - 5.2", "LOW"),
            ("Hemoglobin", "9.8", "g/dL", "12.0 - 15.5", "LOW"),
            ("Hematocrit", "30.5", "%", "36.0 - 46.0", "LOW"),
            ("MCV", "72", "fL", "80 - 100", "LOW"),
            ("MCH", "23.4", "pg", "27.0 - 33.0", "LOW"),
            ("Platelet Count", "285", "K/uL", "150 - 450", "Normal"),
            ("Serum Ferritin", "8", "ng/mL", "15 - 150", "LOW"),
            ("Serum Iron", "28", "mcg/dL", "50 - 170", "LOW"),
            ("Total Iron Binding (TIBC)", "440", "mcg/dL", "250 - 400", "HIGH"),
        ],
        notes="Microcytic hypochromic red blood cell indices (low MCV, low MCH) with severely reduced ferritin.\nPlatelet and leukocyte counts remain within normal established parameters."
    )


if __name__ == "__main__":
    create_all_sample_pdfs()
