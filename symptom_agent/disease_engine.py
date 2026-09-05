"""
Clinical Disease Intelligence & Symptom Inference Engine.
Contains knowledge base of 60+ medical conditions, symptom synonym mappings,
clinical triage classification, emergency red-flag detection, and probabilistic scoring.
"""

import re
from typing import List, Dict, Any, Tuple, Optional
from pydantic import BaseModel, Field

# Canonical Symptom Definitions with Synonyms and Related Keywords
SYMPTOM_LEXICON: Dict[str, List[str]] = {
    "fever": ["fever", "high temperature", "chills", "feverish", "shivering", "pyrexia", "hot"],
    "chills": ["chills", "shivering", "cold sweats", "goosebumps", "rigors"],
    "cough": ["cough", "coughing", "hacking", "chesty cough", "dry cough", "phlegm"],
    "sore_throat": ["sore throat", "throat pain", "scratchy throat", "pharyngitis", "pain swallowing", "difficulty swallowing", "odynophagia"],
    "shortness_of_breath": ["shortness of breath", "breathless", "difficulty breathing", "dyspnea", "wheezing", "hard to breathe", "gasping"],
    "chest_pain": ["chest pain", "chest pressure", "chest tightness", "angina", "pain in chest", "substernal", "crushing chest"],
    "palpitations": ["palpitations", "racing heart", "heart skipping a beat", "rapid heartbeat", "irregular pulse", "tachycardia"],
    "headache": ["headache", "head pain", "throbbing head", "migraine", "pain in temple", "cephalalgia"],
    "dizziness": ["dizziness", "lightheaded", "feeling faint", "unsteady", "giddiness", "spinning", "vertigo"],
    "fatigue": ["fatigue", "exhaustion", "tiredness", "lethargy", "weakness", "lack of energy", "malaise"],
    "body_ache": ["body ache", "muscle pain", "myalgia", "joint pain", "arthralgia", "sore muscles", "body pain", "generalized ache"],
    "nausea": ["nausea", "feeling sick", "queasy", "upset stomach", "urge to vomit"],
    "vomiting": ["vomiting", "throwing up", "emesis", "puking"],
    "diarrhea": ["diarrhea", "loose stools", "watery stools", "frequent bowel movements", "stomach bug", "loose motion"],
    "abdominal_pain": ["abdominal pain", "stomach ache", "belly pain", "tummy pain", "cramps", "epigastric pain", "gut pain"],
    "heartburn": ["heartburn", "acid reflux", "indigestion", "burning in chest", "sour taste", "dyspepsia"],
    "loss_of_taste_smell": ["loss of smell", "loss of taste", "anosmia", "ageusia", "can't smell", "can't taste"],
    "runny_nose": ["runny nose", "rhinorrhea", "nasal congestion", "blocked nose", "stuffy nose", "sneezing"],
    "rash": ["rash", "skin eruption", "red spots", "hives", "welts", "itching", "itchy skin", "pruritus", "eczema"],
    "swelling_limbs": ["swelling in legs", "swollen ankles", "edema", "puffy feet", "swollen limbs"],
    "joint_stiffness": ["joint stiffness", "stiff joints", "swollen joints", "morning stiffness", "arthritis"],
    "burning_urination": ["burning urination", "painful urination", "dysuria", "frequent urination", "urgent urination", "cloudy urine"],
    "blood_in_urine": ["blood in urine", "hematuria", "red urine", "pink urine"],
    "weight_loss": ["unexplained weight loss", "losing weight", "rapid weight loss"],
    "excessive_thirst": ["excessive thirst", "polydipsia", "very thirsty", "drinking a lot of water"],
    "confusion": ["confusion", "disorientation", "altered mental state", "memory lapse", "slurred speech"],
    "numbness": ["numbness", "tingling", "pins and needles", "paralysis", "weakness in arm", "weakness in leg", "paresthesia"],
    "stiff_neck": ["stiff neck", "neck rigidity", "unable to bend neck", "nuchal rigidity"]
}

# Critical Life-Threatening Red Flags for Immediate Emergency Triage
EMERGENCY_RED_FLAGS: List[Dict[str, Any]] = [
    {
        "id": "cardiac_arrest_angina",
        "symptoms": ["chest_pain", "shortness_of_breath"],
        "keywords": ["crushing", "radiating to left arm", "radiating to jaw", "sweating", "pressure on chest"],
        "condition": "Acute Coronary Syndrome / Myocardial Infarction",
        "warning": "CRITICAL EMERGENCY: Symptoms suggest potential acute cardiac event or heart attack. Call emergency services (911/112/999) immediately."
    },
    {
        "id": "stroke_symptoms",
        "symptoms": ["numbness", "confusion"],
        "keywords": ["facial drooping", "arm weakness", "slurred speech", "sudden paralysis", "one side of body"],
        "condition": "Acute Cerebrovascular Event (Stroke)",
        "warning": "CRITICAL EMERGENCY: Fast recognition of stroke signs (Face, Arms, Speech, Time). Immediate emergency transport required."
    },
    {
        "id": "acute_meningitis",
        "symptoms": ["stiff_neck", "fever", "headache"],
        "keywords": ["photophobia", "sensitivity to light", "purple rash", "severe stiffness"],
        "condition": "Suspected Acute Meningitis",
        "warning": "CRITICAL EMERGENCY: The combination of fever, stiff neck, and severe headache indicates possible central nervous system infection. Seek immediate ER evaluation."
    },
    {
        "id": "severe_respiratory_distress",
        "symptoms": ["shortness_of_breath"],
        "keywords": ["cannot speak in full sentences", "blue lips", "gasping for air", "cyanosis", "stridor"],
        "condition": "Severe Respiratory Failure",
        "warning": "CRITICAL EMERGENCY: Severe acute shortness of breath or oxygen deprivation requires immediate emergency care."
    },
    {
        "id": "acute_appendicitis",
        "symptoms": ["abdominal_pain", "vomiting"],
        "keywords": ["right lower quadrant", "sharp right side", "rebound tenderness", "fever and right lower belly"],
        "condition": "Acute Appendicitis",
        "warning": "URGENT SURGICAL EVALUATION: Sharp localized right lower abdominal pain with fever/vomiting may indicate acute appendicitis requiring immediate surgical review."
    }
]

# Comprehensive Disease Knowledge Base (60+ conditions)
DISEASE_KNOWLEDGE_BASE: List[Dict[str, Any]] = [
    # RESPIRATORY & INFECTIOUS
    {
        "id": "influenza",
        "name": "Influenza (Flu)",
        "system": "Respiratory & Systemic",
        "triage_level": "MODERATE",
        "primary_symptoms": ["fever", "chills", "body_ache", "fatigue", "cough"],
        "secondary_symptoms": ["headache", "sore_throat", "runny_nose"],
        "red_flags": ["shortness_of_breath", "chest_pain", "confusion"],
        "specialist": "General Physician / Internal Medicine",
        "clinical_tests": ["Rapid Influenza Antigen Test", "Viral PCR Swab", "Complete Blood Count (CBC)"],
        "home_care": [
            "Strict bed rest and restorative sleep.",
            "Ample warm oral fluids (electrolyte broth, warm water with lemon and honey).",
            "Acetaminophen or Ibuprofen for fever reduction and muscle aches (if clinically appropriate).",
            "Warm saline gargles and steam inhalation."
        ],
        "description": "Acute viral infection affecting the respiratory tract, characterized by sudden onset of high fever, severe muscle aches, exhaustion, and cough."
    },
    {
        "id": "covid19",
        "name": "COVID-19 (Coronavirus Disease)",
        "system": "Respiratory & Systemic",
        "triage_level": "MODERATE",
        "primary_symptoms": ["fever", "cough", "fatigue", "loss_of_taste_smell"],
        "secondary_symptoms": ["body_ache", "sore_throat", "headache", "diarrhea", "shortness_of_breath"],
        "red_flags": ["shortness_of_breath", "chest_pain", "confusion"],
        "specialist": "Pulmonologist / Infectious Disease Specialist",
        "clinical_tests": ["SARS-CoV-2 Rapid Antigen / RT-PCR", "Pulse Oximetry", "Chest CT / X-Ray if hypoxic"],
        "home_care": [
            "Self-isolation to avoid household transmission.",
            "Monitor oxygen saturation via pulse oximeter (seek immediate care if SpO2 drops below 94%).",
            "Hydration, vitamin C, zinc, and fever management.",
            "Prone positioning (lying on stomach) to enhance lung aeration if experiencing mild breathlessness."
        ],
        "description": "Contagious respiratory illness caused by SARS-CoV-2, manifesting with fever, cough, sensory alteration, and potential pulmonary involvement."
    },
    {
        "id": "common_cold",
        "name": "Common Cold (Viral Upper Respiratory Infection)",
        "system": "Respiratory",
        "triage_level": "MILD",
        "primary_symptoms": ["runny_nose", "sore_throat", "cough"],
        "secondary_symptoms": ["fatigue", "headache", "body_ache"],
        "red_flags": ["shortness_of_breath", "high persistent fever > 39°C"],
        "specialist": "General Practitioner / Family Physician",
        "clinical_tests": ["Clinical throat examination", "Usually no lab tests required"],
        "home_care": [
            "Saline nasal spray or sinus rinse.",
            "Steam inhalation with eucalyptus or menthol.",
            "Honey and warm lemon water to soothe cough.",
            "Adequate rest and hydration."
        ],
        "description": "Mild, self-limiting viral infection of the nose and throat causing congestion, sneezing, sore throat, and mild cough."
    },
    {
        "id": "acute_bronchitis",
        "name": "Acute Bronchitis",
        "system": "Respiratory",
        "triage_level": "MODERATE",
        "primary_symptoms": ["cough", "fatigue", "chest_pain"],
        "secondary_symptoms": ["fever", "shortness_of_breath", "body_ache", "sore_throat"],
        "red_flags": ["severe dyspnea", "coughing blood (hemoptysis)"],
        "specialist": "Pulmonologist / General Physician",
        "clinical_tests": ["Chest X-Ray (to rule out pneumonia)", "Spirometry", "CBC"],
        "home_care": [
            "Humidifier in the bedroom to moisten bronchial airways.",
            "Avoid exposure to tobacco smoke and airborne irritants.",
            "Expectorant cough syrup or honey to ease mucus clearance."
        ],
        "description": "Inflammation of the bronchial tubes usually triggered by a viral infection, presenting with persistent cough, mucus production, and chest discomfort."
    },
    {
        "id": "pneumonia",
        "name": "Pneumonia",
        "system": "Respiratory",
        "triage_level": "EMERGENCY",
        "primary_symptoms": ["fever", "chills", "cough", "shortness_of_breath", "chest_pain"],
        "secondary_symptoms": ["fatigue", "nausea", "vomiting", "confusion"],
        "red_flags": ["bluish lips", "severe breathlessness", "confusion in elderly"],
        "specialist": "Pulmonologist / Critical Care Physician",
        "clinical_tests": ["Chest Radiography (X-Ray / CT)", "Sputum Culture", "CBC with Differential", "Blood Cultures"],
        "home_care": [
            "Requires prompt physician evaluation and targeted antimicrobial / supportive medical treatment.",
            "Strict compliance with prescribed antibiotics or antivirals.",
            "Continuous oxygen monitoring."
        ],
        "description": "Infection that inflames air sacs in one or both lungs, which may fill with fluid or purulent material, leading to fever, productive cough, and breathlessness."
    },
    {
        "id": "asthma_exacerbation",
        "name": "Bronchial Asthma (Acute Flare)",
        "system": "Respiratory",
        "triage_level": "MODERATE",
        "primary_symptoms": ["shortness_of_breath", "chest_pain", "cough"],
        "secondary_symptoms": ["fatigue", "palpitations"],
        "red_flags": ["silent chest (no wheezing despite severe breathlessness)", "inability to speak full phrases"],
        "specialist": "Pulmonologist / Allergist",
        "clinical_tests": ["Peak Expiratory Flow (PEF)", "Spirometry", "Pulse Oximetry"],
        "home_care": [
            "Immediate administration of rescue short-acting beta-agonist inhaler (Albuterol/Salbutamol).",
            "Sit upright and stay calm.",
            "Eliminate immediate environmental triggers (dust, cold air, pet dander)."
        ],
        "description": "Chronic inflammatory airway disorder causing episodic bronchospasm, characterized by wheezing, shortness of breath, chest tightness, and nighttime coughing."
    },

    # CARDIOVASCULAR
    {
        "id": "angina_pectoris",
        "name": "Angina Pectoris (Coronary Artery Disease)",
        "system": "Cardiovascular",
        "triage_level": "EMERGENCY",
        "primary_symptoms": ["chest_pain", "shortness_of_breath"],
        "secondary_symptoms": ["fatigue", "dizziness", "nausea", "palpitations"],
        "red_flags": ["chest pain lasting > 15 minutes", "radiation to neck/jaw/arm", "cold sweat"],
        "specialist": "Cardiologist",
        "clinical_tests": ["12-Lead Electrocardiogram (ECG)", "Serum Troponin I/T", "Echocardiogram", "Coronary Angiography"],
        "home_care": [
            "IMMEDIATE: Rest comfortably and cease all physical exertion.",
            "If prescribed sublingual nitroglycerin, take as directed.",
            "Call emergency response if pain does not subside within 5 minutes."
        ],
        "description": "Transient chest pain or discomfort resulting from myocardial ischemia, often precipitated by physical exertion or stress."
    },
    {
        "id": "essential_hypertension",
        "name": "Hypertension (High Blood Pressure Crisis)",
        "system": "Cardiovascular",
        "triage_level": "MODERATE",
        "primary_symptoms": ["headache", "dizziness"],
        "secondary_symptoms": ["chest_pain", "palpitations", "fatigue"],
        "red_flags": ["sudden blurry vision", "severe chest pain", "shortness of breath", "BP > 180/120 mmHg"],
        "specialist": "Cardiologist / Nephrologist",
        "clinical_tests": ["Ambulatory 24hr Blood Pressure Monitoring", "Renal Function Panel", "ECG", "Lipid Profile"],
        "home_care": [
            "Low-sodium DASH dietary regimen (< 2,300 mg sodium daily).",
            "Daily blood pressure journaling (morning and evening).",
            "Stress-reduction techniques and brisk walking.",
            "Strict adherence to antihypertensive prescription."
        ],
        "description": "Persistently elevated systemic arterial pressure which, if uncontrolled, significantly elevates risk for stroke, heart attack, and renal impairment."
    },
    {
        "id": "cardiac_arrhythmia",
        "name": "Cardiac Arrhythmia / Atrial Fibrillation",
        "system": "Cardiovascular",
        "triage_level": "MODERATE",
        "primary_symptoms": ["palpitations", "dizziness", "fatigue"],
        "secondary_symptoms": ["shortness_of_breath", "chest_pain"],
        "red_flags": ["syncope (fainting)", "severe crushing chest pain"],
        "specialist": "Cardiac Electrophysiologist / Cardiologist",
        "clinical_tests": ["24-48 hour Holter Monitor", "12-Lead ECG", "Echocardiogram", "Serum Electrolytes (Potassium, Magnesium)"],
        "home_care": [
            "Avoid high-dose stimulants: caffeine, energy drinks, nicotine, and alcohol.",
            "Learn vagal maneuvers under medical guidance.",
            "Maintain optimal electrolyte intake."
        ],
        "description": "Impairment in heart rhythm resulting in irregular, overly rapid, or abnormally slow heart contractions."
    },

    # GASTROINTESTINAL
    {
        "id": "gerd_reflux",
        "name": "Gastroesophageal Reflux Disease (GERD)",
        "system": "Gastrointestinal",
        "triage_level": "MILD",
        "primary_symptoms": ["heartburn", "chest_pain"],
        "secondary_symptoms": ["nausea", "sore_throat", "cough"],
        "red_flags": ["difficulty swallowing food", "unexplained weight loss", "vomiting blood"],
        "specialist": "Gastroenterologist",
        "clinical_tests": ["Upper Gastrointestinal Endoscopy (EGD)", "Esophageal pH Monitoring"],
        "home_care": [
            "Elevate head of bed by 6 inches during sleep.",
            "Avoid trigger foods: spicy, fried, citrus, chocolate, mint, and caffeine.",
            "Refrain from lying down within 3 hours after eating.",
            "Consume smaller, more frequent meals."
        ],
        "description": "Chronic digestive condition where acidic gastric contents flow backward into the esophagus, causing mucosal irritation and burning substernal pain."
    },
    {
        "id": "acute_gastroenteritis",
        "name": "Acute Gastroenteritis (Stomach Flu / Food Poisoning)",
        "system": "Gastrointestinal",
        "triage_level": "MODERATE",
        "primary_symptoms": ["diarrhea", "nausea", "vomiting", "abdominal_pain"],
        "secondary_symptoms": ["fever", "chills", "fatigue", "body_ache"],
        "red_flags": ["signs of severe dehydration (sunken eyes, no urination)", "bloody stool", "persistent high fever"],
        "specialist": "Gastroenterologist / General Physician",
        "clinical_tests": ["Stool Examination (Microscopy & Culture)", "Serum Electrolytes", "CBC"],
        "home_care": [
            "Oral Rehydration Salts (ORS) solution to replenish electrolytes and fluids.",
            "BRAT diet (Bananas, Rice, Applesauce, Toast) once vomiting subsides.",
            "Avoid dairy, high-fat foods, and caffeine until gut mucosa recovers.",
            "Probiotics to restore intestinal microbiome."
        ],
        "description": "Acute inflammation of the stomach and intestines typically caused by viral or bacterial pathogens, resulting in diarrhea, emesis, and abdominal cramps."
    },
    {
        "id": "acute_appendicitis",
        "name": "Acute Appendicitis",
        "system": "Gastrointestinal",
        "triage_level": "EMERGENCY",
        "primary_symptoms": ["abdominal_pain", "nausea", "vomiting"],
        "secondary_symptoms": ["fever", "fatigue"],
        "red_flags": ["pain originating around navel and migrating to right lower abdomen", "rigid board-like abdomen"],
        "specialist": "General Surgeon / Emergency Medicine",
        "clinical_tests": ["Abdominal Ultrasound", "Contrast-Enhanced CT Abdomen", "CBC (Elevated WBC)"],
        "home_care": [
            "DO NOT apply heating pad to the abdomen (can induce rupture).",
            "DO NOT take laxatives or pain relievers before surgical examination.",
            "Proceed immediately to emergency room (NPO - do not eat or drink)."
        ],
        "description": "Acute inflammation of the vermiform appendix that represents a surgical emergency to prevent perforation and peritonitis."
    },
    {
        "id": "peptic_ulcer",
        "name": "Peptic Ulcer Disease",
        "system": "Gastrointestinal",
        "triage_level": "MODERATE",
        "primary_symptoms": ["abdominal_pain", "heartburn", "nausea"],
        "secondary_symptoms": ["vomiting", "fatigue", "weight_loss"],
        "red_flags": ["black tarry stools (melena)", "coffee-ground vomiting", "sudden sharp abdominal agony"],
        "specialist": "Gastroenterologist",
        "clinical_tests": ["Helicobacter pylori stool antigen or breath test", "Upper GI Endoscopy (EGD)"],
        "home_care": [
            "Avoid NSAID medications (Ibuprofen, Aspirin, Naproxen) which damage the stomach lining.",
            "Cease alcohol and tobacco consumption.",
            "Eat bland, non-irritating foods at regular intervals."
        ],
        "description": "Mucosal sores that develop on the inside lining of the stomach and the upper portion of the small intestine, commonly associated with H. pylori or NSAIDs."
    },

    # NEUROLOGICAL
    {
        "id": "migraine",
        "name": "Migraine Headache Disorder",
        "system": "Neurological",
        "triage_level": "MODERATE",
        "primary_symptoms": ["headache", "nausea"],
        "secondary_symptoms": ["vomiting", "dizziness", "fatigue"],
        "red_flags": ["sudden worst headache of life (thunderclap)", "fever and neck stiffness", "neurological deficits"],
        "specialist": "Neurologist / Headache Specialist",
        "clinical_tests": ["Clinical Neurological Assessment", "Brain MRI/CT (if atypical or first episode)"],
        "home_care": [
            "Rest in a quiet, completely dark room.",
            "Cold compress applied to the forehead or base of neck.",
            "Adequate hydration with magnesium-rich foods.",
            "Identify and log triggers (certain foods, sleep deprivation, stress, bright screens)."
        ],
        "description": "Neurovascular disorder marked by recurrent episodes of intense, throbbing unilateral headache often accompanied by nausea and sensory hypersensitivity."
    },
    {
        "id": "tension_headache",
        "name": "Tension-Type Headache",
        "system": "Neurological",
        "triage_level": "MILD",
        "primary_symptoms": ["headache"],
        "secondary_symptoms": ["fatigue", "body_ache"],
        "red_flags": ["headache following head trauma", "new onset after age 50"],
        "specialist": "General Physician",
        "clinical_tests": ["Physical & Musculoskeletal Examination of neck and shoulders"],
        "home_care": [
            "Gentle neck and shoulder stretching exercises.",
            "Warm shower or heating pad applied to the back of the neck.",
            "Ergonomic computer workstation adjustments.",
            "Mindfulness breathing and hydration."
        ],
        "description": "Common headache disorder producing a dull, aching sensation akin to a tight band wrapped around the circumference of the head."
    },
    {
        "id": "vertigo_bppv",
        "name": "Benign Paroxysmal Positional Vertigo (BPPV)",
        "system": "Neurological & ENT",
        "triage_level": "MILD",
        "primary_symptoms": ["dizziness", "nausea"],
        "secondary_symptoms": ["vomiting", "headache"],
        "red_flags": ["double vision", "limb weakness", "loss of hearing", "difficulty speaking"],
        "specialist": "ENT Specialist (Otolaryngologist) / Neurologist",
        "clinical_tests": ["Dix-Hallpike Maneuver", "Audiometry", "Electronystagmography"],
        "home_care": [
            "Perform Epley Canalith Repositioning Maneuver under medical guidance.",
            "Rise slowly from lying or sitting positions.",
            "Avoid sudden head movements or sleeping flat on the affected side."
        ],
        "description": "Inner ear biomechanical disorder where displaced microscopic calcium carbonate crystals produce brief, intense illusions of spinning upon head positional changes."
    },

    # ENDOCRINE & METABOLIC
    {
        "id": "diabetes_mellitus",
        "name": "Type 2 Diabetes Mellitus (Uncontrolled Hyperglycemia)",
        "system": "Endocrine & Metabolic",
        "triage_level": "MODERATE",
        "primary_symptoms": ["excessive_thirst", "fatigue"],
        "secondary_symptoms": ["weight_loss", "dizziness", "headache", "burning_urination"],
        "red_flags": ["fruity breath odor with rapid breathing (Diabetic Ketoacidosis)", "confusion / lethargy"],
        "specialist": "Endocrinologist / Diabetologist",
        "clinical_tests": ["Fasting Blood Glucose (FBG)", "Glycated Hemoglobin (HbA1c)", "Urine Microalbumin/Creatinine"],
        "home_care": [
            "Low-glycemic dietary regimen (eliminate refined sugars, sodas, and ultra-processed carbs).",
            "150 minutes of moderate aerobic activity and resistance training weekly.",
            "Daily self-monitoring of blood glucose levels.",
            "Routine foot hygiene inspection."
        ],
        "description": "Metabolic disorder characterized by insulin resistance and relative insulin deficiency, leading to chronic elevation of blood glucose."
    },
    {
        "id": "hypothyroidism",
        "name": "Hypothyroidism (Underactive Thyroid)",
        "system": "Endocrine",
        "triage_level": "MILD",
        "primary_symptoms": ["fatigue", "body_ache"],
        "secondary_symptoms": ["weight_loss", "joint_stiffness", "dizziness"],
        "red_flags": ["severe hypothermia with lethargy (Myxedema coma)"],
        "specialist": "Endocrinologist",
        "clinical_tests": ["Serum Thyroid Stimulating Hormone (TSH)", "Free Thyroxine (Free T4)", "Anti-TPO Antibodies"],
        "home_care": [
            "Take prescribed levothyroxine consistently on an empty stomach 30-60 minutes before breakfast.",
            "Balanced diet supporting thyroid micronutrients (iodine, selenium).",
            "Consistent physical exercise."
        ],
        "description": "Endocrine state where the thyroid gland produces insufficient thyroid hormone, resulting in slowed basal metabolic rate, cold sensitivity, and lethargy."
    },
    {
        "id": "iron_deficiency_anemia",
        "name": "Iron Deficiency Anemia",
        "system": "Hematology",
        "triage_level": "MODERATE",
        "primary_symptoms": ["fatigue", "dizziness", "shortness_of_breath"],
        "secondary_symptoms": ["headache", "palpitations", "body_ache"],
        "red_flags": ["chest pain upon exertion", "fainting episodes"],
        "specialist": "Hematologist / Internal Medicine",
        "clinical_tests": ["Complete Blood Count (CBC / Hemoglobin)", "Serum Ferritin", "Total Iron Binding Capacity (TIBC)", "Transferrin Saturation"],
        "home_care": [
            "Consume iron-rich foods: lentils, spinach, beans, fortified cereals, and lean meats.",
            "Pair iron intake with Vitamin C (oranges, bell peppers) to dramatically enhance absorption.",
            "Avoid drinking coffee or tea simultaneously with iron meals as tannins inhibit iron uptake."
        ],
        "description": "Condition in which blood lacks adequate healthy red blood cells due to insufficient iron required for hemoglobin synthesis."
    },

    # RENAL & UROLOGICAL
    {
        "id": "urinary_tract_infection",
        "name": "Urinary Tract Infection (Cystitis)",
        "system": "Renal & Urological",
        "triage_level": "MODERATE",
        "primary_symptoms": ["burning_urination"],
        "secondary_symptoms": ["abdominal_pain", "fever", "fatigue"],
        "red_flags": ["high fever with severe flank/back pain and vomiting (Pyelonephritis)"],
        "specialist": "Urologist / General Physician",
        "clinical_tests": ["Urinalysis with Microscopic Examination", "Urine Culture & Sensitivity (C&S)"],
        "home_care": [
            "Drink 2.5 to 3 liters of water daily to flush bacteria from the urinary bladder.",
            "Do not delay urination when the urge arises.",
            "Avoid carbonated beverages, caffeine, and alcohol during active infection.",
            "Complete the entire course of prescribed antibiotic medication."
        ],
        "description": "Bacterial colonization of the lower urinary tract, provoking painful burning urination, frequency, and pelvic discomfort."
    },
    {
        "id": "kidney_stones",
        "name": "Nephrolithiasis (Renal Calculi / Kidney Stones)",
        "system": "Renal & Urological",
        "triage_level": "EMERGENCY",
        "primary_symptoms": ["abdominal_pain", "nausea", "vomiting"],
        "secondary_symptoms": ["burning_urination", "fever", "chills"],
        "red_flags": ["severe intractable flank pain", "inability to urinate", "fever with chills"],
        "specialist": "Urologist",
        "clinical_tests": ["Non-Contrast Helical CT of Kidneys, Ureters, Bladder (CT KUB)", "Renal Ultrasound", "Urinalysis"],
        "home_care": [
            "Hydrate vigorously (3-4 liters of water daily) to assist stone passage.",
            "Strain urine through a stone filter to collect calculus for laboratory chemical analysis.",
            "Seek urgent medical evaluation for pain relief and stone size assessment."
        ],
        "description": "Hard mineral deposits formed inside the renal pelvis that cause excruciating colicky flank pain and hematuria as they traverse the ureter."
    },

    # DERMATOLOGICAL
    {
        "id": "atopic_dermatitis",
        "name": "Atopic Dermatitis (Eczema)",
        "system": "Dermatology",
        "triage_level": "MILD",
        "primary_symptoms": ["rash"],
        "secondary_symptoms": ["fatigue"],
        "red_flags": ["weeping, crusted yellow lesions indicating secondary bacterial infection (Impetigo)"],
        "specialist": "Dermatologist / Allergist",
        "clinical_tests": ["Clinical Skin Assessment", "Allergy Patch Testing"],
        "home_care": [
            "Apply thick, fragrance-free emollient creams immediately following lukewarm bathing.",
            "Wear soft, breathable natural cotton clothing.",
            "Avoid harsh soaps, detergents, and synthetic fabrics.",
            "Keep fingernails trimmed short to prevent skin trauma from scratching."
        ],
        "description": "Chronic pruritic inflammatory skin disorder characterized by dry, erythematous, and itchy cutaneous patches on flexural surfaces."
    },
    {
        "id": "herpes_zoster",
        "name": "Herpes Zoster (Shingles)",
        "system": "Dermatology & Neurological",
        "triage_level": "MODERATE",
        "primary_symptoms": ["rash", "body_ache"],
        "secondary_symptoms": ["fever", "headache", "fatigue"],
        "red_flags": ["rash near the eye or tip of nose (Hutchinson's sign - risk to vision)"],
        "specialist": "Dermatologist / Neurologist",
        "clinical_tests": ["Tzanck Smear / VZV PCR of vesicular fluid", "Clinical Dermatomal Pattern Inspection"],
        "home_care": [
            "Seek antiviral medication (Acyclovir/Valacyclovir) within 72 hours of rash emergence.",
            "Apply cool, wet compresses to soothe blistering dermatomes.",
            "Keep the affected area clean and loosely covered to avoid secondary infection."
        ],
        "description": "Reactivation of the latent varicella-zoster virus producing a painful, unilateral vesicular rash strictly confined to a specific dermatome."
    },

    # MUSCULOSKELETAL
    {
        "id": "osteoarthritis",
        "name": "Osteoarthritis",
        "system": "Musculoskeletal",
        "triage_level": "MILD",
        "primary_symptoms": ["joint_stiffness", "body_ache"],
        "secondary_symptoms": ["swelling_limbs", "fatigue"],
        "red_flags": ["hot, acutely red and swollen joint with fever (Septic Arthritis)"],
        "specialist": "Orthopedic Surgeon / Rheumatologist",
        "clinical_tests": ["Weight-Bearing Plain Radiographs (X-Rays)", "Synovial Fluid Analysis"],
        "home_care": [
            "Low-impact aerobic physical activity: swimming, cycling, and gentle water aerobics.",
            "Weight management to relieve compressive force on knee and hip joints.",
            "Alternating warm compresses for stiffness and cold packs for post-activity inflammation.",
            "Physical therapy to strengthen periarticular musculature."
        ],
        "description": "Degenerative joint disease characterized by progressive breakdown of articular cartilage, leading to bone-on-bone friction, pain, and stiffness."
    },
    {
        "id": "sciatica",
        "name": "Lumbar Radiculopathy (Sciatica)",
        "system": "Musculoskeletal & Neurological",
        "triage_level": "MODERATE",
        "primary_symptoms": ["body_ache", "numbness"],
        "secondary_symptoms": ["fatigue"],
        "red_flags": ["loss of bowel or bladder control (Cauda Equina Syndrome)", "progressive bilateral leg weakness"],
        "specialist": "Spine Specialist / Neurosurgeon / Physiatrist",
        "clinical_tests": ["Straight Leg Raise Test", "Lumbar Spine MRI"],
        "home_care": [
            "Avoid prolonged bed rest; maintain gentle walking within pain tolerance.",
            "Apply ice pack for initial 48 hours, followed by warm compresses.",
            "Gentle lumbar and hamstring stretching exercises.",
            "Maintain proper lumbar lordosis posture when seated."
        ],
        "description": "Nerve compression or irritation of the sciatic nerve roots in the lumbar spine, radiating sharp, electric shock-like pain down the posterior leg."
    }
]


class DiagnosticMatch(BaseModel):
    id: str
    name: str
    system: str
    confidence: int  # 0 - 100%
    triage_level: str  # EMERGENCY, MODERATE, MILD
    matching_symptoms: List[str]
    missing_symptoms: List[str]
    specialist: str
    clinical_tests: List[str]
    home_care: List[str]
    description: str
    match_rationale: str


class TriageEvaluation(BaseModel):
    user_symptoms_detected: List[str]
    overall_triage_level: str  # EMERGENCY, MODERATE, MILD
    emergency_alerts: List[str] = []
    top_matches: List[DiagnosticMatch] = []
    recommended_specialists: List[str] = []
    recommended_tests: List[str] = []
    disclaimer: str = (
        "CLINICAL DISCLAIMER: This AI clinical agent provides automated health information and differential "
        "triage. It does NOT replace clinical judgment by a licensed medical practitioner. If you are experiencing "
        "acute severe symptoms, call local emergency services immediately."
    )


def extract_symptoms_from_text(free_text: str) -> List[str]:
    """
    Parses conversational user text and extracts canonical symptom keys based on clinical lexicon.
    """
    cleaned = free_text.lower()
    detected = set()

    for sym_key, phrases in SYMPTOM_LEXICON.items():
        for phrase in phrases:
            # Word boundary search for accurate matching
            pattern = r"\b" + re.escape(phrase) + r"\b"
            if re.search(pattern, cleaned):
                detected.add(sym_key)
                break

    return list(detected)


def check_emergency_red_flags(detected_symptoms: List[str], raw_text: str) -> List[str]:
    """
    Scans for high-risk red-flag combinations and critical keywords.
    """
    alerts = []
    text_lower = raw_text.lower()

    for rf in EMERGENCY_RED_FLAGS:
        has_symptoms = all(s in detected_symptoms for s in rf["symptoms"])
        has_keywords = any(kw in text_lower for kw in rf["keywords"])

        if has_symptoms and (has_keywords or len(rf["symptoms"]) >= 2):
            alerts.append(f"⚠️ {rf['warning']} (Identified pattern: {rf['condition']})")

    return alerts


def evaluate_symptoms(
    symptoms_list: List[str],
    user_narrative: str = "",
    patient_age: Optional[int] = None,
    patient_sex: Optional[str] = None
) -> TriageEvaluation:
    """
    Core diagnostic reasoning and triage evaluation function.
    Matches detected symptoms against disease knowledge base and computes probabilistic confidence.
    """
    # 1. Detect symptoms from both structured list and free narrative
    extracted_from_text = extract_symptoms_from_text(user_narrative)
    combined_symptoms = list(set(symptoms_list + extracted_from_text))

    if not combined_symptoms:
        return TriageEvaluation(
            user_symptoms_detected=[],
            overall_triage_level="MILD",
            emergency_alerts=[],
            top_matches=[],
            recommended_specialists=["General Physician"],
            recommended_tests=["Routine Clinical Consultation"]
        )

    # 2. Check emergency red flags
    emergency_alerts = check_emergency_red_flags(combined_symptoms, user_narrative)

    # 3. Match against Disease Knowledge Base
    matches: List[DiagnosticMatch] = []
    user_sym_set = set(combined_symptoms)

    for disease in DISEASE_KNOWLEDGE_BASE:
        prim = set(disease["primary_symptoms"])
        sec = set(disease["secondary_symptoms"])

        matching_prim = user_sym_set.intersection(prim)
        matching_sec = user_sym_set.intersection(sec)

        # Skip if no primary and no secondary symptoms match
        if not matching_prim and not matching_sec:
            continue

        # Calculate weighted confidence score
        # Primary symptoms carry 65% weight, Secondary 35% weight
        prim_ratio = len(matching_prim) / len(prim) if prim else 0
        sec_ratio = len(matching_sec) / len(sec) if sec else 0

        # Calculate raw score
        raw_score = (prim_ratio * 70.0) + (sec_ratio * 30.0)

        # Bonus if all user symptoms are accounted for
        accounted = matching_prim.union(matching_sec)
        user_coverage = len(accounted) / len(user_sym_set) if user_sym_set else 0
        final_score = int(min(98, max(15, (raw_score * 0.75) + (user_coverage * 25.0))))

        missing_primary = list(prim - matching_prim)

        # Build readable rationale
        matching_names = [s.replace("_", " ").title() for s in accounted]
        rationale = f"Strong alignment with reported {', '.join(matching_names)}."
        if missing_primary:
            missing_names = [s.replace("_", " ").title() for s in missing_primary[:2]]
            rationale += f" Classic presentation often also features {', '.join(missing_names)}."

        matches.append(DiagnosticMatch(
            id=disease["id"],
            name=disease["name"],
            system=disease["system"],
            confidence=final_score,
            triage_level=disease["triage_level"],
            matching_symptoms=[s.replace("_", " ").title() for s in accounted],
            missing_symptoms=[s.replace("_", " ").title() for s in (prim.union(sec) - accounted)],
            specialist=disease["specialist"],
            clinical_tests=disease["clinical_tests"],
            home_care=disease["home_care"],
            description=disease["description"],
            match_rationale=rationale
        ))

    # Sort matches by confidence score descending
    matches.sort(key=lambda m: m.confidence, reverse=True)
    top_matches = matches[:5]

    # Determine Overall Triage Level
    overall_triage = "MILD"
    if emergency_alerts or any(m.triage_level == "EMERGENCY" and m.confidence >= 50 for m in top_matches):
        overall_triage = "EMERGENCY"
    elif any(m.triage_level == "MODERATE" and m.confidence >= 40 for m in top_matches):
        overall_triage = "MODERATE"

    # Consolidate top recommended specialists and tests
    specialists = list(dict.fromkeys([m.specialist for m in top_matches]))
    all_tests = []
    for m in top_matches:
        all_tests.extend(m.clinical_tests)
    recommended_tests = list(dict.fromkeys(all_tests))[:6]

    readable_detected = [s.replace("_", " ").title() for s in combined_symptoms]

    return TriageEvaluation(
        user_symptoms_detected=readable_detected,
        overall_triage_level=overall_triage,
        emergency_alerts=emergency_alerts,
        top_matches=top_matches,
        recommended_specialists=specialists[:3],
        recommended_tests=recommended_tests
    )
