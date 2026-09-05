"""
Conversational Clinical Triage & Health Agent.
Handles multi-turn patient dialogue, symptom extraction, differential diagnostic reasoning,
specialist recommendations, and automatic medication inquiry detection with
seamless redirection to the integrated MedLens Online Pharmacy.
"""

import os
import sys
import json
from typing import List, Dict, Any, Optional

# Ensure sibling/parent imports work
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
sys.path.insert(0, os.path.dirname(__file__))

from disease_engine import evaluate_symptoms, extract_symptoms_from_text, TriageEvaluation
try:
    from pharmacy import detect_medications_in_text
except ImportError:
    # Fallback if imported from a different context
    import importlib.util
    pharm_path = os.path.join(os.path.dirname(__file__), "..", "pharmacy.py")
    spec = importlib.util.spec_from_file_location("pharmacy", pharm_path)
    pharmacy = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(pharmacy)
    detect_medications_in_text = pharmacy.detect_medications_in_text


def generate_local_agent_response(user_message: str, history: List[Dict[str, str]] = None) -> Dict[str, Any]:
    """
    Built-in conversational clinical agent for offline and instant use.
    Performs symptom extraction, runs diagnostic engine, detects medication queries,
    and coordinates automatic pharmacy redirection.
    """
    history = history or []

    # 1. Check for specific tablet / medication inquiry first
    med_detection = detect_medications_in_text(user_message)

    # Aggregate conversation context to detect cumulative symptoms
    full_conversation = " ".join([h.get("content", "") for h in history] + [user_message])
    detected_keys = extract_symptoms_from_text(full_conversation)

    evaluation = evaluate_symptoms(symptoms_list=detected_keys, user_narrative=full_conversation)

    paragraphs = []

    # If medication detected, prioritize comprehensive pharmaceutical information & redirect notice
    if med_detection.get("detected"):
        prod = med_detection["primary_product"]
        paragraphs.append(f"💊 **MedLens Medication Intelligence**: You asked about **{prod['name']}**.")
        paragraphs.append(med_detection["educational_note"])
        if evaluation.user_symptoms_detected:
            paragraphs.append(f"\n*Related symptoms noted in this consultation: {', '.join(evaluation.user_symptoms_detected)}.*")

        text_response = "\n\n".join(paragraphs)
        return {
            "reply": text_response,
            "evaluation": evaluation.model_dump(),
            "medication_detected": True,
            "redirect_to_pharmacy": True,
            "target_product_id": med_detection["target_product_id"],
            "primary_product": prod,
            "all_products": med_detection.get("all_products", []),
            "redirect_reason": med_detection["redirect_reason"]
        }

    # Standard Symptom Consultation
    if not evaluation.user_symptoms_detected:
        text_response = (
            "Hello! I am your AI Clinical Triage & Health Assistant. I can help evaluate your symptoms, identify likely "
            "conditions, assess triage urgency, recommend appropriate specialists, and help you find tablets or medications.\n\n"
            "Could you describe what symptoms you are experiencing, how long they have been present, "
            "and whether you have any fever, pain, or breathlessness?"
        )
    else:
        symptoms_str = ", ".join(evaluation.user_symptoms_detected)
        paragraphs.append(f"Thank you for sharing your symptoms. Based on our conversation, I have identified: **{symptoms_str}**.")

        # Triage urgency alert
        if evaluation.overall_triage_level == "EMERGENCY":
            paragraphs.append(
                "🚨 **URGENT MEDICAL ALERT**: One or more of your symptoms suggest a potentially acute or high-priority "
                "condition requiring immediate emergency evaluation. Please seek in-person medical care or call local emergency services."
            )
            for alert in evaluation.emergency_alerts:
                paragraphs.append(f"- {alert}")
        elif evaluation.overall_triage_level == "MODERATE":
            paragraphs.append(
                "⚠️ **Triage Urgency: Moderate**. Your presentation warrants a clinical consultation with a healthcare "
                "provider within the next 24 to 48 hours to confirm the diagnosis and initiate appropriate therapy."
            )
        else:
            paragraphs.append(
                "🟢 **Triage Urgency: Low / Routine**. Your symptoms appear mild and self-limiting, which can often be "
                "supported with appropriate home care, rest, and fluid intake."
            )

        # Top Diagnostic Matches
        if evaluation.top_matches:
            paragraphs.append("\n### 🔍 Probable Conditions Evaluated:")
            for m in evaluation.top_matches[:3]:
                paragraphs.append(
                    f"1. **{m.name}** ({m.confidence}% Match) — *{m.match_rationale}*\n"
                    f"   - **Recommended Specialist**: {m.specialist}\n"
                    f"   - **Common Investigations**: {', '.join(m.clinical_tests[:3])}"
                )

        # Home care supportive guidance
        if evaluation.top_matches and evaluation.top_matches[0].home_care:
            paragraphs.append("\n### 💡 Recommended Supportive Care:")
            for step in evaluation.top_matches[0].home_care[:3]:
                paragraphs.append(f"- {step}")

        paragraphs.append(
            "\n*If you require specific medications (such as Paracetamol, Metformin, Atorvastatin, or Ibuprofen) or wish to book a consultation, simply ask and I will guide you immediately.*"
        )
        text_response = "\n\n".join(paragraphs)

    return {
        "reply": text_response,
        "evaluation": evaluation.model_dump(),
        "medication_detected": False,
        "redirect_to_pharmacy": False
    }


def run_chat_triage(
    user_message: str,
    api_key: Optional[str] = None,
    gemini_api_key: Optional[str] = None,
    history: List[Dict[str, str]] = None
) -> Dict[str, Any]:
    """
    Main chat orchestration endpoint.
    Automatically identifies medications and performs clinical reasoning.
    """
    history = history or []
    effective_api_key = api_key or gemini_api_key

    # If medication is directly detected in query, local pharmaceutical engine responds with exact product match & redirect
    med_detect = detect_medications_in_text(user_message)
    if med_detect.get("detected"):
        return generate_local_agent_response(user_message, history=history)

    # If Gemini API key is provided and valid, use Gemini with clinical guardrails
    if effective_api_key and effective_api_key.strip():
        try:
            from google import genai
            from google.genai import types

            client = genai.Client(api_key=effective_api_key.strip())

            # Also evaluate deterministic baseline
            detected_keys = extract_symptoms_from_text(user_message)
            eval_data = evaluate_symptoms(symptoms_list=detected_keys, user_narrative=user_message)

            system_instruction = (
                "You are an empathetic, highly knowledgeable AI Clinical Assistant named MedLens Assistant. "
                "Analyze the user's symptoms, explain probable conditions, emphasize triage urgency, "
                "suggest appropriate medical specialists, and recommend when to seek emergency care. "
                "Never provide a definitive diagnosis or unauthorized prescription. "
                "If the patient inquires about medications or tablets, explain their standard usage and advise them "
                "that they can purchase them via MedLens Online Pharmacy."
            )

            prompt = (
                f"Patient Message: {user_message}\n"
                f"Clinically Extracted Symptoms: {', '.join(eval_data.user_symptoms_detected)}\n"
                f"Triage Urgency: {eval_data.overall_triage_level}\n"
                f"Probable conditions evaluated: {', '.join([m.name for m in eval_data.top_matches[:2]])}\n"
            )

            response = client.models.generate_content(
                model="gemini-2.5-flash",
                contents=prompt,
                config=types.GenerateContentConfig(
                    system_instruction=system_instruction,
                    temperature=0.2,
                )
            )

            reply_text = response.text or ""
            return {
                "reply": reply_text,
                "evaluation": eval_data.model_dump(),
                "medication_detected": False,
                "redirect_to_pharmacy": False
            }
        except Exception as e:
            print(f"Gemini chat fallback to local engine: {e}")
            return generate_local_agent_response(user_message, history=history)

    return generate_local_agent_response(user_message, history=history)
