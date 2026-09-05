/**
 * MediCure AI - Clinical Diagnostic & Triage Agent Frontend Logic
 */

// Global State
let symptomCategories = {};
let selectedSymptoms = new Set();
let activeCategoryKey = "Head, Brain & ENT";
let currentEvaluation = null;
let chatHistory = [];
let quickScenarios = [];

document.addEventListener("DOMContentLoaded", async () => {
  loadSavedSettings();
  await loadSymptomCategories();
  await loadQuickScenarios();
});

// Settings Management
function loadSavedSettings() {
  const savedKey = localStorage.getItem("medicure_gemini_api_key");
  if (savedKey) {
    const el = document.getElementById("geminiKeyInput");
    if (el) el.value = savedKey;
  }
}

function getGeminiKey() {
  return localStorage.getItem("medicure_gemini_api_key") || "";
}

function saveAgentSettings() {
  const el = document.getElementById("geminiKeyInput");
  if (el) {
    localStorage.setItem("medicure_gemini_api_key", el.value.trim());
    closeModal("settingsModal");
    alert("Settings saved successfully!");
  }
}

function getHeaders(extra = {}) {
  const headers = { ...extra };
  const key = getGeminiKey();
  if (key) headers["x-gemini-api-key"] = key;
  return headers;
}

// Modal management
function openModal(id) {
  const el = document.getElementById(id);
  if (el) el.classList.remove("hidden");
  if (window.lucide) lucide.createIcons();
}

function closeModal(id) {
  const el = document.getElementById(id);
  if (el) el.classList.add("hidden");
}

// Switch between Analyzer and Chat view
function switchMainView(view) {
  const analyzerEl = document.getElementById("viewAnalyzer");
  const chatEl = document.getElementById("viewChat");
  const btnAnalyzer = document.getElementById("btnTabAnalyzer");
  const btnChat = document.getElementById("btnTabChat");

  if (view === "analyzer") {
    analyzerEl.classList.remove("hidden");
    chatEl.classList.add("hidden");
    btnAnalyzer.className = "px-3 py-1.5 rounded-md bg-teal-600 text-white shadow-xs transition flex items-center gap-1.5";
    btnChat.className = "px-3 py-1.5 rounded-md text-slate-400 hover:text-slate-200 transition flex items-center gap-1.5";
  } else {
    analyzerEl.classList.add("hidden");
    chatEl.classList.remove("hidden");
    btnChat.className = "px-3 py-1.5 rounded-md bg-teal-600 text-white shadow-xs transition flex items-center gap-1.5";
    btnAnalyzer.className = "px-3 py-1.5 rounded-md text-slate-400 hover:text-slate-200 transition flex items-center gap-1.5";
    // Scroll chat to bottom
    const chatContainer = document.getElementById("chatMessages");
    if (chatContainer) chatContainer.scrollTop = chatContainer.scrollHeight;
  }
  if (window.lucide) lucide.createIcons();
}

// Load Symptom Categories & Render Pills
async function loadSymptomCategories() {
  try {
    const res = await fetch("/api/symptoms/list");
    if (!res.ok) throw new Error("Could not fetch symptoms");
    symptomCategories = await res.json();
    renderCategoryTabs();
    renderCategorySymptoms(Object.keys(symptomCategories)[0]);
  } catch (err) {
    console.error("Failed to load symptoms list:", err);
  }
}

function renderCategoryTabs() {
  const container = document.getElementById("categoryTabsContainer");
  if (!container) return;
  container.innerHTML = "";

  Object.keys(symptomCategories).forEach((catName, idx) => {
    const btn = document.createElement("button");
    btn.type = "button";
    btn.className = `px-2.5 py-1 text-[11px] font-bold rounded-lg transition ${
      catName === activeCategoryKey
        ? "bg-sky-500/20 text-sky-300 border border-sky-500/40"
        : "text-slate-400 hover:text-slate-200 hover:bg-slate-800/60"
    }`;
    btn.textContent = catName;
    btn.onclick = () => {
      activeCategoryKey = catName;
      renderCategoryTabs();
      renderCategorySymptoms(catName);
    };
    container.appendChild(btn);
  });
}

function renderCategorySymptoms(catName) {
  const container = document.getElementById("symptomsPillsContainer");
  if (!container || !symptomCategories[catName]) return;
  container.innerHTML = "";

  symptomCategories[catName].forEach((sym) => {
    const isSelected = selectedSymptoms.has(sym.key);
    const pill = document.createElement("button");
    pill.type = "button";
    pill.className = `symptom-tag px-3 py-1.5 rounded-xl text-xs font-semibold border flex items-center gap-1.5 ${
      isSelected
        ? "selected"
        : "bg-slate-900/80 text-slate-300 border-slate-700/80 hover:border-slate-500 hover:bg-slate-800"
    }`;
    pill.innerHTML = `
      <i data-lucide="${sym.icon || 'circle'}" class="w-3.5 h-3.5 ${isSelected ? 'text-white' : 'text-teal-400'}"></i>
      <span>${sym.label}</span>
    `;
    pill.onclick = () => toggleSymptom(sym.key, pill);
    container.appendChild(pill);
  });

  if (window.lucide) lucide.createIcons();
}

function toggleSymptom(symKey) {
  if (selectedSymptoms.has(symKey)) {
    selectedSymptoms.delete(symKey);
  } else {
    selectedSymptoms.add(symKey);
  }
  updateSelectedCount();
  renderCategorySymptoms(activeCategoryKey);
}

function deselectAllSymptoms() {
  selectedSymptoms.clear();
  updateSelectedCount();
  renderCategorySymptoms(activeCategoryKey);
}

function updateSelectedCount() {
  const countEl = document.getElementById("activeSymptomsCount");
  if (countEl) countEl.textContent = selectedSymptoms.size;
}

function clearNarrative() {
  document.getElementById("narrativeInput").value = "";
}

// =========================================================================
// DIAGNOSTIC ANALYSIS EXECUTION
// =========================================================================
async function performDiagnosticAnalysis() {
  const narrative = document.getElementById("narrativeInput").value.trim();
  const symptomsArray = Array.from(selectedSymptoms);
  const age = document.getElementById("patientAgeInput").value ? parseInt(document.getElementById("patientAgeInput").value) : null;
  const sex = document.getElementById("patientSexInput").value;

  if (symptomsArray.length === 0 && !narrative) {
    alert("Please select at least one symptom or type your symptoms into the narrative box.");
    return;
  }

  const btn = document.getElementById("btnAnalyze");
  btn.disabled = true;
  btn.innerHTML = `<i data-lucide="loader-2" class="w-4 h-4 animate-spin"></i> Analyzing Clinical Patterns...`;
  if (window.lucide) lucide.createIcons();

  try {
    const res = await fetch("/api/diagnose", {
      method: "POST",
      headers: getHeaders({ "Content-Type": "application/json" }),
      body: JSON.stringify({
        symptoms: symptomsArray,
        narrative: narrative,
        age: age,
        sex: sex
      })
    });

    if (!res.ok) throw new Error("Diagnostic assessment failed");
    currentEvaluation = await res.json();
    renderDiagnosticResults(currentEvaluation);
  } catch (err) {
    alert(`Error: ${err.message}`);
  } finally {
    btn.disabled = false;
    btn.innerHTML = `<i data-lucide="zap" class="w-4 h-4"></i><span>Analyze Symptoms & Rectify Disease</span>`;
    if (window.lucide) lucide.createIcons();
  }
}

function renderDiagnosticResults(evalData) {
  // 1. Triage Banner & Badges
  const triageBanner = document.getElementById("triageBanner");
  const indicator = document.getElementById("triageIndicatorBadge");
  const subtitle = document.getElementById("triageSubtitle");
  const emergencyBar = document.getElementById("emergencyBar");
  const emergencyBarText = document.getElementById("emergencyBarText");

  const level = evalData.overall_triage_level || "MILD";

  if (level === "EMERGENCY") {
    triageBanner.className = "glass-panel rounded-2xl p-5 border-l-4 border-rose-500 bg-rose-950/30 flex flex-col sm:flex-row sm:items-center justify-between gap-4";
    indicator.className = "px-3 py-1 rounded-full text-xs font-black uppercase bg-rose-900 text-rose-100 border border-rose-600 shadow-md shadow-rose-900/40 animate-pulse";
    indicator.textContent = "🚨 EMERGENCY / HIGH ALERT";
    subtitle.textContent = "Urgent clinical attention or immediate emergency room assessment advised.";
    
    // Global Emergency Bar
    emergencyBar.classList.remove("hidden");
    if (evalData.emergency_alerts && evalData.emergency_alerts.length > 0) {
      emergencyBarText.textContent = evalData.emergency_alerts[0];
    }
  } else if (level === "MODERATE") {
    triageBanner.className = "glass-panel rounded-2xl p-5 border-l-4 border-amber-500 bg-amber-950/20 flex flex-col sm:flex-row sm:items-center justify-between gap-4";
    indicator.className = "px-3 py-1 rounded-full text-xs font-black uppercase bg-amber-900/80 text-amber-200 border border-amber-600";
    indicator.textContent = "⚠️ MODERATE / CLINICAL VISIT";
    subtitle.textContent = "Schedule an evaluation with a physician within 24 to 48 hours.";
    emergencyBar.classList.add("hidden");
  } else {
    triageBanner.className = "glass-panel rounded-2xl p-5 border-l-4 border-emerald-500 bg-emerald-950/20 flex flex-col sm:flex-row sm:items-center justify-between gap-4";
    indicator.className = "px-3 py-1 rounded-full text-xs font-black uppercase bg-emerald-900/80 text-emerald-200 border border-emerald-600";
    indicator.textContent = "🟢 ROUTINE / HOME CARE";
    subtitle.textContent = "Symptoms appear mild. Practice supportive home care and hydration.";
    emergencyBar.classList.add("hidden");
  }

  // 2. Detected Symptoms Tags
  const detectedRow = document.getElementById("detectedSymptomsRow");
  detectedRow.innerHTML = "";
  (evalData.user_symptoms_detected || []).forEach(s => {
    const span = document.createElement("span");
    span.className = "px-2 py-0.5 rounded-md text-[11px] font-semibold bg-slate-800 text-teal-300 border border-slate-700";
    span.textContent = s;
    detectedRow.appendChild(span);
  });

  // 3. Emergency Red Flag Alerts
  const redFlagContainer = document.getElementById("redFlagAlertContainer");
  redFlagContainer.innerHTML = "";
  if (evalData.emergency_alerts && evalData.emergency_alerts.length > 0) {
    redFlagContainer.classList.remove("hidden");
    evalData.emergency_alerts.forEach(alertText => {
      const card = document.createElement("div");
      card.className = "p-4 rounded-xl bg-rose-950/70 border border-rose-800/80 text-rose-200 text-xs flex items-start gap-3 shadow-lg shadow-rose-950/50";
      card.innerHTML = `
        <i data-lucide="alert-octagon" class="w-5 h-5 text-rose-400 shrink-0 mt-0.5"></i>
        <div class="leading-relaxed font-medium">${escapeHtml(alertText)}</div>
      `;
      redFlagContainer.appendChild(card);
    });
  } else {
    redFlagContainer.classList.add("hidden");
  }

  // 4. Disease Matches List
  const resultsList = document.getElementById("diagnosticResultsList");
  resultsList.innerHTML = "";

  if (!evalData.top_matches || evalData.top_matches.length === 0) {
    resultsList.innerHTML = `
      <div class="text-center py-8 text-slate-400 text-xs">
        No conditions strongly match the entered symptoms. Try specifying more symptoms or expanding your narrative.
      </div>
    `;
    return;
  }

  evalData.top_matches.forEach((m, idx) => {
    const card = document.createElement("div");
    card.className = "glass-card rounded-2xl p-5 space-y-3 transition hover:border-teal-500/50";

    // Urgency pill
    let triageBadge = `<span class="px-2 py-0.5 text-[10px] font-bold rounded bg-slate-800 text-slate-300">Routine</span>`;
    if (m.triage_level === "EMERGENCY") {
      triageBadge = `<span class="px-2 py-0.5 text-[10px] font-bold rounded bg-rose-950 text-rose-300 border border-rose-800">Emergency</span>`;
    } else if (m.triage_level === "MODERATE") {
      triageBadge = `<span class="px-2 py-0.5 text-[10px] font-bold rounded bg-amber-950 text-amber-300 border border-amber-800">Moderate</span>`;
    }

    // Matching symptoms chips
    const matchingChips = m.matching_symptoms.map(s => 
      `<span class="px-2 py-0.5 rounded text-[10px] font-semibold bg-teal-950/80 text-teal-300 border border-teal-800/70">✓ ${escapeHtml(s)}</span>`
    ).join(" ");

    // Missing symptoms chips
    const missingChips = m.missing_symptoms.slice(0, 3).map(s => 
      `<span class="px-2 py-0.5 rounded text-[10px] text-slate-400 bg-slate-900 border border-slate-800">○ ${escapeHtml(s)}</span>`
    ).join(" ");

    // Home care list
    const homeCareList = m.home_care.map(h => `<li class="flex items-start gap-2 text-[11px] text-slate-300"><i data-lucide="check" class="w-3.5 h-3.5 text-teal-400 shrink-0 mt-0.5"></i><span>${escapeHtml(h)}</span></li>`).join("");

    card.innerHTML = `
      <div class="flex flex-col sm:flex-row sm:items-center justify-between gap-2">
        <div class="flex items-center gap-2.5">
          <span class="w-6 h-6 rounded-full bg-slate-800 text-teal-400 text-xs font-bold flex items-center justify-center border border-slate-700">#${idx + 1}</span>
          <h3 class="text-base font-extrabold text-white">${escapeHtml(m.name)}</h3>
          ${triageBadge}
        </div>
        <div class="flex items-center gap-2">
          <span class="text-xs font-bold text-teal-400">${m.confidence}% Confidence Match</span>
        </div>
      </div>

      <!-- Confidence Bar -->
      <div class="w-full h-2 rounded-full bg-slate-800 overflow-hidden">
        <div class="h-full bg-gradient-to-r from-teal-500 via-sky-500 to-indigo-500 rounded-full transition-all duration-500" style="width: ${m.confidence}%;"></div>
      </div>

      <!-- Description & Rationale -->
      <p class="text-xs text-slate-300 leading-relaxed">${escapeHtml(m.description)}</p>
      <div class="text-[11px] text-sky-300/90 font-medium bg-sky-950/30 p-2.5 rounded-lg border border-sky-900/40">
        💡 <strong>Inference Rationale:</strong> ${escapeHtml(m.match_rationale)}
      </div>

      <!-- Symptom breakdown -->
      <div class="pt-2 border-t border-slate-800/80 flex flex-wrap items-center gap-1.5 text-xs">
        <span class="text-[11px] text-slate-500 font-semibold mr-1">Matching:</span>
        ${matchingChips}
        ${missingChips ? `<span class="text-[11px] text-slate-500 font-semibold ml-2 mr-1">Typical but absent:</span> ${missingChips}` : ""}
      </div>

      <!-- Specialist & Testing Recommendation -->
      <div class="grid grid-cols-1 sm:grid-cols-2 gap-2 pt-2 text-xs">
        <div class="bg-slate-900/90 p-2.5 rounded-xl border border-slate-800/80">
          <span class="text-[10px] font-bold text-sky-400 uppercase tracking-wider block">Recommended Specialist</span>
          <span class="font-semibold text-slate-200">${escapeHtml(m.specialist)}</span>
        </div>
        <div class="bg-slate-900/90 p-2.5 rounded-xl border border-slate-800/80">
          <span class="text-[10px] font-bold text-teal-400 uppercase tracking-wider block">Diagnostic Testing</span>
          <span class="text-slate-300 text-[11px]">${escapeHtml(m.clinical_tests.slice(0, 2).join(" • "))}</span>
        </div>
      </div>

      <!-- Expandable Home Care Guidelines -->
      <details class="group pt-2">
        <summary class="text-xs font-bold text-teal-400 cursor-pointer list-none flex items-center justify-between hover:text-teal-300">
          <span>View Home Care & Supportive Measures (${m.home_care.length})</span>
          <i data-lucide="chevron-down" class="w-4 h-4 transition group-open:rotate-180"></i>
        </summary>
        <ul class="mt-2.5 space-y-1.5 pl-1 border-t border-slate-800/60 pt-2">
          ${homeCareList}
        </ul>
      </details>
    `;
    resultsList.appendChild(card);
  });

  // 5. Next Steps Panel
  const nextStepsPanel = document.getElementById("nextStepsPanel");
  const specialistsList = document.getElementById("recommendedSpecialistsList");
  const testsList = document.getElementById("recommendedTestsList");

  nextStepsPanel.classList.remove("hidden");
  specialistsList.innerHTML = "";
  (evalData.recommended_specialists || []).forEach(spec => {
    const li = document.createElement("li");
    li.className = "flex items-center gap-1.5";
    li.innerHTML = `<i data-lucide="arrow-right" class="w-3 h-3 text-sky-400"></i><span>${escapeHtml(spec)}</span>`;
    specialistsList.appendChild(li);
  });

  testsList.innerHTML = "";
  (evalData.recommended_tests || []).forEach(test => {
    const li = document.createElement("li");
    li.className = "flex items-center gap-1.5";
    li.innerHTML = `<i data-lucide="check-circle" class="w-3 h-3 text-teal-400"></i><span>${escapeHtml(test)}</span>`;
    testsList.appendChild(li);
  });

  if (window.lucide) lucide.createIcons();
}

// =========================================================================
// AI DOCTOR CONVERSATIONAL CHAT LOGIC
// =========================================================================
async function handleChatSubmit(event) {
  event.preventDefault();
  const inputEl = document.getElementById("chatInput");
  const message = inputEl.value.trim();
  if (!message) return;

  inputEl.value = "";
  appendChatBubble("user", message);
  chatHistory.push({ role: "user", content: message });

  // Show typing indicator
  const typingIndicator = appendTypingIndicator();

  try {
    const res = await fetch("/api/chat", {
      method: "POST",
      headers: getHeaders({ "Content-Type": "application/json" }),
      body: JSON.stringify({
        message: message,
        history: chatHistory
      })
    });

    if (!res.ok) throw new Error("Chat request failed");
    const data = await res.json();

    typingIndicator.remove();
    appendChatBubble("assistant", data.reply);
    chatHistory.push({ role: "assistant", content: data.reply });

    // Update Live Mini Diagnostic Card on the right
    if (data.evaluation) {
      updateChatDiagnosticSidecard(data.evaluation);
    }
  } catch (err) {
    typingIndicator.remove();
    appendChatBubble("assistant", "I apologize, but I encountered an error evaluating your query. Please try again or switch to the Diagnostic Analyzer tab.");
  }
}

function sendQuickPrompt(promptText) {
  const inputEl = document.getElementById("chatInput");
  inputEl.value = promptText;
  document.getElementById("chatForm").dispatchEvent(new Event("submit"));
}

function appendChatBubble(sender, text) {
  const container = document.getElementById("chatMessages");
  const isUser = sender === "user";

  const bubbleWrapper = document.createElement("div");
  bubbleWrapper.className = `flex items-start gap-3 ${isUser ? "flex-row-reverse" : ""}`;

  const avatar = document.createElement("div");
  avatar.className = `w-8 h-8 rounded-full flex items-center justify-center text-white shrink-0 ${
    isUser ? "bg-sky-600" : "bg-teal-600"
  }`;
  avatar.innerHTML = `<i data-lucide="${isUser ? 'user' : 'bot'}" class="w-4 h-4"></i>`;

  const bubble = document.createElement("div");
  bubble.className = `p-3.5 text-xs max-w-xl space-y-2 leading-relaxed ${
    isUser
      ? "bg-sky-600 text-white rounded-2xl rounded-tr-none shadow-md shadow-sky-600/20"
      : "bg-slate-800/90 border border-slate-700/70 text-slate-100 rounded-2xl rounded-tl-none shadow-md"
  }`;

  // Basic formatting for bold and lists
  let formatted = escapeHtml(text)
    .replace(/\*\*(.*?)\*\*/g, "<strong>$1</strong>")
    .replace(/\n\n/g, "<br><br>")
    .replace(/\n- /g, "<br>• ");

  bubble.innerHTML = formatted;

  bubbleWrapper.appendChild(avatar);
  bubbleWrapper.appendChild(bubble);
  container.appendChild(bubbleWrapper);

  container.scrollTop = container.scrollHeight;
  if (window.lucide) lucide.createIcons();
}

function appendTypingIndicator() {
  const container = document.getElementById("chatMessages");
  const wrapper = document.createElement("div");
  wrapper.className = "flex items-start gap-3";
  wrapper.innerHTML = `
    <div class="w-8 h-8 rounded-full bg-teal-600 flex items-center justify-center text-white shrink-0">
      <i data-lucide="bot" class="w-4 h-4"></i>
    </div>
    <div class="bg-slate-800/80 border border-slate-700/60 rounded-2xl rounded-tl-none p-3 text-xs text-slate-400 flex items-center gap-1.5">
      <span class="w-1.5 h-1.5 bg-teal-400 rounded-full animate-bounce"></span>
      <span class="w-1.5 h-1.5 bg-teal-400 rounded-full animate-bounce [animation-delay:0.2s]"></span>
      <span class="w-1.5 h-1.5 bg-teal-400 rounded-full animate-bounce [animation-delay:0.4s]"></span>
      <span class="ml-1 text-[11px]">Dr. Clara is analyzing symptoms...</span>
    </div>
  `;
  container.appendChild(wrapper);
  container.scrollTop = container.scrollHeight;
  if (window.lucide) lucide.createIcons();
  return wrapper;
}

function updateChatDiagnosticSidecard(evalData) {
  const badge = document.getElementById("chatTriageBadge");
  const symptomsContainer = document.getElementById("chatDetectedSymptoms");
  const miniMatches = document.getElementById("chatMiniMatches");

  if (evalData.overall_triage_level === "EMERGENCY") {
    badge.className = "text-[10px] font-bold px-2 py-0.5 rounded-full bg-rose-950 text-rose-300 border border-rose-800 animate-pulse";
    badge.textContent = "EMERGENCY";
  } else if (evalData.overall_triage_level === "MODERATE") {
    badge.className = "text-[10px] font-bold px-2 py-0.5 rounded-full bg-amber-950 text-amber-300 border border-amber-800";
    badge.textContent = "MODERATE";
  } else {
    badge.className = "text-[10px] font-bold px-2 py-0.5 rounded-full bg-emerald-950 text-emerald-300 border border-emerald-800";
    badge.textContent = "ROUTINE";
  }

  symptomsContainer.innerHTML = "";
  if (evalData.user_symptoms_detected && evalData.user_symptoms_detected.length > 0) {
    evalData.user_symptoms_detected.forEach(s => {
      const chip = document.createElement("span");
      chip.className = "px-2 py-0.5 rounded bg-slate-800 text-teal-300 border border-slate-700 text-[10px]";
      chip.textContent = s;
      symptomsContainer.appendChild(chip);
    });
  } else {
    symptomsContainer.innerHTML = `<span class="text-slate-500 italic text-[11px]">None detected yet</span>`;
  }

  miniMatches.innerHTML = "";
  if (evalData.top_matches && evalData.top_matches.length > 0) {
    evalData.top_matches.slice(0, 3).forEach(m => {
      const row = document.createElement("div");
      row.className = "p-2 bg-slate-900/80 rounded-lg border border-slate-800 flex items-center justify-between";
      row.innerHTML = `
        <span class="font-bold text-slate-200">${escapeHtml(m.name)}</span>
        <span class="text-teal-400 font-extrabold text-[11px]">${m.confidence}%</span>
      `;
      miniMatches.appendChild(row);
    });
  } else {
    miniMatches.innerHTML = `<span class="text-slate-500 italic text-[11px]">No high confidence matches yet.</span>`;
  }
}

function clearChatHistory() {
  chatHistory = [];
  document.getElementById("chatMessages").innerHTML = `
    <div class="flex items-start gap-3">
      <div class="w-8 h-8 rounded-full bg-teal-600 flex items-center justify-center text-white shrink-0">
        <i data-lucide="bot" class="w-4 h-4"></i>
      </div>
      <div class="bg-slate-800/80 border border-slate-700/60 rounded-2xl rounded-tl-none p-3.5 text-xs text-slate-200 max-w-xl space-y-2">
        <p>Chat history cleared. What symptoms are you experiencing today?</p>
      </div>
    </div>
  `;
  if (window.lucide) lucide.createIcons();
}

// =========================================================================
// 1-CLICK QUICK TEST SCENARIOS
// =========================================================================
async function loadQuickScenarios() {
  try {
    const res = await fetch("/api/scenarios");
    if (!res.ok) return;
    quickScenarios = await res.json();
    renderScenariosModal();
  } catch (err) {
    console.error("Error fetching scenarios:", err);
  }
}

function renderScenariosModal() {
  const container = document.getElementById("scenariosList");
  if (!container) return;
  container.innerHTML = "";

  quickScenarios.forEach(sc => {
    const card = document.createElement("div");
    card.className = "p-3.5 bg-slate-800/70 hover:bg-slate-800 border border-slate-700/60 rounded-xl cursor-pointer transition flex items-center justify-between gap-3";
    card.onclick = () => loadScenario(sc);

    const symptomBadges = sc.symptoms.map(s => 
      `<span class="px-1.5 py-0.2 rounded text-[10px] bg-slate-700 text-slate-300">${s.replace('_', ' ')}</span>`
    ).join(" ");

    card.innerHTML = `
      <div>
        <h4 class="text-xs font-bold text-white">${escapeHtml(sc.title)}</h4>
        <p class="text-[11px] text-slate-400 mt-0.5">${escapeHtml(sc.description)}</p>
        <div class="flex flex-wrap gap-1 mt-1.5">${symptomBadges}</div>
      </div>
      <button class="px-3 py-1.5 text-xs font-bold text-teal-400 bg-teal-950/60 border border-teal-800/60 rounded-lg hover:bg-teal-900/60 shrink-0">
        Load & Analyze
      </button>
    `;
    container.appendChild(card);
  });
}

function loadScenario(sc) {
  closeModal("scenariosModal");
  switchMainView("analyzer");

  // Select the symptoms
  selectedSymptoms.clear();
  sc.symptoms.forEach(s => selectedSymptoms.add(s));
  updateSelectedCount();
  renderCategorySymptoms(activeCategoryKey);

  // Set the narrative
  document.getElementById("narrativeInput").value = sc.narrative;

  // Run analysis automatically!
  performDiagnosticAnalysis();
}

// Escaping helper
function escapeHtml(str) {
  if (!str) return "";
  return String(str)
    .replace(/&/g, "&amp;")
    .replace(/</g, "&lt;")
    .replace(/>/g, "&gt;")
    .replace(/"/g, "&quot;")
    .replace(/'/g, "&#039;");
}
