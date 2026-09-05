"""
Data models for the MedLens AI Medical Agent and Healthcare Platform.
Defines schemas for:
- Patient Profile & Medical Intake
- Medical Reports & Lab Results with strict Reference-Range Awareness
- Source Provenance Tracking
- AI Patient-Friendly Summaries with safety guardrails
- User Authentication & Roles (Patient, Doctor, Admin)
- Integrated Consultation Bookings (Online & In-Person)
- Emergency Ambulance Dispatch & Tracking
- Online Pharmacy Products, Orders & Medication Detection
- Clinical Inconsistency / Conflict Alerts
"""
from enum import Enum
from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field
from datetime import datetime


class UserRole(str, Enum):
    PATIENT = "PATIENT"
    DOCTOR = "DOCTOR"
    ADMIN = "ADMIN"


class User(BaseModel):
    user_id: str
    email: str
    password_hash: str  # In demo/simulated environment
    full_name: str
    role: UserRole = UserRole.PATIENT
    phone: Optional[str] = None
    linked_patient_id: Optional[str] = None
    created_at: str = Field(default_factory=lambda: datetime.now().strftime("%Y-%m-%d %H:%M:%S"))


class UserSession(BaseModel):
    token: str
    user: User


class ProvenanceType(str, Enum):
    USER_PROVIDED = "User Provided"
    REPORT_EXTRACTED = "Extracted from Report"
    AI_GENERATED = "AI Generated"


class ProvenanceRecord(BaseModel):
    source_type: ProvenanceType
    source_name: str = "User Intake"
    snippet: Optional[str] = None
    page_number: Optional[int] = None
    extracted_at: str = Field(default_factory=lambda: datetime.now().strftime("%Y-%m-%d %H:%M:%S"))


class ValueStatus(str, Enum):
    LOW = "LOW"
    NORMAL = "NORMAL"
    HIGH = "HIGH"
    UNSPECIFIED = "UNSPECIFIED"  # When report does not supply reference range
    INCONCLUSIVE = "INCONCLUSIVE"


class LabVerification(BaseModel):
    is_verified: bool = False
    verified_by: Optional[str] = None
    verified_at: Optional[str] = None
    clinician_notes: Optional[str] = None


class LabResult(BaseModel):
    id: str
    test_name: str
    category: str = "General"  # e.g., Hematology, Metabolic, Lipid, Urinalysis, Thyroid
    value: str
    numeric_value: Optional[float] = None
    unit: str = ""
    reference_range_raw: Optional[str] = None
    ref_low: Optional[float] = None
    ref_high: Optional[float] = None
    ref_textual: Optional[str] = None
    status: ValueStatus = ValueStatus.UNSPECIFIED
    status_reason: str = ""
    observation_notes: Optional[str] = None
    test_date: Optional[str] = None
    provenance: ProvenanceRecord
    verification: LabVerification = Field(default_factory=LabVerification)


class SymptomItem(BaseModel):
    name: str
    severity: str = "Mild"  # Mild, Moderate, Severe
    duration: str = ""
    notes: Optional[str] = None
    provenance: ProvenanceRecord = Field(default_factory=lambda: ProvenanceRecord(source_type=ProvenanceType.USER_PROVIDED, source_name="Patient Intake"))


class MedicationItem(BaseModel):
    name: str
    dosage: str = ""
    frequency: str = ""
    purpose: Optional[str] = None
    provenance: ProvenanceRecord = Field(default_factory=lambda: ProvenanceRecord(source_type=ProvenanceType.USER_PROVIDED, source_name="Patient Intake"))


class AllergyItem(BaseModel):
    allergen: str
    reaction: str = ""
    severity: str = "Mild"
    provenance: ProvenanceRecord = Field(default_factory=lambda: ProvenanceRecord(source_type=ProvenanceType.USER_PROVIDED, source_name="Patient Intake"))


class ConditionItem(BaseModel):
    condition_name: str
    diagnosed_year_or_date: str = ""
    status: str = "Active"  # Active, In Remission, Resolved
    provenance: ProvenanceRecord = Field(default_factory=lambda: ProvenanceRecord(source_type=ProvenanceType.USER_PROVIDED, source_name="Patient Intake"))


class PatientProfile(BaseModel):
    patient_id: str
    full_name: str
    age: Optional[int] = None
    sex: str = "Unspecified"  # Female, Male, Other, Unspecified
    dob: Optional[str] = None
    blood_type: Optional[str] = None
    contact_phone: Optional[str] = None
    emergency_contact: Optional[str] = None
    symptoms: List[SymptomItem] = []
    existing_conditions: List[ConditionItem] = []
    allergies: List[AllergyItem] = []
    medications: List[MedicationItem] = []
    surgical_history: List[str] = []
    lifestyle_notes: Optional[str] = None
    last_updated: str = Field(default_factory=lambda: datetime.now().strftime("%Y-%m-%d %H:%M:%S"))
    provenance: ProvenanceRecord = Field(default_factory=lambda: ProvenanceRecord(source_type=ProvenanceType.USER_PROVIDED, source_name="Patient Intake Form"))


class ProcessedReport(BaseModel):
    report_id: str
    filename: str
    file_type: str
    upload_time: str = Field(default_factory=lambda: datetime.now().strftime("%Y-%m-%d %H:%M:%S"))
    report_date: Optional[str] = None
    facility_or_doctor: Optional[str] = None
    extracted_tests: List[LabResult] = []
    raw_text_preview: str = ""
    extraction_method: str = "Deterministic Clinical NLP"  # or "Google Gemini AI"


class PatientFriendlySummary(BaseModel):
    overview: str
    key_findings: List[str] = []
    out_of_range_explanations: List[Dict[str, str]] = []
    questions_for_doctor: List[str] = []
    disclaimer: str = (
        "IMPORTANT MEDICAL DISCLAIMER: This summary is generated for informational and organizational "
        "purposes only. It does NOT constitute a medical diagnosis, clinical opinion, or treatment advice. "
        "Laboratory values must always be interpreted in clinical context by your licensed healthcare provider."
    )
    generated_at: str = Field(default_factory=lambda: datetime.now().strftime("%Y-%m-%d %H:%M:%S"))
    generation_engine: str = "Clinical Summary Engine"


class ConflictAlert(BaseModel):
    alert_id: str
    severity: str  # "HIGH", "MODERATE", "INFO"
    category: str  # "DRUG_ALLERGY", "DRUG_CONDITION", "LAB_ABNORMALITY"
    title: str
    description: str
    recommendation: str


class StructuredMedicalRecord(BaseModel):
    record_id: str
    patient: PatientProfile
    reports: List[ProcessedReport] = []
    all_lab_results: List[LabResult] = []
    summary: Optional[PatientFriendlySummary] = None
    conflicts: List[ConflictAlert] = []
    created_at: str = Field(default_factory=lambda: datetime.now().strftime("%Y-%m-%d %H:%M:%S"))
    updated_at: str = Field(default_factory=lambda: datetime.now().strftime("%Y-%m-%d %H:%M:%S"))


# =====================================================================
# BOOKINGS & HEALTHCARE SERVICES MODELS
# =====================================================================

class BookingType(str, Enum):
    ONLINE_CONSULTATION = "online"
    IN_PERSON_APPOINTMENT = "in_person"


class BookingStatus(str, Enum):
    CONFIRMED = "confirmed"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    CANCELLED = "cancelled"


class DoctorProfile(BaseModel):
    doctor_id: str
    name: str
    title: str
    specialty: str
    experience_years: int
    qualification: str
    hospital_affiliation: str
    consultation_fee: float
    avatar_color: str = "sky"
    available_slots: List[str] = []
    rating: float = 4.9


class ConsultationBooking(BaseModel):
    booking_id: str
    patient_id: str
    patient_name: str
    patient_phone: Optional[str] = None
    doctor_id: str
    doctor_name: str
    specialty: str
    booking_type: BookingType
    appointment_date: str
    time_slot: str
    status: BookingStatus = BookingStatus.CONFIRMED
    notes: Optional[str] = None
    fee: float = 0.0
    meeting_link: Optional[str] = None  # Simulated secure video room link for online consultations
    clinic_branch: Optional[str] = None  # Hospital/Clinic address for in-person visits
    created_at: str = Field(default_factory=lambda: datetime.now().strftime("%Y-%m-%d %H:%M:%S"))


# =====================================================================
# EMERGENCY AMBULANCE MODELS
# =====================================================================

class AmbulanceStatus(str, Enum):
    REQUESTED = "requested"
    DISPATCHED = "dispatched"
    EN_ROUTE = "en_route"
    ARRIVED = "arrived"
    COMPLETED = "completed"
    CANCELLED = "cancelled"


class AmbulanceRequest(BaseModel):
    request_id: str
    patient_id: str
    patient_name: str
    contact_phone: str
    emergency_type: str  # Cardiac, Acute Trauma, Respiratory, Stroke, Severe Allergy, General
    severity_level: str = "CRITICAL"
    pickup_address: str
    landmark: Optional[str] = None
    latitude: Optional[float] = 37.7749
    longitude: Optional[float] = -122.4194
    dispatch_status: AmbulanceStatus = AmbulanceStatus.DISPATCHED
    vehicle_number: str = "AMB-MED-902"
    vehicle_type: str = "Advanced Cardiac Life Support (ACLS)"
    paramedic_team: str = "Paramedic Unit 7 (Lead: Paramedic Johnson)"
    paramedic_contact: str = "+1 (800) 555-0911"
    eta_minutes: int = 6
    destination_hospital: str = "MedLens Metropolitan Emergency Trauma Center"
    requested_at: str = Field(default_factory=lambda: datetime.now().strftime("%Y-%m-%d %H:%M:%S"))
    updated_at: str = Field(default_factory=lambda: datetime.now().strftime("%Y-%m-%d %H:%M:%S"))


# =====================================================================
# ONLINE PHARMACY & MEDICATION MODELS
# =====================================================================

class PharmacyProduct(BaseModel):
    product_id: str
    name: str
    generic_name: str
    category: str  # Pain Relief, Cardiovascular, Diabetes, Antibiotics, Allergy, Digestive, Vitamins
    strength: str  # e.g., "500 mg", "20 mg", "10 mg"
    dosage_form: str  # Tablet, Capsule, Syrup, Inhaler
    price: float
    discount_price: Optional[float] = None
    pack_size: str  # e.g., "Strip of 10 Tablets", "Bottle of 60 Capsules"
    in_stock: bool = True
    stock_quantity: int = 50
    rx_required: bool = False
    rating: float = 4.8
    description: str
    uses: List[str] = []
    side_effects: List[str] = []
    dosage_guidance: str
    precautions: str
    badge: Optional[str] = None


class CartItem(BaseModel):
    product_id: str
    product_name: str
    strength: str
    price: float
    quantity: int = 1


class PharmacyOrder(BaseModel):
    order_id: str
    patient_id: str
    customer_name: str
    customer_email: str
    customer_phone: str
    delivery_address: str
    items: List[CartItem] = []
    subtotal: float
    delivery_fee: float = 0.0
    total_amount: float
    payment_method: str = "Cash on Delivery / Online"
    status: str = "Confirmed (Packaging for Dispatch)"
    tracking_number: str
    prescription_uploaded: bool = False
    created_at: str = Field(default_factory=lambda: datetime.now().strftime("%Y-%m-%d %H:%M:%S"))
