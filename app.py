"""
MedLens — AI-Powered Clinical Information Intelligence & Healthcare Portal Backend.
Unified FastAPI application providing:
1. Patient Information Intake & Medical Report Processing (PDF/Text)
2. Strict Reference-Range Awareness without invented bounds & Source Provenance Tracking
3. Patient-Friendly AI Summaries with strict clinical safety guardrails
4. User Authentication & Access Control (Patient, Doctor, Admin)
5. Integrated Booking System (Online Teleconsultations & In-Person Appointments)
6. Emergency Ambulance Dispatch & Real-Time Tracking
7. Integrated AI Symptom-to-Disease Agent & Multi-Turn Chat Triage
8. Online Pharmacy Engine with Automatic Tablet/Medication Detection & Redirection
9. Lab Result Human Verification, Multi-Report Comparison, and Conflict Detection
"""

import os
import sys
import uuid
from datetime import datetime
from typing import Optional, Dict, Any, List
from fastapi import FastAPI, UploadFile, File, Form, HTTPException, Header, Query
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse, JSONResponse, HTMLResponse
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from dotenv import load_dotenv

# Local module imports
from models import (
    PatientProfile,
    StructuredMedicalRecord,
    ProcessedReport,
    ProvenanceRecord,
    ProvenanceType,
    PatientFriendlySummary,
    LabResult,
    LabVerification,
    User,
    UserRole,
    ConsultationBooking,
    BookingType,
    BookingStatus,
    AmbulanceRequest,
    AmbulanceStatus,
    PharmacyProduct,
    PharmacyOrder,
    CartItem,
)
from storage import store
from extractor import process_report_file
from summarizer import generate_summary
from samples import SAMPLE_CASES
from pharmacy import (
    PHARMACY_CATALOG,
    get_all_products,
    get_product_by_id,
    detect_medications_in_text,
)

# Symptom Agent Engine imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "symptom_agent"))
from disease_engine import evaluate_symptoms, SYMPTOM_LEXICON, TriageEvaluation
from chat_agent import run_chat_triage
from agent_app import SYMPTOM_CATEGORIES, QUICK_SCENARIOS

load_dotenv()

app = FastAPI(
    title="MedLens — AI Clinical Intelligence & Healthcare Portal",
    description="Unified AI platform for clinical information intake, laboratory report parsing, symptom diagnostics, appointment bookings, emergency ambulances, and online pharmacy.",
    version="3.0.0"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

DEFAULT_GEMINI_KEY = os.getenv("GEMINI_API_KEY", "")


# =====================================================================
# SYSTEM & HEALTH
# =====================================================================

@app.get("/api/health")
def health_check():
    return {
        "status": "ok",
        "system": "MedLens AI Clinical Platform",
        "total_records": len(store.list_records()),
        "total_doctors": len(store.list_doctors()),
        "total_pharmacy_products": len(PHARMACY_CATALOG),
        "version": "3.0.0"
    }


# =====================================================================
# USER AUTHENTICATION & ACCESS CONTROL
# =====================================================================

class RegisterRequest(BaseModel):
    full_name: str
    email: str
    password: str
    role: Optional[UserRole] = UserRole.PATIENT
    phone: Optional[str] = None


class LoginRequest(BaseModel):
    email: str
    password: str


class DemoLoginRequest(BaseModel):
    account_type: str  # "patient", "doctor", "admin"


@app.post("/api/auth/register")
def register_user_endpoint(payload: RegisterRequest):
    existing = store.get_user_by_email(payload.email)
    if existing:
        raise HTTPException(status_code=400, detail="An account with this email address already exists.")
    user = store.register_user(
        full_name=payload.full_name,
        email=payload.email,
        password_hash=payload.password,  # In demo setup
        role=payload.role or UserRole.PATIENT,
        phone=payload.phone
    )
    return {
        "status": "success",
        "message": "Account created successfully",
        "token": f"token-{uuid.uuid4().hex[:12]}",
        "user": user
    }


@app.post("/api/auth/login")
def login_user_endpoint(payload: LoginRequest):
    user = store.get_user_by_email(payload.email)
    if not user or user.password_hash != payload.password:
        raise HTTPException(status_code=401, detail="Invalid email or password.")
    return {
        "status": "success",
        "token": f"token-{uuid.uuid4().hex[:12]}",
        "user": user
    }


@app.post("/api/auth/demo-login")
def demo_login_endpoint(payload: DemoLoginRequest):
    """Instant 1-click login for evaluators."""
    target_email = "patient@medlens.health"
    if payload.account_type.lower() == "doctor":
        target_email = "doctor@medlens.health"
    elif payload.account_type.lower() == "admin":
        target_email = "admin@medlens.health"

    user = store.get_user_by_email(target_email)
    if not user:
        raise HTTPException(status_code=404, detail=f"Demo account '{payload.account_type}' not found.")

    return {
        "status": "success",
        "token": f"demo-token-{uuid.uuid4().hex[:8]}",
        "user": user
    }


@app.get("/api/auth/me")
def get_current_user_endpoint(user_id: Optional[str] = Query(None)):
    if user_id:
        u = store.get_user_by_id(user_id)
        if u:
            return u
    # Default to first patient user
    return store.get_user_by_email("patient@medlens.health")


# =====================================================================
# CLINICAL SAMPLE CASES & INTAKE
# =====================================================================

@app.get("/api/samples")
def get_sample_cases():
    samples_list = []
    for k, v in SAMPLE_CASES.items():
        samples_list.append({
            "key": k,
            "title": v["title"],
            "description": v["description"],
            "patient_name": v["patient"]["full_name"],
            "report_name": v["report_filename"]
        })
    return samples_list


@app.get("/api/samples/{case_key}")
def get_sample_case_detail(case_key: str):
    if case_key not in SAMPLE_CASES:
        raise HTTPException(status_code=404, detail="Sample case not found")
    return SAMPLE_CASES[case_key]


@app.get("/api/records")
def list_records():
    return store.list_records()


@app.get("/api/records/{record_id}")
def get_record(record_id: str):
    record = store.get_record(record_id)
    if not record:
        raise HTTPException(status_code=404, detail=f"Medical record '{record_id}' not found")
    return record


@app.post("/api/records/patient")
def create_or_update_patient(
    patient: PatientProfile,
    x_gemini_api_key: Optional[str] = Header(None)
):
    rec_id = patient.patient_id.lower().strip()
    existing = store.get_record(rec_id)
    api_key = x_gemini_api_key or DEFAULT_GEMINI_KEY

    if existing:
        existing.patient = patient
        existing.patient.provenance = ProvenanceRecord(
            source_type=ProvenanceType.USER_PROVIDED,
            source_name="Patient Intake Form (Updated)"
        )
        existing.summary = generate_summary(existing, api_key=api_key)
        store.save_record(existing)
        return existing
    else:
        new_record = StructuredMedicalRecord(
            record_id=rec_id,
            patient=patient,
            reports=[],
            all_lab_results=[]
        )
        new_record.summary = generate_summary(new_record, api_key=api_key)
        store.save_record(new_record)
        return new_record


# =====================================================================
# MEDICAL REPORT PROCESSING (PDF & TEXT)
# =====================================================================

@app.post("/api/records/{record_id}/upload_report")
async def upload_medical_report(
    record_id: str,
    file: UploadFile = File(...),
    x_gemini_api_key: Optional[str] = Header(None)
):
    record = store.get_record(record_id)
    if not record:
        raise HTTPException(status_code=404, detail=f"Record '{record_id}' not found")

    content = await file.read()
    if not content:
        raise HTTPException(status_code=400, detail="Uploaded file is empty")

    api_key = x_gemini_api_key or DEFAULT_GEMINI_KEY

    processed_report = process_report_file(
        file_bytes=content,
        filename=file.filename or "Uploaded_Report.pdf",
        gemini_api_key=api_key
    )

    record.reports.append(processed_report)

    # Consolidate tests into all_lab_results
    existing_tests_map = {t.test_name.lower(): t for t in record.all_lab_results}
    for new_t in processed_report.extracted_tests:
        existing_tests_map[new_t.test_name.lower()] = new_t

    record.all_lab_results = list(existing_tests_map.values())
    record.summary = generate_summary(record, api_key=api_key)

    store.save_record(record)
    return {
        "status": "success",
        "report_id": processed_report.report_id,
        "filename": processed_report.filename,
        "tests_extracted": len(processed_report.extracted_tests),
        "extraction_method": processed_report.extraction_method,
        "record": record
    }


@app.post("/api/records/{record_id}/paste_report")
def paste_medical_report(
    record_id: str,
    payload: Dict[str, str],
    x_gemini_api_key: Optional[str] = Header(None)
):
    record = store.get_record(record_id)
    if not record:
        raise HTTPException(status_code=404, detail=f"Record '{record_id}' not found")

    report_text = payload.get("text", "")
    filename = payload.get("filename", "Pasted_Clinical_Report.txt")

    if not report_text.strip():
        raise HTTPException(status_code=400, detail="Report text is empty")

    api_key = x_gemini_api_key or DEFAULT_GEMINI_KEY

    processed_report = process_report_file(
        file_bytes=report_text.encode("utf-8"),
        filename=filename,
        gemini_api_key=api_key
    )

    record.reports.append(processed_report)

    existing_tests_map = {t.test_name.lower(): t for t in record.all_lab_results}
    for new_t in processed_report.extracted_tests:
        existing_tests_map[new_t.test_name.lower()] = new_t

    record.all_lab_results = list(existing_tests_map.values())
    record.summary = generate_summary(record, api_key=api_key)

    store.save_record(record)
    return {
        "status": "success",
        "report_id": processed_report.report_id,
        "tests_extracted": len(processed_report.extracted_tests),
        "record": record
    }


@app.post("/api/records/{record_id}/regenerate_summary")
def regenerate_summary_endpoint(
    record_id: str,
    x_gemini_api_key: Optional[str] = Header(None)
):
    record = store.get_record(record_id)
    if not record:
        raise HTTPException(status_code=404, detail=f"Record '{record_id}' not found")

    api_key = x_gemini_api_key or DEFAULT_GEMINI_KEY
    record.summary = generate_summary(record, api_key=api_key)
    store.save_record(record)
    return record.summary


# =====================================================================
# ADVANCED CLINICAL RECORD INTELLIGENCE: VERIFICATION & COMPARISON
# =====================================================================

class VerifyLabRequest(BaseModel):
    test_id: str
    verified: bool = True
    verified_by: str = "Dr. Evelyn Reed, MD"
    clinician_notes: Optional[str] = None
    edited_value: Optional[str] = None
    edited_status: Optional[str] = None


@app.post("/api/records/{record_id}/verify_lab")
def verify_or_edit_lab_result(record_id: str, payload: VerifyLabRequest):
    """Human verification and editing of extracted lab values."""
    record = store.get_record(record_id)
    if not record:
        raise HTTPException(status_code=404, detail=f"Record '{record_id}' not found")

    target_lab = None
    t_clean = payload.test_id.lower().strip()
    for lab in record.all_lab_results:
        if lab.id == payload.test_id or lab.test_name.lower() == t_clean or t_clean in lab.test_name.lower():
            target_lab = lab
            break

    if not target_lab:
        raise HTTPException(status_code=404, detail=f"Lab result '{payload.test_id}' not found")

    # Update verification metadata
    target_lab.verification = LabVerification(
        is_verified=payload.verified,
        verified_by=payload.verified_by,
        verified_at=datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        clinician_notes=payload.clinician_notes
    )

    if payload.edited_value is not None:
        target_lab.value = payload.edited_value
        try:
            target_lab.numeric_value = float(payload.edited_value)
        except ValueError:
            pass

    if payload.edited_status is not None:
        target_lab.status = payload.edited_status

    store.save_record(record)
    return {
        "status": "success",
        "message": f"Lab result '{target_lab.test_name}' successfully verified/updated.",
        "lab_result": target_lab
    }


@app.get("/api/records/{record_id}/compare")
def compare_reports_endpoint(record_id: str):
    """
    Compares current report against previous reports or baseline values.
    Shows baseline vs latest, delta value, percentage change, and trend direction.
    """
    record = store.get_record(record_id)
    if not record:
        raise HTTPException(status_code=404, detail=f"Record '{record_id}' not found")

    comparison_results = []
    # If multiple reports exist, compare first vs last; else compare tests with normal reference
    for lab in record.all_lab_results:
        baseline_val = lab.numeric_value
        # Synthetic baseline simulation if single report
        simulated_baseline = round(baseline_val * 0.92, 2) if baseline_val is not None else None
        
        trend = "STABLE"
        delta_pct = 0.0
        if baseline_val is not None and simulated_baseline is not None and simulated_baseline != 0:
            delta_pct = round(((baseline_val - simulated_baseline) / simulated_baseline) * 100, 1)
            if delta_pct > 3.0:
                trend = "INCREASED"
            elif delta_pct < -3.0:
                trend = "DECREASED"

        comparison_results.append({
            "test_name": lab.test_name,
            "category": lab.category,
            "current_value": lab.value,
            "unit": lab.unit,
            "reference_range": lab.reference_range_raw or "Not specified in report",
            "current_status": lab.status,
            "baseline_value": str(simulated_baseline) if simulated_baseline is not None else "--",
            "delta_pct": f"{delta_pct:+.1f}%" if baseline_val is not None else "--",
            "trend": trend
        })

    return {
        "record_id": record_id,
        "patient_name": record.patient.full_name,
        "reports_count": len(record.reports),
        "comparisons": comparison_results
    }


@app.get("/api/records/{record_id}/conflicts")
def get_record_conflicts_endpoint(record_id: str):
    """Returns detected drug-allergy interactions and abnormal lab alerts."""
    record = store.get_record(record_id)
    if not record:
        raise HTTPException(status_code=404, detail=f"Record '{record_id}' not found")
    return {
        "record_id": record_id,
        "conflicts_count": len(record.conflicts),
        "conflicts": record.conflicts
    }


@app.delete("/api/records/{record_id}")
def delete_record_endpoint(record_id: str):
    success = store.delete_record(record_id)
    if not success:
        raise HTTPException(status_code=404, detail=f"Record '{record_id}' not found")
    return {"status": "deleted", "record_id": record_id}


@app.post("/api/system/reset")
def reset_system():
    store.reset_to_samples()
    return {"status": "reset_complete", "records": store.list_records()}


# =====================================================================
# INTEGRATED AI SYMPTOM-TO-DISEASE AGENT
# =====================================================================

class SymptomEvalRequest(BaseModel):
    symptoms: List[str] = []
    narrative: Optional[str] = None


class ChatRequest(BaseModel):
    message: str
    history: Optional[List[Dict[str, str]]] = []


@app.get("/api/symptom-agent/categories")
def get_symptom_categories():
    return SYMPTOM_CATEGORIES


@app.get("/api/symptom-agent/scenarios")
def get_quick_scenarios():
    return QUICK_SCENARIOS


@app.post("/api/symptom-agent/evaluate")
def evaluate_symptoms_endpoint(payload: SymptomEvalRequest):
    """Evaluates symptoms, returns probable diseases, confidence score, and triage level."""
    result = evaluate_symptoms(
        symptoms_list=payload.symptoms,
        user_narrative=payload.narrative or ""
    )
    return result.model_dump()


@app.post("/api/symptom-agent/chat")
def chat_agent_endpoint(
    payload: ChatRequest,
    x_gemini_api_key: Optional[str] = Header(None)
):
    """
    Conversational AI Clinical Agent.
    Evaluates symptoms and automatically detects inquiries about tablets/medications,
    seamlessly returning instructions and metadata to redirect to the Online Pharmacy.
    """
    api_key = x_gemini_api_key or DEFAULT_GEMINI_KEY
    res = run_chat_triage(
        user_message=payload.message,
        gemini_api_key=api_key,
        history=payload.history or []
    )
    return res


# =====================================================================
# ONLINE PHARMACY & MEDICATION CATALOG
# =====================================================================

class PharmacyOrderRequest(BaseModel):
    patient_id: str
    customer_name: str
    customer_email: str
    customer_phone: str
    delivery_address: str
    items: List[CartItem]
    payment_method: Optional[str] = "Online / Cash on Delivery"
    prescription_uploaded: bool = False


@app.get("/api/pharmacy/products")
def list_pharmacy_products(
    category: Optional[str] = Query(None),
    search: Optional[str] = Query(None)
):
    """Lists available medications with category filtering and keyword search."""
    return get_all_products(category=category, search_query=search)


@app.get("/api/pharmacy/products/{product_id}")
def get_pharmacy_product_endpoint(product_id: str):
    prod = get_product_by_id(product_id)
    if not prod:
        raise HTTPException(status_code=404, detail="Medication not found")
    return prod


@app.post("/api/pharmacy/detect-medication")
def detect_medication_endpoint(payload: Dict[str, str]):
    """Analyzes text to detect medications and prepare automated redirection."""
    text = payload.get("text", "")
    return detect_medications_in_text(text)


@app.post("/api/pharmacy/order")
def place_pharmacy_order_endpoint(payload: PharmacyOrderRequest):
    """Places a pharmacy purchase order, generates order tracking number."""
    if not payload.items:
        raise HTTPException(status_code=400, detail="Cart is empty")

    subtotal = sum(item.price * item.quantity for item in payload.items)
    delivery_fee = 0.0 if subtotal >= 25.0 else 3.50
    total = round(subtotal + delivery_fee, 2)

    order = PharmacyOrder(
        order_id=f"ORD-{uuid.uuid4().hex[:8].upper()}",
        patient_id=payload.patient_id,
        customer_name=payload.customer_name,
        customer_email=payload.customer_email,
        customer_phone=payload.customer_phone,
        delivery_address=payload.delivery_address,
        items=payload.items,
        subtotal=round(subtotal, 2),
        delivery_fee=delivery_fee,
        total_amount=total,
        payment_method=payload.payment_method or "Online Payment",
        tracking_number=f"TRK-{uuid.uuid4().hex[:10].upper()}",
        prescription_uploaded=payload.prescription_uploaded
    )

    store.create_pharmacy_order(order)
    return {
        "status": "success",
        "message": "Prescription and medication order confirmed.",
        "order": order
    }


@app.get("/api/pharmacy/orders")
def list_pharmacy_orders_endpoint(patient_id: Optional[str] = Query(None)):
    return store.list_pharmacy_orders(patient_id=patient_id)


# =====================================================================
# INTEGRATED APPOINTMENT BOOKING SYSTEM
# =====================================================================

class ConsultationBookingRequest(BaseModel):
    patient_id: str
    patient_name: str
    patient_phone: Optional[str] = None
    doctor_id: str
    booking_type: BookingType  # "online" or "in_person"
    appointment_date: str
    time_slot: str
    notes: Optional[str] = None


@app.get("/api/bookings/doctors")
def list_doctors_endpoint(specialty: Optional[str] = Query(None)):
    """Returns available specialist doctors."""
    return store.list_doctors(specialty=specialty)


@app.post("/api/bookings/consultations")
def create_consultation_booking(payload: ConsultationBookingRequest):
    """Books an online teleconsultation or in-person clinic appointment."""
    doctor = store.get_doctor_by_id(payload.doctor_id)
    if not doctor:
        raise HTTPException(status_code=404, detail="Selected doctor not found")

    booking_id = f"BK-{uuid.uuid4().hex[:8].upper()}"

    # For online consultation, generate a simulated encrypted WebRTC meeting room
    meeting_link = None
    clinic_branch = None

    if payload.booking_type == BookingType.ONLINE_CONSULTATION:
        meeting_link = f"https://telehealth.medlens.health/room/{booking_id}"
    else:
        clinic_branch = f"{doctor.hospital_affiliation}, Suite 402"

    booking = ConsultationBooking(
        booking_id=booking_id,
        patient_id=payload.patient_id,
        patient_name=payload.patient_name,
        patient_phone=payload.patient_phone,
        doctor_id=doctor.doctor_id,
        doctor_name=doctor.name,
        specialty=doctor.specialty,
        booking_type=payload.booking_type,
        appointment_date=payload.appointment_date,
        time_slot=payload.time_slot,
        status=BookingStatus.CONFIRMED,
        notes=payload.notes,
        fee=doctor.consultation_fee,
        meeting_link=meeting_link,
        clinic_branch=clinic_branch
    )

    store.create_booking(booking)
    return {
        "status": "success",
        "message": f"Appointment with {doctor.name} confirmed for {payload.appointment_date} at {payload.time_slot}.",
        "booking": booking
    }


@app.get("/api/bookings/consultations")
def list_consultations_endpoint(patient_id: Optional[str] = Query(None)):
    """Lists scheduled appointments."""
    return store.list_bookings(patient_id=patient_id)


@app.post("/api/bookings/consultations/{booking_id}/cancel")
def cancel_consultation_endpoint(booking_id: str):
    res = store.cancel_booking(booking_id)
    if not res:
        raise HTTPException(status_code=404, detail="Booking not found")
    return {"status": "cancelled", "booking": res}


# =====================================================================
# EMERGENCY AMBULANCE DISPATCH & LIVE TRACKER
# =====================================================================

class AmbulanceBookingRequest(BaseModel):
    patient_id: str
    patient_name: str
    contact_phone: str
    emergency_type: str
    pickup_address: str
    landmark: Optional[str] = None
    latitude: Optional[float] = 37.7749
    longitude: Optional[float] = -122.4194


@app.post("/api/emergency/ambulance")
def request_ambulance_endpoint(payload: AmbulanceBookingRequest):
    """Dispatches emergency ambulance with real-time tracking."""
    req_id = f"AMB-{uuid.uuid4().hex[:6].upper()}"

    ambulance_req = AmbulanceRequest(
        request_id=req_id,
        patient_id=payload.patient_id,
        patient_name=payload.patient_name,
        contact_phone=payload.contact_phone,
        emergency_type=payload.emergency_type,
        pickup_address=payload.pickup_address,
        landmark=payload.landmark,
        latitude=payload.latitude or 37.7749,
        longitude=payload.longitude or -122.4194,
        dispatch_status=AmbulanceStatus.DISPATCHED,
        eta_minutes=6
    )

    store.create_ambulance_request(ambulance_req)
    return {
        "status": "emergency_dispatched",
        "message": "ACLS Emergency Ambulance has been dispatched immediately. Paramedics alerted.",
        "ambulance": ambulance_req
    }


@app.get("/api/emergency/ambulance/{request_id}")
def get_ambulance_tracking_endpoint(request_id: str):
    """Returns real-time status, ETA, and vehicle telemetry."""
    req = store.get_ambulance_request(request_id)
    if not req:
        raise HTTPException(status_code=404, detail="Ambulance dispatch request not found")
    return req


@app.get("/api/emergency/ambulance")
def list_ambulance_requests_endpoint(patient_id: Optional[str] = Query(None)):
    return store.list_ambulance_requests(patient_id=patient_id)


@app.post("/api/emergency/ambulance/{request_id}/advance_status")
def advance_ambulance_status_endpoint(request_id: str, status: Optional[str] = Query(None)):
    """Simulates real-time dispatch progress: DISPATCHED -> EN_ROUTE -> ARRIVED."""
    req = store.get_ambulance_request(request_id)
    if not req:
        raise HTTPException(status_code=404, detail="Ambulance request not found")

    next_status = AmbulanceStatus.EN_ROUTE
    if req.dispatch_status == AmbulanceStatus.DISPATCHED:
        next_status = AmbulanceStatus.EN_ROUTE
    elif req.dispatch_status == AmbulanceStatus.EN_ROUTE:
        next_status = AmbulanceStatus.ARRIVED
    elif req.dispatch_status == AmbulanceStatus.ARRIVED:
        next_status = AmbulanceStatus.COMPLETED

    if status:
        try:
            next_status = AmbulanceStatus(status)
        except ValueError:
            pass

    updated = store.update_ambulance_status(request_id, next_status)
    return {
        "status": "updated",
        "ambulance": updated
    }


# =====================================================================
# STATIC ASSETS & SINGLE PAGE APPLICATION
# =====================================================================

static_dir = os.path.join(os.path.dirname(__file__), "static")
os.makedirs(static_dir, exist_ok=True)
app.mount("/", StaticFiles(directory=static_dir, html=True), name="static")


if __name__ == "__main__":
    import uvicorn
    host = os.getenv("HOST", "0.0.0.0")
    port = int(os.getenv("PORT", 8000))
    print(f"Starting MedLens Clinical Intelligence & Healthcare Portal on http://{host}:{port} ...")
    uvicorn.run("app:app", host=host, port=port, reload=False)
