/* Flood Risk Prediction and Early Warning Decision Support System - UI Prototype Logic */
/* Client-side prototype only: all data is demo data, no backend calls. */

(function () {
  "use strict";

  /* ---------- District data (Sindh, Pakistan) ---------- */
  var DISTRICTS = [
    { name: "Dadu", lat: 26.73, lon: 67.78, prob: 82, level: "HIGH", factors: ["Heavy rainfall", "Low elevation", "River proximity"] },
    { name: "Larkana", lat: 27.56, lon: 68.21, prob: 78, level: "HIGH", factors: ["Heavy rainfall", "River proximity", "Flat terrain"] },
    { name: "Thatta", lat: 24.75, lon: 67.92, prob: 75, level: "HIGH", factors: ["River delta exposure", "Heavy rainfall", "Low elevation"] },
    { name: "Jacobabad", lat: 28.28, lon: 68.44, prob: 74, level: "HIGH", factors: ["High temperature", "River proximity", "Repeated flood history"] },
    { name: "Sukkur", lat: 27.71, lon: 68.86, prob: 55, level: "MEDIUM", factors: ["River proximity", "Moderate rainfall"] },
    { name: "Hyderabad", lat: 25.38, lon: 68.37, prob: 52, level: "MEDIUM", factors: ["Moderate rainfall", "Urban drainage pressure"] },
    { name: "Badin", lat: 24.66, lon: 68.84, prob: 48, level: "MEDIUM", factors: ["Coastal exposure", "Moderate rainfall"] },
    { name: "Shikarpur", lat: 27.95, lon: 68.29, prob: 45, level: "MEDIUM", factors: ["River proximity", "Flat terrain"] },
    { name: "Ghotki", lat: 28.00, lon: 69.32, prob: 22, level: "LOW", factors: ["Higher elevation", "Low recent rainfall"] },
    { name: "Karachi", lat: 24.86, lon: 67.01, prob: 18, level: "LOW", factors: ["Urban drainage", "Coastal defenses"] }
  ];

  var LEVEL_COLOR = { HIGH: "#D32F2F", MEDIUM: "#E6A81B", LOW: "#2E9E57" };

  var ROLES = {
    authority: { label: "Disaster Management Authority", icon: "\uD83C\uDFDB\uFE0F" },
    ngo: { label: "NGO / Relief Organization", icon: "\uD83E\uDD1D" },
    public: { label: "Public User", icon: "\uD83D\uDC68\u200D\uD83D\uDC69\u200D\uD83D\uDC67" }
  };

  var state = { role: null, live: false, chartsReady: false, charts: {}, map: null, markers: {}, riskLayer: null, histLayer: null };

  /* Demo credentials for the seeded database users (password: demo1234) */
  var DEMO_ACCOUNTS = {
    authority: "authority.demo@flooddss.pk",
    ngo: "ngo.demo@flooddss.pk",
    public: "public.demo@flooddss.pk"
  };

  function api() { return (typeof window.FloodDSS !== "undefined") ? window.FloodDSS : null; }

  /* ---------- Login ---------- */
  var roleCards = document.querySelectorAll(".role-card");
  var loginBtn = document.getElementById("loginBtn");

  if (roleCards.length) {
    roleCards.forEach(function (card) {
      card.addEventListener("click", function () {
        roleCards.forEach(function (c) { c.classList.remove("selected"); });
        card.classList.add("selected");
        state.role = card.getAttribute("data-role");
        var emailInput = document.getElementById("loginEmail");
        var passInput = document.getElementById("loginPassword");
        if (emailInput) emailInput.value = DEMO_ACCOUNTS[state.role] || "";
        if (passInput) passInput.value = "demo1234";
        loginBtn.disabled = false;
      });
    });
  }

  function enterApp(role) {
    document.getElementById("loginScreen").style.display = "none";
    document.getElementById("appShell").classList.add("active");
    applyRole(role);
    showPage("dashboard");
    initCharts();
    initMap();
    if (state.live) {
      refreshLiveDashboard();
      refreshLiveMap();
      refreshLiveAlerts();
      preloadDecisionData();
    }
  }

  if (loginBtn) {
    loginBtn.addEventListener("click", async function () {
      if (!state.role) return;
      loginBtn.disabled = true;
      loginBtn.textContent = "Connecting…";
      var email = (document.getElementById("loginEmail") || {}).value || "";
      var password = (document.getElementById("loginPassword") || {}).value || "";
      var client = api();
      var loggedIn = false;
      if (client && email && password) {
        try {
          var res = await client.login(email.trim(), password);
          if (res.ok) {
            loggedIn = true;
            state.live = true;
            if (res.data && res.data.role) state.role = res.data.role;
          }
        } catch (e) { loggedIn = false; }
      }
      if (!loggedIn) {
        state.live = false;
        var banner = document.getElementById("demoBanner");
        if (banner) {
          banner.style.display = "";
          var baseEl = document.getElementById("demoApiBase");
          if (baseEl && client) baseEl.textContent = client.getBase();
        }
      }
      loginBtn.disabled = false;
      loginBtn.textContent = "Login";
      enterApp(state.role);
    });
  }

  /* ---------- Role switching ---------- */
  function applyRole(role) {
    state.role = role;
    var badge = document.getElementById("roleBadge");
    badge.querySelector(".role-name").textContent = ROLES[role].label;

    var navLinks = document.querySelectorAll(".sidebar nav a[data-page]");
    navLinks.forEach(function (a) {
      var allowed = a.getAttribute("data-roles").split(",");
      if (allowed.indexOf(role) === -1) {
        a.classList.add("hidden");
      } else {
        a.classList.remove("hidden");
      }
    });

    document.getElementById("adminSections").style.display = (role === "authority") ? "" : "none";
    document.getElementById("ngoPanel").style.display = (role === "ngo") ? "" : "none";
    document.getElementById("publicHero").style.display = (role === "public") ? "" : "none";
    document.getElementById("dashboardStandard").style.display = (role === "public") ? "none" : "";

    var activeLink = document.querySelector(".sidebar nav a.active");
    if (activeLink && activeLink.classList.contains("hidden")) {
      showPage("dashboard");
    }
  }

  var roleBadge = document.getElementById("roleBadge");
  if (roleBadge) {
    roleBadge.addEventListener("click", function () {
      var order = ["authority", "ngo", "public"];
      var next = order[(order.indexOf(state.role) + 1) % order.length];
      applyRole(next);
    });
  }

  /* ---------- Router ---------- */
  function showPage(pageId) {
    document.querySelectorAll(".page").forEach(function (p) { p.classList.remove("active"); });
    document.getElementById("page-" + pageId).classList.add("active");
    document.querySelectorAll(".sidebar nav a[data-page]").forEach(function (a) {
      a.classList.toggle("active", a.getAttribute("data-page") === pageId);
    });
    if (pageId === "map" && state.map) {
      setTimeout(function () { state.map.invalidateSize(); }, 120);
    }
    if (pageId === "decision" && typeof loadDecisionPage === "function") {
      loadDecisionPage();
    }
    if (pageId === "alert-center" && typeof loadAlertCenterPage === "function") {
      loadAlertCenterPage();
    }
  }

  document.querySelectorAll(".sidebar nav a[data-page]").forEach(function (a) {
    a.addEventListener("click", function () { showPage(a.getAttribute("data-page")); });
  });

  /* ---------- Alerts bell ---------- */
  var bell = document.getElementById("alertsBell");
  if (bell) {
    bell.addEventListener("click", function () {
      showPage("dashboard");
      var feed = document.getElementById("alertsFeed");
      if (feed) feed.scrollIntoView({ behavior: "smooth", block: "center" });
    });
  }

  /* ---------- Charts (Chart.js) ---------- */
  function initCharts() {
    if (state.chartsReady || typeof Chart === "undefined") return;
    state.chartsReady = true;

    Chart.defaults.font.family = "'Segoe UI', Roboto, Arial, sans-serif";

    // Rainfall trends: monthly totals (mm), Sindh average
    state.charts.rainfall = new Chart(document.getElementById("chartRainfall"), {
      type: "line",
      data: {
        labels: ["Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"],
        datasets: [{
          label: "Rainfall (mm)",
          data: [8, 10, 12, 9, 14, 38, 152, 176, 92, 18, 6, 5],
          borderColor: "#123A63",
          backgroundColor: "rgba(18,58,99,0.12)",
          fill: true,
          tension: 0.35,
          pointBackgroundColor: "#E8641B"
        }]
      },
      options: {
        responsive: true,
        plugins: { legend: { display: false }, title: { display: true, text: "Monthly Rainfall Trends (mm) - Sindh" } },
        scales: { y: { beginAtZero: true } }
      }
    });

    // Flood frequency analysis 2010-2025
    state.charts.frequency = new Chart(document.getElementById("chartFrequency"), {
      type: "bar",
      data: {
        labels: ["2010", "2011", "2012", "2013", "2014", "2015", "2016", "2017", "2018", "2019", "2020", "2021", "2022", "2023", "2024", "2025"],
        datasets: [{
          label: "Flood events",
          data: [9, 3, 2, 2, 3, 2, 2, 3, 1, 2, 4, 3, 11, 4, 5, 4],
          backgroundColor: "#E8641B"
        }]
      },
      options: {
        responsive: true,
        plugins: { legend: { display: false }, title: { display: true, text: "Flood Frequency Analysis (events per year)" } },
        scales: { y: { beginAtZero: true, ticks: { stepSize: 2 } } }
      }
    });

    // Risk distribution doughnut
    state.charts.distribution = new Chart(document.getElementById("chartDistribution"), {
      type: "doughnut",
      data: {
        labels: ["LOW", "MEDIUM", "HIGH"],
        datasets: [{
          data: [12, 9, 5],
          backgroundColor: ["#2E9E57", "#E6A81B", "#D32F2F"]
        }]
      },
      options: {
        responsive: true,
        plugins: { title: { display: true, text: "Risk Distribution (monitored districts)" } }
      }
    });
  }

  /* ---------- Live dashboard data (falls back to demo data on any error) ---------- */
  function setText(id, text) {
    var el = document.getElementById(id);
    if (el) el.textContent = text;
  }

  async function refreshLiveDashboard() {
    var client = api();
    if (!client || !state.live) return;
    try {
      var s = await client.getSummary();
      if (s.ok && s.data) {
        setText("statAlerts", s.data.active_alerts);
        setText("statAlertsSub", "active alerts in the system");
        setText("statHighRisk", s.data.high_risk_areas);
        setText("statHighRiskSub", "districts at HIGH risk");
        setText("statEvents", s.data.total_historical_events);
        setText("statEventsSub", "recorded flood events");
        setText("statStatus", s.data.current_risk_status);
        setText("statStatusSub", "overall current risk status");
      }
      var t = await client.getRainfallTrends();
      if (t.ok && Array.isArray(t.data) && t.data.length && state.charts.rainfall) {
        state.charts.rainfall.data.labels = t.data.map(function (p) { return p.label || p.month || ""; });
        state.charts.rainfall.data.datasets[0].data = t.data.map(function (p) { return p.value != null ? p.value : p.rainfall_mm; });
        state.charts.rainfall.update();
      }
      var f = await client.getFloodFrequency();
      if (f.ok && Array.isArray(f.data) && f.data.length && state.charts.frequency) {
        state.charts.frequency.data.labels = f.data.map(function (p) { return p.label || p.year || ""; });
        state.charts.frequency.data.datasets[0].data = f.data.map(function (p) { return p.value != null ? p.value : p.events; });
        state.charts.frequency.update();
      }
      var d = await client.getRiskDistribution();
      if (d.ok && d.data && state.charts.distribution) {
        var dist = d.data;
        var order = ["LOW", "MEDIUM", "HIGH"];
        state.charts.distribution.data.labels = order;
        state.charts.distribution.data.datasets[0].data = order.map(function (k) { return dist[k] != null ? dist[k] : (dist[k.toLowerCase()] || 0); });
        state.charts.distribution.update();
      }
    } catch (e) { /* keep demo data */ }
  }

  async function refreshLiveAlerts() {
    var client = api();
    if (!client || !state.live) return;
    try {
      var r = await client.getAlerts(true);
      if (!r.ok || !r.data || !r.data.items) return;
      var feed = document.getElementById("alertsFeed");
      if (!feed) return;
      var html = "<h3>Recent Alerts</h3>";
      var sevClass = { info: "sev-low", watch: "sev-low", warning: "sev-medium", emergency: "sev-high" };
      r.data.items.slice(0, 6).forEach(function (a) {
        var sev = (a.severity || "info").toLowerCase();
        html += "<div class='alert-item'><div class='alert-sev " + (sevClass[sev] || "sev-low") + "'></div>" +
          "<div class='alert-body'><strong>" + a.title + "</strong>" + a.message +
          "<div class='alert-time'>" + (a.issued_at || "").slice(0, 10) + "</div></div></div>";
      });
      feed.innerHTML = html;
    } catch (e) { /* keep demo alerts */ }
  }

  async function refreshLiveMap() {
    var client = api();
    if (!client || !state.live || !state.map || !state.riskLayer) return;
    try {
      var r = await client.getRiskLayers();
      if (!r.ok || !r.data || !Array.isArray(r.data.features)) return;
      state.riskLayer.clearLayers();
      state.markers = {};
      r.data.features.forEach(function (ft) {
        var p = ft.properties || {};
        var coords = (ft.geometry && ft.geometry.coordinates) || [0, 0];
        var level = p.risk_level || "LOW";
        var prob = (p.probability != null) ? Math.round(p.probability) : 0;
        var marker = L.circleMarker([coords[1], coords[0]], {
          radius: 10 + prob / 12,
          fillColor: LEVEL_COLOR[level] || "#95a5a6",
          color: "#fff", weight: 2, opacity: 1, fillOpacity: 0.85
        }).bindPopup(riskPopupHtml(p, prob, level));
        state.riskLayer.addLayer(marker);
        state.markers[String(p.district_name).toLowerCase()] = marker;
      });
    } catch (e) { /* keep demo markers */ }
  }

  /* ---------- Leaflet map ---------- */
  function popupHtml(d) {
    return "<h4>" + d.name + " District</h4>" +
      "<b>Risk Probability:</b> " + d.prob + "%<br>" +
      "<b>Risk Level:</b> <span class='badge badge-" + d.level.toLowerCase() + "'>" + d.level + "</span><br>" +
      "<b>Main factors:</b> " + d.factors.join(", ");
  }

  function initMap() {
    if (state.map || typeof L === "undefined") return;
    var map = L.map("map").setView([26.5, 68.5], 7);
    state.map = map;

    L.tileLayer("https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png", {
      attribution: "&copy; OpenStreetMap contributors",
      maxZoom: 18
    }).addTo(map);

    var riskLayer = L.layerGroup();
    DISTRICTS.forEach(function (d) {
      var marker = L.circleMarker([d.lat, d.lon], {
        radius: 10 + d.prob / 12,
        fillColor: LEVEL_COLOR[d.level],
        color: "#fff",
        weight: 2,
        opacity: 1,
        fillOpacity: 0.85
      }).bindPopup(popupHtml(d));
      riskLayer.addLayer(marker);
      state.markers[d.name.toLowerCase()] = marker;
    });
    riskLayer.addTo(map);
    state.riskLayer = riskLayer;

    // Historical flood layer: approximate 2010 and 2022 flood extents (demo polygons)
    var histLayer = L.layerGroup();
    var poly2010 = L.polygon([[24.3, 67.4], [24.3, 68.5], [25.3, 68.5], [25.3, 67.4]], {
      color: "#1A6FB5", weight: 2, fillColor: "#4DA3E0", fillOpacity: 0.35
    }).bindPopup("<h4>2010 Super Flood Extent</h4>Thatta / Badin region (demo polygon)");
    var poly2022 = L.polygon([[26.3, 67.3], [26.3, 68.3], [27.2, 68.3], [27.2, 67.3]], {
      color: "#1A6FB5", weight: 2, fillColor: "#4DA3E0", fillOpacity: 0.35
    }).bindPopup("<h4>2022 Flood Extent</h4>Dadu / Larkana region (demo polygon)");
    histLayer.addLayer(poly2010);
    histLayer.addLayer(poly2022);
    state.histLayer = histLayer;

    document.getElementById("toggleRisk").addEventListener("change", function (e) {
      if (e.target.checked) { riskLayer.addTo(map); } else { map.removeLayer(riskLayer); }
    });
    document.getElementById("toggleHist").addEventListener("change", function (e) {
      if (e.target.checked) { histLayer.addTo(map); } else { map.removeLayer(histLayer); }
    });

    document.getElementById("mapSearchBtn").addEventListener("click", searchDistrict);
    document.getElementById("mapSearch").addEventListener("keydown", function (e) {
      if (e.key === "Enter") searchDistrict();
    });

    // Legend
    var legend = L.control({ position: "bottomright" });
    legend.onAdd = function () {
      var div = L.DomUtil.create("div", "info legend");
      div.style.background = "#fff";
      div.style.padding = "10px 12px";
      div.style.borderRadius = "8px";
      div.style.fontSize = "12px";
      div.innerHTML = "<b>Risk Level</b><br>" +
        "<span style='color:#2E9E57'>&#9679;</span> Low Risk<br>" +
        "<span style='color:#E6A81B'>&#9679;</span> Medium Risk<br>" +
        "<span style='color:#D32F2F'>&#9679;</span> High Risk";
      return div;
    };
    legend.addTo(map);

    // Phase 4 layers: vulnerability, infrastructure, boundaries, live history
    if (typeof initPhase4Layers === "function") initPhase4Layers(map);
  }

  function searchDistrict() {
    var q = document.getElementById("mapSearch").value.trim().toLowerCase();
    if (!q || !state.map) return;
    var hit = null;
    DISTRICTS.forEach(function (d) {
      if (d.name.toLowerCase().indexOf(q) !== -1) hit = d;
    });
    if (hit) {
      state.map.setView([hit.lat, hit.lon], 9);
      state.markers[hit.name.toLowerCase()].openPopup();
    } else {
      alert("District not found. Try: Dadu, Larkana, Thatta, Sukkur, Hyderabad, Badin, Ghotki, Karachi, Jacobabad, Shikarpur.");
    }
  }

  /* ---------- Risk assessment scorer (weighted data-driven model, client-side demo) ---------- */
  function clamp01(v) { return Math.max(0, Math.min(1, v)); }

  function computeRisk(input) {
    var r = clamp01(input.rainfall / 400) * 0.31;
    var t = clamp01((input.temperature - 20) / 20) * 0.08;
    var h = clamp01(input.humidity / 100) * 0.10;
    var e = (1 - clamp01(input.elevation / 500)) * 0.18;
    var rd = (1 - clamp01(input.riverDist / 25)) * 0.16;
    var s = (1 - clamp01(input.slope / 15)) * 0.08;
    var p = clamp01(input.popDensity / 1000) * 0.03;
    var ev = clamp01(input.prevEvents / 6) * 0.04;
    var sv = clamp01(input.severity / 5) * 0.02;
    var prob = Math.round((r + t + h + e + rd + s + p + ev + sv) * 100);
    var level = prob >= 65 ? "HIGH" : (prob >= 35 ? "MEDIUM" : "LOW");
    return { probability: prob, level: level };
  }

  function deriveFactors(input) {
    var factors = [];
    if (input.rainfall > 200) factors.push("Heavy rainfall");
    if (input.elevation < 100) factors.push("Low elevation");
    if (input.riverDist < 5) factors.push("River proximity");
    if (input.humidity > 75) factors.push("High humidity");
    if (input.slope < 3) factors.push("Flat terrain, poor drainage");
    if (input.prevEvents >= 3) factors.push("History of repeated flooding");
    if (input.severity >= 2) factors.push("Previous severe flood damage");
    return factors.slice(0, 3);
  }

  function deriveRecommendations(level) {
    var recs = ["Prepare evacuation plans", "Monitor water levels", "Contact emergency services"];
    if (level === "HIGH") {
      recs.push("Move livestock and valuables to higher ground");
      recs.push("Follow evacuation orders from PDMA Sindh");
    } else if (level === "MEDIUM") {
      recs.push("Keep emergency supplies ready");
    } else {
      recs.push("Stay informed through official alerts");
    }
    return recs;
  }

  var assessBtn = document.getElementById("assessBtn");
  if (assessBtn) {
    assessBtn.addEventListener("click", async function () {
      var locationRaw = document.getElementById("fLocation").value || "Unknown Location";
      var district = locationRaw.replace(/\s+District$/i, "").trim() || locationRaw;
      var input = {
        rainfall: parseFloat(document.getElementById("fRainfall").value) || 0,
        temperature: parseFloat(document.getElementById("fTemp").value) || 0,
        humidity: parseFloat(document.getElementById("fHumidity").value) || 0,
        elevation: parseFloat(document.getElementById("fElevation").value) || 0,
        riverDist: parseFloat(document.getElementById("fRiver").value) || 0,
        slope: parseFloat(document.getElementById("fSlope").value) || 0,
        popDensity: parseFloat(document.getElementById("fPop").value) || 0,
        prevEvents: parseInt(document.getElementById("fEvents").value, 10) || 0,
        severity: parseInt(document.getElementById("fSeverity").value, 10) || 0
      };

      /* Try the live backend first; fall back to the client-side scorer. */
      var probability, level, factors, recs;
      var client = api();
      var usedLive = false;
      if (client && state.live) {
        try {
          var payload = {
            district_name: district,
            rainfall_mm: input.rainfall,
            temperature_c: input.temperature,
            humidity_pct: input.humidity,
            elevation_m: input.elevation,
            river_distance_km: input.riverDist,
            slope_deg: input.slope,
            population_density: input.popDensity,
            prev_flood_events: input.prevEvents,
            last_severity: input.severity
          };
          var modelEl = document.getElementById("fModel");
          var model = modelEl ? modelEl.value : null;
          var res = await client.predictRisk(payload, model);
          if (res.ok && res.data) {
            usedLive = true;
            probability = Math.round(res.data.probability * 100);
            level = res.data.risk_level;
            factors = res.data.main_factors || [];
            recs = res.data.recommendations || [];
          }
        } catch (e) { usedLive = false; }
      }
      if (!usedLive) {
        var result = computeRisk(input);
        probability = result.probability;
        level = result.level;
        factors = deriveFactors(input);
        recs = deriveRecommendations(level);
      }

      document.getElementById("rLocation").textContent = locationRaw;
      document.getElementById("rProb").textContent = probability + "%";
      var lvl = document.getElementById("rLevel");
      lvl.textContent = level;
      lvl.className = "badge badge-" + level.toLowerCase();

      document.getElementById("rFactors").innerHTML = factors.map(function (f) { return "<li>" + f + "</li>"; }).join("");
      document.getElementById("rRecs").innerHTML = recs.map(function (r2) { return "<li>" + r2 + "</li>"; }).join("");
      document.getElementById("resultCard").classList.add("show");
      document.getElementById("resultCard").scrollIntoView({ behavior: "smooth", block: "nearest" });

      // Log into predictions history table
      var tbody = document.getElementById("predictionsBody");
      var row = document.createElement("tr");
      var now = new Date();
      var src = usedLive ? " (live API)" : " (demo)";
      row.innerHTML = "<td>" + (tbody.rows.length + 1) + "</td>" +
        "<td>" + locationRaw + src + "</td>" +
        "<td>" + probability + "%</td>" +
        "<td><span class='badge badge-" + level.toLowerCase() + "'>" + level + "</span></td>" +
        "<td>" + now.toISOString().slice(0, 10) + "</td>";
      tbody.insertBefore(row, tbody.firstChild);
    });
  }

  /* ---------- CSV export ---------- */
  var exportBtn = document.getElementById("exportCsvBtn");
  if (exportBtn) {
    exportBtn.addEventListener("click", function () {
      var rows = [];
      var table = document.getElementById("predictionsTable");
      var trs = table.querySelectorAll("tr");
      trs.forEach(function (tr) {
        var cells = [];
        tr.querySelectorAll("th, td").forEach(function (cell) { cells.push('"' + cell.textContent.trim().replace(/"/g, '""') + '"'); });
        rows.push(cells.join(","));
      });
      var blob = new Blob([rows.join("\n")], { type: "text/csv;charset=utf-8;" });
      var url = URL.createObjectURL(blob);
      var a = document.createElement("a");
      a.href = url;
      a.download = "flood_risk_predictions.csv";
      document.body.appendChild(a);
      a.click();
      document.body.removeChild(a);
      URL.revokeObjectURL(url);
    });
  }

  /* ================= PHASE 4 — GIS intelligence + decision support ================= */

  var PRIORITY_COLOR = { CRITICAL: "#D32F2F", HIGH: "#E8641B", MEDIUM: "#E6A81B", LOW: "#2E9E57" };
  var INFRA_COLOR = { hospital: "#C0392B", rescue_center: "#1A6FB5", emergency_facility: "#7D3C98", shelter: "#2E9E57" };
  var INFRA_LABEL = { hospital: "Hospital", rescue_center: "Rescue centre", emergency_facility: "Emergency facility", shelter: "Shelter" };
  var MONTHS = ["Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"];

  state.vulnLayer = null;
  state.infraLayer = null;
  state.boundsLayer = null;
  state.decision = null;
  state.sheltersByDistrict = {};

  function esc(s) {
    return String(s == null ? "" : s).replace(/[&<>"']/g, function (c) {
      return { "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;" }[c];
    });
  }

  /* Demo fallback decision-support data (offline mode). */
  var DEMO_DECISION = {
    summary: {
      high_risk_districts: [
        { district_name: "Dadu", province: "Sindh", probability: 0.82, risk_level: "HIGH", model_version: "mlp-v1",
          top_factors: [{ feature: "rainfall_mm", contribution: 0.34 }, { feature: "river_distance_km", contribution: 0.21 }, { feature: "elevation_m", contribution: 0.15 }],
          recommended_actions: ["Prepare evacuation plans", "Monitor water levels", "Contact emergency services"] },
        { district_name: "Larkana", province: "Sindh", probability: 0.78, risk_level: "HIGH", model_version: "mlp-v1",
          top_factors: [{ feature: "rainfall_mm", contribution: 0.31 }, { feature: "humidity_pct", contribution: 0.18 }],
          recommended_actions: ["Prepare evacuation plans", "Monitor water levels"] }
      ],
      active_alerts: [
        { title: "Flash flood warning — Dadu", message: "Heavy rainfall detected.", severity: "warning", district_name: "Dadu", issued_at: "2026-09-26T06:00:00" }
      ],
      latest_predictions: [
        { district_name: "Dadu", probability: 0.82, risk_level: "HIGH", model_version: "mlp-v1" },
        { district_name: "Larkana", probability: 0.78, risk_level: "HIGH", model_version: "mlp-v1" },
        { district_name: "Sukkur", probability: 0.55, risk_level: "MEDIUM", model_version: "mlp-v1" }
      ],
      resource_overview: {
        shelters: { count: 6, total_capacity: 5400 },
        infrastructure_by_type: { hospital: 13, rescue_center: 12, emergency_facility: 12 },
        allocations_by_status: { planned: 5, dispatched: 1 }
      },
      vulnerability_hotspots: [
        { district_name: "Karachi", province: "Sindh", vulnerability_index: 0.8, population_density: 3650, risk_level: "LOW", priority: "HIGH" },
        { district_name: "Dadu", province: "Sindh", vulnerability_index: 0.3315, population_density: 268, risk_level: "HIGH", priority: "CRITICAL" }
      ]
    },
    trends: {
      year_wise: [
        { district_name: "Dadu", yearly: [{ year: 2022, events: 3, avg_severity: 4.3 }], total_events: 5, trend_2017_2024_vs_2010_2016: "increasing" }
      ],
      seasonal_pattern: [
        { month: 7, events: 9 }, { month: 8, events: 21 }, { month: 9, events: 12 }
      ]
    }
  };

  /* Enriched district popup: risk + explanation + actions + vulnerability + shelters. */
  function riskPopupHtml(p, prob, level) {
    var name = p.district_name;
    var html = "<h4>" + esc(name) + " District</h4>" +
      "<b>Risk Probability:</b> " + prob + "%<br>" +
      "<b>Risk Level:</b> <span class='badge badge-" + String(level).toLowerCase() + "'>" + esc(level) + "</span><br>" +
      "<b>Main factors:</b> " + esc((p.main_factors || []).join(", ") || "—");
    var dec = state.decision;
    if (dec) {
      var hr = null;
      (dec.high_risk_districts || []).forEach(function (h) { if (h.district_name === name) hr = h; });
      if (hr) {
        if (hr.top_factors && hr.top_factors.length) {
          html += "<br><b>Contributing factors:</b><ul style='margin:4px 0;padding-left:18px;font-size:12px;'>";
          hr.top_factors.slice(0, 4).forEach(function (f) {
            var label = (f && f.feature) ? f.feature : f;
            var contrib = (f && f.contribution != null) ? " (" + Math.round(f.contribution * 100) + "%)" : "";
            html += "<li>" + esc(label) + esc(contrib) + "</li>";
          });
          html += "</ul>";
        }
        if (hr.recommended_actions && hr.recommended_actions.length) {
          html += "<b>Recommended actions:</b><ul style='margin:4px 0;padding-left:18px;font-size:12px;'>";
          hr.recommended_actions.slice(0, 3).forEach(function (a) { html += "<li>" + esc(a) + "</li>"; });
          html += "</ul>";
        }
      }
      var hs = null;
      (dec.vulnerability_hotspots || []).forEach(function (h) { if (h.district_name === name) hs = h; });
      if (hs) {
        html += "<b>Vulnerability index:</b> " + hs.vulnerability_index +
          " <span class='badge badge-" + hs.priority.toLowerCase() + "'>" + hs.priority + "</span><br>";
      }
      var sh = state.sheltersByDistrict[name];
      if (sh) html += "<b>Emergency shelters:</b> " + sh.count + " (capacity " + sh.capacity + ")<br>";
    }
    return html;
  }

  /* Preload decision summary + shelter counts for popup enrichment. */
  async function preloadDecisionData() {
    var client = api();
    if (!client || !state.live) return;
    try {
      var r = await client.getDecisionSummary();
      if (r.ok && r.data) state.decision = r.data;
      var s = await client.getShelters();
      if (s.ok && s.data && Array.isArray(s.data.features)) {
        var by = {};
        s.data.features.forEach(function (ft) {
          var pr = ft.properties || {};
          var d = pr.district_name || "Unknown";
          by[d] = by[d] || { count: 0, capacity: 0 };
          by[d].count += 1;
          by[d].capacity += pr.capacity || 0;
        });
        state.sheltersByDistrict = by;
      }
    } catch (e) { /* popups keep basic content */ }
  }

  /* ---------- Phase 4 map layers ---------- */
  function initPhase4Layers(map) {
    state.vulnLayer = L.layerGroup();
    state.infraLayer = L.layerGroup();
    state.boundsLayer = L.layerGroup();

    function wireToggle(id, layer) {
      var el = document.getElementById(id);
      if (!el) return;
      el.addEventListener("change", function (e) {
        if (e.target.checked) { layer.addTo(map); } else { map.removeLayer(layer); }
      });
    }
    wireToggle("toggleVuln", state.vulnLayer);
    wireToggle("toggleInfra", state.infraLayer);
    wireToggle("toggleBounds", state.boundsLayer);

    var client = api();
    if (!client || !state.live) return;

    // Vulnerability layer
    client.getVulnerabilityMap().then(function (r) {
      if (!r.ok || !r.data || !Array.isArray(r.data.features)) return;
      r.data.features.forEach(function (ft) {
        var pr = ft.properties || {};
        var coords = (ft.geometry && ft.geometry.coordinates) || [0, 0];
        var prio = pr.priority || "LOW";
        L.circleMarker([coords[1], coords[0]], {
          radius: 9, fillColor: PRIORITY_COLOR[prio] || "#95a5a6",
          color: "#fff", weight: 2, opacity: 1, fillOpacity: 0.8
        }).bindPopup("<h4>" + esc(pr.district_name) + " District</h4>" +
          "<b>Vulnerability index:</b> " + pr.vulnerability_index + "<br>" +
          "<b>Population density:</b> " + pr.population_density + " /km²<br>" +
          "<b>Risk level:</b> " + esc(pr.risk_level || "—") + "<br>" +
          "<b>Priority:</b> <span class='badge badge-" + prio.toLowerCase() + "'>" + prio + "</span>"
        ).addTo(state.vulnLayer);
      });
    }).catch(function () {});

    // Infrastructure layer
    client.getInfrastructure().then(function (r) {
      if (!r.ok || !r.data || !Array.isArray(r.data.features)) return;
      r.data.features.forEach(function (ft) {
        var pr = ft.properties || {};
        var coords = (ft.geometry && ft.geometry.coordinates) || [0, 0];
        L.circleMarker([coords[1], coords[0]], {
          radius: 7, fillColor: INFRA_COLOR[pr.type] || "#7f8c8d",
          color: "#fff", weight: 2, opacity: 1, fillOpacity: 0.9
        }).bindPopup("<h4>" + esc(pr.name) + "</h4>" +
          "<b>Type:</b> " + esc(INFRA_LABEL[pr.type] || pr.type) + "<br>" +
          "<b>District:</b> " + esc(pr.district_name || "—") + "<br>" +
          (pr.capacity != null ? "<b>Capacity:</b> " + pr.capacity + "<br>" : "") +
          "<b>Status:</b> " + esc(pr.operational_status || "—") + "<br>" +
          (pr.contact_phone ? "<b>Phone:</b> " + esc(pr.contact_phone) + "<br>" : "") +
          (pr.is_sample_data ? "<small style='color:#a00;'>Sample data — replace with authoritative registry before operational use.</small>" : "")
        ).addTo(state.infraLayer);
      });
    }).catch(function () {});

    // District boundaries (polygons when loaded)
    client.getBoundaries().then(function (r) {
      if (!r.ok || !r.data || !Array.isArray(r.data.features)) return;
      L.geoJSON(r.data, {
        style: { color: "#123A63", weight: 1.5, fillOpacity: 0.05 }
      }).bindPopup(function (layer) {
        return "<b>" + esc((layer.feature.properties || {}).district_name || "District") + "</b>";
      }).addTo(state.boundsLayer);
    }).catch(function () {});

    // Live historical flood points merged into the history layer
    client.getHistoricalFloods().then(function (r) {
      if (!r.ok || !r.data || !Array.isArray(r.data.features) || !state.histLayer) return;
      r.data.features.slice(0, 200).forEach(function (ft) {
        var pr = ft.properties || {};
        var coords = (ft.geometry && ft.geometry.coordinates) || [0, 0];
        L.circleMarker([coords[1], coords[0]], {
          radius: 4, fillColor: "#1A6FB5", color: "#fff", weight: 1, fillOpacity: 0.85
        }).bindPopup("<h4>" + esc(pr.district_name) + " — " + (pr.year || "") + "</h4>" +
          "<b>Severity:</b> " + esc(pr.severity_label || pr.severity || "—") + "<br>" +
          (pr.rainfall_mm != null ? "<b>Rainfall:</b> " + pr.rainfall_mm + " mm<br>" : "") +
          (pr.affected_population != null ? "<b>Affected:</b> " + pr.affected_population + "<br>" : "") +
          (pr.source ? "<small>Source: " + esc(pr.source) + "</small>" : "")
        ).addTo(state.histLayer);
      });
    }).catch(function () {});
  }

  /* ---------- Decision support page ---------- */
  function factorLabel(f) {
    if (f && typeof f === "object" && f.feature) {
      return f.feature + (f.contribution != null ? " (" + Math.round(f.contribution * 100) + "%)" : "");
    }
    return String(f);
  }

  function renderDecisionSummary(data) {
    var hr = data.high_risk_districts || [];
    var hrHtml = hr.length ? "<table class='data'><tr><th>District</th><th>Probability</th><th>Level</th><th>Model</th><th>Top factors</th><th>Recommended actions</th></tr>" : "<p class='muted'>No high-risk districts in the latest assessment cycle.</p>";
    hr.forEach(function (h) {
      hrHtml += "<tr><td><strong>" + esc(h.district_name) + "</strong></td>" +
        "<td>" + Math.round(h.probability * 100) + "%</td>" +
        "<td><span class='badge badge-high'>" + esc(h.risk_level) + "</span></td>" +
        "<td><small>" + esc(h.model_version || "") + "</small></td>" +
        "<td><small>" + esc((h.top_factors || []).slice(0, 3).map(factorLabel).join("; ")) + "</small></td>" +
        "<td><small>" + esc((h.recommended_actions || []).slice(0, 3).join("; ")) + "</small></td></tr>";
    });
    if (hr.length) hrHtml += "</table>";
    setHtml("dsHighRisk", hrHtml);

    var alerts = data.active_alerts || [];
    setHtml("dsAlerts", alerts.length
      ? alerts.map(function (a) {
          return "<div class='alert-item'><div class='alert-sev sev-" + sevClass(a.severity) + "'></div>" +
            "<div class='alert-body'><strong>" + esc(a.title) + "</strong>" + esc(a.message || "") +
            "<div class='alert-time'>" + esc(a.district_name || "") + " · " + esc((a.issued_at || "").slice(0, 10)) + "</div></div></div>";
        }).join("")
      : "<p class='muted'>No active alerts.</p>");

    var preds = data.latest_predictions || [];
    setHtml("dsPredictions", preds.length
      ? "<table class='data'><tr><th>District</th><th>Probability</th><th>Level</th><th>Model</th></tr>" +
        preds.map(function (p) {
          return "<tr><td>" + esc(p.district_name) + "</td><td>" + Math.round(p.probability * 100) + "%</td>" +
            "<td><span class='badge badge-" + String(p.risk_level).toLowerCase() + "'>" + esc(p.risk_level) + "</span></td>" +
            "<td><small>" + esc(p.model_version || "") + "</small></td></tr>";
        }).join("") + "</table>"
      : "<p class='muted'>No predictions yet.</p>");

    var ro = data.resource_overview || {};
    var sh = ro.shelters || {};
    var ib = ro.infrastructure_by_type || {};
    var ab = ro.allocations_by_status || {};
    var resHtml = "<table class='data'>" +
      "<tr><td>Emergency shelters</td><td><strong>" + (sh.count || 0) + "</strong> (capacity " + (sh.total_capacity || 0) + ")</td></tr>" +
      Object.keys(ib).map(function (t) {
        return "<tr><td>" + esc(INFRA_LABEL[t] || t) + "s</td><td><strong>" + ib[t] + "</strong></td></tr>";
      }).join("") +
      Object.keys(ab).map(function (s) {
        return "<tr><td>Allocations — " + esc(s) + "</td><td><strong>" + ab[s] + "</strong></td></tr>";
      }).join("") + "</table>" +
      (ro.sample_data_warning ? "<p class='muted' style='font-size:12px;color:#a00;'>Infrastructure locations are sample data — replace with authoritative registries before operational use.</p>" : "");
    setHtml("dsResources", resHtml);

    var hot = data.vulnerability_hotspots || [];
    setHtml("dsHotspots", hot.length
      ? "<table class='data'><tr><th>District</th><th>Vulnerability</th><th>Density</th><th>Priority</th></tr>" +
        hot.map(function (h) {
          return "<tr><td>" + esc(h.district_name) + "</td><td>" + h.vulnerability_index + "</td><td>" + h.population_density + "</td>" +
            "<td><span class='badge badge-" + h.priority.toLowerCase() + "'>" + h.priority + "</span></td></tr>";
        }).join("") + "</table>"
      : "<p class='muted'>No hotspots identified.</p>");

    var allocPanel = document.getElementById("dsAllocPanel");
    if (allocPanel) {
      if (data.allocations && state.role === "authority") {
        allocPanel.style.display = "";
        var al = data.allocations;
        setHtml("dsAllocations", al.length
          ? "<table class='data'><tr><th>District</th><th>Resource</th><th>Qty</th><th>Status</th><th>Notes</th></tr>" +
            al.map(function (a) {
              return "<tr><td>" + esc(a.district_name || "") + "</td><td>" + esc(a.resource_type) + "</td><td>" + a.quantity +
                "</td><td>" + esc(a.status) + "</td><td><small>" + esc(a.notes || "") + "</small></td></tr>";
            }).join("") + "</table>"
          : "<p class='muted'>No allocations recorded.</p>");
      } else {
        allocPanel.style.display = "none";
      }
    }
  }

  function sevClass(sev) {
    sev = String(sev || "").toLowerCase();
    if (sev === "emergency" || sev === "high" || sev === "warning") return "high";
    if (sev === "watch" || sev === "medium") return "medium";
    return "low";
  }

  function setHtml(id, html) {
    var el = document.getElementById(id);
    if (el) el.innerHTML = html;
  }

  function svgBars(elId, labels, values, color) {
    var el = document.getElementById(elId);
    if (!el) return;
    var max = Math.max.apply(null, values.concat([1]));
    var W = 680, H = 230, padL = 36, padB = 46, padT = 12;
    var bw = (W - padL - 10) / values.length;
    var s = "<svg viewBox='0 0 " + W + " " + H + "' style='width:100%;height:auto;' role='img'>";
    values.forEach(function (v, i) {
      var h = (H - padT - padB) * v / max;
      var x = padL + i * bw + 2, y = H - padB - h;
      s += "<rect x='" + x.toFixed(1) + "' y='" + y.toFixed(1) + "' width='" + Math.max(bw - 5, 2).toFixed(1) +
        "' height='" + Math.max(h, 1).toFixed(1) + "' fill='" + color + "' rx='2'>" +
        "<title>" + esc(labels[i]) + ": " + v + "</title></rect>";
      var cx = (x + bw / 2).toFixed(1);
      s += "<text x='" + cx + "' y='" + (H - 12) + "' font-size='10' text-anchor='end' transform='rotate(-40 " + cx + " " + (H - 12) + ")'>" + esc(labels[i]) + "</text>";
    });
    s += "<line x1='" + padL + "' y1='" + (H - padB) + "' x2='" + (W - 6) + "' y2='" + (H - padB) + "' stroke='#999'/>";
    s += "<text x='4' y='" + (H - padB) + "' font-size='10'>" + max + "</text>";
    s += "<text x='4' y='14' font-size='10'>0</text>";
    s += "</svg>";
    el.innerHTML = s;
  }

  function renderTrends(trends) {
    // Aggregate year-wise counts across districts.
    var yearTotals = {};
    (trends.year_wise || []).forEach(function (d) {
      (d.yearly || []).forEach(function (y) {
        yearTotals[y.year] = (yearTotals[y.year] || 0) + y.events;
      });
    });
    var years = Object.keys(yearTotals).map(Number).sort(function (a, b) { return a - b; });
    if (!years.length) {
      setHtml("chartYearly", "<p class='muted'>No trend data available.</p>");
    } else {
      svgBars("chartYearly", years.map(String), years.map(function (y) { return yearTotals[y]; }), "#E8641B");
    }
    var seasonal = trends.seasonal_pattern || [];
    var sLabels = [], sVals = [];
    for (var m = 1; m <= 12; m++) {
      var hit = null;
      seasonal.forEach(function (sp) { if (sp.month === m) hit = sp; });
      sLabels.push(MONTHS[m - 1]);
      sVals.push(hit ? hit.events : 0);
    }
    svgBars("chartSeasonal", sLabels, sVals, "#1A6FB5");
  }

  async function loadDecisionPage() {
    var client = api();
    var data = null;
    if (client && state.live) {
      try {
        var r = await client.getDecisionSummary();
        if (r.ok && r.data) data = r.data;
      } catch (e) { /* demo fallback */ }
    }
    if (!data) data = DEMO_DECISION.summary;
    state.decision = data;
    renderDecisionSummary(data);

    var trends = null;
    if (client && state.live) {
      try {
        var t = await client.getTrends();
        if (t.ok && t.data) trends = t.data;
      } catch (e) { /* demo fallback */ }
    }
    if (!trends) trends = DEMO_DECISION.trends;
    renderTrends(trends);
  }

  /* ---------- Pre-fill predictions history table ---------- */
  function seedPredictions() {
    var tbody = document.getElementById("predictionsBody");
    if (!tbody || tbody.rows.length) return;
    var seed = [
      ["Dadu", "82%", "HIGH", "2026-09-20"],
      ["Larkana", "78%", "HIGH", "2026-09-20"],
      ["Thatta", "75%", "HIGH", "2026-09-19"],
      ["Jacobabad", "74%", "HIGH", "2026-09-19"],
      ["Sukkur", "55%", "MEDIUM", "2026-09-18"],
      ["Hyderabad", "52%", "MEDIUM", "2026-09-18"],
      ["Badin", "48%", "MEDIUM", "2026-09-17"],
      ["Shikarpur", "45%", "MEDIUM", "2026-09-17"]
    ];
    seed.forEach(function (s, i) {
      var row = document.createElement("tr");
      row.innerHTML = "<td>" + (i + 1) + "</td><td>" + s[0] + "</td><td>" + s[1] + "</td>" +
        "<td><span class='badge badge-" + s[2].toLowerCase() + "'>" + s[2] + "</span></td><td>" + s[3] + "</td>";
      tbody.appendChild(row);
    });
  }
  seedPredictions();

  /* ---------- Alert Center (authority) ---------- */
  function escHtml(t) {
    return String(t == null ? "" : t).replace(/[&<>"']/g, function (c) {
      return { "&": "&amp;", "<": "&lt;", ">": "&gt;", "\"": "&quot;", "'": "&#39;" }[c];
    });
  }

  async function loadAlertCenterPage() {
    await Promise.all([loadReportsQueue(), loadAlertHistory()]);
    var form = document.getElementById("alertForm");
    if (form && !form.dataset.bound) {
      form.dataset.bound = "1";
      form.addEventListener("submit", submitAlertForm);
    }
    var reloadBtn = document.getElementById("reloadReportsBtn");
    if (reloadBtn && !reloadBtn.dataset.bound) {
      reloadBtn.dataset.bound = "1";
      reloadBtn.addEventListener("click", loadReportsQueue);
    }
    var filt = document.getElementById("reportStatusFilter");
    if (filt && !filt.dataset.bound) {
      filt.dataset.bound = "1";
      filt.addEventListener("change", loadReportsQueue);
    }
  }
  window.loadAlertCenterPage = loadAlertCenterPage;

  async function loadReportsQueue() {
    var body = document.getElementById("reportsBody");
    var count = document.getElementById("reportQueueCount");
    if (!body) return;
    body.innerHTML = "<tr><td colspan='5'>Loading…</td></tr>";
    var status = document.getElementById("reportStatusFilter").value;
    var r = await api().getReports(status || null);
    if (!r.ok) { body.innerHTML = "<tr><td colspan='5'>Failed to load (" + escHtml(r.error) + ")</td></tr>"; return; }
    var rows = r.data || [];
    if (count) count.textContent = "(" + rows.length + ")";
    if (!rows.length) { body.innerHTML = "<tr><td colspan='5'>No reports in this queue.</td></tr>"; return; }
    body.innerHTML = "";
    rows.forEach(function (rep) {
      var tr = document.createElement("tr");
      var actions = "";
      if (rep.status === "pending") {
        actions = "<button class='btn-mini ok' data-act='verified'>Verify</button>" +
                  "<button class='btn-mini no' data-act='rejected'>Reject</button>";
      } else if (rep.status === "verified") {
        actions = "<button class='btn-mini done' data-act='resolved'>Resolve</button>";
      }
      tr.innerHTML = "<td>" + escHtml(rep.district_name) + "</td>" +
        "<td>" + escHtml(rep.category || "—") + "</td>" +
        "<td>" + escHtml(rep.severity) + "</td>" +
        "<td><span class='badge badge-" + escHtml(rep.status) + "'>" + escHtml(rep.status) + "</span></td>" +
        "<td><div class='row-actions'>" + actions + "</div></td>";
      tr.querySelectorAll("button[data-act]").forEach(function (btn) {
        btn.addEventListener("click", async function () {
          var note = rep.status === "pending" && btn.dataset.act === "rejected"
            ? prompt("Rejection reason (optional):") : null;
          var vr = await api().verifyReport(rep.id, btn.dataset.act, note);
          if (vr.ok) { loadReportsQueue(); } else { alert("Failed: " + vr.error); }
        });
      });
      body.appendChild(tr);
    });
  }

  async function loadAlertHistory() {
    var body = document.getElementById("alertHistoryBody");
    if (!body) return;
    body.innerHTML = "<tr><td colspan='6'>Loading…</td></tr>";
    var r = await api().getAlerts(false);
    if (!r.ok) { body.innerHTML = "<tr><td colspan='6'>Failed to load (" + escHtml(r.error) + ")</td></tr>"; return; }
    var items = (r.data && r.data.items) || r.data || [];
    if (!items.length) { body.innerHTML = "<tr><td colspan='6'>No alerts issued yet.</td></tr>"; return; }
    body.innerHTML = "";
    items.slice(0, 20).forEach(function (a) {
      var tr = document.createElement("tr");
      tr.innerHTML = "<td>" + escHtml(a.title) + "</td>" +
        "<td><span class='badge badge-" + escHtml(a.severity) + "'>" + escHtml(a.severity) + "</span></td>" +
        "<td>" + escHtml(a.model_version || "—") + "</td>" +
        "<td>" + (a.probability != null ? Math.round(a.probability * 100) + "%" : "—") + "</td>" +
        "<td>" + (a.is_active ? "yes" : "no") + "</td>" +
        "<td>" + escHtml((a.issued_at || "").slice(0, 16).replace("T", " ")) + "</td>";
      body.appendChild(tr);
    });
  }

  async function submitAlertForm(e) {
    e.preventDefault();
    var msg = document.getElementById("alertFormMsg");
    msg.textContent = ""; msg.className = "form-msg";
    var r = await api().createAlert({
      district_name: document.getElementById("alertDistrict").value.trim(),
      title: document.getElementById("alertTitle").value.trim(),
      message: document.getElementById("alertMessage").value.trim(),
      severity: document.getElementById("alertSeverity").value
    });
    if (r.ok) {
      msg.textContent = "Alert issued."; msg.className = "form-msg ok";
      document.getElementById("alertForm").reset();
      loadAlertHistory();
    } else {
      msg.textContent = "Failed: " + r.error; msg.className = "form-msg err";
    }
  }
})();
