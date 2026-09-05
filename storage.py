"""
Storage module for Structured Medical Records.
Provides in-memory caching and persistent JSON storage.
Auto-initializes with preloaded clinical sample cases for immediate review.
"""

import json
import os
import uuid
from typing import Dict, List, Optional
from models import (
    StructuredMedicalRecord,
    PatientProfile,
    ProcessedReport,
    PatientFriendlySummary,
    LabResult,
)
from samples import SAMPLE_CASES
from extractor import process_report_file
from summarizer import generate_summary

DATA_DIR = os.path.join(os.path.dirname(__file__), "data")
STORAGE_FILE = os.path.join(DATA_DIR, "records.json")


class RecordStore:
    def __init__(self):
        self._records: Dict[str, StructuredMedicalRecord] = {}
        self._ensure_storage()

    def _ensure_storage(self):
        os.makedirs(DATA_DIR, exist_ok=True)
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

    def _initialize_samples(self):
        """Initializes storage with realistic sample cases so the system is immediately usable."""
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

                # Generate initial summary
                med_record.summary = generate_summary(med_record)
                self._records[record_id] = med_record
            except Exception as e:
                print(f"Failed to initialize sample case {case_key}: {e}")

        self.persist()

    def persist(self):
        """Writes current records to JSON file."""
        try:
            os.makedirs(DATA_DIR, exist_ok=True)
            data = {k: v.model_dump() for k, v in self._records.items()}
            with open(STORAGE_FILE, "w", encoding="utf-8") as f:
                json.dump(data, f, indent=2)
        except Exception as e:
            print(f"Failed to persist records: {e}")

    def list_records(self) -> List[Dict[str, Any]]:
        """Returns lightweight list of patient records for the selector/nav."""
        out = []
        for r in self._records.values():
            out.append({
                "record_id": r.record_id,
                "patient_name": r.patient.full_name,
                "age": r.patient.age,
                "sex": r.patient.sex,
                "reports_count": len(r.reports),
                "tests_count": len(r.all_lab_results),
                "updated_at": r.updated_at
            })
        return out

    def get_record(self, record_id: str) -> Optional[StructuredMedicalRecord]:
        return self._records.get(record_id)

    def save_record(self, record: StructuredMedicalRecord) -> StructuredMedicalRecord:
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
        """Resets the database back to default sample records."""
        self._records.clear()
        self._initialize_samples()


# Global storage instance
store = RecordStore()
