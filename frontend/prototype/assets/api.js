/* Flood Risk DSS - live API client.
 * Works over file:// with no build step. All calls are defensive: any network
 * failure resolves to { ok:false, error } so the prototype can fall back to
 * its built-in demo data. JWTs are kept in localStorage.
 */
(function () {
  "use strict";

  var DEFAULT_BASE = "http://localhost:8000/api/v1";

  function getBase() {
    try {
      return localStorage.getItem("FR_DSS_API_BASE") || DEFAULT_BASE;
    } catch (e) { return DEFAULT_BASE; }
  }
  function setBase(url) {
    try { localStorage.setItem("FR_DSS_API_BASE", url); } catch (e) {}
  }

  function getTokens() {
    try {
      return {
        access: localStorage.getItem("FR_DSS_ACCESS") || null,
        refresh: localStorage.getItem("FR_DSS_REFRESH") || null,
        role: localStorage.getItem("FR_DSS_ROLE") || null
      };
    } catch (e) { return { access: null, refresh: null, role: null }; }
  }
  function saveTokens(access, refresh, role) {
    try {
      if (access) localStorage.setItem("FR_DSS_ACCESS", access);
      if (refresh) localStorage.setItem("FR_DSS_REFRESH", refresh);
      if (role) localStorage.setItem("FR_DSS_ROLE", role);
    } catch (e) {}
  }
  function clearTokens() {
    try {
      localStorage.removeItem("FR_DSS_ACCESS");
      localStorage.removeItem("FR_DSS_REFRESH");
      localStorage.removeItem("FR_DSS_ROLE");
    } catch (e) {}
  }

  async function raw(path, method, body, token) {
    var headers = { "Content-Type": "application/json" };
    if (token) headers["Authorization"] = "Bearer " + token;
    var res = await fetch(getBase() + path, {
      method: method || "GET",
      headers: headers,
      body: body ? JSON.stringify(body) : undefined
    });
    var data = null;
    try { data = await res.json(); } catch (e) {}
    return { status: res.status, data: data };
  }

  /* One authenticated request with a single automatic token refresh on 401. */
  async function request(path, opts) {
    opts = opts || {};
    var method = opts.method || "GET";
    var tokens = getTokens();
    try {
      var r = await raw(path, method, opts.body, opts.auth === false ? null : tokens.access);
      if (r.status === 401 && opts.auth !== false && tokens.refresh && !opts._retried) {
        var ref = await raw("/auth/refresh", "POST", { refresh_token: tokens.refresh }, null);
        if (ref.status === 200 && ref.data && ref.data.access_token) {
          saveTokens(ref.data.access_token, ref.data.refresh_token || tokens.refresh, ref.data.role || tokens.role);
          opts._retried = true;
          return request(path, opts);
        }
        clearTokens();
        return { ok: false, status: 401, error: "unauthorized" };
      }
      if (r.status >= 200 && r.status < 300) return { ok: true, status: r.status, data: r.data };
      var detail = (r.data && (r.data.detail || r.data.message)) || ("HTTP " + r.status);
      return { ok: false, status: r.status, error: detail };
    } catch (e) {
      return { ok: false, status: 0, error: "network" };
    }
  }

  var api = {
    getBase: getBase,
    setBase: setBase,
    tokens: getTokens,
    clearTokens: clearTokens,

    async checkOnline() {
      try {
        var res = await fetch(getBase().replace(/\/api\/v1$/, "") + "/health", { method: "GET" });
        return res.ok;
      } catch (e) { return false; }
    },

    async login(email, password) {
      var r = await request("/auth/login", { method: "POST", body: { email: email, password: password }, auth: false });
      if (r.ok) saveTokens(r.data.access_token, r.data.refresh_token, r.data.role);
      return r;
    },
    async register(name, email, password, role, location_name) {
      var r = await request("/auth/register", {
        method: "POST",
        body: { name: name, email: email, password: password, role: role || "public", location_name: location_name || null },
        auth: false
      });
      if (r.ok) saveTokens(r.data.access_token, r.data.refresh_token, r.data.role);
      return r;
    },
    async logout() { clearTokens(); return { ok: true }; },

    /* Dashboard */
    getSummary: function () { return request("/dashboard/summary"); },
    getRainfallTrends: function () { return request("/dashboard/rainfall-trends"); },
    getFloodFrequency: function () { return request("/dashboard/flood-frequency"); },
    getRiskDistribution: function () { return request("/dashboard/risk-distribution"); },

    /* GIS + risk */
    getRiskLayers: function () { return request("/gis/risk-layers"); },
    getRiskLayer: function () { return request("/gis/risk-layer"); },
    getHistoricalFloods: function (params) {
      var q = [];
      if (params) {
        if (params.district_name) q.push("district_name=" + encodeURIComponent(params.district_name));
        if (params.from_year) q.push("from_year=" + encodeURIComponent(params.from_year));
        if (params.to_year) q.push("to_year=" + encodeURIComponent(params.to_year));
      }
      return request("/gis/historical-floods" + (q.length ? "?" + q.join("&") : ""));
    },
    getVulnerabilityMap: function () { return request("/gis/vulnerability-map"); },
    getInfrastructure: function (type, district) {
      var q = [];
      if (type) q.push("type=" + encodeURIComponent(type));
      if (district) q.push("district_name=" + encodeURIComponent(district));
      return request("/gis/infrastructure" + (q.length ? "?" + q.join("&") : ""));
    },
    getBoundaries: function () { return request("/gis/boundaries"); },
    getShelters: function () { return request("/gis/shelters"); },
    getDistricts: function () { return request("/gis/districts"); },

    /* Decision support */
    getDecisionSummary: function () { return request("/decision-support/summary"); },
    getTrends: function () { return request("/decision-support/trends"); },
    getResources: function () { return request("/decision-support/resources"); },
    getAlerts: function (activeOnly) {
      return request("/alerts" + (activeOnly ? "?active_only=true" : ""));
    },
    createAlert: function (payload) {
      return request("/alerts", { method: "POST", body: payload });
    },
    getReports: function (status, category) {
      var q = [];
      if (status) q.push("status=" + encodeURIComponent(status));
      if (category) q.push("category=" + encodeURIComponent(category));
      return request("/admin/reports" + (q.length ? "?" + q.join("&") : ""));
    },
    verifyReport: function (reportId, status, note) {
      return request("/admin/reports/" + reportId + "/verify",
        { method: "PATCH", body: { status: status, note: note || null } });
    },
    predictRisk: function (input, model) {
      var path = "/risk/predict" + (model ? ("?model=" + encodeURIComponent(model)) : "");
      return request(path, { method: "POST", body: input });
    }
  };

  window.FloodDSS = api;
})();
