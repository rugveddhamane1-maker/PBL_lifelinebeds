/**
 * LifeLine - Hospital Staff Rapid Bed Management Console
 * Fast, touch-friendly interface for emergency triage desks and nurses.
 */

let staffSession = null;
let currentHospitalBeds = [];
let staffWs = null;

// Check stored session
function checkStaffSession() {
  const saved = localStorage.getItem("lifeline_staff_session");
  if (saved) {
    try {
      staffSession = JSON.parse(saved);
      showStaffDashboard();
      return;
    } catch (e) {
      localStorage.removeItem("lifeline_staff_session");
    }
  }
  showLoginForm();
}

function showLoginForm() {
  document.getElementById("staffLoginSection").classList.remove("hidden");
  document.getElementById("staffDashboardSection").classList.add("hidden");
  loadHospitalOptions();
}

function showStaffDashboard() {
  document.getElementById("staffLoginSection").classList.add("hidden");
  document.getElementById("staffDashboardSection").classList.remove("hidden");
  document.getElementById("staffHospName").textContent = staffSession.hospital_name;
  document.getElementById("staffWelcome").textContent = `Logged in: ${staffSession.staff_name} (${staffSession.role})`;
  loadStaffBeds();
  loadStaffAuditLogs();
  initStaffWebSocket();
}

// Populate Hospital dropdown for login
async function loadHospitalOptions() {
  const select = document.getElementById("staffHospSelect");
  if (!select) return;
  try {
    const res = await fetch("/api/hospitals");
    const data = await res.json();
    select.innerHTML = '<option value="">Select Your Hospital...</option>' + 
      data.map(h => `<option value="${h.id}">${h.name} (${h.hospital_code})</option>`).join('');
  } catch (e) {
    console.error("Failed to load hospitals for staff login:", e);
  }
}

// Handle PIN Login
async function handleStaffLogin(e) {
  e.preventDefault();
  const hospId = document.getElementById("staffHospSelect").value;
  const pin = document.getElementById("staffPinInput").value;
  const errorEl = document.getElementById("loginErrorMsg");

  if (!hospId || !pin) {
    errorEl.textContent = "Please select a hospital and enter the staff PIN code.";
    errorEl.classList.remove("hidden");
    return;
  }

  try {
    const res = await fetch("/api/staff/login", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ hospital_id: parseInt(hospId), pin_code: pin })
    });

    if (!res.ok) {
      const errData = await res.json();
      errorEl.textContent = errData.detail || "Authentication failed. Incorrect PIN.";
      errorEl.classList.remove("hidden");
      return;
    }

    staffSession = await res.json();
    localStorage.setItem("lifeline_staff_session", JSON.stringify(staffSession));
    errorEl.classList.add("hidden");
    showStaffDashboard();

  } catch (err) {
    console.error("Login request failed:", err);
    errorEl.textContent = "Server communication error. Please try again.";
    errorEl.classList.remove("hidden");
  }
}

function staffLogout() {
  localStorage.removeItem("lifeline_staff_session");
  staffSession = null;
  if (staffWs) staffWs.close();
  showLoginForm();
}

// Fetch beds for the logged-in hospital
async function loadStaffBeds() {
  if (!staffSession) return;
  try {
    const res = await fetch(`/api/hospitals/${staffSession.hospital_id}`);
    const hosp = await res.json();
    currentHospitalBeds = hosp.beds || [];
    renderStaffBedCounters();
  } catch (e) {
    console.error("Failed to load staff beds:", e);
  }
}

// Render rapid counter buttons
function renderStaffBedCounters() {
  const container = document.getElementById("staffCountersContainer");
  if (!container) return;

  const icons = {
    "ICU": "fa-heart-pulse text-rose-500",
    "NICU": "fa-baby text-amber-500",
    "VENTILATOR": "fa-lungs text-blue-500",
    "OXYGEN": "fa-wind text-teal-500",
    "GENERAL": "fa-bed text-indigo-500"
  };

  container.innerHTML = currentHospitalBeds.map(b => {
    const iconClass = icons[b.bed_type.toUpperCase()] || "fa-bed text-slate-500";
    const isFull = b.available_beds <= 0;
    const isAtMax = b.available_beds >= b.total_beds;

    return `
      <div class="bg-white p-5 rounded-2xl border border-slate-200/80 shadow-sm flex flex-col justify-between">
        <div class="flex items-center justify-between">
          <div class="flex items-center gap-2">
            <i class="fa-solid ${iconClass} text-lg"></i>
            <h4 class="font-bold text-slate-900 text-base">${b.bed_type} Ward</h4>
          </div>
          <span class="text-xs px-2.5 py-1 rounded-full font-bold ${b.available_beds > 2 ? 'bg-emerald-100 text-emerald-800' : (b.available_beds > 0 ? 'bg-amber-100 text-amber-800' : 'bg-rose-100 text-rose-800')}">
            ${b.available_beds > 0 ? `${b.available_beds} Vacant` : 'FULL'}
          </span>
        </div>

        <div class="my-5 text-center">
          <div class="text-5xl font-black text-slate-900" id="staff-count-${b.bed_type}">
            ${b.available_beds}
          </div>
          <div class="text-xs text-slate-400 mt-1">
            Available out of ${b.total_beds} Total Beds (${b.occupied_beds} Occupied)
          </div>
        </div>

        <!-- Rapid Touch Buttons -->
        <div class="grid grid-cols-2 gap-3">
          <button 
            onclick="updateBedCount('${b.bed_type}', 'decrement')" 
            ${isFull ? 'disabled' : ''} 
            class="py-3 px-4 bg-rose-50 hover:bg-rose-100 text-rose-700 font-bold rounded-xl border border-rose-200 active:scale-95 transition disabled:opacity-40 disabled:cursor-not-allowed flex items-center justify-center gap-2 text-sm shadow-sm">
            <i class="fa-solid fa-minus"></i> Admit Patient
          </button>

          <button 
            onclick="updateBedCount('${b.bed_type}', 'increment')" 
            ${isAtMax ? 'disabled' : ''} 
            class="py-3 px-4 bg-emerald-50 hover:bg-emerald-100 text-emerald-700 font-bold rounded-xl border border-emerald-200 active:scale-95 transition disabled:opacity-40 disabled:cursor-not-allowed flex items-center justify-center gap-2 text-sm shadow-sm">
            <i class="fa-solid fa-plus"></i> Vacated Bed
          </button>
        </div>
      </div>
    `;
  }).join('');
}

// Rapid Bed Update Request
async function updateBedCount(bedType, action) {
  if (!staffSession) return;

  try {
    const res = await fetch(`/api/hospitals/${staffSession.hospital_id}/beds/update`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        bed_type: bedType,
        action: action,
        updated_by: `${staffSession.staff_name} (${staffSession.role})`
      })
    });

    if (!res.ok) {
      const err = await res.json();
      alert("Update error: " + (err.detail || "Unable to update"));
      return;
    }

    const data = await res.json();
    // Update local bed
    const bed = currentHospitalBeds.find(b => b.bed_type === bedType);
    if (bed) {
      bed.available_beds = data.bed.available_beds;
      bed.occupied_beds = data.bed.occupied_beds;
      renderStaffBedCounters();
    }
    loadStaffAuditLogs();

  } catch (err) {
    console.error("Bed update request failed:", err);
  }
}

// Load Recent Staff Audit Logs
async function loadStaffAuditLogs() {
  try {
    const res = await fetch("/api/audit-logs?limit=15");
    const logs = await res.json();
    const container = document.getElementById("staffAuditLogTable");
    if (!container) return;

    container.innerHTML = logs.map(l => {
      const isInc = l.change_type === "INCREMENT";
      const icon = isInc ? "fa-arrow-up text-emerald-500" : "fa-arrow-down text-rose-500";
      const badge = isInc ? "bg-emerald-50 text-emerald-700 border-emerald-200" : "bg-rose-50 text-rose-700 border-rose-200";
      const timeStr = new Date(l.timestamp).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit', second: '2-digit' });

      return `
        <tr class="border-b border-slate-100 hover:bg-slate-50 text-xs">
          <td class="py-2.5 px-3 text-slate-500">${timeStr}</td>
          <td class="py-2.5 px-3 font-semibold text-slate-800">${l.bed_type}</td>
          <td class="py-2.5 px-3">
            <span class="inline-flex items-center gap-1 px-2 py-0.5 rounded border text-[11px] font-bold ${badge}">
              <i class="fa-solid ${icon}"></i> ${l.previous_count} → ${l.new_count}
            </span>
          </td>
          <td class="py-2.5 px-3 text-slate-600">${l.updated_by}</td>
        </tr>
      `;
    }).join('');
  } catch (e) {
    console.error("Failed to load audit logs:", e);
  }
}

// Staff WebSocket Listener
function initStaffWebSocket() {
  const protocol = window.location.protocol === "https:" ? "wss:" : "ws:";
  const wsUrl = `${protocol}//${window.location.host}/ws/beds`;

  staffWs = new WebSocket(wsUrl);
  staffWs.onmessage = (event) => {
    try {
      const data = JSON.parse(event.data);
      if (data.event === "BED_UPDATED") {
        if (staffSession && data.hospital_id === staffSession.hospital_id) {
          const bed = currentHospitalBeds.find(b => b.bed_type === data.bed_type);
          if (bed) {
            bed.available_beds = data.available_beds;
            bed.occupied_beds = data.occupied_beds;
            renderStaffBedCounters();
          }
        }
        loadStaffAuditLogs();
      }
    } catch (e) {}
  };
}

document.addEventListener("DOMContentLoaded", () => {
  checkStaffSession();
  const form = document.getElementById("staffLoginForm");
  if (form) form.addEventListener("submit", handleStaffLogin);
});
