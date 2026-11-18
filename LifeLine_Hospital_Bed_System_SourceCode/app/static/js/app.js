/**
 * LifeLine - Real-Time Hospital Bed Availability Frontend Engine
 * Powered by WebSockets, REST API & Web Audio API
 */

let hospitals = [];
let localities = [];
let activeBedFilter = "ALL";
let searchQuery = "";
let selectedLocality = "ALL";
let soundEnabled = true;
let ws = null;
let reconnectInterval = 2000;

// Web Audio API tone generator (No external MP3 required!)
function playTone(freq = 587.33, duration = 0.25) {
  if (!soundEnabled) return;
  try {
    const audioCtx = new (window.AudioContext || window.webkitAudioContext)();
    const osc = audioCtx.createOscillator();
    const gain = audioCtx.createGain();
    osc.type = "sine";
    osc.frequency.setValueAtTime(freq, audioCtx.currentTime);
    gain.gain.setValueAtTime(0.15, audioCtx.currentTime);
    gain.gain.exponentialRampToValueAtTime(0.001, audioCtx.currentTime + duration);
    osc.connect(gain);
    gain.connect(audioCtx.destination);
    osc.start();
    osc.stop(audioCtx.currentTime + duration);
  } catch (e) {
    console.warn("AudioContext not permitted yet:", e);
  }
}

// Play pleasant double chime on bed update
function playChime(isPositive = true) {
  if (isPositive) {
    playTone(523.25, 0.15); // C5
    setTimeout(() => playTone(659.25, 0.25), 120); // E5
  } else {
    playTone(440, 0.15); // A4
    setTimeout(() => playTone(392, 0.25), 120); // G4
  }
}

// Initial Data Fetch
async function loadData() {
  try {
    const [hospRes, locRes] = await Promise.all([
      fetch("/api/hospitals"),
      fetch("/api/localities")
    ]);
    hospitals = await hospRes.json();
    localities = await locRes.json();
    populateLocalityDropdown();
    renderHospitals();
    updateStatSummary();
  } catch (err) {
    console.error("Error loading hospitals:", err);
    showToast("Failed to load hospital data. Retrying...", "red");
  }
}

function populateLocalityDropdown() {
  const select = document.getElementById("localityFilter");
  if (!select) return;
  select.innerHTML = '<option value="ALL">All Localities / Areas</option>';
  localities.forEach(loc => {
    const opt = document.createElement("option");
    opt.value = loc;
    opt.textContent = loc;
    select.appendChild(opt);
  });
}

// WebSocket Connection & Real-Time Sync
function initWebSocket() {
  const protocol = window.location.protocol === "https:" ? "wss:" : "ws:";
  const wsUrl = `${protocol}//${window.location.host}/ws/beds`;
  const badge = document.getElementById("wsStatusBadge");

  ws = new WebSocket(wsUrl);

  ws.onopen = () => {
    console.log("🟢 Connected to Bed Availability WebSocket");
    if (badge) {
      badge.innerHTML = `<span class="w-2.5 h-2.5 bg-emerald-500 rounded-full inline-block mr-1.5 pulse-live"></span> Live Sync Connected`;
      badge.className = "inline-flex items-center px-3 py-1 text-xs font-semibold rounded-full bg-emerald-50 text-emerald-700 border border-emerald-200";
    }
    reconnectInterval = 2000;
  };

  ws.onmessage = (event) => {
    try {
      const data = JSON.parse(event.data);
      if (data.event === "BED_UPDATED") {
        handleBedUpdate(data);
      }
    } catch (e) {
      console.error("WebSocket message parse error:", e);
    }
  };

  ws.onclose = () => {
    console.warn("⚠️ WebSocket disconnected. Reconnecting in", reconnectInterval / 1000, "seconds...");
    if (badge) {
      badge.innerHTML = `<span class="w-2.5 h-2.5 bg-amber-500 rounded-full inline-block mr-1.5"></span> Reconnecting Sync...`;
      badge.className = "inline-flex items-center px-3 py-1 text-xs font-semibold rounded-full bg-amber-50 text-amber-700 border border-amber-200";
    }
    setTimeout(initWebSocket, reconnectInterval);
    reconnectInterval = Math.min(reconnectInterval * 1.5, 10000);
  };

  ws.onerror = (err) => {
    console.error("WebSocket error:", err);
    ws.close();
  };
}

// Handle Real-Time WebSocket Bed Update Event
function handleBedUpdate(data) {
  const hosp = hospitals.find(h => h.id === data.hospital_id);
  if (!hosp) return;

  const bed = hosp.beds.find(b => b.bed_type === data.bed_type);
  if (bed) {
    const isIncrease = data.available_beds > bed.available_beds;
    bed.available_beds = data.available_beds;
    bed.occupied_beds = data.occupied_beds;
    bed.total_beds = data.total_beds;
    hosp.last_updated = data.timestamp;

    playChime(isIncrease);

    const icon = isIncrease ? "🟢" : "⚠️";
    const msg = `${icon} <b>${data.hospital_name}</b>: ${data.bed_type} available beds updated to <b>${data.available_beds}</b> (${data.change_desc})`;
    showToast(msg, isIncrease ? "green" : "blue");

    renderHospitals();
    updateStatSummary();

    // Trigger visual flash on updated card
    const card = document.getElementById(`hospital-card-${data.hospital_id}`);
    if (card) {
      card.classList.remove("card-flash-update");
      void card.offsetWidth; // trigger reflow
      card.classList.add("card-flash-update");
    }
  }
}

// Render Hospital Cards
function renderHospitals() {
  const container = document.getElementById("hospitalsContainer");
  if (!container) return;

  // Filter hospitals
  const filtered = hospitals.filter(h => {
    // Search query match
    const q = searchQuery.toLowerCase().trim();
    const matchesSearch = !q || 
      h.name.toLowerCase().includes(q) ||
      h.locality.toLowerCase().includes(q) ||
      h.address.toLowerCase().includes(q) ||
      h.pincode.includes(q);

    // Locality match
    const matchesLocality = selectedLocality === "ALL" || h.locality.toLowerCase() === selectedLocality.toLowerCase();

    // Bed type filter
    let matchesBed = true;
    if (activeBedFilter !== "ALL") {
      const targetBed = h.beds.find(b => b.bed_type.toUpperCase() === activeBedFilter.toUpperCase());
      matchesBed = targetBed && targetBed.available_beds > 0;
    }

    return matchesSearch && matchesLocality && matchesBed;
  });

  if (filtered.length === 0) {
    container.innerHTML = `
      <div class="col-span-full py-16 text-center bg-white rounded-2xl border border-dashed border-slate-300 shadow-sm">
        <div class="w-16 h-16 mx-auto mb-4 bg-rose-50 text-rose-500 rounded-full flex items-center justify-center text-2xl font-bold">
          !
        </div>
        <h3 class="text-lg font-bold text-slate-800">No Hospitals Found</h3>
        <p class="text-slate-500 text-sm max-w-md mx-auto mt-1">
          No hospital matches your current search or bed availability filters. Try clearing filters or switching categories.
        </p>
        <button onclick="resetFilters()" class="mt-4 px-4 py-2 bg-slate-900 text-white rounded-xl text-sm font-semibold hover:bg-slate-800 transition">
          Clear All Filters
        </button>
      </div>
    `;
    return;
  }

  container.innerHTML = filtered.map(h => {
    // Check critical ICU status
    const icuBed = h.beds.find(b => b.bed_type === "ICU");
    const icuAvail = icuBed ? icuBed.available_beds : 0;
    const isIcuCritical = icuAvail <= 2;

    return `
      <div id="hospital-card-${h.id}" class="bg-white rounded-2xl border border-slate-200/80 shadow-sm hover:shadow-md transition-all duration-300 overflow-hidden flex flex-col justify-between">
        
        <!-- Header -->
        <div class="p-5 border-b border-slate-100 bg-gradient-to-r from-slate-50/50 to-white">
          <div class="flex items-start justify-between gap-3">
            <div>
              <div class="flex items-center gap-2 flex-wrap">
                <span class="px-2.5 py-0.5 rounded-full text-xs font-semibold ${h.type.includes('Government') ? 'bg-blue-50 text-blue-700 border border-blue-200' : 'bg-purple-50 text-purple-700 border border-purple-200'}">
                  ${h.type}
                </span>
                ${isIcuCritical && icuAvail > 0 ? `
                  <span class="px-2 py-0.5 rounded-full text-xs font-semibold bg-amber-50 text-amber-700 border border-amber-200 flex items-center gap-1">
                    <span class="w-1.5 h-1.5 rounded-full bg-amber-500 animate-ping"></span> Critical ICU Shortage
                  </span>
                ` : ''}
                ${icuAvail === 0 ? `
                  <span class="px-2 py-0.5 rounded-full text-xs font-semibold bg-rose-50 text-rose-700 border border-rose-200">
                    ICU Full
                  </span>
                ` : ''}
              </div>
              <h3 class="text-lg font-bold text-slate-900 mt-2 leading-snug">${h.name}</h3>
              <p class="text-xs text-slate-500 mt-1 flex items-center gap-1">
                <i class="fa-solid fa-location-dot text-rose-500"></i> ${h.address}, ${h.locality} - ${h.pincode}
              </p>
            </div>
            
            <a href="tel:${h.contact_emergency}" class="flex-shrink-0 w-11 h-11 bg-rose-600 hover:bg-rose-700 text-white rounded-xl flex items-center justify-center shadow-lg shadow-rose-600/30 transition-transform active:scale-95" title="Call Emergency Casualty">
              <i class="fa-solid fa-phone-volume text-lg"></i>
            </a>
          </div>

          <!-- Feature tags -->
          <div class="flex items-center gap-2 mt-3 text-xs text-slate-600">
            ${h.ambulance_available ? '<span class="inline-flex items-center gap-1 bg-slate-100 px-2 py-1 rounded-md"><i class="fa-solid fa-truck-medical text-slate-700"></i> Ambulance</span>' : ''}
            ${h.oxygen_plant_active ? '<span class="inline-flex items-center gap-1 bg-slate-100 px-2 py-1 rounded-md"><i class="fa-solid fa-wind text-slate-700"></i> Oxygen Plant</span>' : ''}
            ${h.blood_bank_available ? '<span class="inline-flex items-center gap-1 bg-slate-100 px-2 py-1 rounded-md"><i class="fa-solid fa-droplet text-rose-600"></i> Blood Bank</span>' : ''}
          </div>
        </div>

        <!-- Bed Breakdown Grid -->
        <div class="p-5">
          <div class="text-xs font-semibold uppercase tracking-wider text-slate-400 mb-3 flex items-center justify-between">
            <span>Live Bed Inventory</span>
            <span class="text-slate-400 font-normal lowercase">real-time sync</span>
          </div>

          <div class="grid grid-cols-2 sm:grid-cols-3 gap-2.5">
            ${h.beds.map(b => renderBedPill(b)).join('')}
          </div>
        </div>

        <!-- Footer Actions -->
        <div class="p-4 bg-slate-50 border-t border-slate-100 flex items-center justify-between text-xs">
          <div class="text-slate-500">
            <span class="text-slate-400">Emergency Casualty:</span>
            <span class="font-semibold text-slate-700 ml-1">${h.contact_emergency}</span>
          </div>
          
          <div class="flex items-center gap-2">
            <button onclick="openTokenModal(${h.id}, '${h.name.replace(/'/g, "\\'")}')" class="px-3 py-1.5 bg-slate-900 hover:bg-slate-800 text-white font-medium rounded-lg shadow-sm transition active:scale-95">
              <i class="fa-solid fa-ticket mr-1"></i> Triage Slip
            </button>
            <a href="https://maps.google.com/?q=${h.latitude || 19.076},${h.longitude || 72.8777}" target="_blank" class="px-3 py-1.5 bg-white border border-slate-300 hover:bg-slate-100 text-slate-700 font-medium rounded-lg transition">
              <i class="fa-solid fa-diamond-turn-right text-indigo-600 mr-1"></i> Route
            </a>
          </div>
        </div>

      </div>
    `;
  }).join('');
}

function renderBedPill(bed) {
  const avail = bed.available_beds;
  const total = bed.total_beds;
  
  let colorBg = "bg-emerald-50 border-emerald-200 text-emerald-800";
  let countColor = "text-emerald-700";
  let badgeText = "Available";

  if (avail === 0) {
    colorBg = "bg-rose-50 border-rose-200 text-rose-800";
    countColor = "text-rose-700";
    badgeText = "FULL";
  } else if (avail <= 2) {
    colorBg = "bg-amber-50 border-amber-200 text-amber-800";
    countColor = "text-amber-700";
    badgeText = "Critical";
  }

  const icons = {
    "ICU": "fa-heart-pulse",
    "NICU": "fa-baby",
    "VENTILATOR": "fa-lungs",
    "OXYGEN": "fa-wind",
    "GENERAL": "fa-bed"
  };
  const icon = icons[bed.bed_type.toUpperCase()] || "fa-bed";

  return `
    <div class="p-2.5 rounded-xl border ${colorBg} flex flex-col justify-between transition-all">
      <div class="flex items-center justify-between text-xs font-semibold">
        <span class="flex items-center gap-1">
          <i class="fa-solid ${icon} text-[11px] opacity-75"></i> ${bed.bed_type}
        </span>
        <span class="text-[10px] font-bold uppercase tracking-wider">${badgeText}</span>
      </div>
      <div class="mt-2 flex items-baseline justify-between">
        <span class="text-xl font-extrabold ${countColor}">${avail}</span>
        <span class="text-[11px] opacity-60">/ ${total} total</span>
      </div>
    </div>
  `;
}

// Summary Metrics Updater
function updateStatSummary() {
  let totalAvail = 0;
  let totalBeds = 0;
  let icuAvail = 0;
  let nicuAvail = 0;
  let ventAvail = 0;

  hospitals.forEach(h => {
    h.beds.forEach(b => {
      totalAvail += b.available_beds;
      totalBeds += b.total_beds;
      if (b.bed_type === "ICU") icuAvail += b.available_beds;
      if (b.bed_type === "NICU") nicuAvail += b.available_beds;
      if (b.bed_type === "VENTILATOR") ventAvail += b.available_beds;
    });
  });

  const elTotalHosp = document.getElementById("statTotalHospitals");
  const elTotalBeds = document.getElementById("statTotalAvailableBeds");
  const elIcuBeds = document.getElementById("statIcuAvailable");
  const elNicuBeds = document.getElementById("statNicuAvailable");
  const elVentBeds = document.getElementById("statVentilatorAvailable");

  if (elTotalHosp) elTotalHosp.textContent = hospitals.length;
  if (elTotalBeds) elTotalBeds.textContent = totalAvail;
  if (elIcuBeds) elIcuBeds.textContent = icuAvail;
  if (elNicuBeds) elNicuBeds.textContent = nicuAvail;
  if (elVentBeds) elVentBeds.textContent = ventAvail;
}

// Toast Notification
function showToast(htmlMessage, theme = "blue") {
  const container = document.getElementById("toastContainer");
  if (!container) return;

  const toast = document.createElement("div");
  const borderColors = {
    green: "border-emerald-500 bg-white text-slate-800",
    blue: "border-blue-500 bg-white text-slate-800",
    red: "border-rose-500 bg-white text-slate-800",
    amber: "border-amber-500 bg-white text-slate-800"
  };

  toast.className = `p-4 rounded-xl border-l-4 shadow-xl text-sm flex items-start gap-3 transition-all duration-300 transform translate-x-full ${borderColors[theme] || borderColors.blue}`;
  toast.innerHTML = `
    <div class="flex-1">${htmlMessage}</div>
    <button onclick="this.parentElement.remove()" class="text-slate-400 hover:text-slate-600 text-xs">✕</button>
  `;

  container.appendChild(toast);

  // Animate slide in
  requestAnimationFrame(() => {
    toast.classList.remove("translate-x-full");
  });

  // Auto remove after 5s
  setTimeout(() => {
    toast.classList.add("opacity-0", "translate-x-full");
    setTimeout(() => toast.remove(), 400);
  }, 5000);
}

// Filters Handlers
function setBedFilter(type) {
  activeBedFilter = type;
  document.querySelectorAll(".filter-pill").forEach(btn => {
    if (btn.dataset.filter === type) {
      btn.className = "filter-pill px-4 py-2 rounded-xl text-xs font-bold bg-slate-900 text-white shadow-sm transition";
    } else {
      btn.className = "filter-pill px-4 py-2 rounded-xl text-xs font-semibold bg-white border border-slate-200 text-slate-700 hover:bg-slate-100 transition";
    }
  });
  renderHospitals();
}

function resetFilters() {
  activeBedFilter = "ALL";
  searchQuery = "";
  selectedLocality = "ALL";
  const searchInput = document.getElementById("searchInput");
  const locSelect = document.getElementById("localityFilter");
  if (searchInput) searchInput.value = "";
  if (locSelect) locSelect.value = "ALL";
  setBedFilter("ALL");
}

// Emergency Triage Slip / Token Generator
function openTokenModal(hospId, hospName) {
  const modal = document.getElementById("tokenModal");
  const hospNameEl = document.getElementById("tokenHospitalName");
  const hospIdInput = document.getElementById("tokenHospitalId");
  const slipCodeEl = document.getElementById("tokenSlipCode");
  
  if (hospNameEl) hospNameEl.textContent = hospName;
  if (hospIdInput) hospIdInput.value = hospId;
  
  // Generate random emergency code: e.g. "EMG-7489"
  const randomCode = "EMG-" + Math.floor(1000 + Math.random() * 9000);
  if (slipCodeEl) slipCodeEl.textContent = randomCode;

  if (modal) modal.classList.remove("hidden");
}

function closeTokenModal() {
  const modal = document.getElementById("tokenModal");
  if (modal) modal.classList.add("hidden");
}

function printTriageSlip() {
  window.print();
}

// Audio Toggle
function toggleAudio() {
  soundEnabled = !soundEnabled;
  const btn = document.getElementById("soundToggleBtn");
  if (btn) {
    btn.innerHTML = soundEnabled ? 
      '<i class="fa-solid fa-volume-high text-emerald-600"></i>' : 
      '<i class="fa-solid fa-volume-xmark text-slate-400"></i>';
  }
}

// Event Listeners on Load
document.addEventListener("DOMContentLoaded", () => {
  loadData();
  initWebSocket();

  const searchInput = document.getElementById("searchInput");
  if (searchInput) {
    searchInput.addEventListener("input", (e) => {
      searchQuery = e.target.value;
      renderHospitals();
    });
  }

  const locSelect = document.getElementById("localityFilter");
  if (locSelect) {
    locSelect.addEventListener("change", (e) => {
      selectedLocality = e.target.value;
      renderHospitals();
    });
  }
});
