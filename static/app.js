/**
 * MediSync AI - Frontend Application Logic
 * Manages patient intake, lab result display, reference-range awareness,
 * source provenance inspection, and AI patient-friendly summary generation.
 */

// Global State
let currentRecordId = null;
let currentRecord = null;
let allRecordsList = [];
let sampleCases = [];
let selectedFile = null;

// On Page Load
document.addEventListener("DOMContentLoaded", async () => {
  loadSavedSettings();
  await loadSampleCasesMetadata();
  await refreshRecordsList();
  setupDropZone();
});

// Settings Management
function loadSavedSettings() {
  const savedKey = localStorage.getItem("medi_gemini_api_key");
  if (savedKey) {
    const input = document.getElementById("geminiApiKeyInput");
    if (input) input.value = savedKey;
  }
}

function getGeminiApiKey() {
  return localStorage.getItem("medi_gemini_api_key") || "";
}

function saveSettings() {
  const input = document.getElementById("geminiApiKeyInput");
  if (input) {
    localStorage.setItem("medi_gemini_api_key", input.value.trim());
    showAlert("Settings saved successfully.", "success");
    closeModal("settingsModal");
  }
}

function getHeaders(extraHeaders = {}) {
  const headers = { ...extraHeaders };
  const key = getGeminiApiKey();
  if (key) {
    headers["x-gemini-api-key"] = key;
  }
  return headers;
}

// UI Alert Helper
function showAlert(message, type = "info") {
  const banner = document.getElementById("alertBanner");
  const msgEl = document.getElementById("alertMessage");
  if (!banner || !msgEl) return;

  msgEl.innerText = message;
  banner.classList.remove("hidden");
  setTimeout(() => {
    banner.classList.add("hidden");
  }, 5000);
}

// Navigation Tabs
function showTab(tabId) {
  const tabs = ["recordTab", "intakeTab", "reportTab", "summaryTab", "provenanceTab"];
  tabs.forEach((t) => {
    const el = document.getElementById(t);
    if (el) el.classList.add("hidden");
  });

  const target = document.getElementById(tabId);
  if (target) target.classList.remove("hidden");

  // Highlight Nav Buttons
  const navMap = {
    recordTab: "nav-record",
    intakeTab: "nav-intake",
    reportTab: "nav-report",
    summaryTab: "nav-summary",
    provenanceTab: "nav-provenance"
  };

  Object.entries(navMap).forEach(([tId, navId]) => {
    const btn = document.getElementById(navId);
    if (btn) {
      if (tId === tabId) {
        btn.classList.add("text-brand-700", "bg-brand-50", "font-semibold");
        btn.classList.remove("text-slate-600");
      } else {
        btn.classList.remove("text-brand-700", "bg-brand-50", "font-semibold");
        btn.classList.add("text-slate-600");
      }
    }
  });

  // Reinitialize icons in newly visible content
  if (window.lucide) {
    lucide.createIcons();
  }
}

// Modal Helpers
function openModal(modalId) {
  const modal = document.getElementById(modalId);
  if (modal) modal.classList.remove("hidden");
  if (window.lucide) lucide.createIcons();
}

function closeModal(modalId) {
  const modal = document.getElementById(modalId);
  if (modal) modal.classList.add("hidden");
}

// Data Fetching: Records List & Details
async function refreshRecordsList() {
  try {
    const res = await fetch("/api/records", { headers: getHeaders() });
    if (!res.ok) throw new Error("Failed to fetch patient records");
    allRecordsList = await res.json();

    populatePatientSelect();

    if (allRecordsList.length > 0) {
      // Pick current or first
      if (!currentRecordId || !allRecordsList.some(r => r.record_id === currentRecordId)) {
        currentRecordId = allRecordsList[0].record_id;
      }
      await loadRecord(currentRecordId);
    } else {
      currentRecord = null;
      currentRecordId = null;
      renderEmptyRecordState();
    }
  } catch (err) {
    console.error("Error refreshing records:", err);
    showAlert("Failed to connect to backend server.", "error");
  }
}

function populatePatientSelect() {
  const select = document.getElementById("patientSelect");
  if (!select) return;
  select.innerHTML = "";

  if (allRecordsList.length === 0) {
    select.innerHTML = `<option value="">No patients available</option>`;
    return;
  }

  allRecordsList.forEach((r) => {
    const opt = document.createElement("option");
    opt.value = r.record_id;
    opt.textContent = `${r.patient_name} (${r.record_id.toUpperCase()})`;
    if (r.record_id === currentRecordId) {
      opt.selected = true;
    }
    select.appendChild(opt);
  });
}

async function switchPatient(recordId) {
  if (!recordId) return;
  currentRecordId = recordId;
  await loadRecord(recordId);
}

async function loadRecord(recordId) {
  try {
    const res = await fetch(`/api/records/${recordId}`, { headers: getHeaders() });
    if (!res.ok) throw new Error("Could not load medical record");
    currentRecord = await res.json();
    currentRecordId = recordId;

    renderStructuredRecordView();
    renderAttachedReports();
    renderSummaryView();
    renderProvenanceView();
    populateCategoryDropdown();

    // Update tests badge in nav
    const badge = document.getElementById("testsBadge");
    if (badge && currentRecord.all_lab_results) {
      badge.textContent = currentRecord.all_lab_results.length;
    }

    if (window.lucide) lucide.createIcons();
  } catch (err) {
    console.error("Error loading record:", err);
    showAlert(`Error loading record: ${err.message}`);
  }
}

// =========================================================================
// RENDER TAB 1: STRUCTURED MEDICAL RECORD
// =========================================================================
function renderStructuredRecordView() {
  if (!currentRecord) return;
  const p = currentRecord.patient;

  // Header Demographics
  document.getElementById("recordPatientName").textContent = p.full_name || "Unknown Patient";
  document.getElementById("recordPatientId").textContent = p.patient_id || "PT-00000";
  document.getElementById("recordAge").textContent = p.age !== null ? p.age : "--";
  document.getElementById("recordSex").textContent = p.sex || "--";
  document.getElementById("recordDob").textContent = p.dob || "Not recorded";
  document.getElementById("recordBlood").textContent = p.blood_type || "Unknown";
  document.getElementById("recordPhone").textContent = p.contact_phone || "No phone listed";

  // Attached Patient Name in other sections
  const attachedPName = document.getElementById("attachedPatientName");
  if (attachedPName) attachedPName.textContent = p.full_name;

  // Counts & Stats
  const reportsCount = currentRecord.reports ? currentRecord.reports.length : 0;
  const labs = currentRecord.all_lab_results || [];
  const flaggedLabs = labs.filter(l => l.status === "HIGH" || l.status === "LOW");
  const normalLabs = labs.filter(l => l.status === "NORMAL");

  document.getElementById("statReportsCount").textContent = reportsCount;
  document.getElementById("statTotalLabs").textContent = labs.length;
  document.getElementById("statFlaggedCount").textContent = flaggedLabs.length;
  document.getElementById("statNormalCount").textContent = normalLabs.length;

  // Render Symptoms List
  const symptomsEl = document.getElementById("recordSymptomsList");
  symptomsEl.innerHTML = "";
  if (p.symptoms && p.symptoms.length > 0) {
    p.symptoms.forEach(s => {
      const item = document.createElement("div");
      item.className = "flex items-start justify-between py-1 border-b border-amber-100/60 last:border-0";
      item.innerHTML = `
        <div>
          <span class="font-semibold text-slate-900">${escapeHtml(s.name)}</span>
          ${s.duration ? `<span class="text-[11px] text-slate-500 ml-1">(${escapeHtml(s.duration)})</span>` : ""}
          ${s.notes ? `<p class="text-[10px] text-slate-500">${escapeHtml(s.notes)}</p>` : ""}
        </div>
        <span class="text-[10px] font-bold px-1.5 py-0.2 rounded ${getSeverityClass(s.severity)}">${s.severity}</span>
      `;
      symptomsEl.appendChild(item);
    });
  } else {
    symptomsEl.innerHTML = `<span class="text-slate-400 italic">No symptoms reported</span>`;
  }

  // Render Medications List
  const medsEl = document.getElementById("recordMedsList");
  medsEl.innerHTML = "";
  if (p.medications && p.medications.length > 0) {
    p.medications.forEach(m => {
      const item = document.createElement("div");
      item.className = "py-1 border-b border-sky-100/60 last:border-0";
      item.innerHTML = `
        <div class="font-semibold text-slate-900">${escapeHtml(m.name)} <span class="text-[11px] text-brand-600 font-medium">${escapeHtml(m.dosage)}</span></div>
        <div class="text-[11px] text-slate-500">${escapeHtml(m.frequency || '')} ${m.purpose ? `• ${escapeHtml(m.purpose)}` : ''}</div>
      `;
      medsEl.appendChild(item);
    });
  } else {
    medsEl.innerHTML = `<span class="text-slate-400 italic">No medications recorded</span>`;
  }

  // Render Conditions List
  const conditionsEl = document.getElementById("recordConditionsList");
  conditionsEl.innerHTML = "";
  if (p.existing_conditions && p.existing_conditions.length > 0) {
    p.existing_conditions.forEach(c => {
      const item = document.createElement("div");
      item.className = "py-1 border-b border-slate-200/60 last:border-0";
      item.innerHTML = `
        <div class="font-semibold text-slate-900">${escapeHtml(c.condition_name)}</div>
        <div class="text-[11px] text-slate-500">${c.diagnosed_year_or_date ? `Diagnosed: ${escapeHtml(c.diagnosed_year_or_date)} • ` : ''}<span class="text-slate-700 font-medium">${c.status}</span></div>
      `;
      conditionsEl.appendChild(item);
    });
  } else {
    conditionsEl.innerHTML = `<span class="text-slate-400 italic">None documented</span>`;
  }

  // Render Allergies List
  const allergiesEl = document.getElementById("recordAllergiesList");
  allergiesEl.innerHTML = "";
  if (p.allergies && p.allergies.length > 0) {
    p.allergies.forEach(a => {
      const item = document.createElement("div");
      item.className = "py-1 border-b border-rose-100/60 last:border-0";
      item.innerHTML = `
        <div class="font-semibold text-rose-900">${escapeHtml(a.allergen)}</div>
        <div class="text-[11px] text-slate-600">${escapeHtml(a.reaction || 'Reaction unspecified')}</div>
      `;
      allergiesEl.appendChild(item);
    });
  } else {
    allergiesEl.innerHTML = `<span class="text-slate-400 italic">No known allergies</span>`;
  }

  // Out of Range Alert Box
  const alertBox = document.getElementById("outOfRangeAlertBox");
  const chipsEl = document.getElementById("outOfRangeChips");
  if (flaggedLabs.length > 0) {
    alertBox.classList.remove("hidden");
    chipsEl.innerHTML = "";
    flaggedLabs.forEach(item => {
      const isHigh = item.status === "HIGH";
      const chip = document.createElement("span");
      chip.className = `inline-flex items-center gap-1.5 px-2.5 py-1 rounded-md text-xs font-semibold ${isHigh ? 'bg-rose-100 text-rose-800 border border-rose-300' : 'bg-sky-100 text-sky-800 border border-sky-300'}`;
      chip.innerHTML = `
        <span>${isHigh ? '▲' : '▼'} ${escapeHtml(item.test_name)}:</span>
        <strong>${escapeHtml(item.value)} ${escapeHtml(item.unit)}</strong>
        <span class="text-[10px] opacity-75">(Ref: ${escapeHtml(item.reference_range_raw || 'Source Limit')})</span>
      `;
      chipsEl.appendChild(chip);
    });
  } else {
    alertBox.classList.add("hidden");
  }

  // Render Labs Table
  filterLabResults();
}

function getSeverityClass(sev) {
  switch ((sev || "").toLowerCase()) {
    case "severe":
      return "bg-rose-200 text-rose-900";
    case "moderate":
      return "bg-amber-200 text-amber-900";
    default:
      return "bg-slate-200 text-slate-800";
  }
}

// Category Dropdown Population
function populateCategoryDropdown() {
  const catSelect = document.getElementById("categoryFilterSelect");
  if (!catSelect || !currentRecord) return;

  const currentVal = catSelect.value;
  const categories = new Set();
  (currentRecord.all_lab_results || []).forEach(t => {
    if (t.category) categories.add(t.category);
  });

  catSelect.innerHTML = `<option value="ALL">All Categories</option>`;
  Array.from(categories).sort().forEach(cat => {
    const opt = document.createElement("option");
    opt.value = cat;
    opt.textContent = cat;
    if (cat === currentVal) opt.selected = true;
    catSelect.appendChild(opt);
  });
}

// Lab Results Filter & Table Render
function filterLabResults() {
  if (!currentRecord) return;

  const search = (document.getElementById("labSearchInput").value || "").toLowerCase().trim();
  const statusFilter = document.getElementById("statusFilterSelect").value;
  const catFilter = document.getElementById("categoryFilterSelect").value;

  const allLabs = currentRecord.all_lab_results || [];
  const filtered = allLabs.filter(item => {
    // Search match
    if (search && !item.test_name.toLowerCase().includes(search) && !item.category.toLowerCase().includes(search)) {
      return false;
    }

    // Status filter
    if (statusFilter === "FLAGGED" && !(item.status === "HIGH" || item.status === "LOW")) {
      return false;
    } else if (statusFilter !== "ALL" && statusFilter !== "FLAGGED" && item.status !== statusFilter) {
      return false;
    }

    // Category filter
    if (catFilter !== "ALL" && item.category !== catFilter) {
      return false;
    }

    return true;
  });

  renderLabsTable(filtered, allLabs.length);
}

function renderLabsTable(labs, totalCount) {
  const tbody = document.getElementById("labsTableBody");
  const showingEl = document.getElementById("showingCount");
  const totalEl = document.getElementById("totalCount");

  showingEl.textContent = labs.length;
  totalEl.textContent = totalCount;
  tbody.innerHTML = "";

  if (labs.length === 0) {
    tbody.innerHTML = `
      <tr>
        <td colspan="5" class="py-8 text-center text-slate-400 text-sm">
          No diagnostic tests match the specified search or filter criteria.
        </td>
      </tr>
    `;
    return;
  }

  labs.forEach(item => {
    const tr = document.createElement("tr");
    tr.className = "hover:bg-slate-50/80 transition group";

    // Status badge formatting
    let statusBadgeHtml = "";
    if (item.status === "HIGH") {
      statusBadgeHtml = `<span class="inline-flex items-center gap-1 px-2 py-0.5 rounded-full text-xs font-bold status-high"><i data-lucide="arrow-up-right" class="w-3 h-3"></i> HIGH</span>`;
    } else if (item.status === "LOW") {
      statusBadgeHtml = `<span class="inline-flex items-center gap-1 px-2 py-0.5 rounded-full text-xs font-bold status-low"><i data-lucide="arrow-down-right" class="w-3 h-3"></i> LOW</span>`;
    } else if (item.status === "NORMAL") {
      statusBadgeHtml = `<span class="inline-flex items-center gap-1 px-2 py-0.5 rounded-full text-xs font-semibold status-normal"><i data-lucide="check" class="w-3 h-3"></i> Normal</span>`;
    } else {
      statusBadgeHtml = `<span class="inline-flex items-center gap-1 px-2 py-0.5 rounded-full text-xs font-medium status-unspecified" title="No range found in report. System does not invent ranges."><i data-lucide="help-circle" class="w-3 h-3 text-slate-400"></i> No Range in Report</span>`;
    }

    // Reference range text
    const isUnspecified = item.status === "UNSPECIFIED" || !item.reference_range_raw || item.reference_range_raw.includes("Not specified");
    const refRangeDisplay = isUnspecified
      ? `<span class="text-slate-400 italic text-xs">Not specified in report</span>`
      : `<span class="font-mono font-medium text-slate-800 text-xs">${escapeHtml(item.reference_range_raw)}</span> <span class="text-[11px] text-slate-500">${escapeHtml(item.unit)}</span>`;

    // Provenance button
    const prov = item.provenance || {};
    const provSnippet = prov.snippet ? escapeHtml(prov.snippet) : "Snippet not captured";
    const provSource = prov.source_name ? escapeHtml(prov.source_name) : "Uploaded Report";
    const pageNum = prov.page_number ? ` (Pg ${prov.page_number})` : "";

    tr.innerHTML = `
      <td class="py-3 px-4">
        <div class="font-semibold text-slate-900">${escapeHtml(item.test_name)}</div>
        <span class="text-[11px] font-medium text-slate-500 bg-slate-100 px-1.5 py-0.2 rounded">${escapeHtml(item.category)}</span>
      </td>
      <td class="py-3 px-4 font-mono font-bold text-slate-900">
        ${escapeHtml(item.value)} <span class="text-xs font-normal text-slate-500">${escapeHtml(item.unit)}</span>
      </td>
      <td class="py-3 px-4">
        ${refRangeDisplay}
        ${item.status_reason ? `<div class="text-[10px] text-slate-400 mt-0.5">${escapeHtml(item.status_reason)}</div>` : ""}
      </td>
      <td class="py-3 px-4 text-center">
        ${statusBadgeHtml}
      </td>
      <td class="py-3 px-4">
        <button type="button" onclick="inspectSnippet('${escapeHtml(item.test_name)}', '${provSource}${pageNum}', '${escapeJs(prov.snippet || '')}')" class="inline-flex items-center gap-1.5 px-2.5 py-1 rounded-md text-xs font-medium badge-report-extracted hover:bg-purple-100 transition" title="Click to view exact source snippet">
          <i data-lucide="file-text" class="w-3 h-3"></i>
          <span class="truncate max-w-[130px]">${provSource}</span>
        </button>
      </td>
    `;
    tbody.appendChild(tr);
  });

  if (window.lucide) lucide.createIcons();
}

function inspectSnippet(testName, sourceInfo, snippet) {
  document.getElementById("snippetModalTitle").textContent = `Source Citation: ${testName}`;
  document.getElementById("snippetModalSubtitle").textContent = `Extracted from ${sourceInfo}`;
  document.getElementById("snippetModalContent").textContent = snippet || "No snippet captured for this result.";
  openModal("snippetModal");
}

// =========================================================================
// RENDER TAB 3: ATTACHED REPORTS
// =========================================================================
function renderAttachedReports() {
  const container = document.getElementById("attachedReportsList");
  const countEl = document.getElementById("attachedReportsCount");
  if (!container || !currentRecord) return;

  const reports = currentRecord.reports || [];
  countEl.textContent = reports.length;
  container.innerHTML = "";

  if (reports.length === 0) {
    container.innerHTML = `
      <div class="text-center py-6 text-slate-400 text-xs italic">
        No reports processed yet for this patient.
      </div>
    `;
    return;
  }

  reports.forEach((rep, idx) => {
    const card = document.createElement("div");
    card.className = "p-3.5 bg-slate-50 border border-slate-200 rounded-lg text-xs space-y-1.5";
    card.innerHTML = `
      <div class="flex items-center justify-between font-bold text-slate-900">
        <span class="flex items-center gap-1.5 truncate max-w-[200px]">
          <i data-lucide="file-text" class="w-3.5 h-3.5 text-brand-600"></i>
          ${escapeHtml(rep.filename)}
        </span>
        <span class="text-[10px] px-2 py-0.5 rounded-full bg-brand-100 text-brand-800 font-semibold">
          ${rep.extracted_tests ? rep.extracted_tests.length : 0} Tests
        </span>
      </div>
      <div class="text-[11px] text-slate-500 flex flex-wrap gap-x-3">
        ${rep.report_date ? `<span>Date: <strong>${escapeHtml(rep.report_date)}</strong></span>` : ''}
        ${rep.facility_or_doctor ? `<span>Facility: <strong>${escapeHtml(rep.facility_or_doctor)}</strong></span>` : ''}
      </div>
      <div class="text-[10px] text-slate-400 pt-1 border-t border-slate-200/60 flex items-center justify-between">
        <span>Engine: ${escapeHtml(rep.extraction_method || 'Deterministic NLP')}</span>
        <span>${escapeHtml(rep.upload_time || '')}</span>
      </div>
    `;
    container.appendChild(card);
  });

  if (window.lucide) lucide.createIcons();
}

// =========================================================================
// RENDER TAB 4: AI PATIENT SUMMARY
// =========================================================================
function renderSummaryView() {
  if (!currentRecord) return;
  const s = currentRecord.summary;

  const overviewEl = document.getElementById("summaryOverview");
  const highlightsEl = document.getElementById("summaryKeyFindings");
  const cardsEl = document.getElementById("summaryOutOfRangeCards");
  const questionsEl = document.getElementById("summaryQuestionsList");
  const disclaimerEl = document.getElementById("summaryDisclaimer");
  const engineBadge = document.getElementById("summaryEngineBadge");

  if (!s) {
    overviewEl.innerHTML = `<span class="text-slate-400 italic">No summary generated yet. Click "Regenerate Summary" to synthesize.</span>`;
    highlightsEl.innerHTML = "";
    cardsEl.innerHTML = "";
    questionsEl.innerHTML = "";
    return;
  }

  // Engine Badge
  if (engineBadge) {
    engineBadge.textContent = s.generation_engine || "Clinical Synthesis Engine";
  }

  // Overview
  overviewEl.textContent = s.overview || "Overview not available.";

  // Key Highlights
  highlightsEl.innerHTML = "";
  if (s.key_findings && s.key_findings.length > 0) {
    s.key_findings.forEach(kf => {
      const li = document.createElement("li");
      li.className = "flex items-start gap-2";
      li.innerHTML = `
        <i data-lucide="check" class="w-4 h-4 text-emerald-600 shrink-0 mt-0.5"></i>
        <span>${escapeHtml(kf)}</span>
      `;
      highlightsEl.appendChild(li);
    });
  } else {
    highlightsEl.innerHTML = `<li class="text-slate-400 italic">No specific highlights recorded.</li>`;
  }

  // Out of Range Cards
  cardsEl.innerHTML = "";
  if (s.out_of_range_explanations && s.out_of_range_explanations.length > 0) {
    s.out_of_range_explanations.forEach(item => {
      const isHigh = item.status === "HIGH";
      const card = document.createElement("div");
      card.className = "p-3.5 rounded-lg border bg-white shadow-2xs " + (isHigh ? "border-rose-200" : "border-sky-200");
      card.innerHTML = `
        <div class="flex items-center justify-between mb-1">
          <div class="font-bold text-xs text-slate-900">${escapeHtml(item.test_name)}</div>
          <span class="text-[10px] font-bold px-1.5 py-0.2 rounded ${isHigh ? 'bg-rose-100 text-rose-800' : 'bg-sky-100 text-sky-800'}">
            ${isHigh ? '▲ HIGH' : '▼ LOW'} (${escapeHtml(item.value)})
          </span>
        </div>
        <div class="text-[11px] text-slate-500 mb-1.5">Source Reference Interval: <strong>${escapeHtml(item.reference_range)}</strong></div>
        <p class="text-xs text-slate-700 leading-relaxed">${escapeHtml(item.explanation)}</p>
      `;
      cardsEl.appendChild(card);
    });
  } else {
    cardsEl.innerHTML = `
      <div class="col-span-2 p-4 text-center text-xs text-emerald-800 bg-emerald-50 rounded-lg border border-emerald-200">
        All analyzed laboratory values fall within their respective source reference ranges!
      </div>
    `;
  }

  // Doctor Questions
  questionsEl.innerHTML = "";
  if (s.questions_for_doctor && s.questions_for_doctor.length > 0) {
    s.questions_for_doctor.forEach(q => {
      const li = document.createElement("li");
      li.className = "flex items-start gap-2";
      li.innerHTML = `
        <i data-lucide="message-square" class="w-3.5 h-3.5 text-sky-600 shrink-0 mt-0.5"></i>
        <span class="font-medium">${escapeHtml(q)}</span>
      `;
      questionsEl.appendChild(li);
    });
  } else {
    questionsEl.innerHTML = `<li>No suggested questions currently generated.</li>`;
  }

  // Disclaimer
  if (disclaimerEl && s.disclaimer) {
    disclaimerEl.textContent = s.disclaimer;
  }

  if (window.lucide) lucide.createIcons();
}

async function regenerateSummary() {
  if (!currentRecordId) return;
  showAlert("Regenerating patient-friendly summary...", "info");

  try {
    const res = await fetch(`/api/records/${currentRecordId}/regenerate_summary`, {
      method: "POST",
      headers: getHeaders()
    });
    if (!res.ok) throw new Error("Failed to regenerate summary");
    const summary = await res.json();
    currentRecord.summary = summary;
    renderSummaryView();
    showAlert("AI summary updated successfully!", "success");
  } catch (err) {
    showAlert(`Error updating summary: ${err.message}`, "error");
  }
}

// =========================================================================
// RENDER TAB 5: SOURCE & PROVENANCE AUDIT TRAIL
// =========================================================================
function renderProvenanceView() {
  if (!currentRecord) return;
  const tbody = document.getElementById("provenanceTableBody");
  if (!tbody) return;
  tbody.innerHTML = "";

  const rows = [];
  const p = currentRecord.patient;

  // Patient Intake fields
  if (p.full_name) {
    rows.push({
      field: "Patient Demographics",
      value: `${p.full_name}, Age: ${p.age || 'N/A'}, Sex: ${p.sex}`,
      category: "User Provided",
      source: "Intake Form",
      snippet: `Self-reported intake by patient at ${p.last_updated || 'Registration'}`
    });
  }

  (p.symptoms || []).forEach(s => {
    rows.push({
      field: `Symptom: ${s.name}`,
      value: `Severity: ${s.severity}, Duration: ${s.duration || 'N/A'}`,
      category: "User Provided",
      source: "Patient Intake Form",
      snippet: s.notes || "Self-reported symptom during clinic intake"
    });
  });

  (p.medications || []).forEach(m => {
    rows.push({
      field: `Medication: ${m.name}`,
      value: `${m.dosage} - ${m.frequency || ''}`,
      category: "User Provided",
      source: "Patient Intake Form",
      snippet: m.purpose || "Patient self-reported active medication"
    });
  });

  (p.allergies || []).forEach(a => {
    rows.push({
      field: `Allergy: ${a.allergen}`,
      value: `Reaction: ${a.reaction || 'Unspecified'}`,
      category: "User Provided",
      source: "Patient Intake Form",
      snippet: "Self-reported allergy history"
    });
  });

  // Laboratory Test items
  (currentRecord.all_lab_results || []).forEach(t => {
    const prov = t.provenance || {};
    const ref = t.reference_range_raw || "Not specified in report";
    rows.push({
      field: `Lab Test: ${t.test_name}`,
      value: `${t.value} ${t.unit} (Ref: ${ref}) [${t.status}]`,
      category: "Extracted from Report",
      source: prov.source_name || "Diagnostic Report",
      snippet: prov.snippet || `Extracted line for ${t.test_name}`
    });
  });

  // AI Summary
  if (currentRecord.summary) {
    rows.push({
      field: "Clinical Synthesis Narrative",
      value: `${(currentRecord.summary.key_findings || []).length} findings, ${(currentRecord.summary.questions_for_doctor || []).length} doctor questions`,
      category: "AI Generated",
      source: currentRecord.summary.generation_engine || "AI Summarizer",
      snippet: "Strictly educational, non-diagnostic synthesis adhering to source-provided reference limits"
    });
  }

  rows.forEach(r => {
    const tr = document.createElement("tr");
    tr.className = "hover:bg-slate-50 transition";

    let badgeClass = "badge-user-provided";
    if (r.category === "Extracted from Report") badgeClass = "badge-report-extracted";
    else if (r.category === "AI Generated") badgeClass = "badge-ai-generated";

    tr.innerHTML = `
      <td class="py-2.5 px-3 font-semibold text-slate-800">${escapeHtml(r.field)}</td>
      <td class="py-2.5 px-3 text-slate-700">${escapeHtml(r.value)}</td>
      <td class="py-2.5 px-3">
        <span class="inline-block px-2 py-0.5 rounded text-[11px] font-semibold ${badgeClass}">
          ${escapeHtml(r.category)}
        </span>
      </td>
      <td class="py-2.5 px-3 text-slate-600">${escapeHtml(r.source)}</td>
      <td class="py-2.5 px-3 text-[11px] text-slate-500 font-mono max-w-xs truncate" title="${escapeHtml(r.snippet)}">
        ${escapeHtml(r.snippet)}
      </td>
    `;
    tbody.appendChild(tr);
  });
}

// =========================================================================
// PATIENT INTAKE FORM LOGIC
// =========================================================================
function resetIntakeForm() {
  document.getElementById("patientIntakeForm").reset();
  document.getElementById("symptomsContainer").innerHTML = "";
  document.getElementById("conditionsContainer").innerHTML = "";
  document.getElementById("medicationsContainer").innerHTML = "";
  document.getElementById("allergiesContainer").innerHTML = "";

  // Auto-generate random ID for new patient
  document.getElementById("intakePatientId").value = "PT-" + Math.floor(10000 + Math.random() * 90000);

  // Add initial empty rows
  addSymptomRow();
  addMedicationRow();
  addConditionRow();
  addAllergyRow();

  if (window.lucide) lucide.createIcons();
}

function addSymptomRow(name = "", severity = "Mild", duration = "", notes = "") {
  const container = document.getElementById("symptomsContainer");
  const row = document.createElement("div");
  row.className = "flex flex-wrap items-center gap-2 bg-slate-50 p-2.5 rounded-lg border border-slate-200 text-xs";
  row.innerHTML = `
    <input type="text" placeholder="Symptom (e.g. Chest pain, Fatigue)" value="${escapeHtml(name)}" class="symptom-name flex-2 min-w-[150px] px-2.5 py-1.5 border border-slate-300 rounded focus:outline-none bg-white">
    <select class="symptom-severity px-2 py-1.5 border border-slate-300 rounded focus:outline-none bg-white font-medium">
      <option value="Mild" ${severity === 'Mild' ? 'selected' : ''}>Mild</option>
      <option value="Moderate" ${severity === 'Moderate' ? 'selected' : ''}>Moderate</option>
      <option value="Severe" ${severity === 'Severe' ? 'selected' : ''}>Severe</option>
    </select>
    <input type="text" placeholder="Duration (e.g. 2 weeks)" value="${escapeHtml(duration)}" class="symptom-duration flex-1 min-w-[100px] px-2.5 py-1.5 border border-slate-300 rounded focus:outline-none bg-white">
    <input type="text" placeholder="Clinical notes" value="${escapeHtml(notes)}" class="symptom-notes flex-2 min-w-[150px] px-2.5 py-1.5 border border-slate-300 rounded focus:outline-none bg-white">
    <button type="button" onclick="this.closest('.flex').remove()" class="text-slate-400 hover:text-rose-600 p-1">
      <i data-lucide="trash-2" class="w-4 h-4"></i>
    </button>
  `;
  container.appendChild(row);
  if (window.lucide) lucide.createIcons();
}

function addConditionRow(name = "", year = "", status = "Active") {
  const container = document.getElementById("conditionsContainer");
  const row = document.createElement("div");
  row.className = "flex flex-wrap items-center gap-2 bg-slate-50 p-2.5 rounded-lg border border-slate-200 text-xs";
  row.innerHTML = `
    <input type="text" placeholder="Condition Name (e.g. Hypertension)" value="${escapeHtml(name)}" class="condition-name flex-3 min-w-[200px] px-2.5 py-1.5 border border-slate-300 rounded focus:outline-none bg-white">
    <input type="text" placeholder="Diagnosed Date/Year (e.g. 2019)" value="${escapeHtml(year)}" class="condition-year flex-1 min-w-[100px] px-2.5 py-1.5 border border-slate-300 rounded focus:outline-none bg-white">
    <select class="condition-status px-2 py-1.5 border border-slate-300 rounded focus:outline-none bg-white font-medium">
      <option value="Active" ${status === 'Active' ? 'selected' : ''}>Active</option>
      <option value="In Remission" ${status === 'In Remission' ? 'selected' : ''}>In Remission</option>
      <option value="Resolved" ${status === 'Resolved' ? 'selected' : ''}>Resolved</option>
    </select>
    <button type="button" onclick="this.closest('.flex').remove()" class="text-slate-400 hover:text-rose-600 p-1">
      <i data-lucide="trash-2" class="w-4 h-4"></i>
    </button>
  `;
  container.appendChild(row);
  if (window.lucide) lucide.createIcons();
}

function addMedicationRow(name = "", dosage = "", frequency = "", purpose = "") {
  const container = document.getElementById("medicationsContainer");
  const row = document.createElement("div");
  row.className = "flex flex-wrap items-center gap-2 bg-slate-50 p-2.5 rounded-lg border border-slate-200 text-xs";
  row.innerHTML = `
    <input type="text" placeholder="Medication (e.g. Metformin)" value="${escapeHtml(name)}" class="med-name flex-2 min-w-[150px] px-2.5 py-1.5 border border-slate-300 rounded focus:outline-none bg-white">
    <input type="text" placeholder="Dosage (e.g. 500mg)" value="${escapeHtml(dosage)}" class="med-dosage flex-1 min-w-[80px] px-2.5 py-1.5 border border-slate-300 rounded focus:outline-none bg-white">
    <input type="text" placeholder="Frequency (e.g. Daily with dinner)" value="${escapeHtml(frequency)}" class="med-freq flex-2 min-w-[140px] px-2.5 py-1.5 border border-slate-300 rounded focus:outline-none bg-white">
    <input type="text" placeholder="Purpose (e.g. Blood sugar)" value="${escapeHtml(purpose)}" class="med-purpose flex-2 min-w-[120px] px-2.5 py-1.5 border border-slate-300 rounded focus:outline-none bg-white">
    <button type="button" onclick="this.closest('.flex').remove()" class="text-slate-400 hover:text-rose-600 p-1">
      <i data-lucide="trash-2" class="w-4 h-4"></i>
    </button>
  `;
  container.appendChild(row);
  if (window.lucide) lucide.createIcons();
}

function addAllergyRow(allergen = "", reaction = "", severity = "Mild") {
  const container = document.getElementById("allergiesContainer");
  const row = document.createElement("div");
  row.className = "flex flex-wrap items-center gap-2 bg-slate-50 p-2.5 rounded-lg border border-slate-200 text-xs";
  row.innerHTML = `
    <input type="text" placeholder="Allergen (e.g. Penicillin, Peanuts)" value="${escapeHtml(allergen)}" class="allergy-name flex-2 min-w-[150px] px-2.5 py-1.5 border border-slate-300 rounded focus:outline-none bg-white">
    <input type="text" placeholder="Reaction (e.g. Hives, Anaphylaxis)" value="${escapeHtml(reaction)}" class="allergy-reaction flex-2 min-w-[150px] px-2.5 py-1.5 border border-slate-300 rounded focus:outline-none bg-white">
    <select class="allergy-severity px-2 py-1.5 border border-slate-300 rounded focus:outline-none bg-white font-medium">
      <option value="Mild" ${severity === 'Mild' ? 'selected' : ''}>Mild</option>
      <option value="Moderate" ${severity === 'Moderate' ? 'selected' : ''}>Moderate</option>
      <option value="Severe" ${severity === 'Severe' ? 'selected' : ''}>Severe</option>
    </select>
    <button type="button" onclick="this.closest('.flex').remove()" class="text-slate-400 hover:text-rose-600 p-1">
      <i data-lucide="trash-2" class="w-4 h-4"></i>
    </button>
  `;
  container.appendChild(row);
  if (window.lucide) lucide.createIcons();
}

async function handlePatientFormSubmit(event) {
  event.preventDefault();

  const fullName = document.getElementById("intakeFullName").value.trim();
  const patientId = document.getElementById("intakePatientId").value.trim();
  const age = document.getElementById("intakeAge").value ? parseInt(document.getElementById("intakeAge").value) : null;
  const sex = document.getElementById("intakeSex").value;
  const dob = document.getElementById("intakeDob").value || null;
  const bloodType = document.getElementById("intakeBloodType").value || null;
  const phone = document.getElementById("intakePhone").value.trim() || null;
  const emergency = document.getElementById("intakeEmergency").value.trim() || null;

  // Collect dynamic symptoms
  const symptoms = [];
  document.querySelectorAll("#symptomsContainer > div").forEach(row => {
    const name = row.querySelector(".symptom-name").value.trim();
    if (name) {
      symptoms.push({
        name,
        severity: row.querySelector(".symptom-severity").value,
        duration: row.querySelector(".symptom-duration").value.trim(),
        notes: row.querySelector(".symptom-notes").value.trim() || null
      });
    }
  });

  // Collect dynamic conditions
  const conditions = [];
  document.querySelectorAll("#conditionsContainer > div").forEach(row => {
    const name = row.querySelector(".condition-name").value.trim();
    if (name) {
      conditions.push({
        condition_name: name,
        diagnosed_year_or_date: row.querySelector(".condition-year").value.trim(),
        status: row.querySelector(".condition-status").value
      });
    }
  });

  // Collect medications
  const medications = [];
  document.querySelectorAll("#medicationsContainer > div").forEach(row => {
    const name = row.querySelector(".med-name").value.trim();
    if (name) {
      medications.push({
        name,
        dosage: row.querySelector(".med-dosage").value.trim(),
        frequency: row.querySelector(".med-freq").value.trim(),
        purpose: row.querySelector(".med-purpose").value.trim() || null
      });
    }
  });

  // Collect allergies
  const allergies = [];
  document.querySelectorAll("#allergiesContainer > div").forEach(row => {
    const allergen = row.querySelector(".allergy-name").value.trim();
    if (allergen) {
      allergies.push({
        allergen,
        reaction: row.querySelector(".allergy-reaction").value.trim(),
        severity: row.querySelector(".allergy-severity").value
      });
    }
  });

  const surgeries = document.getElementById("intakeSurgeries").value.split("\n").map(s => s.trim()).filter(Boolean);
  const lifestyle = document.getElementById("intakeLifestyle").value.trim() || null;

  const payload = {
    patient_id: patientId,
    full_name: fullName,
    age,
    sex,
    dob,
    blood_type: bloodType,
    contact_phone: phone,
    emergency_contact: emergency,
    symptoms,
    existing_conditions: conditions,
    medications,
    allergies,
    surgical_history: surgeries,
    lifestyle_notes: lifestyle
  };

  try {
    const res = await fetch("/api/records/patient", {
      method: "POST",
      headers: getHeaders({ "Content-Type": "application/json" }),
      body: JSON.stringify(payload)
    });

    if (!res.ok) throw new Error("Failed to save patient profile");
    const record = await res.json();

    showAlert(`Patient intake for "${fullName}" saved successfully!`, "success");
    await refreshRecordsList();
    currentRecordId = record.record_id;
    await loadRecord(currentRecordId);
    showTab("recordTab");
  } catch (err) {
    showAlert(`Error saving intake: ${err.message}`, "error");
  }
}

// =========================================================================
// REPORT UPLOAD & EXTRACTION LOGIC
// =========================================================================
function setReportUploadMode(mode) {
  const fileArea = document.getElementById("uploadFileArea");
  const pasteArea = document.getElementById("uploadPasteArea");
  const btnFile = document.getElementById("btnModeFile");
  const btnPaste = document.getElementById("btnModePaste");

  if (mode === "file") {
    fileArea.classList.remove("hidden");
    pasteArea.classList.add("hidden");
    btnFile.classList.add("bg-white", "text-brand-700", "shadow-xs");
    btnFile.classList.remove("text-slate-600");
    btnPaste.classList.remove("bg-white", "text-brand-700", "shadow-xs");
    btnPaste.classList.add("text-slate-600");
  } else {
    fileArea.classList.add("hidden");
    pasteArea.classList.remove("hidden");
    btnPaste.classList.add("bg-white", "text-brand-700", "shadow-xs");
    btnPaste.classList.remove("text-slate-600");
    btnFile.classList.remove("bg-white", "text-brand-700", "shadow-xs");
    btnFile.classList.add("text-slate-600");
  }
}

function setupDropZone() {
  const dropZone = document.getElementById("dropZone");
  const fileInput = document.getElementById("reportFileInput");

  if (!dropZone || !fileInput) return;

  dropZone.addEventListener("click", () => fileInput.click());

  dropZone.addEventListener("dragover", (e) => {
    e.preventDefault();
    dropZone.classList.add("border-brand-500", "bg-brand-50/50");
  });

  dropZone.addEventListener("dragleave", () => {
    dropZone.classList.remove("border-brand-500", "bg-brand-50/50");
  });

  dropZone.addEventListener("drop", (e) => {
    e.preventDefault();
    dropZone.classList.remove("border-brand-500", "bg-brand-50/50");
    if (e.dataTransfer.files.length > 0) {
      setChosenFile(e.dataTransfer.files[0]);
    }
  });
}

function handleFileSelected(event) {
  if (event.target.files.length > 0) {
    setChosenFile(event.target.files[0]);
  }
}

function setChosenFile(file) {
  selectedFile = file;
  document.getElementById("selectedFileName").textContent = file.name;
  document.getElementById("selectedFileSize").textContent = (file.size / 1024).toFixed(1) + " KB";
  document.getElementById("selectedFileInfo").classList.remove("hidden");
  document.getElementById("btnProcessFile").disabled = false;
}

function clearSelectedFile() {
  selectedFile = null;
  document.getElementById("reportFileInput").value = "";
  document.getElementById("selectedFileInfo").classList.add("hidden");
  document.getElementById("btnProcessFile").disabled = true;
}

async function submitFileUpload() {
  if (!selectedFile || !currentRecordId) {
    showAlert("Please select a valid report file and ensure a patient is active.", "error");
    return;
  }

  const indicator = document.getElementById("processingIndicator");
  indicator.classList.remove("hidden");
  document.getElementById("btnProcessFile").disabled = true;

  const formData = new FormData();
  formData.append("file", selectedFile);

  try {
    const res = await fetch(`/api/records/${currentRecordId}/upload_report`, {
      method: "POST",
      headers: getHeaders(),
      body: formData
    });

    if (!res.ok) {
      const errData = await res.json().catch(() => ({}));
      throw new Error(errData.detail || "Failed to process report");
    }

    const data = await res.json();
    showAlert(`Successfully extracted ${data.tests_extracted} lab results from ${data.filename}!`, "success");
    clearSelectedFile();
    await loadRecord(currentRecordId);
    showTab("recordTab");
  } catch (err) {
    showAlert(`Extraction failed: ${err.message}`, "error");
  } finally {
    indicator.classList.add("hidden");
    document.getElementById("btnProcessFile").disabled = false;
  }
}

async function submitPasteReport() {
  if (!currentRecordId) {
    showAlert("Please select or create a patient first.", "error");
    return;
  }

  const text = document.getElementById("pasteReportText").value.trim();
  const filename = document.getElementById("pasteFilename").value.trim() || "Pasted_Report.txt";

  if (!text) {
    showAlert("Please paste some laboratory or clinical report text.", "error");
    return;
  }

  const indicator = document.getElementById("processingIndicator");
  indicator.classList.remove("hidden");

  try {
    const res = await fetch(`/api/records/${currentRecordId}/paste_report`, {
      method: "POST",
      headers: getHeaders({ "Content-Type": "application/json" }),
      body: JSON.stringify({ text, filename })
    });

    if (!res.ok) throw new Error("Failed to process text report");
    const data = await res.json();

    showAlert(`Successfully extracted ${data.tests_extracted} tests into patient record!`, "success");
    document.getElementById("pasteReportText").value = "";
    await loadRecord(currentRecordId);
    showTab("recordTab");
  } catch (err) {
    showAlert(`Error processing report: ${err.message}`, "error");
  } finally {
    indicator.classList.add("hidden");
  }
}

function insertSampleReportText() {
  const sample = `METROPOLITAN DIAGNOSTIC LABORATORIES
Date of Service: 09/02/2026
Ordering Physician: Dr. Sarah Bennett, MD

TEST NAME                    RESULT   UNITS      REFERENCE INTERVAL   STATUS
Fasting Blood Glucose        142      mg/dL      70 - 99              HIGH
Hemoglobin A1c               7.4      %          4.0 - 5.6            HIGH
Serum Creatinine             0.9      mg/dL      0.6 - 1.2            Normal
Blood Urea Nitrogen (BUN)    16       mg/dL      7 - 20               Normal
Total Cholesterol            215      mg/dL      < 200                HIGH
Triglycerides                185      mg/dL      < 150                HIGH
HDL Cholesterol              42       mg/dL      > 40                 Normal
Random Urine Protein         18       mg/dL                           [Pending range]
`;
  document.getElementById("pasteReportText").value = sample;
  document.getElementById("pasteFilename").value = "Routine_Lab_Panel.txt";
}

// =========================================================================
// DEMO CASES & 1-CLICK TEST DRIVE
// =========================================================================
async function loadSampleCasesMetadata() {
  try {
    const res = await fetch("/api/samples");
    if (res.ok) {
      sampleCases = await res.json();
      renderDemoModalCases();
    }
  } catch (e) {
    console.error("Failed to load sample cases:", e);
  }
}

function renderDemoModalCases() {
  const container = document.getElementById("demoCasesContainer");
  if (!container) return;
  container.innerHTML = "";

  sampleCases.forEach(c => {
    const card = document.createElement("div");
    card.className = "p-4 border border-slate-200 hover:border-brand-400 rounded-xl bg-slate-50 hover:bg-brand-50/30 cursor-pointer transition flex items-start justify-between gap-3";
    card.onclick = () => loadDemoCase(c.key);

    card.innerHTML = `
      <div>
        <div class="font-bold text-sm text-slate-900 flex items-center gap-2">
          ${escapeHtml(c.title)}
          <span class="text-[10px] px-2 py-0.2 rounded bg-brand-100 text-brand-800 font-semibold">1-Click Load</span>
        </div>
        <p class="text-xs text-slate-600 mt-1">${escapeHtml(c.description)}</p>
        <div class="flex items-center gap-3 mt-2 text-[11px] text-slate-500 font-medium">
          <span>Patient: <strong>${escapeHtml(c.patient_name)}</strong></span>
          <span>Sample Report: <code>${escapeHtml(c.report_name)}</code></span>
        </div>
      </div>
      <button type="button" class="shrink-0 p-2 text-brand-600 hover:text-brand-800">
        <i data-lucide="chevron-right" class="w-5 h-5"></i>
      </button>
    `;
    container.appendChild(card);
  });

  if (window.lucide) lucide.createIcons();
}

async function loadDemoCase(caseKey) {
  closeModal("demoModal");
  showAlert(`Loading ${caseKey}...`, "info");

  try {
    const res = await fetch(`/api/samples/${caseKey}`);
    if (!res.ok) throw new Error("Could not fetch case");
    const caseData = await res.json();

    // 1. Submit patient profile
    const pRes = await fetch("/api/records/patient", {
      method: "POST",
      headers: getHeaders({ "Content-Type": "application/json" }),
      body: JSON.stringify(caseData.patient)
    });
    if (!pRes.ok) throw new Error("Failed to save patient");
    const rec = await pRes.json();

    // 2. Submit report text
    await fetch(`/api/records/${rec.record_id}/paste_report`, {
      method: "POST",
      headers: getHeaders({ "Content-Type": "application/json" }),
      body: JSON.stringify({
        text: caseData.report_text,
        filename: caseData.report_filename
      })
    });

    await refreshRecordsList();
    currentRecordId = rec.record_id;
    await loadRecord(currentRecordId);
    showTab("recordTab");
    showAlert(`Successfully loaded demo case: ${caseData.title}!`, "success");
  } catch (err) {
    showAlert(`Error loading demo case: ${err.message}`, "error");
  }
}

// Export JSON Record
function downloadJsonExport() {
  if (!currentRecord) {
    showAlert("No active patient record to export.", "error");
    return;
  }
  const dataStr = "data:text/json;charset=utf-8," + encodeURIComponent(JSON.stringify(currentRecord, null, 2));
  const downloadAnchor = document.createElement("a");
  downloadAnchor.setAttribute("href", dataStr);
  downloadAnchor.setAttribute("download", `MedicalRecord_${currentRecord.record_id}.json`);
  document.body.appendChild(downloadAnchor);
  downloadAnchor.click();
  downloadAnchor.remove();
}

// Reset Database
async function resetDatabaseToDefaults() {
  if (!confirm("Are you sure you want to reset all medical records back to default sample cases?")) {
    return;
  }
  closeModal("settingsModal");
  showAlert("Resetting database...", "info");

  try {
    const res = await fetch("/api/system/reset", { method: "POST" });
    if (!res.ok) throw new Error("Reset failed");
    await refreshRecordsList();
    showAlert("Database reset to defaults.", "success");
  } catch (e) {
    showAlert("Failed to reset database.", "error");
  }
}

function renderEmptyRecordState() {
  document.getElementById("recordPatientName").textContent = "No Patient Selected";
  document.getElementById("recordPatientId").textContent = "PT-00000";
  document.getElementById("recordAge").textContent = "--";
  document.getElementById("recordSex").textContent = "--";
  document.getElementById("labsTableBody").innerHTML = `
    <tr>
      <td colspan="5" class="py-8 text-center text-slate-400 text-sm">
        No patient records available. Click "+ New Intake" or "Demo Cases" to get started!
      </td>
    </tr>
  `;
}

// String escaping utilities
function escapeHtml(str) {
  if (str === null || str === undefined) return "";
  return String(str)
    .replace(/&/g, "&amp;")
    .replace(/</g, "&lt;")
    .replace(/>/g, "&gt;")
    .replace(/"/g, "&quot;")
    .replace(/'/g, "&#039;");
}

function escapeJs(str) {
  if (!str) return "";
  return String(str).replace(/'/g, "\\'").replace(/"/g, '\\"').replace(/\n/g, "\\n");
}
