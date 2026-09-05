"""
Comprehensive Unit & Integration Test Suite for MediSync AI.
Validates:
1. Patient Intake data structures and User-Provided provenance.
2. Medical Report Processing (PDF and text).
3. Reference-Range Awareness (Low, Normal, High, and Unspecified / No Invented Ranges).
4. Provenance tracking and snippet citations.
5. AI Summary generation with safety guardrails.
"""

import unittest
from fastapi.testclient import TestClient

from app import app
from extractor import (
    parse_reference_range,
    evaluate_value_against_range,
    parse_lab_report_deterministic,
    determine_category,
)
from models import ValueStatus, ProvenanceType
from summarizer import generate_deterministic_summary
from storage import store


class TestMedicalAIAgent(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.client = TestClient(app)

    def test_health_check(self):
        response = self.client.get("/api/health")
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertEqual(data["status"], "ok")
        self.assertGreaterEqual(data["total_records"], 1)

    def test_sample_cases_endpoint(self):
        response = self.client.get("/api/samples")
        self.assertEqual(response.status_code, 200)
        samples = response.json()
        self.assertGreaterEqual(len(samples), 3)
        sample_keys = [s["key"] for s in samples]
        self.assertIn("case_1_diabetes", sample_keys)
        self.assertIn("case_2_cardiac", sample_keys)
        self.assertIn("case_3_hematology", sample_keys)

    def test_reference_range_parsing(self):
        # Between range
        low, high, text = parse_reference_range("70 - 99")
        self.assertEqual(low, 70.0)
        self.assertEqual(high, 99.0)
        self.assertIsNone(text)

        # Less than range
        low, high, text = parse_reference_range("< 200")
        self.assertIsNone(low)
        self.assertEqual(high, 200.0)

        # Greater than range
        low, high, text = parse_reference_range("> 60")
        self.assertEqual(low, 60.0)
        self.assertIsNone(high)

        # Empty / unspecified range (MUST NOT INVENT)
        low, high, text = parse_reference_range(None)
        self.assertIsNone(low)
        self.assertIsNone(high)
        self.assertIsNone(text)

        low, high, text = parse_reference_range("Not Provided")
        self.assertIsNone(low)
        self.assertIsNone(high)
        self.assertIsNone(text)

    def test_reference_range_awareness_evaluation(self):
        # Case 1: Within normal range
        status, reason = evaluate_value_against_range(
            value_str="85",
            ref_low=70.0,
            ref_high=99.0,
            ref_textual=None,
            has_range_in_source=True,
            unit="mg/dL"
        )
        self.assertEqual(status, ValueStatus.NORMAL)

        # Case 2: Above normal range (HIGH)
        status, reason = evaluate_value_against_range(
            value_str="142",
            ref_low=70.0,
            ref_high=99.0,
            ref_textual=None,
            has_range_in_source=True,
            unit="mg/dL"
        )
        self.assertEqual(status, ValueStatus.HIGH)
        self.assertIn("above source reference range", reason)

        # Case 3: Below normal range (LOW)
        status, reason = evaluate_value_against_range(
            value_str="9.5",
            ref_low=12.0,
            ref_high=15.5,
            ref_textual=None,
            has_range_in_source=True,
            unit="g/dL"
        )
        self.assertEqual(status, ValueStatus.LOW)
        self.assertIn("below source reference range", reason)

        # Case 4: No range in source (CRITICAL: system MUST NOT invent ranges)
        status, reason = evaluate_value_against_range(
            value_str="18",
            ref_low=None,
            ref_high=None,
            ref_textual=None,
            has_range_in_source=False,
            unit="mg/dL"
        )
        self.assertEqual(status, ValueStatus.UNSPECIFIED)
        self.assertIn("No reference range specified in source report", reason)

    def test_deterministic_report_parser(self):
        report_text = """
METROPOLITAN CLINICAL LABS
Collection Date: 09/01/2026

TEST NAME                    RESULT   UNITS      REFERENCE INTERVAL   STATUS
Fasting Blood Glucose        135      mg/dL      70 - 99              HIGH
Total Cholesterol            220      mg/dL      < 200                HIGH
HDL Cholesterol              35       mg/dL      > 40                 LOW
Serum Creatinine             0.9      mg/dL      0.6 - 1.2            Normal
Serum Ferritin               8        ng/mL      15 - 150             LOW
Random Urine Protein         14       mg/dL                           Pending
"""
        results = parse_lab_report_deterministic(report_text, source_filename="TestLab.txt", page_num=1)
        self.assertGreaterEqual(len(results), 5)

        results_by_name = {r.test_name.lower(): r for r in results}

        # Verify Glucose is HIGH
        glucose = results_by_name.get("fasting blood glucose")
        self.assertIsNotNone(glucose)
        self.assertEqual(glucose.status, ValueStatus.HIGH)
        self.assertEqual(glucose.numeric_value, 135.0)
        self.assertEqual(glucose.unit, "mg/dL")
        self.assertEqual(glucose.provenance.source_type, ProvenanceType.REPORT_EXTRACTED)
        self.assertEqual(glucose.provenance.source_name, "TestLab.txt")

        # Verify Creatinine is NORMAL
        creat = results_by_name.get("serum creatinine")
        self.assertIsNotNone(creat)
        self.assertEqual(creat.status, ValueStatus.NORMAL)

        # Verify Ferritin is LOW
        ferritin = results_by_name.get("serum ferritin")
        self.assertIsNotNone(ferritin)
        self.assertEqual(ferritin.status, ValueStatus.LOW)

        # Verify Urine Protein has NO hallucinated reference range
        urine = results_by_name.get("random urine protein")
        self.assertIsNotNone(urine)
        self.assertEqual(urine.status, ValueStatus.UNSPECIFIED)
        self.assertIn("Not specified in report", urine.reference_range_raw)

    def test_patient_intake_api(self):
        payload = {
            "patient_id": "TEST-PT-999",
            "full_name": "Alexander Hayes",
            "age": 42,
            "sex": "Male",
            "dob": "1984-06-12",
            "blood_type": "O+",
            "contact_phone": "+1 555 123 4567",
            "emergency_contact": "Claire Hayes (Spouse)",
            "symptoms": [
                {"name": "Frequent Headaches", "severity": "Moderate", "duration": "1 week", "notes": "Frontal throbbing"}
            ],
            "existing_conditions": [
                {"condition_name": "Mild Hypertension", "diagnosed_year_or_date": "2020", "status": "Active"}
            ],
            "medications": [
                {"name": "Amlodipine", "dosage": "5 mg", "frequency": "Daily", "purpose": "Blood pressure"}
            ],
            "allergies": [
                {"allergen": "Sulfa", "reaction": "Rash", "severity": "Mild"}
            ]
        }

        response = self.client.post("/api/records/patient", json=payload)
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertEqual(data["record_id"], "test-pt-999")
        self.assertEqual(data["patient"]["full_name"], "Alexander Hayes")
        self.assertEqual(data["patient"]["provenance"]["source_type"], "User Provided")

        # Retrieve through GET
        get_res = self.client.get("/api/records/test-pt-999")
        self.assertEqual(get_res.status_code, 200)
        self.assertEqual(get_res.json()["patient"]["age"], 42)

    def test_paste_report_api(self):
        # Ensure patient exists
        self.client.post("/api/records/patient", json={
            "patient_id": "test-paste-patient",
            "full_name": "Test Paste User",
            "age": 35
        })

        report_text = """
CITY HEALTH LAB
TEST NAME                    RESULT   UNITS      REFERENCE INTERVAL
Hemoglobin                   10.5     g/dL       12.0 - 16.0
White Blood Count            7.5      K/uL       4.0 - 11.0
"""
        response = self.client.post(
            "/api/records/test-paste-patient/paste_report",
            json={"text": report_text, "filename": "City_Health_Report.txt"}
        )
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertEqual(data["status"], "success")
        self.assertEqual(data["tests_extracted"], 2)

        # Check that record summary was regenerated and contains questions for doctor
        record = self.client.get("/api/records/test-paste-patient").json()
        self.assertIsNotNone(record["summary"])
        self.assertIn("IMPORTANT MEDICAL DISCLAIMER", record["summary"]["disclaimer"])
        self.assertGreaterEqual(len(record["summary"]["questions_for_doctor"]), 1)

    def test_pdf_upload_api(self):
        import os, uuid
        pdf_path = os.path.join("sample_reports", "Metabolic_Panel_Vance.pdf")
        self.assertTrue(os.path.exists(pdf_path), "Sample PDF should exist")

        pid = f"pdf-test-{uuid.uuid4().hex[:6]}"

        # Create patient
        self.client.post("/api/records/patient", json={
            "patient_id": pid,
            "full_name": "Eleanor Vance PDF",
            "age": 54
        })

        with open(pdf_path, "rb") as f:
            files = {"file": ("Metabolic_Panel_Vance.pdf", f, "application/pdf")}
            response = self.client.post(
                f"/api/records/{pid}/upload_report",
                files=files
            )

        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertEqual(data["status"], "success")
        self.assertGreaterEqual(data["tests_extracted"], 5)
        self.assertEqual(data["filename"], "Metabolic_Panel_Vance.pdf")

        # Verify extracted record
        rec = self.client.get(f"/api/records/{pid}").json()
        self.assertEqual(len(rec["reports"]), 1)
        test_names = [t["test_name"].lower() for t in rec["all_lab_results"]]
        self.assertTrue(any("glucose" in n for n in test_names))

        # Cleanup
        self.client.delete(f"/api/records/{pid}")


if __name__ == "__main__":
    unittest.main()
