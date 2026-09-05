"""
FastAPI Application Backend for Medical AI Agent.
Coordinates patient intake, medical report processing, structured record generation,
provenance tracking, reference-range awareness, and patient-friendly AI summaries.
"""

import os
import uuid
from typing import Optional, Dict, Any, List
from fastapi import FastAPI, UploadFile, File, Form, HTTPException, Header, Query
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse, JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from dotenv import load_dotenv

from models import (
    PatientProfile,
    StructuredMedicalRecord,
    ProcessedReport,
    ProvenanceRecord,
    ProvenanceType,
    PatientFriendlySummary,
    LabResult,
)
from storage import store
from extractor import process_report_file
from summarizer import generate_summary
from samples import SAMPLE_CASES

load_dotenv()

app = FastAPI(
    title="Clinical AI Medical Record System",
    description="Intelligent Patient Intake, Report Processing, and Structured Medical Records",
    version="1.0.0"
)

# Enable CORS for local development
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Global or environment Gemini key
DEFAULT_GEMINI_KEY = os.getenv("GEMINI_API_KEY", "")


@app.get("/api/health")
def health_check():
    return {"status": "ok", "total_records": len(store.list_records())}


@app.get("/api/samples")
def get_sample_cases():
    """Returns list and metadata of preloaded sample cases."""
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
    """Returns the full sample patient data and report text for populating forms."""
    if case_key not in SAMPLE_CASES:
        raise HTTPException(status_code=404, detail="Sample case not found")
    return SAMPLE_CASES[case_key]


@app.get("/api/records")
def list_records():
    """Returns a list of all structured patient records."""
    return store.list_records()


@app.get("/api/records/{record_id}")
def get_record(record_id: str):
    """Retrieves a single structured medical record by ID."""
    record = store.get_record(record_id)
    if not record:
        raise HTTPException(status_code=404, detail=f"Medical record '{record_id}' not found")
    return record


@app.post("/api/records/patient")
def create_or_update_patient(
    patient: PatientProfile,
    x_gemini_api_key: Optional[str] = Header(None)
):
    """Creates a new patient profile or updates an existing intake."""
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


@app.post("/api/records/{record_id}/upload_report")
async def upload_medical_report(
    record_id: str,
    file: UploadFile = File(...),
    x_gemini_api_key: Optional[str] = Header(None)
):
    """
    Processes an uploaded PDF or TXT lab report, extracts all test results,
    evaluates reference ranges without inventing bounds, tracks source provenance,
    and updates the medical record.
    """
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

    # Attach to record
    record.reports.append(processed_report)

    # Consolidate tests into all_lab_results (updating duplicates by test name)
    existing_tests_map = {t.test_name.lower(): t for t in record.all_lab_results}
    for new_t in processed_report.extracted_tests:
        existing_tests_map[new_t.test_name.lower()] = new_t

    record.all_lab_results = list(existing_tests_map.values())

    # Regenerate patient-friendly AI summary
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
    """
    Processes pasted clinical text report, extracts results with provenance,
    and updates the medical record.
    """
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
    """Regenerates the AI patient-friendly summary for an existing record."""
    record = store.get_record(record_id)
    if not record:
        raise HTTPException(status_code=404, detail=f"Record '{record_id}' not found")

    api_key = x_gemini_api_key or DEFAULT_GEMINI_KEY
    record.summary = generate_summary(record, api_key=api_key)
    store.save_record(record)
    return record.summary


@app.delete("/api/records/{record_id}")
def delete_record_endpoint(record_id: str):
    """Deletes a record."""
    success = store.delete_record(record_id)
    if not success:
        raise HTTPException(status_code=404, detail=f"Record '{record_id}' not found")
    return {"status": "deleted", "record_id": record_id}


@app.post("/api/system/reset")
def reset_system():
    """Resets storage back to initial clinical sample cases."""
    store.reset_to_samples()
    return {"status": "reset_complete", "records": store.list_records()}


# Mount static directory for the single page web application
static_dir = os.path.join(os.path.dirname(__file__), "static")
os.makedirs(static_dir, exist_ok=True)
app.mount("/", StaticFiles(directory=static_dir, html=True), name="static")


if __name__ == "__main__":
    import uvicorn
    host = os.getenv("HOST", "0.0.0.0")
    port = int(os.getenv("PORT", 8000))
    print(f"Starting Medical AI Agent Web Application on http://{host}:{port} ...")
    uvicorn.run("app:app", host=host, port=port, reload=False)
