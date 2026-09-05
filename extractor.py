"""
Extractor module for medical and laboratory reports.
Supports PDF extraction (via pypdf), plain text parsing,
deterministic clinical NLP with strict source-only reference range evaluation,
and optional Google Gemini AI structured extraction.
"""

import re
import uuid
import os
from typing import List, Tuple, Optional, Dict, Any
from io import BytesIO
from pypdf import PdfReader

from models import (
    LabResult,
    ValueStatus,
    ProvenanceRecord,
    ProvenanceType,
    ProcessedReport,
)

# Common clinical test definitions and categories for intelligent grouping
KNOWN_TEST_CATEGORIES = {
    # Hematology / CBC
    "WBC": "Hematology",
    "WHITE BLOOD COUNT": "Hematology",
    "LEUKOCYTES": "Hematology",
    "RBC": "Hematology",
    "RED BLOOD COUNT": "Hematology",
    "HEMOGLOBIN": "Hematology",
    "HGB": "Hematology",
    "HEMATOCRIT": "Hematology",
    "HCT": "Hematology",
    "PLATELETS": "Hematology",
    "PLATELET COUNT": "Hematology",
    "MCV": "Hematology",
    "MCH": "Hematology",
    "MCHC": "Hematology",
    "RDW": "Hematology",
    "NEUTROPHILS": "Hematology",
    "LYMPHOCYTES": "Hematology",
    "MONOCYTES": "Hematology",
    "EOSINOPHILS": "Hematology",
    "BASOPHILS": "Hematology",

    # Comprehensive / Basic Metabolic Panel (CMP / BMP)
    "GLUCOSE": "Metabolic Panel",
    "FASTING GLUCOSE": "Metabolic Panel",
    "RANDOM GLUCOSE": "Metabolic Panel",
    "CALCIUM": "Metabolic Panel",
    "SODIUM": "Electrolytes",
    "POTASSIUM": "Electrolytes",
    "CHLORIDE": "Electrolytes",
    "CARBON DIOXIDE": "Electrolytes",
    "CO2": "Electrolytes",
    "BICARBONATE": "Electrolytes",
    "BUN": "Renal Function",
    "BLOOD UREA NITROGEN": "Renal Function",
    "CREATININE": "Renal Function",
    "EGFR": "Renal Function",
    "TOTAL PROTEIN": "Hepatic Panel",
    "ALBUMIN": "Hepatic Panel",
    "GLOBULIN": "Hepatic Panel",
    "BILIRUBIN TOTAL": "Hepatic Panel",
    "TOTAL BILIRUBIN": "Hepatic Panel",
    "BILIRUBIN DIRECT": "Hepatic Panel",
    "ALP": "Hepatic Panel",
    "ALKALINE PHOSPHATASE": "Hepatic Panel",
    "ALT": "Hepatic Panel",
    "SGPT": "Hepatic Panel",
    "AST": "Hepatic Panel",
    "SGOT": "Hepatic Panel",

    # Lipid Panel
    "CHOLESTEROL": "Lipid Panel",
    "TOTAL CHOLESTEROL": "Lipid Panel",
    "TRIGLYCERIDES": "Lipid Panel",
    "HDL": "Lipid Panel",
    "HDL CHOLESTEROL": "Lipid Panel",
    "LDL": "Lipid Panel",
    "LDL CHOLESTEROL": "Lipid Panel",
    "VLDL": "Lipid Panel",
    "CHOL/HDL RATIO": "Lipid Panel",

    # Diabetes & Endocrine
    "HBA1C": "Endocrine & Diabetes",
    "HEMOGLOBIN A1C": "Endocrine & Diabetes",
    "GLYCOSYLATED HEMOGLOBIN": "Endocrine & Diabetes",
    "TSH": "Thyroid Function",
    "FREE T4": "Thyroid Function",
    "FREE T3": "Thyroid Function",
    "TOTAL T3": "Thyroid Function",
    "VITAMIN D": "Vitamins & Minerals",
    "25-OH VITAMIN D": "Vitamins & Minerals",
    "VITAMIN B12": "Vitamins & Minerals",
    "FERRITIN": "Iron Studies",
    "SERUM IRON": "Iron Studies",
    "TIBC": "Iron Studies",
    "TRANSFERRIN": "Iron Studies",

    # Inflammatory & Cardiac
    "CRP": "Inflammatory Markers",
    "C-REACTIVE PROTEIN": "Inflammatory Markers",
    "HS-CRP": "Inflammatory Markers",
    "ESR": "Inflammatory Markers",
    "TROPONIN": "Cardiac Markers",
    "TROPONIN I": "Cardiac Markers",
    "BNP": "Cardiac Markers",
    "NT-PROBNP": "Cardiac Markers",

    # Urinalysis
    "URINE PROTEIN": "Urinalysis",
    "URINE GLUCOSE": "Urinalysis",
    "URINE SPECIFIC GRAVITY": "Urinalysis",
    "URINE PH": "Urinalysis",
    "URINE LEUKOCYTE ESTERASE": "Urinalysis",
    "URINE NITRITE": "Urinalysis",
}


def extract_text_from_pdf(pdf_bytes: bytes) -> List[Tuple[int, str]]:
    """
    Extracts text page by page from PDF bytes.
    Returns list of tuples: (page_number, page_text).
    """
    pages_text = []
    try:
        reader = PdfReader(BytesIO(pdf_bytes))
        for idx, page in enumerate(reader.pages):
            text = page.extract_text() or ""
            pages_text.append((idx + 1, text))
    except Exception as e:
        print(f"Error reading PDF: {e}")
        # fallback: empty or partial
    return pages_text


def parse_reference_range(range_str: Optional[str]) -> Tuple[Optional[float], Optional[float], Optional[str]]:
    """
    Parses a reference range string strictly into (ref_low, ref_high, ref_textual).
    DOES NOT INVENT any numbers. If none is found, returns (None, None, None).
    Examples:
      '70 - 99' -> (70.0, 99.0, None)
      '0.5 - 1.2' -> (0.5, 1.2, None)
      '< 200' -> (None, 200.0, None)
      '<= 100' -> (None, 100.0, None)
      '> 60' -> (60.0, None, None)
      '>= 60' -> (60.0, None, None)
      'Negative' -> (None, None, 'Negative')
    """
    if not range_str or range_str.strip().lower() in ["", "none", "n/a", "not provided", "unspecified", "-"]:
        return None, None, None

    cleaned = range_str.strip()

    # Pattern 1: Low - High (e.g., 70 - 99, 4.0-5.5, 13.5 to 17.5)
    match_between = re.search(r"([0-9]+(?:\.[0-9]+)?)\s*(?:-|–|—|to)\s*([0-9]+(?:\.[0-9]+)?)", cleaned, re.IGNORECASE)
    if match_between:
        try:
            low = float(match_between.group(1))
            high = float(match_between.group(2))
            return low, high, None
        except ValueError:
            pass

    # Pattern 2: Less than (< 200, <= 100)
    match_less = re.search(r"(?:<|<=|less\s+than)\s*([0-9]+(?:\.[0-9]+)?)", cleaned, re.IGNORECASE)
    if match_less:
        try:
            high = float(match_less.group(1))
            return None, high, None
        except ValueError:
            pass

    # Pattern 3: Greater than (> 60, >= 60)
    match_greater = re.search(r"(?:>|>=|greater\s+than)\s*([0-9]+(?:\.[0-9]+)?)", cleaned, re.IGNORECASE)
    if match_greater:
        try:
            low = float(match_greater.group(1))
            return low, None, None
        except ValueError:
            pass

    # Textual reference range (e.g. Negative, Non-reactive, Normal)
    textual_matches = ["negative", "non-reactive", "nonreactive", "normal", "clear", "nil", "absent"]
    for tm in textual_matches:
        if tm in cleaned.lower():
            return None, None, cleaned

    return None, None, cleaned


def evaluate_value_against_range(
    value_str: str,
    ref_low: Optional[float],
    ref_high: Optional[float],
    ref_textual: Optional[str],
    has_range_in_source: bool,
    unit: str = ""
) -> Tuple[ValueStatus, str]:
    """
    Evaluates value against source-provided reference range.
    CRITICAL: Never invents reference ranges. If no range is in source, marks UNSPECIFIED.
    """
    if not has_range_in_source or (ref_low is None and ref_high is None and not ref_textual):
        return (
            ValueStatus.UNSPECIFIED,
            "No reference range specified in source report (system does not assume or invent standard ranges)."
        )

    # Try to extract numeric value
    num_match = re.search(r"[-+]?[0-9]*\.?[0-9]+", value_str)
    if num_match:
        try:
            num_val = float(num_match.group(0))

            # Case: Both low and high defined (e.g. 70 - 99)
            if ref_low is not None and ref_high is not None:
                if num_val < ref_low:
                    return (
                        ValueStatus.LOW,
                        f"Value {num_val} is below source reference range ({ref_low} - {ref_high} {unit})."
                    )
                elif num_val > ref_high:
                    return (
                        ValueStatus.HIGH,
                        f"Value {num_val} is above source reference range ({ref_low} - {ref_high} {unit})."
                    )
                else:
                    return (
                        ValueStatus.NORMAL,
                        f"Value {num_val} is within source reference range ({ref_low} - {ref_high} {unit})."
                    )

            # Case: Only high defined (e.g. < 200)
            if ref_high is not None and ref_low is None:
                if num_val > ref_high:
                    return (
                        ValueStatus.HIGH,
                        f"Value {num_val} exceeds source upper threshold (< {ref_high} {unit})."
                    )
                else:
                    return (
                        ValueStatus.NORMAL,
                        f"Value {num_val} is within source upper threshold (< {ref_high} {unit})."
                    )

            # Case: Only low defined (e.g. > 60)
            if ref_low is not None and ref_high is None:
                if num_val < ref_low:
                    return (
                        ValueStatus.LOW,
                        f"Value {num_val} is below source lower threshold (> {ref_low} {unit})."
                    )
                else:
                    return (
                        ValueStatus.NORMAL,
                        f"Value {num_val} meets or exceeds source lower threshold (> {ref_low} {unit})."
                    )
        except ValueError:
            pass

    # Textual evaluation
    v_clean = value_str.strip().lower()
    if ref_textual:
        ref_clean = ref_textual.strip().lower()
        if ("negative" in ref_clean and "negative" in v_clean) or ("normal" in ref_clean and "normal" in v_clean):
            return ValueStatus.NORMAL, f"Value matches source normal reference '{ref_textual}'."
        if ("negative" in ref_clean and "positive" in v_clean) or ("normal" in ref_clean and "abnormal" in v_clean):
            return ValueStatus.HIGH, f"Value '{value_str}' differs from source normal reference '{ref_textual}'."

    return (
        ValueStatus.INCONCLUSIVE,
        "Result could not be automatically evaluated against non-numeric reference range."
    )


def determine_category(test_name: str) -> str:
    """Categorizes test by standard medical panel."""
    t_upper = test_name.upper().strip()
    for key, cat in KNOWN_TEST_CATEGORIES.items():
        if key in t_upper or t_upper in key:
            return cat
    if any(term in t_upper for term in ["URINE", "URINARY"]):
        return "Urinalysis"
    if any(term in t_upper for term in ["CHOLESTEROL", "LIPID", "TRIGLYCERIDE"]):
        return "Lipid Panel"
    if any(term in t_upper for term in ["THYROID", "TSH", "T3", "T4"]):
        return "Thyroid Function"
    if any(term in t_upper for term in ["HEMOGLOBIN", "PLATELET", "WBC", "RBC", "BLOOD COUNT"]):
        return "Hematology"
    if any(term in t_upper for term in ["GLUCOSE", "SUGAR", "A1C"]):
        return "Endocrine & Diabetes"
    if any(term in t_upper for term in ["KIDNEY", "CREATININE", "UREA", "BUN", "EGFR"]):
        return "Renal Function"
    if any(term in t_upper for term in ["LIVER", "ALT", "AST", "BILIRUBIN", "SGPT", "SGOT"]):
        return "Hepatic Panel"
    return "Diagnostic Lab"


def extract_report_metadata(text: str) -> Dict[str, Optional[str]]:
    """Extracts report date, facility, and physician if detectable."""
    meta = {"report_date": None, "facility_or_doctor": None}

    # Search for dates (e.g., 2024-03-15, 03/15/2024, 15-Mar-2024, March 15, 2024)
    date_patterns = [
        r"(?:Date|Collected|Reported|Date of Service|D\.O\.S\.|Collection Date)[:\s]+([0-9]{1,2}[/-][0-9]{1,2}[/-][0-9]{2,4})",
        r"(?:Date|Collected|Reported)[:\s]+([0-9]{4}[/-][0-9]{1,2}[/-][0-9]{1,2})",
        r"([A-Za-z]{3,9}\s+[0-9]{1,2},\s+[0-9]{4})",
    ]
    for pattern in date_patterns:
        m = re.search(pattern, text, re.IGNORECASE)
        if m:
            meta["report_date"] = m.group(1).strip()
            break

    # Search for facility / lab name
    facility_patterns = [
        r"(?:Laboratory|Facility|Clinic|Hospital|Lab Name)[:\s]+([A-Za-z0-9\s,\.\-&]{4,40})",
        r"([A-Za-z\s]+(?:Diagnostic|Diagnostics|Laboratories|Laboratory|Hospital|Medical Center|Pathology|Health Clinic))",
    ]
    for pattern in facility_patterns:
        m = re.search(pattern, text, re.IGNORECASE)
        if m:
            val = m.group(1).strip().split("\n")[0]
            if len(val) > 3 and not any(skip in val.lower() for skip in ["test", "patient", "result"]):
                meta["facility_or_doctor"] = val
                break

    return meta


def parse_lab_report_deterministic(
    raw_text: str,
    source_filename: str = "Uploaded_Report.pdf",
    page_num: int = 1
) -> List[LabResult]:
    """
    Deterministic clinical NLP parser for lab and medical reports.
    Extracts test names, numeric/text values, units, reference ranges, and observations.
    CRITICAL: Preserves strict provenance and ref-range awareness.
    """
    results: List[LabResult] = []
    lines = raw_text.splitlines()

    # Common unit list for regex anchor
    # mg/dL, g/dL, mmol/L, %, uIU/mL, pg/mL, ng/mL, /uL, K/uL, M/uL, fl, 10^3/uL, etc.
    units_regex = r"(?:mg/dL|g/dL|mmol/L|umol/L|µmol/L|mEq/L|uIU/mL|µIU/mL|mIU/L|IU/L|U/L|pg/mL|ng/mL|ng/dL|mcg/dL|µg/dL|/uL|/µL|K/uL|M/uL|10\^3/uL|10\^6/uL|fl|fL|pg|%|sec|seconds|mm/hr|ratio)?"

    # Pattern A: Standard tabular row
    # Test Name (text) | Result (num or text) | Unit | Reference Range (Low - High or < High or > Low) | (Optional Flag)
    # E.g.: "Fasting Blood Glucose   126   mg/dL   70 - 99   HIGH"
    # E.g.: "Total Cholesterol       215   mg/dL   < 200     H"
    # E.g.: "TSH                     2.45  uIU/mL  0.4 - 4.0 Normal"
    # E.g.: "Hemoglobin              14.2  g/dL    13.0 - 17.5"
    tabular_pattern = re.compile(
        r"^([A-Za-z0-9\s\(\)\/\-\.\+]{2,40}?)"  # Test name
        r"\s{2,}"                                # 2+ spaces separating
        r"([<>~]?\s*[0-9]+(?:\.[0-9]+)?|[A-Za-z]+)"  # Value
        r"(?:\s+(" + units_regex + r"))?"       # Unit (optional)
        r"(?:\s{2,}|(?<=[0-9A-Za-z])\s+)"      # Spacer
        r"([<>=\s0-9\.\-–—to]+|Negative|Normal|Clear|Non-reactive)?"  # Reference range (optional)
        r"(?:\s+(High|Low|H|L|Normal|Abnormal|Critical|Alert|\*))?$",  # Source Flag (optional)
        re.IGNORECASE
    )

    # Pattern B: Colon / delimited lines
    # E.g.: "Serum Creatinine: 1.1 mg/dL (Reference Range: 0.7 - 1.3 mg/dL)"
    # E.g.: "HbA1c: 6.8 % [4.0 - 5.6]"
    # E.g.: "White Blood Count: 7.2 10^3/uL (Ref: 4.5 - 11.0)"
    colon_pattern = re.compile(
        r"^([A-Za-z0-9\s\(\)\/\-\+]{2,35}):\s*"  # Test Name
        r"([<>~]?\s*[0-9]+(?:\.[0-9]+)?|[A-Za-z]+)\s*"  # Value
        r"([A-Za-z%\/\^0-9\s]{0,12}?)"  # Unit
        r"(?:\s*(?:[\(\[\{]|Ref(?:erence)?(?:\s*Range)?[:\s]*)\s*([0-9\.\s\-–—to<>=]+|Negative|Normal|Clear)[\)\]\}]?)?",
        re.IGNORECASE
    )

    seen_names = set()

    for line in lines:
        cleaned_line = line.strip()
        if not cleaned_line or len(cleaned_line) < 4:
            continue

        # Skip headers and metadata lines
        upper_l = cleaned_line.upper()
        if any(h in upper_l for h in ["TEST NAME", "REFERENCE INTERVAL", "PAGE ", "PATIENT NAME", "COLLECTION DATE", "ACCESSION", "ORDERING PHYSICIAN"]):
            continue

        test_name = None
        raw_val = None
        unit = ""
        ref_raw = None
        obs_notes = None

        # Attempt Tabular Match
        m_tab = tabular_pattern.match(cleaned_line)
        if m_tab:
            cand_name = m_tab.group(1).strip()
            cand_val = m_tab.group(2).strip()
            cand_unit = (m_tab.group(3) or "").strip()
            cand_ref = (m_tab.group(4) or "").strip()
            cand_flag = (m_tab.group(5) or "").strip()

            # Filter out false positives
            if len(cand_name) > 1 and not cand_name.lower().startswith(("date", "page", "phone", "dr.", "lab")):
                test_name = cand_name
                raw_val = cand_val
                unit = cand_unit
                ref_raw = cand_ref if cand_ref else None
                if cand_flag:
                    obs_notes = f"Report flagged as: {cand_flag}"

        # Attempt Colon Match if not matched
        if not test_name:
            m_col = colon_pattern.match(cleaned_line)
            if m_col:
                cand_name = m_col.group(1).strip()
                cand_val = m_col.group(2).strip()
                cand_unit = (m_col.group(3) or "").strip()
                cand_ref = (m_col.group(4) or "").strip()

                if len(cand_name) > 1 and not cand_name.lower().startswith(("phone", "address", "dr", "doctor", "dob", "mrn", "patient", "specimen")):
                    test_name = cand_name
                    raw_val = cand_val
                    unit = cand_unit
                    ref_raw = cand_ref if cand_ref else None

        # Robust multi-column fallback: handles lines with or without reference ranges
        if not test_name:
            tokens = [t.strip() for t in re.split(r"\s{2,}|\t+", cleaned_line) if t.strip()]
            if len(tokens) >= 2:
                c_name = tokens[0]
                # Check if first token is a valid test name (not a section header or number)
                if not re.match(r"^[0-9]+(?:\.[0-9]+)?$", c_name) and not c_name.lower().startswith(("date", "page", "mrn", "patient", "dr.", "lab", "flag", "status")):
                    # Check token 1 or 2 for numeric value
                    for idx, tok in enumerate(tokens[1:], start=1):
                        m_val = re.search(r"^([<>~]?\s*[0-9]+(?:\.[0-9]+)?|[A-Za-z]+)$", tok)
                        if m_val:
                            test_name = c_name
                            raw_val = tok
                            remaining_tokens = tokens[idx+1:]
                            # Inspect remaining tokens for unit, range, flag
                            for rem in remaining_tokens:
                                # Check if it's a known unit
                                if re.match(r"^(mg/dL|g/dL|mmol/L|mEq/L|uIU/mL|µIU/mL|pg/mL|ng/mL|ng/dL|K/uL|M/uL|fl|%|ratio|sec|mm/hr)$", rem, re.IGNORECASE):
                                    unit = rem
                                # Check if it's a reference range
                                elif re.search(r"[0-9]+(?:\.[0-9]+)?\s*[-–—to]\s*[0-9]+(?:\.[0-9]+)?|[<>]\s*[0-9]+(?:\.[0-9]+)?", rem):
                                    ref_raw = rem
                                elif rem.lower() in ["negative", "normal", "non-reactive", "clear"]:
                                    ref_raw = rem
                                elif rem.lower() in ["high", "low", "h", "l", "abnormal", "critical", "pending"]:
                                    obs_notes = f"Observation/Status: {rem}"
                            break

        # Process valid extracted test result
        if test_name and raw_val:
            clean_name = test_name.strip(" :-_")
            norm_key = clean_name.lower()

            # Prevent immediate duplicate lines
            if norm_key in seen_names:
                continue
            seen_names.add(norm_key)

            # Extract numeric value if applicable
            num_val = None
            m_num = re.search(r"[-+]?[0-9]*\.?[0-9]+", raw_val)
            if m_num:
                try:
                    num_val = float(m_num.group(0))
                except ValueError:
                    num_val = None

            # Reference range parsing (ONLY from source!)
            has_source_range = bool(ref_raw and ref_raw.strip())
            ref_low, ref_high, ref_textual = parse_reference_range(ref_raw)

            # Evaluate status strictly using source range
            status, status_reason = evaluate_value_against_range(
                value_str=raw_val,
                ref_low=ref_low,
                ref_high=ref_high,
                ref_textual=ref_textual,
                has_range_in_source=has_source_range,
                unit=unit
            )

            # Provenance record pointing directly to line snippet and page
            provenance = ProvenanceRecord(
                source_type=ProvenanceType.REPORT_EXTRACTED,
                source_name=source_filename,
                snippet=cleaned_line,
                page_number=page_num
            )

            lab_item = LabResult(
                id=str(uuid.uuid4())[:8],
                test_name=clean_name,
                category=determine_category(clean_name),
                value=raw_val,
                numeric_value=num_val,
                unit=unit,
                reference_range_raw=ref_raw if has_source_range else "Not specified in report",
                ref_low=ref_low,
                ref_high=ref_high,
                ref_textual=ref_textual,
                status=status,
                status_reason=status_reason,
                observation_notes=obs_notes,
                provenance=provenance
            )
            results.append(lab_item)

    # Pass 2: Sequential multi-line scanner (handles PDF stream outputs where cells are on separate newlines)
    clean_lines = [l.strip() for l in lines if l.strip()]
    i = 0
    while i < len(clean_lines) - 1:
        line_i = clean_lines[i]
        line_next = clean_lines[i + 1]

        # Check if line_next is a numerical value
        is_num = bool(re.match(r"^[-+]?[0-9]*\.?[0-9]+$", line_next))
        if is_num and 2 <= len(line_i) <= 45 and not re.match(r"^[0-9]+(?:\.[0-9]+)?$", line_i):
            upper_test = line_i.upper()
            if not any(h in upper_test for h in ["TEST NAME", "RESULT", "PAGE", "MRN", "PHONE", "PATIENT", "DATE", "DIRECTOR", "LABORATORIES", "CLIA", "UNITS", "REFERENCE", "FLAG"]):
                norm_k = line_i.strip(" :-_").lower()
                if norm_k not in seen_names:
                    t_name = line_i.strip(" :-_")
                    val = line_next
                    u = ""
                    r_raw = None
                    notes = None
                    adv = 2

                    # Check for unit
                    if i + 2 < len(clean_lines):
                        cand_unit = clean_lines[i + 2]
                        if re.match(r"^(mg/dL|g/dL|mmol/L|mEq/L|uIU/mL|µIU/mL|pg/mL|ng/mL|ng/dL|K/uL|M/uL|fl|%|ratio|sec|mm/hr|mL/min|U/L)$", cand_unit, re.IGNORECASE):
                            u = cand_unit
                            adv = 3

                    # Check for reference range
                    if i + adv < len(clean_lines):
                        cand_range = clean_lines[i + adv]
                        if re.search(r"[0-9]+(?:\.[0-9]+)?\s*[-–—to]\s*[0-9]+(?:\.[0-9]+)?|[<>]\s*[0-9]+(?:\.[0-9]+)?", cand_range) or cand_range.lower() in ["negative", "normal"]:
                            r_raw = cand_range
                            adv += 1

                    # Check for flag
                    if i + adv < len(clean_lines):
                        cand_flag = clean_lines[i + adv]
                        if cand_flag.lower() in ["high", "low", "normal", "abnormal", "critical", "pending"]:
                            notes = f"Report flagged as: {cand_flag}"
                            adv += 1

                    seen_names.add(norm_k)

                    num_val = None
                    try:
                        num_val = float(val)
                    except ValueError:
                        pass

                    has_source_range = bool(r_raw and r_raw.strip())
                    ref_low, ref_high, ref_textual = parse_reference_range(r_raw)
                    status, status_reason = evaluate_value_against_range(
                        value_str=val,
                        ref_low=ref_low,
                        ref_high=ref_high,
                        ref_textual=ref_textual,
                        has_range_in_source=has_source_range,
                        unit=u
                    )

                    prov = ProvenanceRecord(
                        source_type=ProvenanceType.REPORT_EXTRACTED,
                        source_name=source_filename,
                        snippet=f"{t_name}: {val} {u} (Ref: {r_raw or 'None'})",
                        page_number=page_num
                    )

                    results.append(LabResult(
                        id=str(uuid.uuid4())[:8],
                        test_name=t_name,
                        category=determine_category(t_name),
                        value=val,
                        numeric_value=num_val,
                        unit=u,
                        reference_range_raw=r_raw if has_source_range else "Not specified in report",
                        ref_low=ref_low,
                        ref_high=ref_high,
                        ref_textual=ref_textual,
                        status=status,
                        status_reason=status_reason,
                        observation_notes=notes,
                        provenance=prov
                    ))
                    i += adv
                    continue
        i += 1

    return results


def extract_with_gemini_ai(
    raw_text: str,
    api_key: str,
    source_filename: str = "Report.pdf"
) -> Optional[List[LabResult]]:
    """
    Uses Google Gemini API for high-level structured laboratory extraction when API key is provided.
    Strictly instructs Gemini to NOT hallucinate reference ranges.
    """
    try:
        from google import genai
        from google.genai import types

        client = genai.Client(api_key=api_key)

        prompt = f"""
You are an expert clinical laboratory data extraction system.
Extract all diagnostic and laboratory tests from the report text below into structured JSON.

CRITICAL INSTRUCTIONS ON REFERENCE RANGES:
1. ONLY extract reference ranges that are EXPLICITLY printed in the provided text.
2. DO NOT invent, assume, lookup, or hallucinate reference ranges.
3. If the document does not show a reference range for a test, set "reference_range_raw": null.
4. Categorize each test into standard clinical domains (e.g. Hematology, Metabolic Panel, Lipid Panel, Thyroid Function, Urinalysis, Renal Function).
5. Identify the exact line or text snippet where the result was found for source provenance.

Return ONLY a JSON array with objects in this exact structure:
[
  {{
    "test_name": "string",
    "category": "string",
    "value": "string",
    "unit": "string",
    "reference_range_raw": "string or null",
    "observation_notes": "string or null",
    "source_snippet": "exact snippet from report"
  }}
]

REPORT TEXT:
{raw_text}
"""

        response = client.models.generate_content(
            model="gemini-2.5-flash",
            contents=prompt,
            config=types.GenerateContentConfig(
                response_mime_type="application/json"
            )
        )

        import json
        data = json.loads(response.text)
        results: List[LabResult] = []

        for item in data:
            t_name = item.get("test_name", "Diagnostic Test")
            t_val = str(item.get("value", ""))
            t_unit = item.get("unit", "") or ""
            ref_raw = item.get("reference_range_raw")
            snippet = item.get("source_snippet", f"{t_name}: {t_val} {t_unit}")

            # Numeric parsing
            num_val = None
            m_num = re.search(r"[-+]?[0-9]*\.?[0-9]+", t_val)
            if m_num:
                try:
                    num_val = float(m_num.group(0))
                except ValueError:
                    num_val = None

            has_source_range = bool(ref_raw and ref_raw.strip())
            ref_low, ref_high, ref_textual = parse_reference_range(ref_raw)

            status, status_reason = evaluate_value_against_range(
                value_str=t_val,
                ref_low=ref_low,
                ref_high=ref_high,
                ref_textual=ref_textual,
                has_range_in_source=has_source_range,
                unit=t_unit
            )

            provenance = ProvenanceRecord(
                source_type=ProvenanceType.REPORT_EXTRACTED,
                source_name=f"{source_filename} (Gemini AI Extraction)",
                snippet=snippet,
                page_number=1
            )

            lab_item = LabResult(
                id=str(uuid.uuid4())[:8],
                test_name=t_name,
                category=item.get("category") or determine_category(t_name),
                value=t_val,
                numeric_value=num_val,
                unit=t_unit,
                reference_range_raw=ref_raw if has_source_range else "Not specified in report",
                ref_low=ref_low,
                ref_high=ref_high,
                ref_textual=ref_textual,
                status=status,
                status_reason=status_reason,
                observation_notes=item.get("observation_notes"),
                provenance=provenance
            )
            results.append(lab_item)

        return results
    except Exception as e:
        print(f"Gemini AI extraction exception (falling back to deterministic parser): {e}")
        return None


def process_report_file(
    file_bytes: bytes,
    filename: str,
    gemini_api_key: Optional[str] = None
) -> ProcessedReport:
    """
    Main processing pipeline for an uploaded medical report.
    Supports PDF or text.
    Uses Gemini AI if API key is provided and valid, otherwise uses deterministic clinical NLP.
    """
    ext = os.path.splitext(filename)[1].lower()
    full_text = ""
    pages_data = []

    if ext == ".pdf":
        pages_data = extract_text_from_pdf(file_bytes)
        full_text = "\n\n".join([f"--- Page {p_num} ---\n{p_txt}" for p_num, p_txt in pages_data])
    else:
        try:
            full_text = file_bytes.decode("utf-8")
        except UnicodeDecodeError:
            full_text = file_bytes.decode("latin-1", errors="ignore")
        pages_data = [(1, full_text)]

    metadata = extract_report_metadata(full_text)

    # Attempt AI Extraction if Gemini API key available
    extracted_tests: List[LabResult] = []
    extraction_method = "Deterministic Clinical NLP"

    if gemini_api_key and gemini_api_key.strip():
        ai_results = extract_with_gemini_ai(full_text[:12000], gemini_api_key.strip(), filename)
        if ai_results and len(ai_results) > 0:
            extracted_tests = ai_results
            extraction_method = "Google Gemini AI (Validated with Strict Source Ranges)"

    # Fallback / Default deterministic parser
    if not extracted_tests:
        all_parsed = []
        for p_num, p_text in pages_data:
            parsed = parse_lab_report_deterministic(p_text, source_filename=filename, page_num=p_num)
            all_parsed.extend(parsed)
        extracted_tests = all_parsed
        extraction_method = "Deterministic Clinical NLP"

    report_id = str(uuid.uuid4())[:8]
    processed_report = ProcessedReport(
        report_id=report_id,
        filename=filename,
        file_type=ext if ext else "text",
        report_date=metadata.get("report_date"),
        facility_or_doctor=metadata.get("facility_or_doctor"),
        extracted_tests=extracted_tests,
        raw_text_preview=full_text[:1500],
        extraction_method=extraction_method
    )

    return processed_report
