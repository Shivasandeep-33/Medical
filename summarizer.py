"""
AI-Powered Patient-Friendly Clinical Summary Generator.
Synthesizes patient intake and laboratory findings into an understandable,
structured overview without providing medical diagnoses or treatment recommendations.
Supports Google Gemini AI generation with clinical guardrails, plus a built-in
deterministic clinical synthesis engine for offline/instant use.
"""

from typing import List, Dict, Optional
from models import (
    StructuredMedicalRecord,
    PatientFriendlySummary,
    ValueStatus,
)

# Patient-friendly descriptions for common laboratory tests
FRIENDLY_TEST_GLOSSARY = {
    "GLUCOSE": "Blood sugar level (reflects short-term energy balance and carbohydrate regulation).",
    "FASTING GLUCOSE": "Fasting blood sugar level measured after an overnight fast.",
    "HBA1C": "Hemoglobin A1c (indicates average blood sugar control over the past 2 to 3 months).",
    "HEMOGLOBIN": "Oxygen-transporting protein found within red blood cells.",
    "HEMATOCRIT": "Percentage of total blood volume made up of red blood cells.",
    "WBC": "White blood cells (cells that support the immune system and respond to inflammation or infection).",
    "PLATELETS": "Blood cells that help form clots to prevent or stop bleeding.",
    "CREATININE": "Metabolic waste product filtered out by healthy kidneys.",
    "BUN": "Blood Urea Nitrogen (a waste product from protein breakdown evaluated for kidney health).",
    "EGFR": "Estimated Glomerular Filtration Rate (an estimate of how efficiently kidneys filter blood).",
    "TOTAL CHOLESTEROL": "Combined measurement of various blood fats (lipids).",
    "LDL": "Low-Density Lipoprotein ('bad' cholesterol that can accumulate in blood vessel walls).",
    "HDL": "High-Density Lipoprotein ('good' cholesterol that carries fats back to the liver).",
    "TRIGLYCERIDES": "Most common type of fat in the bloodstream, often linked to calorie intake and metabolism.",
    "ALT": "Alanine Aminotransferase (an enzyme located primarily inside liver cells).",
    "AST": "Aspartate Aminotransferase (an enzyme found in the liver, heart, and muscle tissue).",
    "BILIRUBIN": "Substance created during the normal breakdown of red blood cells, processed by the liver.",
    "TSH": "Thyroid Stimulating Hormone (pituitary messenger that directs thyroid hormone production).",
    "VITAMIN D": "Essential nutrient necessary for bone density, calcium absorption, and immune support.",
    "FERRITIN": "Protein that stores iron inside body tissues for future red blood cell production.",
    "POTASSIUM": "Crucial mineral and electrolyte regulating fluid balance, nerve signals, and heart rhythm.",
    "SODIUM": "Essential electrolyte maintaining proper water balance and cellular blood pressure.",
    "CALCIUM": "Mineral essential for healthy bones, muscle contractions, and nerve impulses."
}


def generate_deterministic_summary(record: StructuredMedicalRecord) -> PatientFriendlySummary:
    """
    Built-in clinical synthesis engine.
    Generates a structured, patient-friendly summary from patient intake and lab records.
    Strictly avoids clinical diagnosis or prescription recommendations.
    """
    patient = record.patient
    all_labs = record.all_lab_results

    # Categorize lab findings
    out_of_range_items = [t for t in all_labs if t.status in [ValueStatus.LOW, ValueStatus.HIGH]]
    normal_items = [t for t in all_labs if t.status == ValueStatus.NORMAL]
    unspecified_items = [t for t in all_labs if t.status == ValueStatus.UNSPECIFIED]

    # 1. Overview Narrative
    age_str = f"{patient.age}-year-old" if patient.age else "Patient"
    sex_str = f"{patient.sex.lower()}" if patient.sex and patient.sex.lower() != "unspecified" else "individual"
    num_reports = len(record.reports)
    total_tests = len(all_labs)

    overview_sentences = [
        f"This unified medical overview aggregates self-reported intake details for a {age_str} {sex_str} "
        f"alongside {total_tests} diagnostic test results extracted from {num_reports} uploaded medical report(s)."
    ]

    if patient.symptoms:
        symptom_summary = ", ".join([f"{s.name} ({s.severity.lower()}, {s.duration or 'ongoing'})" for s in patient.symptoms[:4]])
        overview_sentences.append(f"Current self-reported symptoms include: {symptom_summary}.")

    if patient.medications:
        med_summary = ", ".join([f"{m.name} {m.dosage}".strip() for m in patient.medications[:4]])
        overview_sentences.append(f"Active reported medications: {med_summary}.")

    overview = " ".join(overview_sentences)

    # 2. Key Findings
    key_findings: List[str] = []

    if out_of_range_items:
        key_findings.append(
            f"{len(out_of_range_items)} diagnostic value(s) fall outside the specific reference ranges provided on the report."
        )
    if normal_items:
        key_findings.append(
            f"{len(normal_items)} test parameter(s) fall comfortably within the source document's established normal ranges."
        )
    if unspecified_items:
        key_findings.append(
            f"{len(unspecified_items)} test(s) had no explicit reference interval printed on the source report."
        )

    if patient.allergies:
        allergy_str = ", ".join([f"{a.allergen} ({a.reaction})" if a.reaction else a.allergen for a in patient.allergies])
        key_findings.append(f"Patient self-reported documented allergies: {allergy_str}.")

    # 3. Out of Range Explanations (with patient-friendly context, avoiding diagnosis)
    out_of_range_explanations: List[Dict[str, str]] = []
    for item in out_of_range_items:
        t_upper = item.test_name.upper()
        glossary_desc = ""
        for k, v in FRIENDLY_TEST_GLOSSARY.items():
            if k in t_upper:
                glossary_desc = f" ({v})"
                break

        direction = "elevated (above source high threshold)" if item.status == ValueStatus.HIGH else "below source low threshold"
        ref_text = item.reference_range_raw or "Source-defined limit"

        explanation = (
            f"Result was {item.value} {item.unit}, which is {direction} of [{ref_text}].{glossary_desc} "
            f"Discuss this with your clinician to understand what this means for your individual health context."
        )
        out_of_range_explanations.append({
            "test_name": item.test_name,
            "status": item.status.value,
            "value": f"{item.value} {item.unit}".strip(),
            "reference_range": ref_text,
            "explanation": explanation
        })

    # 4. Questions to Discuss with Physician
    questions_for_doctor: List[str] = [
        "How do these laboratory results relate to my current symptoms and day-to-day energy levels?",
    ]

    if out_of_range_items:
        flagged_names = ", ".join([item.test_name for item in out_of_range_items[:3]])
        questions_for_doctor.append(
            f"What follow-up steps, lifestyle adjustments, or repeat testing do you recommend regarding my {flagged_names}?"
        )

    if patient.medications:
        questions_for_doctor.append(
            "Are my current medications still at optimal dosages based on these latest lab results and kidney/liver markers?"
        )

    questions_for_doctor.append(
        "When should I schedule my next routine check-up or follow-up blood work?"
    )

    return PatientFriendlySummary(
        overview=overview,
        key_findings=key_findings,
        out_of_range_explanations=out_of_range_explanations,
        questions_for_doctor=questions_for_doctor,
        generation_engine="Clinical Synthesis Engine (Deterministic & Guardrailed)"
    )


def generate_gemini_summary(record: StructuredMedicalRecord, api_key: str) -> Optional[PatientFriendlySummary]:
    """
    Generates a patient-friendly summary using Google Gemini with strict guardrails:
    - NO medical diagnosis
    - NO drug prescriptions or dosage adjustments
    - Plain, empathetic, educational language
    - Explicit reference to source reference ranges
    """
    try:
        from google import genai
        from google.genai import types
        import json

        client = genai.Client(api_key=api_key)

        # Prepare payload summary for prompt
        patient_info = {
            "age": record.patient.age,
            "sex": record.patient.sex,
            "symptoms": [{"name": s.name, "severity": s.severity, "duration": s.duration} for s in record.patient.symptoms],
            "conditions": [c.condition_name for c in record.patient.existing_conditions],
            "medications": [{"name": m.name, "dosage": m.dosage} for m in record.patient.medications],
            "allergies": [{"allergen": a.allergen, "reaction": a.reaction} for a in record.patient.allergies],
        }

        labs_info = [
            {
                "test": l.test_name,
                "value": f"{l.value} {l.unit}".strip(),
                "status": l.status.value,
                "source_ref_range": l.reference_range_raw,
                "category": l.category
            }
            for l in record.all_lab_results
        ]

        prompt = f"""
You are a helpful clinical communication assistant. Your task is to produce a concise, patient-friendly summary of the medical information provided below.

CRITICAL SAFETY & MEDICAL INSTRUCTIONS:
1. DO NOT provide a medical diagnosis (e.g. do not say "You have diabetes" or "You have anemia").
2. DO NOT provide treatment recommendations or medication alterations.
3. Explain lab findings in simple, easy-to-understand terms.
4. Only reference the source reference ranges provided. Do not fabricate ranges.
5. Provide helpful, constructive questions the patient can ask their doctor.

PATIENT INTAKE:
{json.dumps(patient_info, indent=2)}

LABORATORY FINDINGS:
{json.dumps(labs_info, indent=2)}

Respond with a JSON object containing:
{{
  "overview": "A concise paragraph summarizing the patient context, reported symptoms, and total reports reviewed.",
  "key_findings": ["Bullet 1", "Bullet 2", "Bullet 3"],
  "out_of_range_explanations": [
    {{
      "test_name": "string",
      "status": "LOW or HIGH",
      "value": "string",
      "reference_range": "string",
      "explanation": "Clear, non-diagnostic explanation of what this test measures and what being outside this specific report's range indicates."
    }}
  ],
  "questions_for_doctor": [
    "Question 1 for doctor",
    "Question 2 for doctor",
    "Question 3 for doctor"
  ]
}}
"""

        response = client.models.generate_content(
            model="gemini-2.5-flash",
            contents=prompt,
            config=types.GenerateContentConfig(
                response_mime_type="application/json"
            )
        )

        data = json.loads(response.text)
        return PatientFriendlySummary(
            overview=data.get("overview", ""),
            key_findings=data.get("key_findings", []),
            out_of_range_explanations=data.get("out_of_range_explanations", []),
            questions_for_doctor=data.get("questions_for_doctor", []),
            generation_engine="Google Gemini 2.5 Flash AI"
        )
    except Exception as e:
        print(f"Gemini summary generation failed: {e}. Falling back to deterministic engine.")
        return None


def generate_summary(record: StructuredMedicalRecord, api_key: Optional[str] = None) -> PatientFriendlySummary:
    """
    Main summary coordinator. Tries Gemini AI if key is provided, otherwise uses the deterministic engine.
    """
    if api_key and api_key.strip():
        gemini_res = generate_gemini_summary(record, api_key.strip())
        if gemini_res:
            return gemini_res

    return generate_deterministic_summary(record)
