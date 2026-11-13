/**
 * CivicPulse AI Command - Frontend Logic & Client Engine
 * Course: CSE276 | Problem Statement: SIH25031
 * Author: Yuvi Kohli (Reg: 12506869, Roll: RK3P25ILB43, Group: K3P25IL)
 */

// Global Configuration
const API_BASE = window.location.origin.startsWith('http') ? window.location.origin : 'http://127.0.0.1:8000';
let activeSkin = localStorage.getItem('civicpulse_skin') || 'dark';
let activeQueueFilterHitl = false;
let isConnectedToApi = false;

// Department Palette
const DEPT_COLORS = {
  WATER: '#38BDF8',
  ROADS: '#F97316',
  ELECTRICAL: '#F59E0B',
  SANITATION: '#10B981',
  HEALTH: '#EF4444'
};

// Preset Grievance Templates
const PRESETS = {
  electric_school: {
    ward: 'Ward 04 - Civil Lines (near Govt Girls Senior Secondary School)',
    text: 'High voltage 11kV electrical wire snapped and hanging loose just 4 feet above ground level outside the school gate. Live current sparking violently, extreme fatal electrocution hazard for children!',
    upvotes: 64
  },
  water_sinkhole: {
    ward: 'Ward 35 - Indiranagar (100 Feet Road Junction)',
    text: 'Major potable drinking water pipeline burst open and clean municipal water is gushing out on the road. Massive road cave-in and sinkhole formed, two cars stuck, zero tap pressure in 400 houses.',
    upvotes: 82
  },
  dengue_outbreak: {
    ward: 'Ward 51 - Jayanagar 7th Block (behind General Hospital)',
    text: 'Severe dengue and chikungunya outbreak risk: Massive stagnant sewage water pool breeding lakhs of mosquito larvae. Over 10 hospital admissions reported in neighborhood, urgent fogging needed.',
    upvotes: 55
  },
  garbage_dhalao: {
    ward: 'Ward 27 - Sadar Bazaar (Bara Hindu Rao Chowk)',
    text: 'Enormous overflowing garbage dump (dhalao) spilling across half the carriage road for 6 days. Stray cattle and dogs scattering plastic everywhere, unbearable stench and flies entering shops.',
    upvotes: 28
  },
  oov_spam: {
    ward: 'Ward 14 - Municipal Zone',
    text: 'asdfghjk zzzzz fix it fast!!',
    upvotes: 1
  }
};

// ============================================================================
// Initialization
// ============================================================================
document.addEventListener('DOMContentLoaded', () => {
  initSkin();
  initTabs();
  initPresetButtons();
  initFormListeners();
  initQueueFilters();
  initModalListeners();
  initReceiptModal();
  
  // Real-time immediate first run
  validateInlineDataQuality();
  runInference(false);
  
  // Healthcheck & Initial Data Fetch
  checkApiHealth().then(() => {
    fetchPriorityQueue();
    fetchAuditLedger();
    fetchModelMetrics();
  });
});

// ============================================================================
// Dual-Skin Management
// ============================================================================
function initSkin() {
  const toggleBtn = document.getElementById('skinToggleBtn');
  const skinLabel = document.getElementById('skinLabel');
  
  applySkin(activeSkin);
  
  toggleBtn.addEventListener('click', () => {
    activeSkin = activeSkin === 'dark' ? 'light' : 'dark';
    applySkin(activeSkin);
    localStorage.setItem('civicpulse_skin', activeSkin);
    showToast(`Switched to ${activeSkin === 'dark' ? 'Pro Operations Dark Skin' : 'Student Academic Light Skin'}`);
  });
}

function applySkin(skin) {
  document.documentElement.setAttribute('data-skin', skin);
  document.body.className = `skin-${skin}`;
  const skinLabel = document.getElementById('skinLabel');
  if (skinLabel) {
    skinLabel.textContent = skin === 'dark' ? 'Skin: Pro Dark Ops' : 'Skin: Academic Light';
  }
}

// ============================================================================
// Tab Navigation
// ============================================================================
function initTabs() {
  const tabButtons = document.querySelectorAll('.nav-tab');
  const tabPanels = document.querySelectorAll('.tab-content');
  
  tabButtons.forEach(btn => {
    btn.addEventListener('click', () => {
      tabButtons.forEach(b => b.classList.remove('active'));
      tabPanels.forEach(p => p.classList.remove('active'));
      
      btn.classList.add('active');
      const targetId = btn.getAttribute('data-tab');
      const panel = document.getElementById(targetId);
      if (panel) panel.classList.add('active');
      
      if (targetId === 'queueTab') fetchPriorityQueue();
      if (targetId === 'auditTab') fetchAuditLedger();
      if (targetId === 'telemetryTab') fetchModelMetrics();
    });
  });
}

// ============================================================================
// Preset Templates
// ============================================================================
function initPresetButtons() {
  const buttons = document.querySelectorAll('.template-btn');
  const wardInput = document.getElementById('wardInput');
  const textInput = document.getElementById('complaintTextInput');
  const upvotesInput = document.getElementById('upvotesInput');
  
  buttons.forEach(btn => {
    btn.addEventListener('click', () => {
      const presetKey = btn.getAttribute('data-preset');
      const data = PRESETS[presetKey];
      if (data) {
        wardInput.value = data.ward;
        textInput.value = data.text;
        upvotesInput.value = data.upvotes;
        validateInlineDataQuality();
        runInference(false); // Live analyze without dispatch
      }
    });
  });
}

// ============================================================================
// Form Listeners & Real-Time Data Quality Gate
// ============================================================================
function initFormListeners() {
  const textInput = document.getElementById('complaintTextInput');
  const form = document.getElementById('grievanceForm');
  const analyzeBtn = document.getElementById('analyzeBtn');
  
  // Real-time debounced typing analysis
  let debounceTimer = null;
  textInput.addEventListener('input', () => {
    validateInlineDataQuality();
    clearTimeout(debounceTimer);
    debounceTimer = setTimeout(() => {
      if (textInput.value.trim().length >= 12) {
        runInference(false);
      }
    }, 250);
  });
  
  analyzeBtn.addEventListener('click', () => runInference(false));
  
  form.addEventListener('submit', (e) => {
    e.preventDefault();
    runInference(true); // Save & dispatch to SQLite
  });
}

function validateInlineDataQuality() {
  const text = document.getElementById('complaintTextInput').value;
  const indicator = document.getElementById('dqInlineIndicator');
  const textSpan = document.getElementById('dqInlineText');
  const pip = indicator.querySelector('.dq-pip');
  
  const charLen = text.length;
  const tokens = text.trim().split(/\s+/).filter(t => t.length > 1);
  const isRepetitive = /(.)\1{4,}/.test(text.toLowerCase());
  
  if (charLen < 12) {
    pip.className = 'dq-pip dq-pip-fail';
    textSpan.textContent = `DQ_FAIL_SHORT (Chars: ${charLen}/12 required)`;
  } else if (tokens.length < 3) {
    pip.className = 'dq-pip dq-pip-fail';
    textSpan.textContent = `DQ_FAIL_MIN_TOKENS (Tokens: ${tokens.length}/3 required)`;
  } else if (isRepetitive) {
    pip.className = 'dq-pip dq-pip-fail';
    textSpan.textContent = 'DQ_FAIL_GIBBERISH (Repetitive pattern)';
  } else {
    pip.className = 'dq-pip dq-pip-pass';
    textSpan.textContent = `DQ_PASS (Chars: ${charLen} | Tokens: ${tokens.length})`;
  }
}

// ============================================================================
// API Communication & Client Fallback Engine
// ============================================================================
function setApiStatus(isOnline) {
  isConnectedToApi = isOnline;
  const chip = document.getElementById('connectionStatusChip');
  const text = document.getElementById('connectionStatusText');
  if (!chip || !text) return;
  const pip = chip.querySelector('.chip-pip');
  
  if (isOnline) {
    pip.className = 'chip-pip chip-pip-online';
    text.textContent = 'API: CONNECTED (FASTAPI)';
  } else {
    pip.className = 'chip-pip chip-pip-offline';
    text.textContent = 'API: CLIENT MODE';
  }
}

async function checkApiHealth() {
  try {
    const res = await fetch(`${API_BASE}/api/health`, { method: 'GET' });
    if (res.ok) {
      setApiStatus(true);
      return true;
    }
  } catch (err) {
    setApiStatus(false);
    return false;
  }
}

async function runInference(dispatchToDb = false) {
  const ward = document.getElementById('wardInput').value;
  const text = document.getElementById('complaintTextInput').value;
  const upvotes = parseInt(document.getElementById('upvotesInput').value || '0', 10);
  
  const payload = {
    raw_text: text,
    ward_location: ward,
    citizen_upvotes: upvotes
  };
  
  const endpoint = dispatchToDb ? `${API_BASE}/api/tickets` : `${API_BASE}/api/predict`;
  
  let result = null;
  try {
    const res = await fetch(endpoint, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(payload)
    });
    if (res.ok) {
      result = await res.json();
      setApiStatus(true);
    } else {
      throw new Error(`HTTP ${res.status}`);
    }
  } catch (error) {
    console.warn('API fetch failed, utilizing client fallback:', error);
    result = executeClientFallbackInference(payload, dispatchToDb);
    setApiStatus(false);
  }
  
  // Normalize response structure
  let stage1 = result.stage1_nlp || result;
  let stage2 = result.stage2_urgency || result;
  
  renderTelemetry(stage1, stage2);
  
  if (dispatchToDb) {
    showToast(`Ticket ${result.ticket_id || 'CP-TKT'} successfully created & dispatched!`);
    fetchPriorityQueue();
    openReceiptModal({
      ticket_id: result.ticket_id || `CP-TKT-${Date.now().toString().slice(-4)}`,
      status: result.status || (stage2.requires_hitl_review ? 'PENDING_REVIEW' : 'DISPATCHED'),
      predicted_department: stage1.predicted_department,
      urgency_tier: stage2.urgency_tier,
      sla_hours: stage2.sla_hours,
      ward_location: ward,
      raw_text: text
    });
  }
}

function renderTelemetry(nlp, urg) {
  // Latency
  const latencyBadge = document.getElementById('latencyBadge');
  if (latencyBadge) latencyBadge.textContent = `LATENCY: ${nlp.inference_latency_ms || 0.8} ms`;
  
  // Department Chip
  const deptChip = document.getElementById('triageDeptChip');
  const dept = nlp.predicted_department || 'SANITATION';
  if (deptChip) {
    deptChip.textContent = dept;
    deptChip.setAttribute('data-dept', dept);
  }
  
  // Urgency
  const score = urg.urgency_score !== undefined ? urg.urgency_score : 50;
  const tier = urg.urgency_tier || 'MEDIUM';
  const sla = urg.sla_hours || 24;
  
  const urgNum = document.getElementById('triageUrgencyNum');
  if (urgNum) urgNum.textContent = Number(score).toFixed(1);
  const badge = document.getElementById('triageUrgencyBadge');
  if (badge) {
    badge.textContent = `${tier} (${sla}h SLA)`;
    badge.className = `urgency-tier-badge tier-${tier.toLowerCase()}`;
  }
  
  // HITL Badge
  const hitlBadge = document.getElementById('triageHitlBadge');
  if (hitlBadge) {
    if (urg.requires_hitl_review) {
      hitlBadge.textContent = 'REQUIRES HITL REVIEW';
      hitlBadge.className = 'hitl-badge hitl-alert';
    } else {
      hitlBadge.textContent = 'AUTO-DISPATCHED';
      hitlBadge.className = 'hitl-badge hitl-pass';
    }
  }
  
  // Diagnostics
  const cEl = document.getElementById('metricTop1Conf');
  if (cEl) cEl.textContent = `${((nlp.top1_confidence || 0.9) * 100).toFixed(1)}%`;
  const mEl = document.getElementById('metricTop2Margin');
  if (mEl) mEl.textContent = `${((nlp.top2_margin || 0.8) * 100).toFixed(1)}%`;
  const eEl = document.getElementById('metricEntropy');
  if (eEl) eEl.textContent = `${(nlp.shannon_entropy || 0.01).toFixed(2)} / 1.0`;
  const hEl = document.getElementById('metricHazardBonus');
  if (hEl) hEl.textContent = `+${urg.hazard_score || 0} pts`;
  
  // Probability Bars
  const probContainer = document.getElementById('probBarsContainer');
  if (probContainer) {
    probContainer.innerHTML = '';
    const probs = nlp.department_probabilities || {
      ELECTRICAL: 0.2, WATER: 0.2, ROADS: 0.2, SANITATION: 0.2, HEALTH: 0.2
    };
    
    Object.keys(probs).forEach(d => {
      const val = probs[d];
      const pct = (val * 100).toFixed(1);
      const row = document.createElement('div');
      row.className = 'prob-bar-row';
      row.innerHTML = `
        <span class="prob-dept-name" style="color: ${DEPT_COLORS[d] || '#fff'}">${d}</span>
        <div class="prob-track">
          <div class="prob-fill" style="width: ${pct}%; background-color: ${DEPT_COLORS[d] || '#38bdf8'}"></div>
        </div>
        <span class="prob-val">${pct}%</span>
      `;
      probContainer.appendChild(row);
    });
  }
  
  // Feature Attribution Tokens
  const cloud = document.getElementById('tokenAttributionCloud');
  if (cloud) {
    cloud.innerHTML = '';
    const tokens = nlp.token_attributions || [];
    if (tokens.length > 0) {
      tokens.forEach(item => {
        const chip = document.createElement('span');
        chip.className = 'token-chip';
        chip.innerHTML = `
          <span class="token-text">${item.token}</span>
          <span class="token-weight">${item.weight > 0 ? '+' : ''}${item.weight}</span>
        `;
        cloud.appendChild(chip);
      });
    } else {
      cloud.innerHTML = '<span class="sub-label">Awaiting input tokens...</span>';
    }
  }
  
  // Formula Breakdown
  const fd = document.getElementById('fDept'); if (fd) fd.textContent = urg.base_dept_weight || 20;
  const fh = document.getElementById('fHazard'); if (fh) fh.textContent = urg.hazard_score || 0;
  const fz = document.getElementById('fZone'); if (fz) fz.textContent = urg.zone_bonus || 0;
  const fu = document.getElementById('fUpvotes'); if (fu) fu.textContent = Number(urg.upvote_bonus || 0).toFixed(1);
  const fp = document.getElementById('fPhi'); if (fp) fp.textContent = Number(urg.confidence_calibration_factor || 1.0).toFixed(2);
  const ft = document.getElementById('fTotal'); if (ft) ft.textContent = Number(score).toFixed(1);
}

// Receipt Modal Handler
function initReceiptModal() {
  const modal = document.getElementById('receiptModal');
  const viewQueueBtn = document.getElementById('rcptViewQueueBtn');
  const newBtn = document.getElementById('rcptNewBtn');
  
  if (viewQueueBtn) {
    viewQueueBtn.addEventListener('click', () => {
      modal.classList.remove('open');
      const queueBtn = document.querySelector('[data-tab="queueTab"]');
      if (queueBtn) queueBtn.click();
    });
  }
  
  if (newBtn) {
    newBtn.addEventListener('click', () => {
      modal.classList.remove('open');
      const input = document.getElementById('complaintTextInput');
      input.value = '';
      input.focus();
      validateInlineDataQuality();
    });
  }
}

function openReceiptModal(data) {
  const modal = document.getElementById('receiptModal');
  if (!modal) return;
  
  document.getElementById('rcptTicketId').textContent = data.ticket_id || 'CP-TKT-2026';
  document.getElementById('rcptStatus').textContent = data.status || 'DISPATCHED';
  
  const dept = data.predicted_department || 'SANITATION';
  const deptChip = document.getElementById('rcptDept');
  deptChip.textContent = dept;
  deptChip.setAttribute('data-dept', dept);
  
  const tier = data.urgency_tier || 'MEDIUM';
  const tierBadge = document.getElementById('rcptTier');
  tierBadge.textContent = tier;
  tierBadge.className = `urgency-tier-badge tier-${tier.toLowerCase()}`;
  
  document.getElementById('rcptSla').textContent = `${data.sla_hours || 24} Hours`;
  document.getElementById('rcptWard').textContent = data.ward_location || 'Municipal Ward';
  document.getElementById('rcptText').textContent = data.raw_text || '';
  
  modal.classList.add('open');
}

// Client-side fallback for static standalone execution without server
function executeClientFallbackInference(payload, dispatch = false) {
  const text = payload.raw_text.toLowerCase();
  let dept = 'SANITATION';
  let hazard = 0;
  let zone = 0;
  
  if (text.includes('wire') || text.includes('sparking') || text.includes('voltage') || text.includes('transformer') || text.includes('electric') || text.includes('light')) {
    dept = 'ELECTRICAL';
    if (text.includes('snapped') || text.includes('sparking') || text.includes('live wire')) hazard = 38;
  } else if (text.includes('pipe') || text.includes('water') || text.includes('leakage') || text.includes('potable') || text.includes('tap') || text.includes('handpump')) {
    dept = 'WATER';
    if (text.includes('sewage mixed') || text.includes('burst')) hazard = text.includes('sinkhole') ? 38 : 20;
  } else if (text.includes('pothole') || text.includes('road') || text.includes('sinkhole') || text.includes('cave-in') || text.includes('footpath')) {
    dept = 'ROADS';
    if (text.includes('cave-in') || text.includes('sinkhole')) hazard = 20;
  } else if (text.includes('dengue') || text.includes('larvae') || text.includes('mosquito') || text.includes('dog bite') || text.includes('jaundice')) {
    dept = 'HEALTH';
    hazard = 20;
  } else {
    dept = 'SANITATION';
    if (text.includes('carcass') || text.includes('biomedical')) hazard = 20;
  }
  
  if (text.includes('school') || text.includes('hospital') || text.includes('college')) {
    zone = 18;
  }
  
  const upvoteBonus = Math.min(10.0, 2.0 * Math.log2(1.0 + (payload.citizen_upvotes || 0)));
  const deptWeight = dept === 'ELECTRICAL' ? 30 : dept === 'WATER' ? 25 : dept === 'HEALTH' ? 25 : dept === 'ROADS' ? 20 : 18;
  const score = Math.max(0, Math.min(100, (deptWeight + hazard + zone + upvoteBonus)));
  
  let tier = 'LOW';
  if (score >= 75) tier = 'CRITICAL';
  else if (score >= 55) tier = 'HIGH';
  else if (score >= 35) tier = 'MEDIUM';
  
  const requiresHitl = hazard >= 35 && text.length < 25;
  
  return {
    stage1_nlp: {
      predicted_department: dept,
      department_probabilities: {
        ELECTRICAL: dept === 'ELECTRICAL' ? 0.98 : 0.005,
        WATER: dept === 'WATER' ? 0.98 : 0.005,
        ROADS: dept === 'ROADS' ? 0.98 : 0.005,
        SANITATION: dept === 'SANITATION' ? 0.98 : 0.005,
        HEALTH: dept === 'HEALTH' ? 0.98 : 0.005
      },
      top1_confidence: 0.98,
      top2_margin: 0.97,
      shannon_entropy: 0.02,
      inference_latency_ms: 0.9,
      token_attributions: [
        { token: dept.toLowerCase(), weight: 2.45 },
        { token: hazard > 0 ? 'hazard' : 'municipal', weight: 1.82 }
      ]
    },
    stage2_urgency: {
      urgency_score: score,
      urgency_tier: tier,
      sla_hours: tier === 'CRITICAL' ? 4 : tier === 'HIGH' ? 12 : tier === 'MEDIUM' ? 24 : 48,
      base_dept_weight: deptWeight,
      hazard_score: hazard,
      zone_bonus: zone,
      upvote_bonus: upvoteBonus,
      confidence_calibration_factor: 1.0,
      requires_hitl_review: requiresHitl,
      hitl_reasons: requiresHitl ? ['HIGH_HAZARD_UNCERTAIN_ROUTING'] : []
    },
    ticket_id: `CP-LOCAL-${Math.floor(Math.random()*9000)+1000}`
  };
}

// ============================================================================
// Priority Dispatch Queue Management
// ============================================================================
function initQueueFilters() {
  document.getElementById('filterDept').addEventListener('change', fetchPriorityQueue);
  document.getElementById('filterTier').addEventListener('change', fetchPriorityQueue);
  
  const hitlBtn = document.getElementById('btnFilterHitl');
  hitlBtn.addEventListener('click', () => {
    activeQueueFilterHitl = !activeQueueFilterHitl;
    hitlBtn.classList.toggle('active', activeQueueFilterHitl);
    fetchPriorityQueue();
  });
  
  document.getElementById('btnRefreshQueue').addEventListener('click', () => {
    fetchPriorityQueue();
    showToast('Queue refreshed from SQLite database.');
  });
}

async function fetchPriorityQueue() {
  const dept = document.getElementById('filterDept').value;
  const tier = document.getElementById('filterTier').value;
  const tbody = document.getElementById('queueTableBody');
  const countBadge = document.getElementById('queueCountBadge');
  
  let url = `${API_BASE}/api/tickets?limit=50`;
  if (dept && dept !== 'ALL') url += `&dept=${dept}`;
  if (tier && tier !== 'ALL') url += `&tier=${tier}`;
  if (activeQueueFilterHitl) url += `&hitl_only=true`;
  
  try {
    const res = await fetch(url);
    if (!res.ok) throw new Error('API offline');
    const data = await res.json();
    const tickets = data.tickets || [];
    
    countBadge.textContent = tickets.length;
    renderQueueTable(tickets);
  } catch (err) {
    countBadge.textContent = 'Demo Mode';
    renderQueueTable([
      {
        ticket_id: 'CP-2026-0001',
        ward_location: 'Ward 04 - Civil Lines (Civil Hospital Gate 2)',
        raw_text: 'High voltage 11kV electrical wire snapped and hanging loose just 4 feet above ground level near hospital.',
        effective_dept: 'ELECTRICAL',
        urgency_score: 96.0,
        effective_urgency_tier: 'CRITICAL',
        sla_deadline_hours: 4,
        requires_hitl: 0,
        status: 'DISPATCHED'
      },
      {
        ticket_id: 'CP-2026-0002',
        ward_location: 'Ward 35 - Indiranagar (100 Feet Road)',
        raw_text: 'Drinking water pipeline burst causing road cave-in and sinkhole.',
        effective_dept: 'WATER',
        urgency_score: 84.0,
        effective_urgency_tier: 'CRITICAL',
        sla_deadline_hours: 4,
        requires_hitl: 1,
        status: 'PENDING_REVIEW'
      }
    ]);
  }
}

function renderQueueTable(tickets) {
  const tbody = document.getElementById('queueTableBody');
  tbody.innerHTML = '';
  
  if (tickets.length === 0) {
    tbody.innerHTML = `<tr><td colspan="8" style="text-align: center; color: var(--text-muted); padding: 2rem;">No complaints match active filter criteria.</td></tr>`;
    return;
  }
  
  tickets.forEach(t => {
    const tr = document.createElement('tr');
    const tier = t.effective_urgency_tier || 'LOW';
    const dept = t.effective_dept || 'SANITATION';
    const isHitl = t.requires_hitl === 1;
    
    tr.innerHTML = `
      <td class="mono"><strong>${t.ticket_id}</strong></td>
      <td style="max-width: 180px;">${t.ward_location}</td>
      <td style="max-width: 300px; font-size: 12px; color: var(--text-secondary);">${t.raw_text}</td>
      <td>
        <span class="dept-chip" data-dept="${dept}" style="font-size: 11px; padding: 2px 6px;">${dept}</span>
      </td>
      <td>
        <span class="urgency-tier-badge tier-${tier.toLowerCase()}">${tier} (${t.urgency_score})</span>
      </td>
      <td class="mono" style="font-size: 11px;">${t.sla_deadline_hours}h Remaining</td>
      <td>
        <span class="hitl-badge ${isHitl ? 'hitl-alert' : 'hitl-pass'}" style="font-size: 10px;">
          ${isHitl ? 'NEEDS REVIEW' : 'AUTO ROUTED'}
        </span>
      </td>
      <td>
        <button class="btn btn-secondary btn-sm override-trigger-btn" data-ticket='${JSON.stringify(t)}'>
          ⚙️ Override
        </button>
      </td>
    `;
    tbody.appendChild(tr);
  });
  
  // Wire up override buttons
  document.querySelectorAll('.override-trigger-btn').forEach(btn => {
    btn.addEventListener('click', () => {
      const ticket = JSON.parse(btn.getAttribute('data-ticket'));
      openOverrideModal(ticket);
    });
  });
}

// ============================================================================
// Human-in-the-Loop Override Modal
// ============================================================================
function initModalListeners() {
  const modal = document.getElementById('overrideModal');
  const closeBtn = document.getElementById('closeOverrideModalBtn');
  const cancelBtn = document.getElementById('cancelOverrideBtn');
  const form = document.getElementById('overrideForm');
  
  closeBtn.addEventListener('click', () => modal.classList.remove('open'));
  cancelBtn.addEventListener('click', () => modal.classList.remove('open'));
  
  form.addEventListener('submit', async (e) => {
    e.preventDefault();
    const ticketId = document.getElementById('overrideTicketId').value;
    const operatorId = document.getElementById('operatorIdInput').value;
    const reasonCode = document.getElementById('reasonCodeSelect').value;
    const newDept = document.getElementById('overrideDeptSelect').value;
    const newTier = document.getElementById('overrideTierSelect').value;
    const notes = document.getElementById('overrideNotes').value;
    
    const payload = {
      operator_id: operatorId,
      reason_code: reasonCode,
      new_dept: newDept,
      new_urgency_tier: newTier,
      notes: notes
    };
    
    try {
      if (isConnectedToApi) {
        const res = await fetch(`${API_BASE}/api/tickets/${ticketId}/override`, {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify(payload)
        });
        if (!res.ok) throw new Error(await res.text());
      }
      modal.classList.remove('open');
      showToast(`Override committed for ${ticketId} [Reason: ${reasonCode}]`);
      fetchPriorityQueue();
      fetchAuditLedger();
    } catch (err) {
      alert(`Override submission error: ${err.message}`);
    }
  });
}

function openOverrideModal(ticket) {
  const modal = document.getElementById('overrideModal');
  document.getElementById('overrideTicketId').value = ticket.ticket_id;
  document.getElementById('modalTicketId').textContent = ticket.ticket_id;
  document.getElementById('modalOrigDept').textContent = ticket.effective_dept;
  document.getElementById('modalOrigTier').textContent = ticket.effective_urgency_tier;
  document.getElementById('overrideDeptSelect').value = ticket.effective_dept;
  document.getElementById('overrideTierSelect').value = ticket.effective_urgency_tier;
  document.getElementById('operatorIdInput').value = 'OP-DELHI-4421';
  modal.classList.add('open');
}

// ============================================================================
// Audit Ledger View
// ============================================================================
async function fetchAuditLedger() {
  const tbody = document.getElementById('auditTableBody');
  const countBadge = document.getElementById('auditCounterBadge');
  
  try {
    const res = await fetch(`${API_BASE}/api/audit-log?limit=50`);
    if (!res.ok) throw new Error('API offline');
    const data = await res.json();
    const records = data.audit_trail || [];
    
    countBadge.textContent = `${records.length} Overrides Logged`;
    tbody.innerHTML = '';
    
    if (records.length === 0) {
      tbody.innerHTML = `<tr><td colspan="7" style="text-align: center; color: var(--text-muted); padding: 2rem;">No manual human overrides recorded in audit ledger.</td></tr>`;
      return;
    }
    
    records.forEach(r => {
      const tr = document.createElement('tr');
      tr.innerHTML = `
        <td class="mono" style="font-size: 11px;">${r.timestamp}</td>
        <td class="mono"><strong>${r.ticket_id}</strong></td>
        <td class="mono" style="color: var(--text-accent);">${r.operator_id}</td>
        <td><span class="brand-badge-tag">${r.reason_code}</span></td>
        <td>${r.previous_dept} &rarr; <strong>${r.new_dept}</strong></td>
        <td>${r.previous_urgency_tier} &rarr; <strong>${r.new_urgency_tier}</strong></td>
        <td style="font-size: 12px; color: var(--text-secondary);">${r.notes || '-'}</td>
      `;
      tbody.appendChild(tr);
    });
  } catch (err) {
    countBadge.textContent = '0 Overrides Logged';
    tbody.innerHTML = `<tr><td colspan="7" style="text-align: center; color: var(--text-muted); padding: 2rem;">Audit ledger ready. Submit an override to append immutable entries.</td></tr>`;
  }
}

// ============================================================================
// Model Telemetry & Matrix View
// ============================================================================
async function fetchModelMetrics() {
  const tbody = document.getElementById('modelComparisonTableBody');
  const cmContainer = document.getElementById('confusionMatrixContainer');
  const cmSummary = document.getElementById('cmSummaryTag');
  
  try {
    const res = await fetch(`${API_BASE}/api/metrics`);
    if (!res.ok) throw new Error('API offline');
    const data = await res.json();
    
    // Model Comparison
    const models = data.model_comparison || [];
    tbody.innerHTML = '';
    models.forEach(m => {
      const isChampion = m.model_name === data.champion_model?.name;
      const tr = document.createElement('tr');
      tr.innerHTML = `
        <td><strong>${m.model_name}</strong></td>
        <td class="mono">${(m.accuracy * 100).toFixed(2)}%</td>
        <td class="mono">${m.macro_precision.toFixed(4)}</td>
        <td class="mono">${m.macro_recall.toFixed(4)}</td>
        <td class="mono"><strong>${m.macro_f1.toFixed(4)}</strong></td>
        <td class="mono">${m.latency_ms} ms</td>
        <td>
          <span class="hitl-badge ${isChampion ? 'hitl-pass' : 'tier-medium'}" style="font-size: 10px;">
            ${isChampion ? '★ CHAMPION PRODUCTION' : 'CANDIDATE'}
          </span>
        </td>
      `;
      tbody.appendChild(tr);
    });
    
    // Confusion Matrix
    const cm = data.confusion_matrix;
    if (cm && cm.labels && cm.matrix) {
      cmSummary.textContent = `Macro-F1: ${data.champion_model?.macro_f1} | Acc: ${(data.champion_model?.accuracy * 100).toFixed(1)}%`;
      let tableHtml = `<table class="cm-table"><thead><tr><th>True \\ Pred</th>`;
      cm.labels.forEach(l => { tableHtml += `<th>${l}</th>`; });
      tableHtml += `</tr></thead><tbody>`;
      
      cm.matrix.forEach((row, i) => {
        tableHtml += `<tr><th>${cm.labels[i]}</th>`;
        row.forEach((val, j) => {
          const isDiag = i === j;
          tableHtml += `<td class="${isDiag ? 'cm-diag' : 'cm-off'}">${val}</td>`;
        });
        tableHtml += `</tr>`;
      });
      tableHtml += `</tbody></table>`;
      cmContainer.innerHTML = tableHtml;
    }
  } catch (err) {
    console.warn('Metrics fetch fallback:', err);
  }
}

// Toast Notification
function showToast(msg) {
  const container = document.getElementById('toastContainer');
  if (!container) return;
  const toast = document.createElement('div');
  toast.className = 'toast';
  toast.textContent = msg;
  container.appendChild(toast);
  setTimeout(() => {
    toast.remove();
  }, 3500);
}
