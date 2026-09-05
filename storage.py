"""
Storage module for Structured Medical Records, User Authentication,
Healthcare Bookings, Ambulance Dispatch, and Pharmacy Orders.
Provides in-memory caching and persistent JSON storage.
"""

import json
import os
import uuid
from typing import Dict, List, Optional, Any
from datetime import datetime
from models import (
    StructuredMedicalRecord,
    PatientProfile,
    ProcessedReport,
    PatientFriendlySummary,
    LabResult,
    LabVerification,
    User,
    UserRole,
    DoctorProfile,
    ConsultationBooking,
    BookingType,
    BookingStatus,
    AmbulanceRequest,
    AmbulanceStatus,
    PharmacyOrder,
    ConflictAlert,
)
from samples import SAMPLE_CASES
from extractor import process_report_file
from summarizer import generate_summary

DATA_DIR = os.path.join(os.path.dirname(__file__), "data")
STORAGE_FILE = os.path.join(DATA_DIR, "records.json")
USERS_FILE = os.path.join(DATA_DIR, "users.json")
BOOKINGS_FILE = os.path.join(DATA_DIR, "bookings.json")
AMBULANCE_FILE = os.path.join(DATA_DIR, "ambulance.json")
ORDERS_FILE = os.path.join(DATA_DIR, "orders.json")

# Preloaded Specialist Doctors Directory
SPECIALIST_DOCTORS: List[DoctorProfile] = [
    DoctorProfile(
        doctor_id="doc-evelyn-reed",
        name="Dr. Evelyn Reed, MD, FACC",
        title="Senior Consultant Cardiologist",
        specialty="Cardiology & Vascular Medicine",
        experience_years=16,
        qualification="MD, Harvard Medical School; FACC Board Certified",
        hospital_affiliation="MedLens Metropolitan Heart & Vascular Center",
        consultation_fee=85.00,
        avatar_color="rose",
        available_slots=["09:30 AM", "11:00 AM", "02:30 PM", "04:15 PM"],
        rating=4.95
    ),
    DoctorProfile(
        doctor_id="doc-marcus-vance",
        name="Dr. Marcus Vance, MD, FACE",
        title="Chief of Endocrinology & Metabolism",
        specialty="Endocrinology & Diabetes Care",
        experience_years=14,
        qualification="MD, Johns Hopkins Medicine; Board Certified Endocrinologist",
        hospital_affiliation="City Metabolic & Diabetes Care Center",
        consultation_fee=80.00,
        avatar_color="amber",
        available_slots=["10:00 AM", "11:30 AM", "03:00 PM", "05:00 PM"],
        rating=4.92
    ),
    DoctorProfile(
        doctor_id="doc-sarah-jenkins",
        name="Dr. Sarah Jenkins, MD",
        title="Lead Family & Primary Care Physician",
        specialty="General Medicine & Family Health",
        experience_years=10,
        qualification="MD, Stanford University School of Medicine",
        hospital_affiliation="Downtown Community Health Hospital",
        consultation_fee=50.00,
        avatar_color="sky",
        available_slots=["09:00 AM", "10:30 AM", "01:30 PM", "03:30 PM", "04:45 PM"],
        rating=4.89
    ),
    DoctorProfile(
        doctor_id="doc-robert-chen",
        name="Dr. Robert Chen, MD, FCCP",
        title="Consultant Pulmonologist & Critical Care",
        specialty="Pulmonology & Respiratory Care",
        experience_years=15,
        qualification="MD, Columbia University; FCCP Fellow",
        hospital_affiliation="Advanced Thoracic & Allergy Institute",
        consultation_fee=75.00,
        avatar_color="teal",
        available_slots=["10:15 AM", "12:00 PM", "02:00 PM", "04:30 PM"],
        rating=4.91
    ),
    DoctorProfile(
        doctor_id="doc-priya-patel",
        name="Dr. Priya Patel, MD, FAAN",
        title="Director of Clinical Neurology",
        specialty="Neurology & Headache Medicine",
        experience_years=12,
        qualification="MD, Penn Medicine; FAAN Certified Neurologist",
        hospital_affiliation="Metropolitan Neurosciences Center",
        consultation_fee=90.00,
        avatar_color="indigo",
        available_slots=["11:00 AM", "01:00 PM", "03:15 PM", "05:15 PM"],
        rating=4.96
    )
]


class RecordStore:
    def __init__(self):
        self._records: Dict[str, StructuredMedicalRecord] = {}
        self._users: Dict[str, User] = {}
        self._bookings: Dict[str, ConsultationBooking] = {}
        self._ambulance_requests: Dict[str, AmbulanceRequest] = {}
        self._orders: Dict[str, PharmacyOrder] = {}
        self._ensure_storage()

    def _ensure_storage(self):
        os.makedirs(DATA_DIR, exist_ok=True)
        
        # Load Records
        if os.path.exists(STORAGE_FILE):
            try:
                with open(STORAGE_FILE, "r", encoding="utf-8") as f:
                    data = json.load(f)
                    for rec_id, rec_dict in data.items():
                        self._records[rec_id] = StructuredMedicalRecord.model_validate(rec_dict)
            except Exception as e:
                print(f"Error loading stored records: {e}. Reinitializing samples.")
                self._initialize_samples()
        else:
            self._initialize_samples()

        # Load or Initialize Users
        if os.path.exists(USERS_FILE):
            try:
                with open(USERS_FILE, "r", encoding="utf-8") as f:
                    u_data = json.load(f)
                    for uid, u_dict in u_data.items():
                        self._users[uid] = User.model_validate(u_dict)
            except Exception as e:
                print(f"Error loading users: {e}. Reinitializing default accounts.")
                self._initialize_default_users()
        else:
            self._initialize_default_users()

        # Load Bookings
        if os.path.exists(BOOKINGS_FILE):
            try:
                with open(BOOKINGS_FILE, "r", encoding="utf-8") as f:
                    b_data = json.load(f)
                    for bid, b_dict in b_data.items():
                        self._bookings[bid] = ConsultationBooking.model_validate(b_dict)
            except Exception as e:
                print(f"Error loading bookings: {e}")

        # Load Ambulance Requests
        if os.path.exists(AMBULANCE_FILE):
            try:
                with open(AMBULANCE_FILE, "r", encoding="utf-8") as f:
                    a_data = json.load(f)
                    for aid, a_dict in a_data.items():
                        self._ambulance_requests[aid] = AmbulanceRequest.model_validate(a_dict)
            except Exception as e:
                print(f"Error loading ambulance requests: {e}")

        # Load Orders
        if os.path.exists(ORDERS_FILE):
            try:
                with open(ORDERS_FILE, "r", encoding="utf-8") as f:
                    o_data = json.load(f)
                    for oid, o_dict in o_data.items():
                        self._orders[oid] = PharmacyOrder.model_validate(o_dict)
            except Exception as e:
                print(f"Error loading pharmacy orders: {e}")

    def _initialize_default_users(self):
        """Initializes standard demo accounts for instant evaluation."""
        self._users = {
            "usr-patient-1": User(
                user_id="usr-patient-1",
                email="patient@medlens.health",
                password_hash="patient123",
                full_name="Eleanor Vance",
                role=UserRole.PATIENT,
                phone="+1 (555) 234-5678",
                linked_patient_id="case_1_diabetes"
            ),
            "usr-doctor-1": User(
                user_id="usr-doctor-1",
                email="doctor@medlens.health",
                password_hash="doctor123",
                full_name="Dr. Evelyn Reed, MD",
                role=UserRole.DOCTOR,
                phone="+1 (555) 888-0199",
                linked_patient_id="case_2_cardiac"
            ),
            "usr-admin-1": User(
                user_id="usr-admin-1",
                email="admin@medlens.health",
                password_hash="admin123",
                full_name="MedLens Clinical Administrator",
                role=UserRole.ADMIN,
                phone="+1 (555) 999-0000"
            )
        }
        self.persist_users()

    def _initialize_samples(self):
        """Initializes storage with realistic sample clinical cases."""
        for case_key, case_data in SAMPLE_CASES.items():
            try:
                patient = PatientProfile.model_validate(case_data["patient"])
                report_bytes = case_data["report_text"].encode("utf-8")
                processed_report = process_report_file(
                    file_bytes=report_bytes,
                    filename=case_data["report_filename"]
                )

                record_id = patient.patient_id.lower()
                med_record = StructuredMedicalRecord(
                    record_id=record_id,
                    patient=patient,
                    reports=[processed_report],
                    all_lab_results=processed_report.extracted_tests
                )

                # Generate initial summary & conflict analysis
                med_record.summary = generate_summary(med_record)
                med_record.conflicts = self._analyze_conflicts(med_record)
                self._records[record_id] = med_record
            except Exception as e:
                print(f"Failed to initialize sample case {case_key}: {e}")

        self.persist()

    def _analyze_conflicts(self, record: StructuredMedicalRecord) -> List[ConflictAlert]:
        """Detects medical inconsistencies, allergy conflicts, and critical lab alerts."""
        alerts: List[ConflictAlert] = []
        patient = record.patient

        # 1. Drug - Allergy Inconsistency Check
        allergy_names = [a.allergen.lower() for a in patient.allergies]
        med_names = [m.name.lower() for m in patient.medications]

        for med in patient.medications:
            m_lower = med.name.lower()
            if any(a in m_lower or ("penicillin" in a and "amox" in m_lower) for a in allergy_names):
                alerts.append(ConflictAlert(
                    alert_id=f"alert-{uuid.uuid4().hex[:6]}",
                    severity="HIGH",
                    category="DRUG_ALLERGY",
                    title=f"Potential Allergen Conflict: {med.name}",
                    description=f"Patient has a recorded allergy ({', '.join(allergy_names)}) while active medication list includes '{med.name}'.",
                    recommendation="Verify medication safety immediately with attending clinician before administration."
                ))

            if "aspirin" in allergy_names and ("ibuprofen" in m_lower or "naproxen" in m_lower):
                alerts.append(ConflictAlert(
                    alert_id=f"alert-{uuid.uuid4().hex[:6]}",
                    severity="HIGH",
                    category="DRUG_ALLERGY",
                    title=f"NSAID Cross-Reactivity Risk: {med.name}",
                    description=f"Patient has recorded Aspirin allergy which may cross-react with '{med.name}'.",
                    recommendation="Review with physician for alternative analgesic selection."
                ))

        # 2. Critical Lab Result Inconsistencies
        for lab in record.all_lab_results:
            if lab.numeric_value is not None:
                # Severe hyperglycemia
                if "glucose" in lab.test_name.lower() and lab.numeric_value > 180:
                    alerts.append(ConflictAlert(
                        alert_id=f"alert-{uuid.uuid4().hex[:6]}",
                        severity="MODERATE",
                        category="LAB_ABNORMALITY",
                        title=f"Significant Hyperglycemia: {lab.test_name} = {lab.value} {lab.unit}",
                        description=f"Value is elevated significantly above standard fasting parameters ({lab.reference_range_raw or 'No range'}).",
                        recommendation="Correlate with current diabetes regimen and HbA1c values."
                    ))
                # Critical Troponin elevation
                if "troponin" in lab.test_name.lower() and lab.status == "HIGH":
                    alerts.append(ConflictAlert(
                        alert_id=f"alert-{uuid.uuid4().hex[:6]}",
                        severity="HIGH",
                        category="LAB_ABNORMALITY",
                        title=f"Critical Biomarker: Elevated Cardiac Troponin",
                        description=f"Result {lab.value} {lab.unit} indicates myocardial injury marker elevation.",
                        recommendation="Requires emergency cardiology clinical review and continuous ECG monitoring."
                    ))

        return alerts

    def persist(self):
        """Writes records to JSON file."""
        try:
            os.makedirs(DATA_DIR, exist_ok=True)
            data = {k: v.model_dump() for k, v in self._records.items()}
            with open(STORAGE_FILE, "w", encoding="utf-8") as f:
                json.dump(data, f, indent=2)
        except Exception as e:
            print(f"Failed to persist records: {e}")

    def persist_users(self):
        try:
            os.makedirs(DATA_DIR, exist_ok=True)
            data = {k: v.model_dump() for k, v in self._users.items()}
            with open(USERS_FILE, "w", encoding="utf-8") as f:
                json.dump(data, f, indent=2)
        except Exception as e:
            print(f"Failed to persist users: {e}")

    def persist_bookings(self):
        try:
            os.makedirs(DATA_DIR, exist_ok=True)
            data = {k: v.model_dump() for k, v in self._bookings.items()}
            with open(BOOKINGS_FILE, "w", encoding="utf-8") as f:
                json.dump(data, f, indent=2)
        except Exception as e:
            print(f"Failed to persist bookings: {e}")

    def persist_ambulance(self):
        try:
            os.makedirs(DATA_DIR, exist_ok=True)
            data = {k: v.model_dump() for k, v in self._ambulance_requests.items()}
            with open(AMBULANCE_FILE, "w", encoding="utf-8") as f:
                json.dump(data, f, indent=2)
        except Exception as e:
            print(f"Failed to persist ambulance requests: {e}")

    def persist_orders(self):
        try:
            os.makedirs(DATA_DIR, exist_ok=True)
            data = {k: v.model_dump() for k, v in self._orders.items()}
            with open(ORDERS_FILE, "w", encoding="utf-8") as f:
                json.dump(data, f, indent=2)
        except Exception as e:
            print(f"Failed to persist orders: {e}")

    # =========================================================================
    # RECORD OPERATIONS
    # =========================================================================

    def list_records(self) -> List[Dict[str, Any]]:
        out = []
        for r in self._records.values():
            out.append({
                "record_id": r.record_id,
                "patient_name": r.patient.full_name,
                "age": r.patient.age,
                "sex": r.patient.sex,
                "reports_count": len(r.reports),
                "tests_count": len(r.all_lab_results),
                "conflicts_count": len(r.conflicts),
                "updated_at": r.updated_at
            })
        return out

    def get_record(self, record_id: str) -> Optional[StructuredMedicalRecord]:
        clean = record_id.lower().strip()
        if clean in self._records:
            return self._records[clean]
        
        # Check by sample case key aliases
        alias_map = {
            "case_1_diabetes": "pt-10482",
            "case_2_cardiac": "pt-29381",
            "case_3_hematology": "pt-38290"
        }
        if clean in alias_map and alias_map[clean] in self._records:
            return self._records[alias_map[clean]]

        # Check by patient name or patient_id inside records
        for rec in self._records.values():
            if rec.patient.patient_id.lower() == clean or rec.patient.full_name.lower() == clean:
                return rec
        return None

    def save_record(self, record: StructuredMedicalRecord) -> StructuredMedicalRecord:
        record.conflicts = self._analyze_conflicts(record)
        record.updated_at = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        self._records[record.record_id] = record
        self.persist()
        return record

    def delete_record(self, record_id: str) -> bool:
        if record_id in self._records:
            del self._records[record_id]
            self.persist()
            return True
        return False

    def reset_to_samples(self):
        self._records.clear()
        self._initialize_samples()

    # =========================================================================
    # USER & AUTH OPERATIONS
    # =========================================================================

    def get_user_by_email(self, email: str) -> Optional[User]:
        clean = email.lower().strip()
        for u in self._users.values():
            if u.email.lower() == clean:
                return u
        return None

    def get_user_by_id(self, user_id: str) -> Optional[User]:
        return self._users.get(user_id)

    def register_user(self, full_name: str, email: str, password_hash: str, role: UserRole = UserRole.PATIENT, phone: Optional[str] = None) -> User:
        user_id = f"usr-{uuid.uuid4().hex[:8]}"
        user = User(
            user_id=user_id,
            email=email.lower().strip(),
            password_hash=password_hash,
            full_name=full_name.strip(),
            role=role,
            phone=phone
        )
        self._users[user_id] = user
        self.persist_users()
        return user

    def list_users(self) -> List[User]:
        return list(self._users.values())

    # =========================================================================
    # DOCTOR & BOOKING OPERATIONS
    # =========================================================================

    def list_doctors(self, specialty: Optional[str] = None) -> List[DoctorProfile]:
        if specialty and specialty.lower() != "all":
            return [d for d in SPECIALIST_DOCTORS if specialty.lower() in d.specialty.lower()]
        return SPECIALIST_DOCTORS

    def get_doctor_by_id(self, doctor_id: str) -> Optional[DoctorProfile]:
        for d in SPECIALIST_DOCTORS:
            if d.doctor_id == doctor_id:
                return d
        return None

    def create_booking(self, booking: ConsultationBooking) -> ConsultationBooking:
        self._bookings[booking.booking_id] = booking
        self.persist_bookings()
        return booking

    def list_bookings(self, patient_id: Optional[str] = None) -> List[ConsultationBooking]:
        all_b = list(self._bookings.values())
        if patient_id:
            return [b for b in all_b if b.patient_id.lower() == patient_id.lower()]
        # Sort newest first
        return sorted(all_b, key=lambda x: x.created_at, reverse=True)

    def cancel_booking(self, booking_id: str) -> Optional[ConsultationBooking]:
        if booking_id in self._bookings:
            self._bookings[booking_id].status = BookingStatus.CANCELLED
            self.persist_bookings()
            return self._bookings[booking_id]
        return None

    # =========================================================================
    # AMBULANCE OPERATIONS
    # =========================================================================

    def create_ambulance_request(self, req: AmbulanceRequest) -> AmbulanceRequest:
        self._ambulance_requests[req.request_id] = req
        self.persist_ambulance()
        return req

    def get_ambulance_request(self, request_id: str) -> Optional[AmbulanceRequest]:
        return self._ambulance_requests.get(request_id)

    def list_ambulance_requests(self, patient_id: Optional[str] = None) -> List[AmbulanceRequest]:
        all_a = list(self._ambulance_requests.values())
        if patient_id:
            return [a for a in all_a if a.patient_id.lower() == patient_id.lower()]
        return sorted(all_a, key=lambda x: x.requested_at, reverse=True)

    def update_ambulance_status(self, request_id: str, status: AmbulanceStatus) -> Optional[AmbulanceRequest]:
        if request_id in self._ambulance_requests:
            req = self._ambulance_requests[request_id]
            req.dispatch_status = status
            req.updated_at = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            if status == AmbulanceStatus.EN_ROUTE:
                req.eta_minutes = max(1, req.eta_minutes - 2)
            elif status == AmbulanceStatus.ARRIVED:
                req.eta_minutes = 0
            self.persist_ambulance()
            return req
        return None

    # =========================================================================
    # PHARMACY ORDER OPERATIONS
    # =========================================================================

    def create_pharmacy_order(self, order: PharmacyOrder) -> PharmacyOrder:
        self._orders[order.order_id] = order
        self.persist_orders()
        return order

    def list_pharmacy_orders(self, patient_id: Optional[str] = None) -> List[PharmacyOrder]:
        all_o = list(self._orders.values())
        if patient_id:
            return [o for o in all_o if o.patient_id.lower() == patient_id.lower()]
        return sorted(all_o, key=lambda x: x.created_at, reverse=True)


# Global storage instance
store = RecordStore()
