/**
 * MedLens — AI-Powered Clinical Information Intelligence & Healthcare Portal Frontend.
 * Coordinates:
 * - Patient Medical Records, Strict Reference-Range Awareness & Provenance
 * - Human Lab Verification & Historical Multi-Report Comparison
 * - Clinical Inconsistency & Drug-Allergy Conflict Alerts
 * - AI Symptom-to-Disease Agent & Multi-Turn Clinical Chat
 * - Automatic Tablet/Medication Detection & Smooth Pharmacy Redirection
 * - Online Pharmacy Catalog, Cart Management & Checkout
 * - Specialist Doctor Appointments (Online Telehealth & In-Person)
 * - Emergency Ambulance Dispatch & Real-Time Telemetry Tracking
 * - User Authentication & Role Management (Patient, Doctor, Admin)
 */

// =====================================================================
// GLOBAL STATE
// =====================================================================
let currentRecordId = "pt-10482"; // Default Eleanor Vance
let currentRecord = null;
let allRecordsList = [];
let sampleCases = [];
let selectedFile = null;

let currentUser = {
  user_id: "usr-patient-1",
  full_name: "Eleanor Vance",
  email: "patient@medlens.health",
  role: "PATIENT"
};

let pharmacyCatalog = [];
let cart = [];
let activeAmbulance = null;
let selectedSymptoms = new Set();
let chatHistory = [];
let redirectTimerId = null;
let targetRedirectMedId = null;

// =====================================================================
// INITIALIZATION ON PAGE LOAD
// =====================================================================
document.addEventListener("DOMContentLoaded", async () => {
  loadSavedSettings();
  await refreshRecordsList();
  await loadSampleCasesMetadata();
  await loadPharmacyProducts();
  await loadDoctorsList();
  await loadSymptomCategories();
  await loadQuickScenarios();
  setupDropZone();
  initDefaultIntakeRows();
});

// Settings & Headers
function loadSavedSettings() {
  const savedKey = localStorage.getItem("medlens_gemini_api_key");
  if (savedKey) {
    const el = document.getElementById("geminiApiKeyInput");
    if (el) el.value = savedKey;
  }
}

function getGeminiApiKey() {
  return localStorage.getItem("medlens_gemini_api_key") || "";
}

function saveSettings() {
  const input = document.getElementById("geminiApiKeyInput");
  if (input) {
    localStorage.setItem("medlens_gemini_api_key", input.value.trim());
    showAlert("Settings saved successfully.", "success");
    closeModal("settingsModal");
  }
}

function getHeaders(extraHeaders = {}) {
  const headers = { ...extraHeaders };
  const key = getGeminiApiKey();
  if (key) headers["x-gemini-api-key"] = key;
  return headers;
}

// Alert notifications
function showAlert(message, type = "info") {
  const banner = document.getElementById("alertBanner");
  const msgEl = document.getElementById("alertMessage");
  const box = document.getElementById("alertBox");
  if (!banner || !msgEl) return;

  msgEl.innerText = message;
  if (box) {
    box.className = "p-3.5 rounded-lg border flex items-start justify-between text-sm shadow-xs " +
      (type === "error" ? "bg-rose-50 border-rose-200 text-rose-900" :
       type === "success" ? "bg-emerald-50 border-emerald-200 text-emerald-900" :
       "bg-sky-50 border-sky-200 text-sky-900");
  }
  banner.classList.remove("hidden");
  setTimeout(() => banner.classList.add("hidden"), 5500);
}

// =====================================================================
// NAVIGATION TABS
// =====================================================================
function showTab(tabId) {
  const tabs = [
    "recordTab", "agentTab", "pharmacyTab", "bookingsTab",
    "ambulanceTab", "intakeTab", "reportTab", "summaryTab", "provenanceTab"
  ];
  tabs.forEach((t) => {
    const el = document.getElementById(t);
    if (el) el.classList.add("hidden");
  });

  const target = document.getElementById(tabId);
  if (target) target.classList.remove("hidden");

  // Highlight active nav button
  const navMap = {
    recordTab: "nav-record",
    agentTab: "nav-agent",
    pharmacyTab: "nav-pharmacy",
    bookingsTab: "nav-bookings",
    ambulanceTab: "nav-ambulance",
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

  if (window.lucide) lucide.createIcons();
}

function openModal(modalId) {
  const m = document.getElementById(modalId);
  if (m) m.classList.remove("hidden");
  if (window.lucide) lucide.createIcons();
}

function closeModal(modalId) {
  const m = document.getElementById(modalId);
  if (m) m.classList.add("hidden");
}

// =====================================================================
// USER AUTHENTICATION & ACCESS CONTROL
// =====================================================================
async function fastDemoLogin(role) {
  try {
    const res = await fetch("/api/auth/demo-login", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ account_type: role })
    });
    const data = await res.json();
    if (data.status === "success") {
      currentUser = data.user;
      updateUserUI();
      showAlert(`Logged in as ${currentUser.full_name} (${currentUser.role})`, "success");
      
      // If patient, switch record to linked patient
      if (currentUser.linked_patient_id) {
        switchPatient(currentUser.linked_patient_id);
      }
    }
  } catch (err) {
    showAlert("Failed to switch demo account: " + err.message, "error");
  }
}

async function loginAsDemo(role) {
  await fastDemoLogin(role);
  closeModal("authModal");
}

async function handleAuthSubmit(e) {
  e.preventDefault();
  const email = document.getElementById("authEmailInput").value.trim();
  const password = document.getElementById("authPasswordInput").value.trim();

  try {
    const res = await fetch("/api/auth/login", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ email, password })
    });
    const data = await res.json();
    if (res.ok && data.status === "success") {
      currentUser = data.user;
      updateUserUI();
      showAlert(`Welcome, ${currentUser.full_name}!`, "success");
      closeModal("authModal");
    } else {
      showAlert(data.detail || "Authentication failed.", "error");
    }
  } catch (err) {
    showAlert("Login error: " + err.message, "error");
  }
}

function updateUserUI() {
  const nameEl = document.getElementById("navUserName");
  const roleEl = document.getElementById("navUserRole");
  if (nameEl) nameEl.innerText = currentUser.full_name;
  if (roleEl) {
    roleEl.innerText = currentUser.role;
    roleEl.className = currentUser.role === "DOCTOR"
      ? "text-[10px] font-bold px-1.5 py-0.5 rounded bg-indigo-100 text-indigo-800 uppercase"
      : "text-[10px] font-bold px-1.5 py-0.5 rounded bg-brand-100 text-brand-800 uppercase";
  }
}

// =====================================================================
// PATIENT RECORDS & STRUCTURED DOSSIER
// =====================================================================
async function refreshRecordsList() {
  try {
    const res = await fetch("/api/records", { headers: getHeaders() });
    if (!res.ok) throw new Error("Could not fetch patient records");
    allRecordsList = await res.json();

    const select = document.getElementById("patientSelect");
    if (select) {
      select.innerHTML = "";
      allRecordsList.forEach((r) => {
        const opt = document.createElement("option");
        opt.value = r.record_id;
        opt.innerText = `${r.patient_name} (${r.record_id.toUpperCase()})`;
        select.appendChild(opt);
      });
      if (allRecordsList.length > 0) {
        currentRecordId = allRecordsList[0].record_id;
        select.value = currentRecordId;
        await loadRecordDetails(currentRecordId);
      }
    }
  } catch (err) {
    console.error(err);
  }
}

async function switchPatient(recordId) {
  currentRecordId = recordId;
  await loadRecordDetails(recordId);
}

async function loadRecordDetails(recordId) {
  try {
    const res = await fetch(`/api/records/${recordId}`, { headers: getHeaders() });
    if (!res.ok) throw new Error("Failed to load record details");
    currentRecord = await res.json();
    renderRecord(currentRecord);
  } catch (err) {
    showAlert("Error loading record: " + err.message, "error");
  }
}

function renderRecord(record) {
  if (!record || !record.patient) return;
  const p = record.patient;

  // Header Demographics
  document.getElementById("recordPatientName").innerText = p.full_name;
  document.getElementById("recordPatientId").innerText = p.patient_id;
  document.getElementById("recordAge").innerText = p.age || "--";
  document.getElementById("recordSex").innerText = p.sex || "Unspecified";
  document.getElementById("recordDob").innerText = p.dob || "--";
  document.getElementById("recordBlood").innerText = p.blood_type || "--";
  document.getElementById("recordPhone").innerText = p.contact_phone || "--";

  // Statistics
  document.getElementById("statReportsCount").innerText = record.reports ? record.reports.length : 0;
  const totalLabs = record.all_lab_results ? record.all_lab_results.length : 0;
  document.getElementById("statTotalLabs").innerText = totalLabs;
  const badge = document.getElementById("testsBadge");
  if (badge) badge.innerText = totalLabs;

  const flaggedLabs = (record.all_lab_results || []).filter(
    (l) => l.status === "HIGH" || l.status === "LOW"
  ).length;
  document.getElementById("statFlaggedLabs").innerText = flaggedLabs;

  // Render Conflict Alerts
  renderConflictAlerts(record.conflicts || []);

  // Render Symptoms List
  const symptomsEl = document.getElementById("recordSymptomsList");
  if (symptomsEl) {
    if (!p.symptoms || p.symptoms.length === 0) {
      symptomsEl.innerHTML = '<p class="text-slate-400 italic">No symptoms reported.</p>';
    } else {
      symptomsEl.innerHTML = p.symptoms.map(s => `
        <div class="p-2 rounded-lg bg-slate-50 border border-slate-100 flex items-start justify-between">
          <div>
            <strong class="font-semibold text-slate-800">${escapeHtml(s.name)}</strong>
            <span class="text-[11px] text-slate-500 block">${s.duration ? `Duration: ${escapeHtml(s.duration)}` : ''}</span>
          </div>
          <span class="px-2 py-0.5 rounded text-[10px] font-bold ${
            s.severity === 'Severe' ? 'bg-rose-100 text-rose-800' :
            s.severity === 'Moderate' ? 'bg-amber-100 text-amber-800' :
            'bg-slate-100 text-slate-700'
          }">${s.severity || 'Mild'}</span>
        </div>
      `).join('');
    }
  }

  // Render Medications
  const medsEl = document.getElementById("recordMedsList");
  if (medsEl) {
    if (!p.medications || p.medications.length === 0) {
      medsEl.innerHTML = '<p class="text-slate-400 italic">No active medications.</p>';
    } else {
      medsEl.innerHTML = p.medications.map(m => `
        <div class="p-2 rounded-lg bg-slate-50 border border-slate-100">
          <div class="flex items-center justify-between">
            <strong class="font-semibold text-slate-800">${escapeHtml(m.name)}</strong>
            <span class="text-[11px] font-mono text-slate-600">${escapeHtml(m.dosage)}</span>
          </div>
          <span class="text-[11px] text-slate-500 block">${escapeHtml(m.frequency || '')}</span>
        </div>
      `).join('');
    }
  }

  // Render Allergies
  const allergiesEl = document.getElementById("recordAllergiesList");
  if (allergiesEl) {
    const list = (p.allergies || []).map(a => `
      <div class="p-2 rounded-lg bg-rose-50/70 border border-rose-200/60 text-xs">
        <strong class="font-semibold text-rose-900">${escapeHtml(a.allergen)}</strong>
        <span class="text-[11px] text-rose-700 block">${escapeHtml(a.reaction || 'Reaction noted')}</span>
      </div>
    `);
    allergiesEl.innerHTML = list.length > 0 ? list.join('') : '<p class="text-slate-400 italic">No allergies recorded.</p>';
  }

  // Render Laboratory Tests Table
  populateCategoryDropdown(record.all_lab_results || []);
  renderLabsTable(record.all_lab_results || []);

  // Render Summary Tab Content
  if (record.summary) {
    renderSummaryTab(record.summary);
  }

  // Render Provenance
  renderProvenanceTab(record);

  if (window.lucide) lucide.createIcons();
}

function renderConflictAlerts(conflicts) {
  const container = document.getElementById("conflictsContainer");
  if (!container) return;
  if (!conflicts || conflicts.length === 0) {
    container.innerHTML = "";
    return;
  }

  container.innerHTML = conflicts.map(c => `
    <div class="p-3 rounded-xl border flex items-start gap-3 ${
      c.severity === 'HIGH' ? 'bg-rose-50 border-rose-200 text-rose-900' : 'bg-amber-50 border-amber-200 text-amber-900'
    }">
      <i data-lucide="${c.severity === 'HIGH' ? 'alert-triangle' : 'info'}" class="w-5 h-5 shrink-0 ${c.severity === 'HIGH' ? 'text-rose-600' : 'text-amber-600'} mt-0.5"></i>
      <div class="text-xs">
        <div class="flex items-center gap-2">
          <strong class="font-bold text-sm">${escapeHtml(c.title)}</strong>
          <span class="px-1.5 py-0.2 rounded text-[10px] font-bold uppercase ${c.severity === 'HIGH' ? 'bg-rose-200 text-rose-900' : 'bg-amber-200 text-amber-900'}">${c.category}</span>
        </div>
        <p class="mt-0.5">${escapeHtml(c.description)}</p>
        <p class="mt-1 font-semibold text-slate-800">Recommendation: ${escapeHtml(c.recommendation)}</p>
      </div>
    </div>
  `).join('');
}

function populateCategoryDropdown(labs) {
  const sel = document.getElementById("labCategoryFilter");
  if (!sel) return;
  const categories = Array.from(new Set(labs.map(l => l.category || "General")));
  sel.innerHTML = '<option value="ALL">All Categories</option>' +
    categories.map(c => `<option value="${escapeHtml(c)}">${escapeHtml(c)}</option>`).join('');
}

function renderLabsTable(labs) {
  const tbody = document.getElementById("labsTableBody");
  if (!tbody) return;

  if (labs.length === 0) {
    tbody.innerHTML = `<tr><td colspan="6" class="p-8 text-center text-slate-400 italic">No laboratory tests extracted yet. Upload a report to view findings.</td></tr>`;
    return;
  }

  tbody.innerHTML = labs.map(lab => {
    const statusClass = lab.status === "HIGH" ? "status-high" :
      lab.status === "LOW" ? "status-low" :
      lab.status === "NORMAL" ? "status-normal" : "status-unspecified";

    const isVerified = lab.verification && lab.verification.is_verified;

    return `
      <tr class="hover:bg-slate-50/80 transition group">
        <td class="py-3 px-4 font-semibold text-slate-900">
          <div>${escapeHtml(lab.test_name)}</div>
          <span class="text-[11px] text-slate-400 font-normal">${escapeHtml(lab.category || "General")}</span>
        </td>
        <td class="py-3 px-4 font-bold text-slate-900">
          ${escapeHtml(lab.value)} <span class="text-xs font-normal text-slate-500">${escapeHtml(lab.unit || "")}</span>
        </td>
        <td class="py-3 px-4 text-xs font-mono text-slate-600">
          ${lab.reference_range_raw ? escapeHtml(lab.reference_range_raw) : '<span class="text-slate-400 italic">Not specified in report</span>'}
        </td>
        <td class="py-3 px-4">
          <span class="inline-flex items-center px-2 py-0.5 rounded text-xs font-bold ${statusClass}">
            ${lab.status}
          </span>
        </td>
        <td class="py-3 px-4 text-xs text-slate-500">
          <div class="flex items-center gap-1 badge-report-extracted px-2 py-0.5 rounded text-[11px] w-fit">
            <i data-lucide="file-text" class="w-3 h-3 text-purple-600"></i>
            <span class="truncate max-w-[130px]">${escapeHtml(lab.provenance ? lab.provenance.source_name : 'Report')}</span>
          </div>
        </td>
        <td class="py-3 px-4 text-right">
          ${isVerified ? `
            <span class="inline-flex items-center gap-1 badge-verified px-2 py-0.5 rounded text-xs font-bold">
              <i data-lucide="check" class="w-3 h-3 text-emerald-600"></i>
              <span>Verified</span>
            </span>
          ` : `
            <button onclick="openVerifyLabModal('${lab.id}', '${escapeHtml(lab.test_name)}', '${escapeHtml(lab.value)}', '${lab.status}')" class="px-2.5 py-1 rounded bg-slate-100 hover:bg-slate-200 text-slate-700 text-xs font-semibold transition">
              Verify / Edit
            </button>
          `}
        </td>
      </tr>
    `;
  }).join('');

  if (window.lucide) lucide.createIcons();
}

function filterLabsTable() {
  if (!currentRecord || !currentRecord.all_lab_results) return;
  const q = (document.getElementById("labSearchInput").value || "").toLowerCase().trim();
  const cat = document.getElementById("labCategoryFilter").value;
  const st = document.getElementById("labStatusFilter").value;

  const filtered = currentRecord.all_lab_results.filter(lab => {
    const matchesQ = !q || lab.test_name.toLowerCase().includes(q) || lab.category.toLowerCase().includes(q);
    const matchesCat = cat === "ALL" || lab.category === cat;
    const matchesSt = st === "ALL" || lab.status === st;
    return matchesQ && matchesCat && matchesSt;
  });

  renderLabsTable(filtered);
}

// Lab Verification Modal
function openVerifyLabModal(testId, testName, val, status) {
  document.getElementById("verifyLabTestId").value = testId;
  document.getElementById("verifyLabTestName").value = testName;
  document.getElementById("verifyLabValue").value = val;
  document.getElementById("verifyLabStatus").value = status || "NORMAL";
  document.getElementById("verifyLabNotes").value = `Verified in clinical review by ${currentUser.full_name}.`;
  openModal("verifyLabModal");
}

async function handleVerifyLabSubmit(e) {
  e.preventDefault();
  const testId = document.getElementById("verifyLabTestId").value;
  const editedVal = document.getElementById("verifyLabValue").value.trim();
  const editedStatus = document.getElementById("verifyLabStatus").value;
  const notes = document.getElementById("verifyLabNotes").value.trim();

  try {
    const res = await fetch(`/api/records/${currentRecordId}/verify_lab`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        test_id: testId,
        verified: true,
        verified_by: currentUser.full_name,
        clinician_notes: notes,
        edited_value: editedVal,
        edited_status: editedStatus
      })
    });
    const data = await res.json();
    if (res.ok && data.status === "success") {
      showAlert(data.message, "success");
      closeModal("verifyLabModal");
      await loadRecordDetails(currentRecordId);
    } else {
      showAlert(data.detail || "Verification failed.", "error");
    }
  } catch (err) {
    showAlert("Error saving verification: " + err.message, "error");
  }
}

// Report Comparison Modal
async function openReportComparisonModal() {
  try {
    const res = await fetch(`/api/records/${currentRecordId}/compare`, { headers: getHeaders() });
    if (!res.ok) throw new Error("Could not load report comparison data");
    const data = await res.json();

    const tbody = document.getElementById("comparisonTableBody");
    if (tbody) {
      tbody.innerHTML = data.comparisons.map(c => `
        <tr class="hover:bg-slate-50 transition">
          <td class="py-2.5 px-3 font-semibold text-slate-900">${escapeHtml(c.test_name)}</td>
          <td class="py-2.5 px-3 font-mono text-slate-600">${c.baseline_value} ${c.unit}</td>
          <td class="py-2.5 px-3 font-bold text-slate-900">${c.current_value} ${c.unit}</td>
          <td class="py-2.5 px-3 font-mono text-slate-500">${escapeHtml(c.reference_range)}</td>
          <td class="py-2.5 px-3 font-mono font-bold ${c.trend === 'INCREASED' ? 'text-rose-600' : c.trend === 'DECREASED' ? 'text-sky-600' : 'text-slate-600'}">
            ${c.delta_pct}
          </td>
          <td class="py-2.5 px-3">
            <span class="px-2 py-0.5 rounded text-[10px] font-bold ${
              c.trend === 'INCREASED' ? 'bg-rose-100 text-rose-800' :
              c.trend === 'DECREASED' ? 'bg-sky-100 text-sky-800' :
              'bg-slate-100 text-slate-700'
            }">${c.trend}</span>
          </td>
        </tr>
      `).join('');
    }

    openModal("comparisonModal");
  } catch (err) {
    showAlert("Comparison error: " + err.message, "error");
  }
}

// =====================================================================
// AI SYMPTOM AGENT & DIAGNOSTIC CHAT
// =====================================================================
async function loadSymptomCategories() {
  try {
    const res = await fetch("/api/symptom-agent/categories");
    if (!res.ok) return;
    const categories = await res.json();

    const container = document.getElementById("symptomCategoriesAccordion");
    if (!container) return;

    container.innerHTML = Object.entries(categories).map(([catName, items]) => `
      <div class="border border-slate-200 rounded-lg p-2.5 bg-slate-50/50">
        <strong class="text-xs font-bold text-slate-800 block mb-1.5">${escapeHtml(catName)}</strong>
        <div class="flex flex-wrap gap-1">
          ${items.map(s => `
            <button onclick="toggleSymptomChip('${s.key}', this)" data-key="${s.key}" class="symptom-chip px-2 py-1 rounded-md text-xs bg-white hover:bg-slate-100 border border-slate-200 text-slate-700 transition">
              ${escapeHtml(s.label)}
            </button>
          `).join('')}
        </div>
      </div>
    `).join('');
  } catch (err) {
    console.error(err);
  }
}

async function loadQuickScenarios() {
  try {
    const res = await fetch("/api/symptom-agent/scenarios");
    if (!res.ok) return;
    const scenarios = await res.json();

    const container = document.getElementById("quickScenariosContainer");
    if (!container) return;

    container.innerHTML = scenarios.slice(0, 4).map(sc => `
      <div onclick="applyQuickScenario('${sc.id}')" class="p-2.5 rounded-lg border border-slate-200 bg-slate-50/70 hover:bg-brand-50 hover:border-brand-200 transition cursor-pointer">
        <strong class="text-xs font-bold text-slate-800 block">${escapeHtml(sc.title)}</strong>
        <p class="text-[11px] text-slate-500 line-clamp-1">${escapeHtml(sc.description)}</p>
      </div>
    `).join('');
  } catch (err) {
    console.error(err);
  }
}

function toggleSymptomChip(key, btn) {
  if (selectedSymptoms.has(key)) {
    selectedSymptoms.delete(key);
    btn.classList.remove("bg-brand-600", "text-white", "font-bold");
    btn.classList.add("bg-white", "text-slate-700");
  } else {
    selectedSymptoms.add(key);
    btn.classList.add("bg-brand-600", "text-white", "font-bold");
    btn.classList.remove("bg-white", "text-slate-700");
  }
  document.getElementById("selectedSymptomsCount").innerText = selectedSymptoms.size;
}

function clearSelectedSymptoms() {
  selectedSymptoms.clear();
  document.querySelectorAll(".symptom-chip").forEach(b => {
    b.classList.remove("bg-brand-600", "text-white", "font-bold");
    b.classList.add("bg-white", "text-slate-700");
  });
  document.getElementById("selectedSymptomsCount").innerText = "0";
}

async function evaluateSelectedSymptoms() {
  if (selectedSymptoms.size === 0) {
    showAlert("Please select at least one symptom to evaluate.", "info");
    return;
  }
  const symptomsArray = Array.from(selectedSymptoms);
  const prompt = `I am presenting with: ${symptomsArray.join(", ")}. Please evaluate possible causes and triage level.`;
  await sendChatMessage(prompt);
}

function applyQuickScenario(scenarioId) {
  fetch("/api/symptom-agent/scenarios")
    .then(r => r.json())
    .then(scenarios => {
      const sc = scenarios.find(s => s.id === scenarioId);
      if (sc) {
        clearSelectedSymptoms();
        (sc.symptoms || []).forEach(k => {
          selectedSymptoms.add(k);
          const btn = document.querySelector(`.symptom-chip[data-key="${k}"]`);
          if (btn) {
            btn.classList.add("bg-brand-600", "text-white", "font-bold");
            btn.classList.remove("bg-white", "text-slate-700");
          }
        });
        document.getElementById("selectedSymptomsCount").innerText = selectedSymptoms.size;
        sendChatMessage(sc.narrative);
      }
    });
}

function sendQuickMedicineQuery(queryText) {
  showTab("agentTab");
  sendChatMessage(queryText);
}

async function handleAgentChatSubmit(e) {
  e.preventDefault();
  const input = document.getElementById("agentChatInput");
  const msg = input.value.trim();
  if (!msg) return;
  input.value = "";
  await sendChatMessage(msg);
}

async function sendChatMessage(userText) {
  appendChatMessage("user", userText);

  // Append typing placeholder
  const typingId = "typing-" + Date.now();
  const container = document.getElementById("agentChatMessages");
  const typingDiv = document.createElement("div");
  typingDiv.id = typingId;
  typingDiv.className = "flex items-start gap-3";
  typingDiv.innerHTML = `
    <div class="w-7 h-7 rounded-full bg-brand-600 text-white flex items-center justify-center text-xs font-bold shrink-0">AI</div>
    <div class="bg-white border border-slate-200 rounded-2xl rounded-tl-xs p-3 shadow-xs text-xs text-slate-500 italic flex items-center gap-2">
      <span class="w-2 h-2 rounded-full bg-brand-500 animate-pulse"></span> Analyzing clinical symptoms & medications...
    </div>
  `;
  container.appendChild(typingDiv);
  container.scrollTop = container.scrollHeight;

  try {
    const res = await fetch("/api/symptom-agent/chat", {
      method: "POST",
      headers: getHeaders({ "Content-Type": "application/json" }),
      body: JSON.stringify({ message: userText, history: chatHistory })
    });
    const data = await res.json();
    const typingEl = document.getElementById(typingId);
    if (typingEl) typingEl.remove();

    chatHistory.push({ role: "user", content: userText });
    chatHistory.push({ role: "assistant", content: data.reply });

    appendChatMessage("assistant", data.reply, data);

    // Update Triage Indicator badge
    if (data.evaluation && data.evaluation.overall_triage_level) {
      const badge = document.getElementById("triageIndicatorBadge");
      if (badge) {
        badge.classList.remove("hidden");
        const lvl = data.evaluation.overall_triage_level;
        badge.innerText = `Triage: ${lvl}`;
        badge.className = lvl === "EMERGENCY"
          ? "px-2.5 py-1 rounded-full text-xs font-black bg-rose-100 text-rose-800 border border-rose-300 siren-active"
          : lvl === "MODERATE"
          ? "px-2.5 py-1 rounded-full text-xs font-bold bg-amber-100 text-amber-800 border border-amber-300"
          : "px-2.5 py-1 rounded-full text-xs font-bold bg-emerald-100 text-emerald-800 border border-emerald-300";
      }
    }

    // AUTOMATIC MEDICATION REDIRECTION TRIGGER
    if (data.redirect_to_pharmacy && data.target_product_id) {
      triggerAutomaticPharmacyRedirect(data.target_product_id, data.primary_product);
    }

  } catch (err) {
    const typingEl = document.getElementById(typingId);
    if (typingEl) typingEl.remove();
    appendChatMessage("assistant", "Clinical reasoning error: " + err.message);
  }
}

function appendChatMessage(sender, text, meta = null) {
  const container = document.getElementById("agentChatMessages");
  if (!container) return;

  const msgDiv = document.createElement("div");
  msgDiv.className = sender === "user" ? "flex items-start justify-end gap-3" : "flex items-start gap-3";

  if (sender === "user") {
    msgDiv.innerHTML = `
      <div class="bg-brand-600 text-white rounded-2xl rounded-tr-xs p-3.5 shadow-xs max-w-lg text-sm">
        ${escapeHtml(text)}
      </div>
      <div class="w-7 h-7 rounded-full bg-slate-800 text-white flex items-center justify-center text-xs font-bold shrink-0">You</div>
    `;
  } else {
    let extraHtml = "";
    // If medication detected, render interactive medicine buy card directly in chat
    if (meta && meta.primary_product) {
      const p = meta.primary_product;
      extraHtml = `
        <div class="mt-3 p-3.5 rounded-xl border border-emerald-300 bg-emerald-50/70 space-y-2">
          <div class="flex items-center justify-between">
            <span class="text-xs font-bold text-emerald-800 flex items-center gap-1.5">
              <i data-lucide="pill" class="w-4 h-4 text-emerald-600"></i>
              <span>Available in MedLens Pharmacy</span>
            </span>
            <span class="text-xs font-black text-emerald-700">$${(p.discount_price || p.price).toFixed(2)}</span>
          </div>
          <p class="text-xs text-slate-700"><strong>${escapeHtml(p.name)}</strong> — ${escapeHtml(p.pack_size)}</p>
          <div class="flex items-center gap-2 pt-1">
            <button onclick="addToCart('${p.product_id}'); toggleCartDrawer();" class="px-3 py-1.5 text-xs font-bold bg-emerald-600 hover:bg-emerald-700 text-white rounded-lg transition flex items-center gap-1">
              <i data-lucide="shopping-cart" class="w-3.5 h-3.5"></i>
              <span>Add to Cart ($${(p.discount_price || p.price).toFixed(2)})</span>
            </button>
            <button onclick="redirectToSpecificProduct('${p.product_id}')" class="px-3 py-1.5 text-xs font-semibold bg-white border border-slate-200 hover:bg-slate-50 text-slate-800 rounded-lg transition">
              View in Pharmacy →
            </button>
          </div>
        </div>
      `;
    }

    msgDiv.innerHTML = `
      <div class="w-7 h-7 rounded-full bg-brand-600 text-white flex items-center justify-center text-xs font-bold shrink-0">AI</div>
      <div class="bg-white border border-slate-200 rounded-2xl rounded-tl-xs p-4 shadow-xs max-w-xl text-slate-800 space-y-2 text-sm leading-relaxed">
        <div class="whitespace-pre-line">${text}</div>
        ${extraHtml}
      </div>
    `;
  }

  container.appendChild(msgDiv);
  container.scrollTop = container.scrollHeight;
  if (window.lucide) lucide.createIcons();
}

// =====================================================================
// AUTOMATIC ONLINE PHARMACY REDIRECTION HANDLER
// =====================================================================
function triggerAutomaticPharmacyRedirect(productId, product) {
  targetRedirectMedId = productId;
  const banner = document.getElementById("pharmacyRedirectBanner");
  const nameEl = document.getElementById("redirectMedName");
  if (banner && nameEl) {
    nameEl.innerText = product ? product.name : "Identified Medication";
    banner.classList.remove("hidden");
  }

  // Clear any existing timer
  if (redirectTimerId) clearTimeout(redirectTimerId);

  // Auto redirect countdown: 2 seconds
  redirectTimerId = setTimeout(() => {
    executePharmacyRedirectNow();
  }, 2200);
}

function cancelPharmacyRedirect() {
  if (redirectTimerId) clearTimeout(redirectTimerId);
  const banner = document.getElementById("pharmacyRedirectBanner");
  if (banner) banner.classList.add("hidden");
  showAlert("Automatic pharmacy redirect cancelled. You can continue your symptom triage.", "info");
}

function executePharmacyRedirectNow() {
  if (redirectTimerId) clearTimeout(redirectTimerId);
  const banner = document.getElementById("pharmacyRedirectBanner");
  if (banner) banner.classList.add("hidden");

  // Smoothly switch tab to Online Pharmacy
  showTab("pharmacyTab");

  // Highlight and focus on the medication in the catalog
  if (targetRedirectMedId) {
    highlightPharmacyProduct(targetRedirectMedId);
  }
}

function redirectToSpecificProduct(productId) {
  targetRedirectMedId = productId;
  executePharmacyRedirectNow();
}

function highlightPharmacyProduct(productId) {
  setTimeout(() => {
    const card = document.getElementById(`prod-card-${productId}`);
    if (card) {
      card.scrollIntoView({ behavior: "smooth", block: "center" });
      card.classList.add("ring-4", "ring-emerald-500", "shadow-xl");
      setTimeout(() => {
        card.classList.remove("ring-4", "ring-emerald-500");
      }, 3500);
    }
  }, 300);
}

// =====================================================================
// ONLINE PHARMACY & SHOPPING CART
// =====================================================================
async function loadPharmacyProducts(category = null, search = null) {
  try {
    let url = "/api/pharmacy/products";
    const params = new URLSearchParams();
    if (category) params.append("category", category);
    if (search) params.append("search", search);
    if (params.toString()) url += `?${params.toString()}`;

    const res = await fetch(url);
    if (!res.ok) throw new Error("Could not load pharmacy products");
    pharmacyCatalog = await res.json();
    renderPharmacyProducts(pharmacyCatalog);
  } catch (err) {
    console.error(err);
  }
}

function renderPharmacyProducts(products) {
  const grid = document.getElementById("pharmacyProductsGrid");
  const countEl = document.getElementById("pharmacyResultCount");
  if (countEl) countEl.innerText = products.length;
  if (!grid) return;

  if (products.length === 0) {
    grid.innerHTML = `<div class="col-span-full p-8 text-center text-slate-400 italic">No medications found matching your criteria.</div>`;
    return;
  }

  grid.innerHTML = products.map(p => `
    <div id="prod-card-${p.product_id}" class="bg-white rounded-xl shadow-xs border border-slate-200 p-4 flex flex-col justify-between hover:shadow-md transition relative group">
      ${p.badge ? `<span class="absolute top-3 right-3 text-[10px] font-bold px-2 py-0.5 rounded-full bg-emerald-50 text-emerald-800 border border-emerald-200">${escapeHtml(p.badge)}</span>` : ''}
      
      <div>
        <div class="flex items-center gap-2 mb-2">
          <span class="w-8 h-8 rounded-lg bg-emerald-100 text-emerald-800 flex items-center justify-center font-bold text-xs">
            💊
          </span>
          <div>
            <h4 class="font-bold text-sm text-slate-900 leading-tight">${escapeHtml(p.name)}</h4>
            <span class="text-[11px] text-slate-500 font-mono">${escapeHtml(p.dosage_form)} • ${escapeHtml(p.strength)}</span>
          </div>
        </div>

        <p class="text-xs text-slate-600 line-clamp-2 mt-1 mb-2.5">${escapeHtml(p.description)}</p>

        <div class="space-y-1 text-xs text-slate-500 border-t border-slate-100 pt-2 mb-3">
          <div><strong class="text-slate-700">Category:</strong> ${escapeHtml(p.category)}</div>
          <div><strong class="text-slate-700">Pack:</strong> ${escapeHtml(p.pack_size)}</div>
          <div>
            <strong class="text-slate-700">Status:</strong>
            ${p.rx_required ? '<span class="text-amber-700 font-semibold">⚠️ Prescription Required</span>' : '<span class="text-emerald-700 font-semibold">✅ OTC Approved</span>'}
          </div>
        </div>
      </div>

      <div class="pt-3 border-t border-slate-100 flex items-center justify-between">
        <div>
          <span class="text-lg font-black text-slate-900">$${(p.discount_price || p.price).toFixed(2)}</span>
          ${p.discount_price ? `<span class="text-xs line-through text-slate-400 ml-1">$${p.price.toFixed(2)}</span>` : ''}
        </div>
        <button onclick="addToCart('${p.product_id}')" class="px-3 py-1.5 rounded-lg bg-emerald-600 hover:bg-emerald-700 text-white font-bold text-xs transition flex items-center gap-1 shadow-xs">
          <i data-lucide="plus" class="w-3.5 h-3.5"></i>
          <span>Add to Cart</span>
        </button>
      </div>
    </div>
  `).join('');

  if (window.lucide) lucide.createIcons();
}

function searchPharmacyProducts(query) {
  loadPharmacyProducts(null, query);
}

function filterPharmacyCategory(cat) {
  document.querySelectorAll(".pharm-cat-btn").forEach(btn => {
    btn.className = "pharm-cat-btn px-3 py-1.5 rounded-full font-medium bg-slate-100 text-slate-700 hover:bg-slate-200 transition";
  });
  if (event && event.target) {
    event.target.className = "pharm-cat-btn px-3 py-1.5 rounded-full font-semibold bg-emerald-600 text-white transition";
  }
  loadPharmacyProducts(cat === "all" ? null : cat);
}

// Cart Drawer Operations
function toggleCartDrawer() {
  const drawer = document.getElementById("cartDrawer");
  if (!drawer) return;
  drawer.classList.toggle("cart-drawer-open");
  renderCart();
  if (window.lucide) lucide.createIcons();
}

function addToCart(productId) {
  const prod = pharmacyCatalog.find(p => p.product_id === productId);
  if (!prod) return;

  const existing = cart.find(i => i.product_id === productId);
  if (existing) {
    existing.quantity += 1;
  } else {
    cart.push({
      product_id: prod.product_id,
      product_name: prod.name,
      strength: prod.strength,
      price: prod.discount_price || prod.price,
      quantity: 1
    });
  }

  updateCartBadges();
  renderCart();
  showAlert(`Added ${prod.name} to cart.`, "success");
}

function updateCartBadges() {
  const totalCount = cart.reduce((sum, item) => sum + item.quantity, 0);
  const badge1 = document.getElementById("cartCountBadge");
  const badge2 = document.getElementById("pharmacyCartBtnBadge");
  if (badge1) badge1.innerText = totalCount;
  if (badge2) badge2.innerText = totalCount;
}

function renderCart() {
  const list = document.getElementById("cartItemsList");
  const btnCheckout = document.getElementById("btnProceedCheckout");
  if (!list) return;

  if (cart.length === 0) {
    list.innerHTML = `<p class="text-slate-400 text-center italic py-8">Your pharmacy cart is empty.</p>`;
    if (btnCheckout) btnCheckout.disabled = true;
    document.getElementById("cartSubtotalText").innerText = "$0.00";
    document.getElementById("cartDeliveryFeeText").innerText = "$0.00";
    document.getElementById("cartTotalText").innerText = "$0.00";
    return;
  }

  let subtotal = 0;
  list.innerHTML = cart.map(item => {
    const itemTotal = item.price * item.quantity;
    subtotal += itemTotal;
    return `
      <div class="p-3 rounded-xl bg-slate-50 border border-slate-200 flex items-center justify-between">
        <div>
          <strong class="font-bold text-xs text-slate-900 block">${escapeHtml(item.product_name)}</strong>
          <span class="text-[11px] text-slate-500 font-mono">$${item.price.toFixed(2)} each</span>
        </div>
        <div class="flex items-center gap-2">
          <button onclick="changeCartQty('${item.product_id}', -1)" class="w-6 h-6 rounded bg-white border border-slate-300 text-slate-700 text-xs font-bold hover:bg-slate-100">-</button>
          <span class="text-xs font-bold text-slate-800 w-4 text-center">${item.quantity}</span>
          <button onclick="changeCartQty('${item.product_id}', 1)" class="w-6 h-6 rounded bg-white border border-slate-300 text-slate-700 text-xs font-bold hover:bg-slate-100">+</button>
          <button onclick="removeCartItem('${item.product_id}')" class="text-rose-500 hover:text-rose-700 ml-1">
            <i data-lucide="trash-2" class="w-3.5 h-3.5"></i>
          </button>
        </div>
      </div>
    `;
  }).join('');

  const delivery = subtotal >= 25.0 ? 0.0 : 3.50;
  const total = subtotal + delivery;

  document.getElementById("cartSubtotalText").innerText = `$${subtotal.toFixed(2)}`;
  document.getElementById("cartDeliveryFeeText").innerText = delivery === 0.0 ? "FREE (Orders over $25)" : `$${delivery.toFixed(2)}`;
  document.getElementById("cartTotalText").innerText = `$${total.toFixed(2)}`;
  if (btnCheckout) btnCheckout.disabled = false;
  if (window.lucide) lucide.createIcons();
}

function changeCartQty(productId, delta) {
  const item = cart.find(i => i.product_id === productId);
  if (!item) return;
  item.quantity += delta;
  if (item.quantity <= 0) {
    cart = cart.filter(i => i.product_id !== productId);
  }
  updateCartBadges();
  renderCart();
}

function removeCartItem(productId) {
  cart = cart.filter(i => i.product_id !== productId);
  updateCartBadges();
  renderCart();
}

function openCheckoutModal() {
  if (cart.length === 0) return;
  openModal("checkoutModal");
}

async function handleCheckoutOrderSubmit(e) {
  e.preventDefault();
  const name = document.getElementById("orderCustomerName").value.trim();
  const addr = document.getElementById("orderDeliveryAddress").value.trim();
  const rxConfirmed = document.getElementById("orderRxCheckbox").checked;

  try {
    const res = await fetch("/api/pharmacy/order", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        patient_id: currentRecordId,
        customer_name: name,
        customer_email: currentUser.email,
        customer_phone: currentRecord ? currentRecord.patient.contact_phone : "+1 555-234-8901",
        delivery_address: addr,
        items: cart,
        prescription_uploaded: rxConfirmed
      })
    });
    const data = await res.json();
    if (res.ok && data.status === "success") {
      showAlert(`🎉 Pharmacy Order Confirmed! Tracking #${data.order.tracking_number}`, "success");
      cart = [];
      updateCartBadges();
      closeModal("checkoutModal");
      toggleCartDrawer();
    } else {
      showAlert(data.detail || "Checkout error", "error");
    }
  } catch (err) {
    showAlert("Order error: " + err.message, "error");
  }
}

// =====================================================================
// HEALTHCARE APPOINTMENTS BOOKING SYSTEM
// =====================================================================
async function loadDoctorsList() {
  try {
    const res = await fetch("/api/bookings/doctors");
    if (!res.ok) return;
    const doctors = await res.json();
    renderDoctorsList(doctors);
  } catch (err) {
    console.error(err);
  }
}

function renderDoctorsList(doctors) {
  const grid = document.getElementById("doctorsListGrid");
  if (!grid) return;

  grid.innerHTML = doctors.map(d => `
    <div class="bg-white rounded-xl shadow-xs border border-slate-200 p-5 flex flex-col justify-between hover:shadow-md transition">
      <div>
        <div class="flex items-start justify-between mb-3">
          <div class="flex items-center gap-3">
            <div class="w-11 h-11 rounded-full bg-${d.avatar_color}-100 text-${d.avatar_color}-700 flex items-center justify-center font-bold text-sm">
              ${d.name.split(' ').slice(1,3).map(n => n[0]).join('')}
            </div>
            <div>
              <h4 class="font-bold text-sm text-slate-900">${escapeHtml(d.name)}</h4>
              <span class="text-xs font-semibold text-brand-600 block">${escapeHtml(d.specialty)}</span>
            </div>
          </div>
          <span class="text-xs font-bold text-amber-600 flex items-center gap-0.5">
            ★ ${d.rating}
          </span>
        </div>

        <p class="text-xs text-slate-500 mb-2">${escapeHtml(d.qualification)} • ${d.experience_years} yrs experience</p>
        <p class="text-xs text-slate-600 mb-3 flex items-center gap-1">
          <i data-lucide="building-2" class="w-3.5 h-3.5 text-slate-400 shrink-0"></i>
          <span>${escapeHtml(d.hospital_affiliation)}</span>
        </p>

        <div class="mb-3">
          <span class="text-[11px] font-bold text-slate-700 block mb-1">Available Slots Today:</span>
          <div class="flex flex-wrap gap-1">
            ${(d.available_slots || []).map(s => `
              <span class="px-2 py-0.5 rounded text-[10px] bg-slate-100 text-slate-700 font-mono">${s}</span>
            `).join('')}
          </div>
        </div>
      </div>

      <div class="pt-3 border-t border-slate-100 flex items-center justify-between">
        <span class="text-sm font-extrabold text-slate-900">$${d.consultation_fee.toFixed(2)}</span>
        <div class="flex items-center gap-2">
          <button onclick="bookConsultation('${d.doctor_id}', 'online', '${(d.available_slots||['10:00 AM'])[0]}')" class="px-3 py-1.5 rounded-lg bg-indigo-600 hover:bg-indigo-700 text-white font-bold text-xs transition">
            Online Video
          </button>
          <button onclick="bookConsultation('${d.doctor_id}', 'in_person', '${(d.available_slots||['11:00 AM'])[0]}')" class="px-3 py-1.5 rounded-lg bg-slate-100 hover:bg-slate-200 text-slate-800 font-bold text-xs transition border border-slate-200">
            In-Person
          </button>
        </div>
      </div>
    </div>
  `).join('');

  if (window.lucide) lucide.createIcons();
}

async function bookConsultation(doctorId, bookingType, slot) {
  try {
    const res = await fetch("/api/bookings/consultations", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        patient_id: currentRecordId,
        patient_name: currentRecord ? currentRecord.patient.full_name : currentUser.full_name,
        patient_phone: currentRecord ? currentRecord.patient.contact_phone : "+1 555-234-8901",
        doctor_id: doctorId,
        booking_type: bookingType,
        appointment_date: "2026-09-12",
        time_slot: slot,
        notes: "Routine medical review."
      })
    });
    const data = await res.json();
    if (res.ok && data.status === "success") {
      showAlert(data.message, "success");
      if (bookingType === "online" && data.booking.meeting_link) {
        launchTelehealthRoom(data.booking.meeting_link);
      }
      switchBookingSubtab("my_bookings");
    } else {
      showAlert(data.detail || "Booking failed", "error");
    }
  } catch (err) {
    showAlert("Booking error: " + err.message, "error");
  }
}

function switchBookingSubtab(subtab) {
  const docSec = document.getElementById("bookingDoctorsSection");
  const mySec = document.getElementById("myBookingsSection");
  const btnOnline = document.getElementById("btnSubtabOnline");
  const btnInPerson = document.getElementById("btnSubtabInPerson");
  const btnMy = document.getElementById("btnSubtabMyBookings");

  if (subtab === "my_bookings") {
    docSec.classList.add("hidden");
    mySec.classList.remove("hidden");
    btnMy.className = "px-3.5 py-2 rounded-lg text-xs font-bold bg-white text-indigo-950 shadow-sm transition";
    btnOnline.className = "px-3.5 py-2 rounded-lg text-xs font-bold bg-indigo-800/80 text-white hover:bg-indigo-700 transition";
    btnInPerson.className = "px-3.5 py-2 rounded-lg text-xs font-bold bg-indigo-800/80 text-white hover:bg-indigo-700 transition";
    refreshBookingsList();
  } else {
    docSec.classList.remove("hidden");
    mySec.classList.add("hidden");
    if (subtab === "online") {
      btnOnline.className = "px-3.5 py-2 rounded-lg text-xs font-bold bg-white text-indigo-950 shadow-sm transition";
      btnInPerson.className = "px-3.5 py-2 rounded-lg text-xs font-bold bg-indigo-800/80 text-white hover:bg-indigo-700 transition";
      btnMy.className = "px-3.5 py-2 rounded-lg text-xs font-bold bg-indigo-800/80 text-white hover:bg-indigo-700 transition";
    } else {
      btnInPerson.className = "px-3.5 py-2 rounded-lg text-xs font-bold bg-white text-indigo-950 shadow-sm transition";
      btnOnline.className = "px-3.5 py-2 rounded-lg text-xs font-bold bg-indigo-800/80 text-white hover:bg-indigo-700 transition";
      btnMy.className = "px-3.5 py-2 rounded-lg text-xs font-bold bg-indigo-800/80 text-white hover:bg-indigo-700 transition";
    }
  }
}

async function refreshBookingsList() {
  try {
    const res = await fetch(`/api/bookings/consultations?patient_id=${currentRecordId}`);
    if (!res.ok) return;
    const bookings = await res.json();
    const list = document.getElementById("myBookingsList");
    if (!list) return;

    if (bookings.length === 0) {
      list.innerHTML = `<p class="text-slate-400 italic text-center py-6">No scheduled consultations yet.</p>`;
      return;
    }

    list.innerHTML = bookings.map(b => `
      <div class="p-4 rounded-xl border border-slate-200 bg-slate-50/50 flex flex-col sm:flex-row sm:items-center justify-between gap-3">
        <div>
          <div class="flex items-center gap-2">
            <strong class="font-bold text-sm text-slate-900">${escapeHtml(b.doctor_name)}</strong>
            <span class="px-2 py-0.5 rounded text-[10px] font-bold uppercase ${b.booking_type === 'online' ? 'bg-indigo-100 text-indigo-800' : 'bg-amber-100 text-amber-800'}">
              ${b.booking_type}
            </span>
          </div>
          <span class="text-xs text-slate-500 block mt-0.5">Specialty: ${escapeHtml(b.specialty)} • ${escapeHtml(b.appointment_date)} at ${escapeHtml(b.time_slot)}</span>
          ${b.clinic_branch ? `<span class="text-[11px] text-slate-600 block mt-0.5">Location: ${escapeHtml(b.clinic_branch)}</span>` : ''}
        </div>
        <div class="flex items-center gap-2">
          ${b.meeting_link && b.status !== 'cancelled' ? `
            <button onclick="launchTelehealthRoom('${b.meeting_link}')" class="px-3 py-1.5 rounded-lg bg-emerald-600 hover:bg-emerald-700 text-white text-xs font-bold transition flex items-center gap-1">
              <i data-lucide="video" class="w-3.5 h-3.5"></i>
              <span>Join Room</span>
            </button>
          ` : ''}
          ${b.status !== 'cancelled' ? `
            <button onclick="cancelAppointment('${b.booking_id}')" class="px-2.5 py-1.5 rounded-lg bg-slate-200 hover:bg-rose-100 hover:text-rose-700 text-slate-700 text-xs font-semibold transition">
              Cancel
            </button>
          ` : `<span class="text-xs text-slate-400 italic">Cancelled</span>`}
        </div>
      </div>
    `).join('');

    if (window.lucide) lucide.createIcons();
  } catch (err) {
    console.error(err);
  }
}

async function cancelAppointment(bookingId) {
  try {
    const res = await fetch(`/api/bookings/consultations/${bookingId}/cancel`, { method: "POST" });
    if (res.ok) {
      showAlert("Appointment cancelled.", "info");
      refreshBookingsList();
    }
  } catch (err) {
    showAlert("Error: " + err.message, "error");
  }
}

function launchTelehealthRoom(link) {
  openModal("telehealthRoomModal");
}

// =====================================================================
// EMERGENCY AMBULANCE DISPATCH & LIVE TRACKER
// =====================================================================
function useCurrentGpsLocation() {
  document.getElementById("ambPickupAddress").value = "452 Oak Ridge Lane, Suite 3B, Downtown Metro (GPS: 37.7749° N, 122.4194° W)";
  showAlert("Current GPS location pinned.", "success");
}

async function handleAmbulanceDispatchSubmit(e) {
  e.preventDefault();
  const emergencyType = document.getElementById("ambEmergencyType").value;
  const pName = document.getElementById("ambPatientName").value.trim();
  const phone = document.getElementById("ambContactPhone").value.trim();
  const address = document.getElementById("ambPickupAddress").value.trim();
  const landmark = document.getElementById("ambLandmark").value.trim();

  try {
    const res = await fetch("/api/emergency/ambulance", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        patient_id: currentRecordId,
        patient_name: pName,
        contact_phone: phone,
        emergency_type: emergencyType,
        pickup_address: address,
        landmark: landmark
      })
    });
    const data = await res.json();
    if (res.ok && data.status === "emergency_dispatched") {
      activeAmbulance = data.ambulance;
      renderAmbulanceTelemetry(activeAmbulance);
      showAlert("🚨 EMERGENCY AMBULANCE DISPATCHED! Paramedics are en route.", "success");
    } else {
      showAlert(data.detail || "Ambulance dispatch error", "error");
    }
  } catch (err) {
    showAlert("Ambulance error: " + err.message, "error");
  }
}

function renderAmbulanceTelemetry(amb) {
  if (!amb) return;
  document.getElementById("ambVehicleNum").innerText = `${amb.vehicle_number} (${amb.vehicle_type})`;
  document.getElementById("ambParamedicName").innerText = amb.paramedic_team;
  document.getElementById("ambDestHospital").innerText = amb.destination_hospital;
  document.getElementById("ambEtaCountdown").innerText = `${amb.eta_minutes} mins`;

  const badge = document.getElementById("ambTrackingStatusBadge");
  const bar = document.getElementById("ambProgressBar");
  const l1 = document.getElementById("stepLabel1");
  const l2 = document.getElementById("stepLabel2");
  const l3 = document.getElementById("stepLabel3");

  if (amb.dispatch_status === "dispatched") {
    badge.innerText = "DISPATCHED";
    badge.className = "px-2.5 py-1 rounded-full text-xs font-black bg-amber-100 text-amber-800 uppercase";
    bar.style.width = "33%";
    l1.className = "text-rose-600 font-bold";
    l2.className = "text-slate-400";
    l3.className = "text-slate-400";
  } else if (amb.dispatch_status === "en_route") {
    badge.innerText = "EN ROUTE (HIGH PRIORITY)";
    badge.className = "px-2.5 py-1 rounded-full text-xs font-black bg-rose-100 text-rose-800 uppercase siren-active";
    bar.style.width = "66%";
    l1.className = "text-rose-600 font-bold";
    l2.className = "text-rose-600 font-bold";
    l3.className = "text-slate-400";
  } else if (amb.dispatch_status === "arrived") {
    badge.innerText = "ARRIVED AT SCENE";
    badge.className = "px-2.5 py-1 rounded-full text-xs font-black bg-emerald-100 text-emerald-800 uppercase";
    bar.style.width = "100%";
    l1.className = "text-rose-600 font-bold";
    l2.className = "text-rose-600 font-bold";
    l3.className = "text-emerald-600 font-bold";
    document.getElementById("ambEtaCountdown").innerText = "ARRIVED";
  }
}

async function advanceAmbulanceStatus() {
  if (!activeAmbulance) {
    showAlert("Please dispatch an ambulance request first.", "info");
    return;
  }
  try {
    const res = await fetch(`/api/emergency/ambulance/${activeAmbulance.request_id}/advance_status`, { method: "POST" });
    const data = await res.json();
    if (res.ok && data.status === "updated") {
      activeAmbulance = data.ambulance;
      renderAmbulanceTelemetry(activeAmbulance);
      showAlert(`Ambulance status updated: ${activeAmbulance.dispatch_status}`, "success");
    }
  } catch (err) {
    showAlert("Error updating ambulance status: " + err.message, "error");
  }
}

function callParamedicsDirect() {
  showAlert("Connecting to Paramedic Unit 7 via Emergency Dispatch Radio...", "info");
}

// =====================================================================
// PATIENT INTAKE FORM HANDLING
// =====================================================================
function initDefaultIntakeRows() {
  addSymptomRow();
  addMedicationRow();
  addAllergyRow();
}

function addSymptomRow(name = "", severity = "Mild", duration = "") {
  const container = document.getElementById("intakeSymptomsContainer");
  if (!container) return;
  const div = document.createElement("div");
  div.className = "flex items-center gap-2";
  div.innerHTML = `
    <input type="text" placeholder="Symptom name (e.g. Fatigue)" value="${escapeHtml(name)}" class="symptom-name-input flex-1 px-3 py-1.5 text-xs bg-slate-50 border border-slate-200 rounded-lg">
    <select class="symptom-severity-input px-2.5 py-1.5 text-xs bg-slate-50 border border-slate-200 rounded-lg">
      <option value="Mild" ${severity === 'Mild' ? 'selected' : ''}>Mild</option>
      <option value="Moderate" ${severity === 'Moderate' ? 'selected' : ''}>Moderate</option>
      <option value="Severe" ${severity === 'Severe' ? 'selected' : ''}>Severe</option>
    </select>
    <input type="text" placeholder="Duration (e.g. 2 weeks)" value="${escapeHtml(duration)}" class="symptom-duration-input w-28 px-2.5 py-1.5 text-xs bg-slate-50 border border-slate-200 rounded-lg">
    <button type="button" onclick="this.parentElement.remove()" class="text-slate-400 hover:text-rose-500">×</button>
  `;
  container.appendChild(div);
}

function addMedicationRow(name = "", dosage = "", freq = "") {
  const container = document.getElementById("intakeMedsContainer");
  if (!container) return;
  const div = document.createElement("div");
  div.className = "flex items-center gap-2";
  div.innerHTML = `
    <input type="text" placeholder="Medication (e.g. Metformin)" value="${escapeHtml(name)}" class="med-name-input flex-1 px-3 py-1.5 text-xs bg-slate-50 border border-slate-200 rounded-lg">
    <input type="text" placeholder="Dosage (e.g. 500 mg)" value="${escapeHtml(dosage)}" class="med-dosage-input w-28 px-2.5 py-1.5 text-xs bg-slate-50 border border-slate-200 rounded-lg">
    <input type="text" placeholder="Frequency (e.g. Twice daily)" value="${escapeHtml(freq)}" class="med-freq-input w-36 px-2.5 py-1.5 text-xs bg-slate-50 border border-slate-200 rounded-lg">
    <button type="button" onclick="this.parentElement.remove()" class="text-slate-400 hover:text-rose-500">×</button>
  `;
  container.appendChild(div);
}

function addAllergyRow(allergen = "", reaction = "") {
  const container = document.getElementById("intakeAllergiesContainer");
  if (!container) return;
  const div = document.createElement("div");
  div.className = "flex items-center gap-2";
  div.innerHTML = `
    <input type="text" placeholder="Allergen (e.g. Penicillin)" value="${escapeHtml(allergen)}" class="allergy-name-input flex-1 px-3 py-1.5 text-xs bg-slate-50 border border-slate-200 rounded-lg">
    <input type="text" placeholder="Reaction (e.g. Hives, anaphylaxis)" value="${escapeHtml(reaction)}" class="allergy-reaction-input flex-1 px-3 py-1.5 text-xs bg-slate-50 border border-slate-200 rounded-lg">
    <button type="button" onclick="this.parentElement.remove()" class="text-slate-400 hover:text-rose-500">×</button>
  `;
  container.appendChild(div);
}

async function handleIntakeSubmit(e) {
  e.preventDefault();
  const patientId = document.getElementById("intakePatientId").value.trim();
  const fullName = document.getElementById("intakeFullName").value.trim();
  const ageVal = document.getElementById("intakeAge").value;
  const sex = document.getElementById("intakeSex").value;
  const bloodType = document.getElementById("intakeBloodType").value;

  const symptoms = [];
  document.querySelectorAll("#intakeSymptomsContainer > div").forEach(r => {
    const n = r.querySelector(".symptom-name-input").value.trim();
    const s = r.querySelector(".symptom-severity-input").value;
    const d = r.querySelector(".symptom-duration-input").value.trim();
    if (n) symptoms.push({ name: n, severity: s, duration: d });
  });

  const meds = [];
  document.querySelectorAll("#intakeMedsContainer > div").forEach(r => {
    const n = r.querySelector(".med-name-input").value.trim();
    const d = r.querySelector(".med-dosage-input").value.trim();
    const f = r.querySelector(".med-freq-input").value.trim();
    if (n) meds.push({ name: n, dosage: d, frequency: f });
  });

  const allergies = [];
  document.querySelectorAll("#intakeAllergiesContainer > div").forEach(r => {
    const a = r.querySelector(".allergy-name-input").value.trim();
    const re = r.querySelector(".allergy-reaction-input").value.trim();
    if (a) allergies.push({ allergen: a, reaction: re, severity: "Moderate" });
  });

  try {
    const res = await fetch("/api/records/patient", {
      method: "POST",
      headers: getHeaders({ "Content-Type": "application/json" }),
      body: JSON.stringify({
        patient_id: patientId,
        full_name: fullName,
        age: ageVal ? parseInt(ageVal) : null,
        sex: sex,
        blood_type: bloodType,
        symptoms: symptoms,
        medications: meds,
        allergies: allergies
      })
    });
    const record = await res.json();
    if (res.ok) {
      showAlert("Patient intake record saved successfully.", "success");
      await refreshRecordsList();
      switchPatient(record.record_id);
      showTab("recordTab");
    } else {
      showAlert("Intake save error: " + (record.detail || "Failed"), "error");
    }
  } catch (err) {
    showAlert("Error saving patient: " + err.message, "error");
  }
}

async function loadSampleCaseToIntake(caseKey) {
  try {
    const res = await fetch(`/api/samples/${caseKey}`);
    if (!res.ok) return;
    const data = await res.json();
    const p = data.patient;

    document.getElementById("intakePatientId").value = p.patient_id;
    document.getElementById("intakeFullName").value = p.full_name;
    document.getElementById("intakeAge").value = p.age || "";
    document.getElementById("intakeSex").value = p.sex || "Female";
    document.getElementById("intakeBloodType").value = p.blood_type || "A+";

    document.getElementById("intakeSymptomsContainer").innerHTML = "";
    (p.symptoms || []).forEach(s => addSymptomRow(s.name, s.severity, s.duration));

    document.getElementById("intakeMedsContainer").innerHTML = "";
    (p.medications || []).forEach(m => addMedicationRow(m.name, m.dosage, m.frequency));

    document.getElementById("intakeAllergiesContainer").innerHTML = "";
    (p.allergies || []).forEach(a => addAllergyRow(a.allergen, a.reaction));

    showAlert(`Pre-populated intake with ${data.title}`, "info");
  } catch (err) {
    showAlert("Failed to load sample: " + err.message, "error");
  }
}

// =====================================================================
// MEDICAL REPORT PROCESSING (PDF & TEXT)
// =====================================================================
function setupDropZone() {
  const zone = document.getElementById("pdfDropZone");
  const fileInput = document.getElementById("pdfFileInput");
  if (!zone || !fileInput) return;

  zone.addEventListener("click", () => fileInput.click());
  zone.addEventListener("dragover", (e) => {
    e.preventDefault();
    zone.classList.add("border-brand-500", "bg-brand-50/50");
  });
  zone.addEventListener("dragleave", () => {
    zone.classList.remove("border-brand-500", "bg-brand-50/50");
  });
  zone.addEventListener("drop", (e) => {
    e.preventDefault();
    zone.classList.remove("border-brand-500", "bg-brand-50/50");
    if (e.dataTransfer.files.length > 0) {
      handleSelectedFile(e.dataTransfer.files[0]);
    }
  });
}

function handleFileSelected(e) {
  if (e.target.files.length > 0) {
    handleSelectedFile(e.target.files[0]);
  }
}

function handleSelectedFile(file) {
  selectedFile = file;
  const nameEl = document.getElementById("selectedFileName");
  const btn = document.getElementById("btnProcessPdf");
  if (nameEl) {
    nameEl.innerText = `Selected: ${file.name} (${(file.size / 1024).toFixed(1)} KB)`;
    nameEl.classList.remove("hidden");
  }
  if (btn) btn.disabled = false;
}

async function uploadSelectedPdf() {
  if (!selectedFile) return;
  const formData = new FormData();
  formData.append("file", selectedFile);

  showAlert("Extracting laboratory tests and strictly parsing reference ranges...", "info");
  try {
    const res = await fetch(`/api/records/${currentRecordId}/upload_report`, {
      method: "POST",
      headers: getHeaders(),
      body: formData
    });
    const data = await res.json();
    if (res.ok && data.status === "success") {
      showAlert(`Report processed! Extracted ${data.tests_extracted} test findings.`, "success");
      await loadRecordDetails(currentRecordId);
      showTab("recordTab");
    } else {
      showAlert(data.detail || "Upload error", "error");
    }
  } catch (err) {
    showAlert("Upload error: " + err.message, "error");
  }
}

async function handlePasteReportSubmit() {
  const text = document.getElementById("pasteReportInput").value.trim();
  if (!text) {
    showAlert("Please paste report text to process.", "info");
    return;
  }

  try {
    const res = await fetch(`/api/records/${currentRecordId}/paste_report`, {
      method: "POST",
      headers: getHeaders({ "Content-Type": "application/json" }),
      body: JSON.stringify({ text: text, filename: "Clinical_Report_Pasted.txt" })
    });
    const data = await res.json();
    if (res.ok && data.status === "success") {
      showAlert(`Extracted ${data.tests_extracted} tests from pasted text.`, "success");
      document.getElementById("pasteReportInput").value = "";
      await loadRecordDetails(currentRecordId);
      showTab("recordTab");
    } else {
      showAlert(data.detail || "Parse error", "error");
    }
  } catch (err) {
    showAlert("Error: " + err.message, "error");
  }
}

// =====================================================================
// AI SUMMARY & PROVENANCE RENDERING
// =====================================================================
function renderSummaryTab(summary) {
  document.getElementById("summaryOverview").innerText = summary.overview || "No summary available.";
  document.getElementById("summaryDisclaimer").innerText = summary.disclaimer;

  const keyFindingsEl = document.getElementById("summaryKeyFindings");
  if (keyFindingsEl) {
    keyFindingsEl.innerHTML = (summary.key_findings || []).map(kf => `
      <div class="p-2.5 rounded-lg bg-slate-50 border border-slate-100 flex items-start gap-2">
        <i data-lucide="check" class="w-4 h-4 text-emerald-600 shrink-0 mt-0.5"></i>
        <span>${escapeHtml(kf)}</span>
      </div>
    `).join('');
  }

  const questionsEl = document.getElementById("summaryQuestions");
  if (questionsEl) {
    questionsEl.innerHTML = (summary.questions_for_doctor || []).map(q => `
      <div class="p-2.5 rounded-lg bg-sky-50/70 border border-sky-100 flex items-start gap-2 text-sky-900">
        <i data-lucide="help-circle" class="w-4 h-4 text-sky-600 shrink-0 mt-0.5"></i>
        <span>${escapeHtml(q)}</span>
      </div>
    `).join('');
  }
}

async function regenerateSummary() {
  try {
    showAlert("Regenerating AI patient summary...", "info");
    const res = await fetch(`/api/records/${currentRecordId}/regenerate_summary`, {
      method: "POST",
      headers: getHeaders()
    });
    const summary = await res.json();
    if (res.ok) {
      renderSummaryTab(summary);
      showAlert("Summary regenerated successfully.", "success");
    }
  } catch (err) {
    showAlert("Summary error: " + err.message, "error");
  }
}

function renderProvenanceTab(record) {
  const container = document.getElementById("provenanceDetailedList");
  if (!container) return;

  const items = [];

  // Demographics lineage
  if (record.patient) {
    items.push(`
      <div class="p-3 rounded-xl bg-white border border-slate-200">
        <div class="flex items-center justify-between mb-1">
          <strong class="text-xs font-bold text-slate-900">Patient Demographics & Symptoms</strong>
          <span class="badge-user-provided text-[10px] font-bold px-2 py-0.5 rounded-full">User Provided</span>
        </div>
        <p class="text-xs text-slate-500">Collected via Patient Intake Form at ${record.patient.last_updated || 'Intake'}</p>
      </div>
    `);
  }

  // Reports lineage
  (record.reports || []).forEach(rep => {
    items.push(`
      <div class="p-3 rounded-xl bg-white border border-slate-200">
        <div class="flex items-center justify-between mb-1">
          <strong class="text-xs font-bold text-slate-900">Report: ${escapeHtml(rep.filename)}</strong>
          <span class="badge-report-extracted text-[10px] font-bold px-2 py-0.5 rounded-full">Report Extracted</span>
        </div>
        <p class="text-xs text-slate-500">Uploaded at ${rep.upload_time} • Method: ${rep.extraction_method}</p>
      </div>
    `);
  });

  container.innerHTML = items.join('');
}

async function loadSampleCasesMetadata() {
  try {
    const res = await fetch("/api/samples");
    if (!res.ok) return;
    sampleCases = await res.json();
  } catch (err) {
    console.error(err);
  }
}

async function resetSystemData() {
  if (!confirm("Reset database back to initial clinical demo cases?")) return;
  try {
    const res = await fetch("/api/system/reset", { method: "POST" });
    if (res.ok) {
      showAlert("System reset complete.", "success");
      closeModal("settingsModal");
      await refreshRecordsList();
    }
  } catch (err) {
    showAlert("Reset failed: " + err.message, "error");
  }
}

function escapeHtml(text) {
  if (!text) return "";
  return String(text)
    .replace(/&/g, "&amp;")
    .replace(/</g, "&lt;")
    .replace(/>/g, "&gt;")
    .replace(/"/g, "&quot;")
    .replace(/'/g, "&#039;");
}
