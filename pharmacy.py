"""
MedLens Online Pharmacy Engine & Medication Intent Detector.
Detects medication and tablet queries from patient text/chat,
provides clinical pharmacology guidance with safety precautions,
and coordinates seamless redirection to the integrated online pharmacy.
"""

import re
from typing import List, Dict, Any, Optional
from models import PharmacyProduct, CartItem, PharmacyOrder

# Comprehensive catalog of commonly searched & prescribed medications
PHARMACY_CATALOG: List[PharmacyProduct] = [
    PharmacyProduct(
        product_id="rx-paracetamol-500",
        name="Paracetamol 500mg (Acetaminophen)",
        generic_name="Paracetamol",
        category="Pain Relief & Fever",
        strength="500 mg",
        dosage_form="Tablet",
        price=4.99,
        discount_price=3.99,
        pack_size="Strip of 20 Tablets",
        in_stock=True,
        stock_quantity=120,
        rx_required=False,
        rating=4.9,
        badge="Best Seller / OTC",
        description="Fast-acting antipyretic and analgesic tablet for reduction of fever and mild-to-moderate aches and pains.",
        uses=["Fever reduction (antipyretic)", "Headache, toothache, and muscular strain", "Post-vaccination discomfort"],
        side_effects=["Rare at therapeutic doses. Avoid alcohol. High doses can cause acute liver toxicity."],
        dosage_guidance="Adults: 1-2 tablets (500-1000mg) every 4-6 hours as needed. Do not exceed 4,000mg (4g) within 24 hours.",
        precautions="Do not combine with other acetaminophen/paracetamol-containing medications to prevent accidental overdose."
    ),
    PharmacyProduct(
        product_id="rx-metformin-500",
        name="Metformin Hydrochloride 500mg",
        generic_name="Metformin",
        category="Diabetes Care",
        strength="500 mg",
        dosage_form="Extended Release Tablet",
        price=12.50,
        discount_price=9.99,
        pack_size="Box of 60 Extended Release Tablets",
        in_stock=True,
        stock_quantity=85,
        rx_required=True,
        rating=4.8,
        badge="Prescription Essential",
        description="First-line oral biguanide antihyperglycemic medication designed to improve insulin sensitivity and glycemic control.",
        uses=["Type 2 Diabetes Mellitus glycemic management", "Insulin resistance support"],
        side_effects=["Mild gastrointestinal discomfort, bloating, or loose stools initially; rare lactic acidosis."],
        dosage_guidance="Take with meals to minimize GI side effects. Starting dose typically 500mg once or twice daily, as titrated by physician.",
        precautions="Requires renal function (eGFR) monitoring prior to initiation and periodically thereafter."
    ),
    PharmacyProduct(
        product_id="rx-atorvastatin-20",
        name="Atorvastatin Calcium 20mg",
        generic_name="Atorvastatin",
        category="Cardiovascular & Lipids",
        strength="20 mg",
        dosage_form="Film-Coated Tablet",
        price=18.00,
        discount_price=14.50,
        pack_size="Pack of 30 Tablets",
        in_stock=True,
        stock_quantity=60,
        rx_required=True,
        rating=4.7,
        badge="Cardiology Care",
        description="HMG-CoA reductase inhibitor (statin) that lowers low-density lipoprotein (LDL) and total cholesterol to mitigate cardiovascular risk.",
        uses=["Primary and secondary hypercholesterolemia", "Prevention of cardiovascular events and plaque stabilization"],
        side_effects=["Occasional mild muscle aches (myalgia), digestive upset, slight elevation in liver enzymes."],
        dosage_guidance="Take once daily at evening or bedtime, with or without food. Follow prescribed dosage strictly.",
        precautions="Avoid large quantities of grapefruit juice. Report unexplained muscle soreness or weakness to your doctor promptly."
    ),
    PharmacyProduct(
        product_id="rx-amoxicillin-500",
        name="Amoxicillin 500mg",
        generic_name="Amoxicillin",
        category="Antibiotics",
        strength="500 mg",
        dosage_form="Capsule",
        price=15.20,
        discount_price=11.90,
        pack_size="Course of 21 Capsules",
        in_stock=True,
        stock_quantity=45,
        rx_required=True,
        rating=4.8,
        badge="Prescription Antibiotic",
        description="Broad-spectrum beta-lactam penicillin-class antibiotic active against susceptible gram-positive and gram-negative bacterial infections.",
        uses=["Bacterial respiratory tract infections", "Acute otitis media", "Skin and soft tissue bacterial infections"],
        side_effects=["Nausea, mild diarrhea, abdominal discomfort, allergic skin rash in sensitive individuals."],
        dosage_guidance="Take one capsule every 8 hours (or as prescribed) with water. Complete full course even if symptoms improve.",
        precautions="Strictly contraindicated in individuals with known penicillin or beta-lactam hypersensitivity."
    ),
    PharmacyProduct(
        product_id="rx-ibuprofen-400",
        name="Ibuprofen 400mg",
        generic_name="Ibuprofen",
        category="Pain Relief & Fever",
        strength="400 mg",
        dosage_form="Coated Tablet",
        price=6.50,
        discount_price=5.25,
        pack_size="Blister Pack of 24 Tablets",
        in_stock=True,
        stock_quantity=110,
        rx_required=False,
        rating=4.8,
        badge="Anti-inflammatory OTC",
        description="Non-steroidal anti-inflammatory drug (NSAID) providing effective relief from acute inflammatory pain, joint stiffness, and fever.",
        uses=["Joint inflammation, arthritis, muscle aches", "Dental pain, dysmenorrhea", "Acute inflammatory swelling"],
        side_effects=["Stomach irritation, heartburn, nausea. Prolonged usage requires stomach mucosal protection."],
        dosage_guidance="Take 1 tablet (400mg) with food or milk. Allow 6-8 hours between doses. Do not exceed 1,200mg/day OTC.",
        precautions="Use with caution in peptic ulcer history, renal insufficiency, or uncontrolled hypertension."
    ),
    PharmacyProduct(
        product_id="rx-cetirizine-10",
        name="Cetirizine Hydrochloride 10mg",
        generic_name="Cetirizine",
        category="Allergy & Antihistamine",
        strength="10 mg",
        dosage_form="Tablet",
        price=7.00,
        discount_price=5.50,
        pack_size="Strip of 30 Tablets",
        in_stock=True,
        stock_quantity=95,
        rx_required=False,
        rating=4.9,
        badge="24h Non-Drowsy Allergy Relief",
        description="Second-generation H1-receptor antihistamine that suppresses histamine-induced allergy symptoms with minimal sedation.",
        uses=["Seasonal and perennial allergic rhinitis", "Urticaria (hives) and pruritus", "Sneezing, itchy watery eyes, runny nose"],
        side_effects=["Mild dry mouth, occasional slight drowsiness in sensitive persons."],
        dosage_guidance="Take 1 tablet (10mg) once daily with water, morning or evening.",
        precautions="Avoid heavy alcohol consumption. Consult physician if you have severe kidney impairment."
    ),
    PharmacyProduct(
        product_id="rx-omeprazole-20",
        name="Omeprazole Delayed-Release 20mg",
        generic_name="Omeprazole",
        category="Digestive Health",
        strength="20 mg",
        dosage_form="Delayed-Release Capsule",
        price=14.00,
        discount_price=10.99,
        pack_size="Bottle of 28 Capsules (4-Week Course)",
        in_stock=True,
        stock_quantity=75,
        rx_required=False,
        rating=4.8,
        badge="Digestive Shield",
        description="Proton pump inhibitor (PPI) that decreases gastric acid production to heal stomach lining and prevent acid reflux.",
        uses=["Gastroesophageal Reflux Disease (GERD)", "Acid indigestion and frequent heartburn", "Gastric and duodenal ulcer healing"],
        side_effects=["Headache, benign stomach cramps, mild diarrhea."],
        dosage_guidance="Swallow whole with a glass of water at least 30-60 minutes before breakfast.",
        precautions="Do not crush or chew delayed-release beads. Prolonged unmonitored usage over a year may affect B12 or magnesium absorption."
    ),
    PharmacyProduct(
        product_id="rx-aspirin-81",
        name="Low-Dose Aspirin 81mg (Enteric Coated)",
        generic_name="Aspirin",
        category="Cardiovascular & Lipids",
        strength="81 mg",
        dosage_form="Enteric-Coated Tablet",
        price=8.50,
        discount_price=6.99,
        pack_size="Bottle of 120 Tablets",
        in_stock=True,
        stock_quantity=90,
        rx_required=False,
        rating=4.9,
        badge="Cardioprotective",
        description="Low-dose antiplatelet therapy indicated for secondary prevention of cardiovascular and cerebrovascular thromboembolic events.",
        uses=["Cardiovascular secondary prevention", "Inhibition of platelet aggregation"],
        side_effects=["Gastric irritation, increased bleeding tendency, easy bruising."],
        dosage_guidance="Take 1 tablet daily as advised by your cardiologist. Enteric coating protects stomach lining.",
        precautions="Contraindicated in bleeding disorders, active stomach ulcers, or salicylate hypersensitivity."
    ),
    PharmacyProduct(
        product_id="rx-azithromycin-500",
        name="Azithromycin 500mg",
        generic_name="Azithromycin",
        category="Antibiotics",
        strength="500 mg",
        dosage_form="Film-Coated Tablet",
        price=21.00,
        discount_price=17.50,
        pack_size="Z-Pack of 3 Tablets (3-Day Regimen)",
        in_stock=True,
        stock_quantity=40,
        rx_required=True,
        rating=4.7,
        badge="Prescription Only",
        description="Broad-spectrum macrolide antibiotic providing tissue-concentrated bactericidal action across short 3 to 5-day therapy cycles.",
        uses=["Acute bacterial bronchitis, community-acquired pneumonia", "Strep throat and tonsillitis in penicillin-allergic patients"],
        side_effects=["Abdominal cramping, loose stools, nausea."],
        dosage_guidance="Take 1 tablet daily for 3 days on an empty stomach or with food, as directed by physician.",
        precautions="Inform provider if you have a history of prolonged QT interval or liver disease."
    ),
    PharmacyProduct(
        product_id="rx-lisinopril-10",
        name="Lisinopril 10mg",
        generic_name="Lisinopril",
        category="Cardiovascular & Lipids",
        strength="10 mg",
        dosage_form="Tablet",
        price=11.00,
        discount_price=8.50,
        pack_size="Pack of 30 Tablets",
        in_stock=True,
        stock_quantity=65,
        rx_required=True,
        rating=4.7,
        badge="Hypertension Care",
        description="Angiotensin-converting enzyme (ACE) inhibitor that relaxes arterial blood vessels to lower elevated blood pressure.",
        uses=["Hypertension management", "Adjunctive therapy in heart failure", "Post-myocardial infarction recovery"],
        side_effects=["Persistent dry cough in a small percentage of patients, dizziness upon standing, elevated potassium."],
        dosage_guidance="Take once daily at the same time each day, with or without food.",
        precautions="Requires periodic monitoring of blood pressure, serum creatinine, and potassium levels."
    ),
    PharmacyProduct(
        product_id="rx-salbutamol-inhaler",
        name="Salbutamol (Albuterol) Inhaler 100mcg",
        generic_name="Salbutamol",
        category="Respiratory Care",
        strength="100 mcg/actuation",
        dosage_form="Metered Dose Inhaler",
        price=24.50,
        discount_price=19.99,
        pack_size="200 Metered Inhalations",
        in_stock=True,
        stock_quantity=50,
        rx_required=True,
        rating=4.9,
        badge="Rapid Bronchodilator",
        description="Short-acting beta2-adrenergic agonist (SABA) providing fast and reliable relief from acute bronchospasm, asthma, and COPD wheeze.",
        uses=["Acute asthma flare-up and bronchospasm relief", "Exercise-induced bronchoconstriction prevention"],
        side_effects=["Transient tremor, elevated heart rate (palpitations), nervousness."],
        dosage_guidance="Inhale 1-2 puffs as needed for acute wheezing. Wait 1 minute between consecutive inhalations.",
        precautions="If requiring more than 3-4 uses per week, consult your pulmonologist for long-term controller medication assessment."
    ),
    PharmacyProduct(
        product_id="rx-vitamin-d3-60k",
        name="Vitamin D3 60,000 IU Softgels",
        generic_name="Cholecalciferol",
        category="Vitamins & Supplements",
        strength="60,000 IU",
        dosage_form="Softgel Capsule",
        price=16.00,
        discount_price=12.99,
        pack_size="Pack of 8 High-Potency Softgels",
        in_stock=True,
        stock_quantity=100,
        rx_required=False,
        rating=4.9,
        badge="Immunity & Bone Health",
        description="Therapeutic high-dose Cholecalciferol formulation designed to rapidly replenish depleted Vitamin D stores and strengthen bone matrix.",
        uses=["Correction of clinically documented Vitamin D deficiency", "Calcium absorption support and osteomalacia prevention"],
        side_effects=["Extremely safe when taken as directed. Do not exceed recommended dosage to prevent hypercalcemia."],
        dosage_guidance="Typically 1 softgel once weekly with a fat-containing meal for 8 weeks, or as directed by doctor.",
        precautions="Verify baseline serum 25-hydroxyvitamin D levels periodically."
    )
]

# Map product names/keywords for fast text matching
MEDICATION_KEYWORD_MAP: Dict[str, str] = {
    "paracetamol": "rx-paracetamol-500",
    "acetaminophen": "rx-paracetamol-500",
    "tylenol": "rx-paracetamol-500",
    "crocin": "rx-paracetamol-500",
    "panadol": "rx-paracetamol-500",
    "calpol": "rx-paracetamol-500",
    "dolo": "rx-paracetamol-500",
    "fever tablet": "rx-paracetamol-500",
    
    "metformin": "rx-metformin-500",
    "glucophage": "rx-metformin-500",
    "glycomet": "rx-metformin-500",
    "diabetes tablet": "rx-metformin-500",
    "sugar tablet": "rx-metformin-500",
    
    "atorvastatin": "rx-atorvastatin-20",
    "lipitor": "rx-atorvastatin-20",
    "cholesterol tablet": "rx-atorvastatin-20",
    "statin": "rx-atorvastatin-20",
    
    "amoxicillin": "rx-amoxicillin-500",
    "amoxil": "rx-amoxicillin-500",
    "augmentin": "rx-amoxicillin-500",
    "mox": "rx-amoxicillin-500",
    
    "ibuprofen": "rx-ibuprofen-400",
    "advil": "rx-ibuprofen-400",
    "motrin": "rx-ibuprofen-400",
    "brufen": "rx-ibuprofen-400",
    "painkiller": "rx-ibuprofen-400",
    
    "cetirizine": "rx-cetirizine-10",
    "zyrtec": "rx-cetirizine-10",
    "cetzine": "rx-cetirizine-10",
    "allergy tablet": "rx-cetirizine-10",
    "antihistamine": "rx-cetirizine-10",
    
    "omeprazole": "rx-omeprazole-20",
    "prilosec": "rx-omeprazole-20",
    "omez": "rx-omeprazole-20",
    "gas tablet": "rx-omeprazole-20",
    "acid tablet": "rx-omeprazole-20",
    "heartburn tablet": "rx-omeprazole-20",
    
    "aspirin": "rx-aspirin-81",
    "ecosprin": "rx-aspirin-81",
    "blood thinner": "rx-aspirin-81",
    
    "azithromycin": "rx-azithromycin-500",
    "zithromax": "rx-azithromycin-500",
    "azithral": "rx-azithromycin-500",
    "z-pack": "rx-azithromycin-500",
    
    "lisinopril": "rx-lisinopril-10",
    "prinivil": "rx-lisinopril-10",
    "zestril": "rx-lisinopril-10",
    "bp tablet": "rx-lisinopril-10",
    
    "salbutamol": "rx-salbutamol-inhaler",
    "albuterol": "rx-salbutamol-inhaler",
    "ventolin": "rx-salbutamol-inhaler",
    "asthma inhaler": "rx-salbutamol-inhaler",
    "inhaler": "rx-salbutamol-inhaler",
    
    "vitamin d": "rx-vitamin-d3-60k",
    "vitamin d3": "rx-vitamin-d3-60k",
    "cholecalciferol": "rx-vitamin-d3-60k"
}


def get_all_products(category: Optional[str] = None, search_query: Optional[str] = None) -> List[PharmacyProduct]:
    """Returns products filtered by optional category and search query."""
    results = PHARMACY_CATALOG
    if category and category.lower() != "all":
        c_clean = category.lower().strip()
        results = [
            p for p in results
            if c_clean == p.category.lower()
            or c_clean in p.category.lower()
            or p.category.lower() in c_clean
        ]
    
    if search_query:
        q = search_query.lower().strip()
        results = [
            p for p in results
            if q in p.name.lower()
            or q in p.generic_name.lower()
            or q in p.category.lower()
            or any(q in u.lower() for u in p.uses)
        ]
    return results


def get_product_by_id(product_id: str) -> Optional[PharmacyProduct]:
    """Retrieves a single medication by product ID."""
    for p in PHARMACY_CATALOG:
        if p.product_id == product_id:
            return p
    return None


def detect_medications_in_text(text: str) -> Dict[str, Any]:
    """
    Analyzes patient input or chat queries to detect mentions of tablets or medications.
    If detected, returns structured details of the matched medication, safety information,
    and a flag indicating automatic pharmacy redirection.
    """
    if not text:
        return {"detected": False, "products": []}

    cleaned = text.lower().strip()
    matched_ids = set()

    # Direct keyword matching
    for kw, pid in MEDICATION_KEYWORD_MAP.items():
        pattern = r"\b" + re.escape(kw) + r"\b"
        if re.search(pattern, cleaned):
            matched_ids.add(pid)

    # General intent triggers like "where to buy tablet", "order medicine", "online pharmacy"
    is_general_pharmacy_query = bool(re.search(
        r"\b(buy|purchase|order|online pharmacy|pharmacy|chemist|medicine store|get pills|buy tablets)\b",
        cleaned
    ))

    # If general buy intent mentioned with symptoms
    if not matched_ids and is_general_pharmacy_query:
        if "fever" in cleaned or "headache" in cleaned or "pain" in cleaned:
            matched_ids.add("rx-paracetamol-500")
        elif "cough" in cleaned or "cold" in cleaned or "allergy" in cleaned:
            matched_ids.add("rx-cetirizine-10")
        elif "stomach" in cleaned or "acidity" in cleaned or "heartburn" in cleaned:
            matched_ids.add("rx-omeprazole-20")
        else:
            # Default to best-sellers
            matched_ids.add("rx-paracetamol-500")

    if not matched_ids:
        return {"detected": False, "products": []}

    matched_products = [p for p in PHARMACY_CATALOG if p.product_id in matched_ids]
    primary_product = matched_products[0] if matched_products else None

    # Construct clinical pharmacy guidance
    educational_note = (
        f"**Medication Insight: {primary_product.name}**\n"
        f"- **Primary Indication**: {', '.join(primary_product.uses[:2])}\n"
        f"- **Standard Dosage Form**: {primary_product.dosage_form} ({primary_product.strength})\n"
        f"- **Guidance**: {primary_product.dosage_guidance}\n"
        f"- **Important Precaution**: {primary_product.precautions}\n"
        f"- **Price**: ${primary_product.discount_price or primary_product.price:.2f} ({primary_product.pack_size})\n"
        f"- **Prescription Status**: {'⚠️ Prescription Required upon checkout' if primary_product.rx_required else '✅ Available Over-The-Counter (OTC)'}\n\n"
        f"🛒 *I am automatically redirecting you to our integrated MedLens Online Pharmacy where you can review safety information, check stock, and place an order.*"
    )

    return {
        "detected": True,
        "primary_product": primary_product.model_dump(),
        "all_products": [p.model_dump() for p in matched_products],
        "redirect_to_pharmacy": True,
        "target_product_id": primary_product.product_id,
        "educational_note": educational_note,
        "redirect_reason": f"Patient inquired about {primary_product.name}"
    }
