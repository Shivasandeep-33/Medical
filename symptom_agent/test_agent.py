"""
Unit & Integration Test Suite for MediCure AI Symptom Diagnostic & Triage Agent.
"""

import unittest
import os
import sys

# Add directory to path
sys.path.insert(0, os.path.dirname(__file__))

from fastapi.testclient import TestClient
from agent_app import app
from disease_engine import extract_symptoms_from_text, evaluate_symptoms


class TestMediCureAIAgent(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.client = TestClient(app)

    def test_health_check(self):
        res = self.client.get("/api/health")
        self.assertEqual(res.status_code, 200)
        self.assertEqual(res.json()["status"], "ok")

    def test_symptom_categories_endpoint(self):
        res = self.client.get("/api/symptoms/list")
        self.assertEqual(res.status_code, 200)
        categories = res.json()
        self.assertIn("Head, Brain & ENT", categories)
        self.assertIn("Chest, Heart & Lungs", categories)
        self.assertIn("Abdomen & Digestion", categories)

    def test_scenarios_endpoint(self):
        res = self.client.get("/api/scenarios")
        self.assertEqual(res.status_code, 200)
        scenarios = res.json()
        self.assertGreaterEqual(len(scenarios), 4)

    def test_free_text_symptom_extraction(self):
        text = "I have a high fever, terrible throat pain, and dry cough since yesterday"
        detected = extract_symptoms_from_text(text)
        self.assertIn("fever", detected)
        self.assertIn("sore_throat", detected)
        self.assertIn("cough", detected)

    def test_respiratory_disease_diagnosis(self):
        res = self.client.post("/api/diagnose", json={
            "symptoms": ["fever", "chills", "body_ache", "fatigue", "cough"],
            "narrative": "Severe body aches and exhaustion with chills and high fever"
        })
        self.assertEqual(res.status_code, 200)
        data = res.json()
        self.assertIn("Fever", data["user_symptoms_detected"])
        self.assertGreaterEqual(len(data["top_matches"]), 1)

        top_disease = data["top_matches"][0]
        self.assertIn("Influenza", top_disease["name"])
        self.assertGreaterEqual(top_disease["confidence"], 60)
        self.assertEqual(top_disease["specialist"], "General Physician / Internal Medicine")

    def test_emergency_red_flag_triage(self):
        res = self.client.post("/api/diagnose", json={
            "symptoms": ["chest_pain", "shortness_of_breath"],
            "narrative": "Crushing chest pain radiating to left arm with breathlessness and sweating"
        })
        self.assertEqual(res.status_code, 200)
        data = res.json()
        self.assertEqual(data["overall_triage_level"], "EMERGENCY")
        self.assertGreaterEqual(len(data["emergency_alerts"]), 1)
        self.assertIn("Cardiologist", data["recommended_specialists"])

    def test_chat_endpoint(self):
        res = self.client.post("/api/chat", json={
            "message": "I've had a bad migraine and nausea for 5 hours",
            "history": []
        })
        self.assertEqual(res.status_code, 200)
        data = res.json()
        self.assertIn("reply", data)
        self.assertIn("evaluation", data)
        self.assertIn("Headache", data["evaluation"]["user_symptoms_detected"])


if __name__ == "__main__":
    unittest.main()
