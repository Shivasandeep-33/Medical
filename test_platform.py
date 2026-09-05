"""
Integration and Functional Test Suite for MedLens Healthcare Platform.
Tests:
1. User Authentication (Register, Login, Demo Accounts)
2. Healthcare Consultation Bookings (Online & In-Person)
3. Emergency Ambulance Dispatch & Real-Time Telemetry Tracking
4. AI Symptom-to-Disease Inference & Emergency Red-Flag Triage
5. Automatic Tablet/Medication Detection & Online Pharmacy Redirection
6. Online Pharmacy Catalog, Cart & Checkout
7. Advanced Clinical Intelligence (Human Verification, Comparison, Conflict Detection)
"""

import unittest
from fastapi.testclient import TestClient
from app import app
from models import ValueStatus, BookingType, BookingStatus, AmbulanceStatus


class TestMedLensPlatform(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.client = TestClient(app)

    # -----------------------------------------------------------------
    # 1. USER AUTHENTICATION & ACCESS CONTROL
    # -----------------------------------------------------------------
    def test_demo_login_patient_and_doctor(self):
        # Demo login as Patient
        resp = self.client.post("/api/auth/demo-login", json={"account_type": "patient"})
        self.assertEqual(resp.status_code, 200)
        data = resp.json()
        self.assertEqual(data["status"], "success")
        self.assertEqual(data["user"]["role"], "PATIENT")
        self.assertIn("Eleanor", data["user"]["full_name"])

        # Demo login as Doctor
        resp_doc = self.client.post("/api/auth/demo-login", json={"account_type": "doctor"})
        self.assertEqual(resp_doc.status_code, 200)
        data_doc = resp_doc.json()
        self.assertEqual(data_doc["user"]["role"], "DOCTOR")
        self.assertIn("Reed", data_doc["user"]["full_name"])

    def test_user_registration_and_login(self):
        test_email = "alex.rivera@example.com"
        reg_payload = {
            "full_name": "Alex Rivera",
            "email": test_email,
            "password": "SecurePassword123",
            "role": "PATIENT",
            "phone": "+1 555-0144"
        }
        resp = self.client.post("/api/auth/register", json=reg_payload)
        # 200 or 400 if already created in persistent store
        if resp.status_code == 200:
            self.assertEqual(resp.json()["status"], "success")

        # Now test login
        login_resp = self.client.post("/api/auth/login", json={
            "email": test_email,
            "password": "SecurePassword123"
        })
        self.assertEqual(login_resp.status_code, 200)
        self.assertEqual(login_resp.json()["user"]["email"], test_email)

    # -----------------------------------------------------------------
    # 2. HEALTHCARE BOOKINGS: ONLINE & IN-PERSON
    # -----------------------------------------------------------------
    def test_doctor_directory(self):
        resp = self.client.get("/api/bookings/doctors")
        self.assertEqual(resp.status_code, 200)
        doctors = resp.json()
        self.assertGreaterEqual(len(doctors), 4)
        specialties = [d["specialty"] for d in doctors]
        self.assertTrue(any("Cardiology" in s for s in specialties))
        self.assertTrue(any("Endocrinology" in s for s in specialties))

    def test_book_online_consultation(self):
        booking_payload = {
            "patient_id": "case_1_diabetes",
            "patient_name": "Eleanor Vance",
            "patient_phone": "+1 555-234-5678",
            "doctor_id": "doc-marcus-vance",
            "booking_type": "online",
            "appointment_date": "2026-09-12",
            "time_slot": "10:00 AM",
            "notes": "Follow-up consultation for elevated HbA1c review."
        }
        resp = self.client.post("/api/bookings/consultations", json=booking_payload)
        self.assertEqual(resp.status_code, 200)
        data = resp.json()
        self.assertEqual(data["status"], "success")
        booking = data["booking"]
        self.assertEqual(booking["booking_type"], "online")
        self.assertIsNotNone(booking["meeting_link"])
        self.assertIn("telehealth", booking["meeting_link"])

    def test_book_in_person_appointment_and_cancel(self):
        booking_payload = {
            "patient_id": "case_2_cardiac",
            "patient_name": "Marcus Thorne",
            "doctor_id": "doc-evelyn-reed",
            "booking_type": "in_person",
            "appointment_date": "2026-09-15",
            "time_slot": "02:30 PM",
            "notes": "Comprehensive cardiovascular physical exam."
        }
        resp = self.client.post("/api/bookings/consultations", json=booking_payload)
        self.assertEqual(resp.status_code, 200)
        b_id = resp.json()["booking"]["booking_id"]

        # Cancel appointment
        cancel_resp = self.client.post(f"/api/bookings/consultations/{b_id}/cancel")
        self.assertEqual(cancel_resp.status_code, 200)
        self.assertEqual(cancel_resp.json()["booking"]["status"], "cancelled")

    # -----------------------------------------------------------------
    # 3. EMERGENCY AMBULANCE DISPATCH & LIVE TRACKER
    # -----------------------------------------------------------------
    def test_emergency_ambulance_lifecycle(self):
        req_payload = {
            "patient_id": "case_2_cardiac",
            "patient_name": "Marcus Thorne",
            "contact_phone": "+1 555-911-0199",
            "emergency_type": "Acute Cardiac Chest Pain",
            "pickup_address": "452 Oak Ridge Lane, Suite 3B, Downtown Metro",
            "landmark": "Near Central Metro Station",
            "latitude": 37.7749,
            "longitude": -122.4194
        }
        resp = self.client.post("/api/emergency/ambulance", json=req_payload)
        self.assertEqual(resp.status_code, 200)
        data = resp.json()
        self.assertEqual(data["status"], "emergency_dispatched")
        amb_id = data["ambulance"]["request_id"]
        self.assertEqual(data["ambulance"]["dispatch_status"], "dispatched")

        # Track status
        track_resp = self.client.get(f"/api/emergency/ambulance/{amb_id}")
        self.assertEqual(track_resp.status_code, 200)
        self.assertEqual(track_resp.json()["request_id"], amb_id)

        # Advance status to EN_ROUTE
        adv_resp = self.client.post(f"/api/emergency/ambulance/{amb_id}/advance_status")
        self.assertEqual(adv_resp.status_code, 200)
        self.assertEqual(adv_resp.json()["ambulance"]["dispatch_status"], "en_route")

    # -----------------------------------------------------------------
    # 4. AI SYMPTOM-TO-DISEASE AGENT
    # -----------------------------------------------------------------
    def test_symptom_evaluation_and_disease_matching(self):
        resp = self.client.post("/api/symptom-agent/evaluate", json={
            "symptoms": ["fever", "chills", "body_ache", "fatigue", "cough"],
            "narrative": "Sudden onset of high fever, muscle fatigue, and dry cough."
        })
        self.assertEqual(resp.status_code, 200)
        data = resp.json()
        self.assertGreaterEqual(len(data["top_matches"]), 1)
        top_disease = data["top_matches"][0]
        self.assertIn("Influenza", top_disease["name"])
        self.assertGreaterEqual(top_disease["confidence"], 60)
        self.assertIsNotNone(top_disease["specialist"])

    def test_emergency_red_flag_alert(self):
        resp = self.client.post("/api/symptom-agent/evaluate", json={
            "symptoms": ["chest_pain", "shortness_of_breath"],
            "narrative": "Crushing central chest pressure radiating to my left arm."
        })
        self.assertEqual(resp.status_code, 200)
        data = resp.json()
        self.assertEqual(data["overall_triage_level"], "EMERGENCY")
        self.assertGreaterEqual(len(data["emergency_alerts"]), 1)

    # -----------------------------------------------------------------
    # 5. MEDICATION DETECTION & ONLINE PHARMACY REDIRECTION
    # -----------------------------------------------------------------
    def test_ai_chat_medication_query_redirects_to_pharmacy(self):
        # When user asks about Paracetamol tablets
        resp = self.client.post("/api/symptom-agent/chat", json={
            "message": "Can I take Paracetamol for my headache? Where can I buy it?",
            "history": []
        })
        self.assertEqual(resp.status_code, 200)
        data = resp.json()
        self.assertTrue(data["medication_detected"])
        self.assertTrue(data["redirect_to_pharmacy"])
        self.assertEqual(data["target_product_id"], "rx-paracetamol-500")
        self.assertIn("Paracetamol", data["primary_product"]["name"])
        self.assertIn("MedLens Online Pharmacy", data["reply"])

    def test_ai_chat_metformin_tablet_detection(self):
        # When user asks about Metformin for diabetes
        resp = self.client.post("/api/symptom-agent/chat", json={
            "message": "I need to order Metformin 500mg tablets for my diabetes.",
            "history": []
        })
        self.assertEqual(resp.status_code, 200)
        data = resp.json()
        self.assertTrue(data["medication_detected"])
        self.assertTrue(data["redirect_to_pharmacy"])
        self.assertEqual(data["target_product_id"], "rx-metformin-500")

    def test_direct_detect_medication_endpoint(self):
        resp = self.client.post("/api/pharmacy/detect-medication", json={
            "text": "What is the price of Atorvastatin cholesterol tablet?"
        })
        self.assertEqual(resp.status_code, 200)
        data = resp.json()
        self.assertTrue(data["detected"])
        self.assertEqual(data["target_product_id"], "rx-atorvastatin-20")

    # -----------------------------------------------------------------
    # 6. ONLINE PHARMACY CATALOG & ORDER PLACEMENT
    # -----------------------------------------------------------------
    def test_pharmacy_products_list_and_search(self):
        # List all
        resp = self.client.get("/api/pharmacy/products")
        self.assertEqual(resp.status_code, 200)
        products = resp.json()
        self.assertGreaterEqual(len(products), 10)

        # Filter by category
        cat_resp = self.client.get("/api/pharmacy/products?category=Pain Relief & Fever")
        self.assertEqual(cat_resp.status_code, 200)
        pain_items = cat_resp.json()
        self.assertTrue(any("Paracetamol" in p["name"] for p in pain_items))

        # Search
        search_resp = self.client.get("/api/pharmacy/products?search=Amoxicillin")
        self.assertEqual(search_resp.status_code, 200)
        self.assertEqual(len(search_resp.json()), 1)
        self.assertEqual(search_resp.json()[0]["product_id"], "rx-amoxicillin-500")

    def test_place_pharmacy_order(self):
        order_payload = {
            "patient_id": "case_1_diabetes",
            "customer_name": "Eleanor Vance",
            "customer_email": "patient@medlens.health",
            "customer_phone": "+1 555-234-5678",
            "delivery_address": "742 Evergreen Terrace, Springfield",
            "items": [
                {
                    "product_id": "rx-paracetamol-500",
                    "product_name": "Paracetamol 500mg",
                    "strength": "500 mg",
                    "price": 3.99,
                    "quantity": 2
                },
                {
                    "product_id": "rx-metformin-500",
                    "product_name": "Metformin Hydrochloride 500mg",
                    "strength": "500 mg",
                    "price": 9.99,
                    "quantity": 1
                }
            ],
            "payment_method": "Credit / Debit Card",
            "prescription_uploaded": True
        }
        resp = self.client.post("/api/pharmacy/order", json=order_payload)
        self.assertEqual(resp.status_code, 200)
        data = resp.json()
        self.assertEqual(data["status"], "success")
        order = data["order"]
        self.assertIsNotNone(order["order_id"])
        self.assertIsNotNone(order["tracking_number"])
        self.assertAlmostEqual(order["subtotal"], 17.97, places=2)

    # -----------------------------------------------------------------
    # 7. CLINICAL RECORD INTELLIGENCE: VERIFY, COMPARE, CONFLICTS
    # -----------------------------------------------------------------
    def test_lab_human_verification_endpoint(self):
        verify_payload = {
            "test_id": "glucose",
            "verified": True,
            "verified_by": "Dr. Evelyn Reed, MD",
            "clinician_notes": "Correlated with fasting venous sample.",
            "edited_status": "HIGH"
        }
        resp = self.client.post("/api/records/case_1_diabetes/verify_lab", json=verify_payload)
        self.assertEqual(resp.status_code, 200)
        data = resp.json()
        self.assertEqual(data["status"], "success")
        self.assertTrue(data["lab_result"]["verification"]["is_verified"])
        self.assertEqual(data["lab_result"]["verification"]["verified_by"], "Dr. Evelyn Reed, MD")

    def test_report_comparison_endpoint(self):
        resp = self.client.get("/api/records/case_1_diabetes/compare")
        self.assertEqual(resp.status_code, 200)
        data = resp.json()
        self.assertEqual(data["record_id"], "case_1_diabetes")
        self.assertGreaterEqual(len(data["comparisons"]), 1)
        # Check comparison structure
        first = data["comparisons"][0]
        self.assertIn("test_name", first)
        self.assertIn("current_value", first)
        self.assertIn("baseline_value", first)
        self.assertIn("trend", first)

    def test_clinical_conflicts_detection(self):
        resp = self.client.get("/api/records/case_1_diabetes/conflicts")
        self.assertEqual(resp.status_code, 200)
        data = resp.json()
        self.assertIn("conflicts", data)


if __name__ == "__main__":
    unittest.main()
