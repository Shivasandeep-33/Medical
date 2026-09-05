"""
Data models for the Medical AI Agent application.
Defines schemas for Patient Profile, Report Metadata, Lab Results,
Structured Record, Provenance Tracking, and AI Summaries.
"""
from enum import Enum
from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field
from datetime import datetime


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


class StructuredMedicalRecord(BaseModel):
    record_id: str
    patient: PatientProfile
    reports: List[ProcessedReport] = []
    all_lab_results: List[LabResult] = []
    summary: Optional[PatientFriendlySummary] = None
    created_at: str = Field(default_factory=lambda: datetime.now().strftime("%Y-%m-%d %H:%M:%S"))
    updated_at: str = Field(default_factory=lambda: datetime.now().strftime("%Y-%m-%d %H:%M:%S"))
