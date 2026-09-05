"""
Conversational Clinical Triage Agent.
Handles multi-turn patient dialogue, symptom extraction, differential diagnostic reasoning,
and specialist recommendations using Gemini 2.5 Flash (with clinical guardrails)
or the built-in intelligent medical reasoning agent when offline.
"""

import os
import json
from typing import List, Dict, Any, Optional
from disease_engine import evaluate_symptoms, extract_symptoms_from_text, TriageEvaluation


def generate_local_agent_response(user_message: str, history: List[Dict[str, str]] = None) -> Dict[str, Any]:
    """
    Built-in conversational clinical agent for offline and instant use.
    Performs symptom extraction, runs diagnostic engine, and synthesizes structured guidance.
    """
    history = history or []

    # Aggregate conversation context to detect cumulative symptoms
    full_conversation = " ".join([h.get("content", "") for h in history] + [user_message])
    detected_keys = extract_symptoms_from_text(full_conversation)

    evaluation = evaluate_symptoms(symptoms_list=detected_keys, user_narrative=full_conversation)

    # Construct thoughtful, conversational doctor-agent response
    paragraphs = []

    if not evaluation.user_symptoms_detected:
        text_response = (
            "Hello! I am your AI Clinical Triage Assistant. I can help evaluate your symptoms, identify likely "
            "conditions, assess urgency levels, and advise which specialist to see.\n\n"
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
            "\n*How severe would you rate your discomfort right now on a scale of 1 to 10? Are there any other symptoms you've noticed?*"
        )
        text_response = "\n\n".join(paragraphs)

    return {
        "reply": text_response,
        "evaluation": evaluation.model_dump()
    }


def generate_gemini_agent_response(
    user_message: str,
    api_key: str,
    history: List[Dict[str, str]] = None
) -> Dict[str, Any]:
    """
    Advanced conversational clinical agent utilizing Google Gemini 2.5 Flash.
    """
    try:
        from google import genai
        from google.genai import types

        client = genai.Client(api_key=api_key)

        # First run our local medical engine to ground the AI with exact clinical knowledge
        full_conversation = " ".join([h.get("content", "") for h in (history or [])] + [user_message])
        detected_keys = extract_symptoms_from_text(full_conversation)
        evaluation = evaluate_symptoms(symptoms_list=detected_keys, user_narrative=full_conversation)

        prompt = f"""
You are Dr. Clara, an empathetic, highly knowledgeable AI Clinical Triage & Health Agent.
Your role is to help users understand what diseases or medical conditions match their reported symptoms,
assess clinical triage urgency (Emergency vs Moderate vs Routine), recommend which medical specialist to consult,
and provide safe, practical home care guidance.

CLINICAL ENGINE ASSESSMENT:
- Detected Symptoms: {json.dumps(evaluation.user_symptoms_detected)}
- Overall Triage Level: {evaluation.overall_triage_level}
- Emergency Alerts: {json.dumps(evaluation.emergency_alerts)}
- Top Probable Conditions: {[m.name + f' ({m.confidence}%)' for m in evaluation.top_matches]}
- Recommended Specialists: {json.dumps(evaluation.recommended_specialists)}

USER MESSAGE:
"{user_message}"

CONVERSATION HISTORY:
{json.dumps(history or [], indent=2)}

INSTRUCTIONS:
1. Speak in a compassionate, professional clinical tone.
2. Clearly explain the top 2-3 probable conditions and WHY they fit the symptoms.
3. Clearly state the triage urgency level. If an emergency red flag is present, emphasize immediate in-person medical care.
4. Recommend the specific medical specialist to consult (e.g. Cardiologist, ENT, Gastroenterologist).
5. Suggest safe supportive remedies (fluids, rest, temperature management) and standard diagnostic tests the doctor may order.
6. Ask 1-2 helpful clarifying follow-up questions.
7. Include a brief medical disclaimer that this is automated educational triage.
"""

        response = client.models.generate_content(
            model="gemini-2.5-flash",
            contents=prompt
        )

        return {
            "reply": response.text,
            "evaluation": evaluation.model_dump()
        }
    except Exception as e:
        print(f"Gemini triage agent error: {e}. Falling back to deterministic clinical engine.")
        return generate_local_agent_response(user_message, history)


def run_chat_triage(
    user_message: str,
    api_key: Optional[str] = None,
    history: List[Dict[str, str]] = None
) -> Dict[str, Any]:
    """
    Main entry point for conversational triage agent.
    """
    if api_key and api_key.strip():
        return generate_gemini_agent_response(user_message, api_key.strip(), history)
    return generate_local_agent_response(user_message, history)
