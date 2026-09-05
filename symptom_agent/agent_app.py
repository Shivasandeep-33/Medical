"""
FastAPI Server for AI Symptom-to-Disease Clinical Diagnostic & Triage Agent.
"""

import os
import sys
from typing import List, Optional, Dict, Any
from fastapi import FastAPI, HTTPException, Header
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from dotenv import load_dotenv

# Ensure local imports work cleanly
sys.path.insert(0, os.path.dirname(__file__))

from disease_engine import evaluate_symptoms, SYMPTOM_LEXICON, TriageEvaluation
from chat_agent import run_chat_triage

load_dotenv()

app = FastAPI(
    title="MediCure AI — Clinical Disease Diagnostic & Triage Agent",
    description="Intelligent AI Agent identifying probable diseases from symptoms with confidence scoring and triage recommendations.",
    version="2.0.0"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

DEFAULT_GEMINI_KEY = os.getenv("GEMINI_API_KEY", "")

# Categorized symptom dictionary for the interactive body system UI
SYMPTOM_CATEGORIES = {
    "Head, Brain & ENT": [
        {"key": "headache", "label": "Headache / Head Pain", "icon": "brain"},
        {"key": "dizziness", "label": "Dizziness / Lightheadedness", "icon": "compass"},
        {"key": "sore_throat", "label": "Sore Throat / Pain Swallowing", "icon": "flame"},
        {"key": "runny_nose", "label": "Runny Nose / Congestion", "icon": "wind"},
        {"key": "stiff_neck", "label": "Stiff Neck / Neck Rigidity", "icon": "shield-alert"},
        {"key": "loss_of_taste_smell", "label": "Loss of Taste or Smell", "icon": "utensils"}
    ],
    "Chest, Heart & Lungs": [
        {"key": "cough", "label": "Cough (Dry or Productive)", "icon": "wind"},
        {"key": "shortness_of_breath", "label": "Shortness of Breath / Wheezing", "icon": "activity"},
        {"key": "chest_pain", "label": "Chest Pain / Pressure", "icon": "heart-pulse"},
        {"key": "palpitations", "label": "Rapid / Irregular Heartbeat", "icon": "zap"}
    ],
    "Abdomen & Digestion": [
        {"key": "abdominal_pain", "label": "Abdominal / Stomach Pain", "icon": "disc"},
        {"key": "nausea", "label": "Nausea / Queasiness", "icon": "alert-circle"},
        {"key": "vomiting", "label": "Vomiting", "icon": "corner-up-left"},
        {"key": "heartburn", "label": "Heartburn / Acid Indigestion", "icon": "flame"},
        {"key": "diarrhea", "label": "Diarrhea / Loose Stools", "icon": "droplets"}
    ],
    "Muscles, Joints & Limbs": [
        {"key": "body_ache", "label": "Body / Muscle Aches", "icon": "crosshair"},
        {"key": "joint_stiffness", "label": "Joint Stiffness / Swelling", "icon": "minimize-2"},
        {"key": "numbness", "label": "Numbness / Tingling", "icon": "fingerprint"},
        {"key": "swelling_limbs", "label": "Swollen Feet / Ankles", "icon": "circle"}
    ],
    "Systemic & Metabolic": [
        {"key": "fever", "label": "Fever / Elevated Temperature", "icon": "thermometer"},
        {"key": "chills", "label": "Chills / Shivering", "icon": "snowflake"},
        {"key": "fatigue", "label": "Severe Fatigue / Exhaustion", "icon": "battery-low"},
        {"key": "rash", "label": "Skin Rash / Itching", "icon": "sparkles"},
        {"key": "burning_urination", "label": "Burning Urination", "icon": "droplet"},
        {"key": "excessive_thirst", "label": "Excessive Thirst", "icon": "cup-soda"},
        {"key": "weight_loss", "label": "Unexplained Weight Loss", "icon": "trending-down"},
        {"key": "confusion", "label": "Confusion / Disorientation", "icon": "help-circle"}
    ]
}

# Quick Test Scenarios for 1-Click Demonstration
QUICK_SCENARIOS = [
    {
        "id": "scenario_flu",
        "title": "Influenza / Flu Presentation",
        "symptoms": ["fever", "chills", "body_ache", "fatigue", "cough", "headache"],
        "narrative": "Sudden onset of high fever (102°F), severe muscle aches all over, chills, dry cough, and exhaustion for the past 24 hours.",
        "description": "Demonstrates viral respiratory diagnosis with multi-symptom coverage."
    },
    {
        "id": "scenario_cardiac_emergency",
        "title": "Suspected Cardiac Event (Emergency Alert)",
        "symptoms": ["chest_pain", "shortness_of_breath", "palpitations"],
        "narrative": "Crushing central chest tightness radiating to the left arm and neck, accompanied by breathlessness and cold sweat.",
        "description": "Demonstrates instantaneous Emergency Red-Flag detection and immediate ER triage."
    },
    {
        "id": "scenario_migraine",
        "title": "Severe Throbbing Headache & Nausea",
        "symptoms": ["headache", "nausea", "dizziness"],
        "narrative": "Severe pulsating pain on the left side of my head, intense nausea, and sensitivity to bright lights and sounds for 8 hours.",
        "description": "Demonstrates neurological differential (Migraine vs Tension Headache) and dark-room home care."
    },
    {
        "id": "scenario_gerd",
        "title": "Substernal Acid Heartburn & Discomfort",
        "symptoms": ["heartburn", "chest_pain", "nausea"],
        "narrative": "Burning sensation behind the breastbone that worsens after meals and when lying down, with a sour taste in mouth.",
        "description": "Demonstrates gastrointestinal reflux identification and dietary guidance."
    },
    {
        "id": "scenario_uti",
        "title": "Urinary Discomfort & Pelvic Pressure",
        "symptoms": ["burning_urination", "abdominal_pain", "fatigue"],
        "narrative": "Sharp burning sensation while urinating, needing to urinate every 30 minutes, and mild lower pelvic pain for 2 days.",
        "description": "Demonstrates urinary infection triage and urology / urinalysis testing."
    }
]


class SymptomEvaluationRequest(BaseModel):
    symptoms: List[str] = []
    narrative: str = ""
    age: Optional[int] = None
    sex: Optional[str] = None


class ChatMessageRequest(BaseModel):
    message: str
    history: List[Dict[str, str]] = []


@app.get("/api/health")
def health_check():
    return {"status": "ok", "service": "MediCure AI Symptom Agent"}


@app.get("/api/symptoms/list")
def get_symptoms_list():
    """Returns categorized canonical symptoms for interactive UI selector."""
    return SYMPTOM_CATEGORIES


@app.get("/api/scenarios")
def get_quick_scenarios():
    """Returns 1-click test scenarios."""
    return QUICK_SCENARIOS


@app.post("/api/diagnose")
def diagnose_symptoms(
    req: SymptomEvaluationRequest
):
    """
    Evaluates symptoms and returns differential diagnosis, confidence scores,
    clinical triage level, specialist routing, and supportive care.
    """
    evaluation = evaluate_symptoms(
        symptoms_list=req.symptoms,
        user_narrative=req.narrative,
        patient_age=req.age,
        patient_sex=req.sex
    )
    return evaluation


@app.post("/api/chat")
def chat_with_agent(
    req: ChatMessageRequest,
    x_gemini_api_key: Optional[str] = Header(None)
):
    """
    Conversational triage endpoint. Chat naturally with the clinical AI agent.
    """
    api_key = x_gemini_api_key or DEFAULT_GEMINI_KEY
    result = run_chat_triage(
        user_message=req.message,
        api_key=api_key,
        history=req.history
    )
    return result


# Mount static directory for frontend
static_dir = os.path.join(os.path.dirname(__file__), "static")
os.makedirs(static_dir, exist_ok=True)
app.mount("/", StaticFiles(directory=static_dir, html=True), name="static")


if __name__ == "__main__":
    import uvicorn
    host = os.getenv("HOST", "0.0.0.0")
    port = int(os.getenv("PORT", 8000))
    print(f"Starting MediCure AI Symptom Agent on http://{host}:{port} ...")
    uvicorn.run("agent_app:app", host=host, port=port, reload=False)
