// ===================================================================
// NE-SHIELD: Command Center JavaScript Client
// ===================================================================

const API_BASE = window.location.origin + '/api';
const WS_URL = (window.location.protocol === 'https:' ? 'wss://' : 'ws://') + window.location.host + '/ws/live';

let currentTab = 'dashboard';
let operationalMode = 'LIVE'; // 'LIVE' or 'DEMO'
let selectedState = '';
let selectedRisk = '';
let wsClient = null;
let miniMap = null;
let mainGisMap = null;
let gisLayerGroups = {};
let rainfallChartInstance = null;
let offlineQueue = [];

// Default credentials for persona testing
const PERSONA_TOKENS = {
  admin: null,
  authority: null,
  officer: null,
  analyst: null,
  citizen: null
};

let activeAuthToken = null;

async function initAuthToken() {
  try {
    const res = await fetch(`${API_BASE}/auth/login`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ email: 'admin@ne-shield.gov.in', password: 'Admin@123' })
    });
    if (res.ok) {
      const data = await res.json();
      activeAuthToken = data.access_token;
      PERSONA_TOKENS.admin = data.access_token;
    }
  } catch (e) {
    console.warn('Auth token auto-init notice:', e.message);
  }
}

function getAuthHeaders() {
  const headers = { 'Content-Type': 'application/json' };
  if (activeAuthToken) {
    headers['Authorization'] = `Bearer ${activeAuthToken}`;
  }
  return headers;
}

// 1. Initialization
document.addEventListener('DOMContentLoaded', async () => {
  lucide.createIcons();
  startIstClock();
  initWebSocket();
  initMiniMap();
  initMainGisMap();
  loadOfflineQueue();
  await initAuthToken();
  refreshAllData();
  fetchSatelliteTelemetry();

  // Periodic polling fallback
  setInterval(() => {
    refreshAllData(true);
  }, 30000);
});

// 2. Real-time IST Clock
function startIstClock() {
  function updateClock() {
    const now = new Date();
    // Format to Indian Standard Time (UTC+5:30)
    const options = {
      timeZone: 'Asia/Kolkata',
      hour12: false,
      year: 'numeric',
      month: 'short',
      day: 'numeric',
      hour: '2-digit',
      minute: '2-digit',
      second: '2-digit'
    };
    const istString = now.toLocaleString('en-IN', options) + ' IST';
    const clockEl = document.getElementById('live-ist-clock');
    if (clockEl) clockEl.textContent = istString;
  }
  updateClock();
  setInterval(updateClock, 1000);
}

// 3. WebSocket Real-time Telemetry
function initWebSocket() {
  const wsStatusEl = document.getElementById('ws-status');
  const wsIndicatorEl = document.getElementById('ws-indicator');

  try {
    wsClient = new WebSocket(WS_URL);

    wsClient.onopen = () => {
      wsStatusEl.textContent = 'LIVE TELEMETRY';
      wsIndicatorEl.className = 'live-pulse';
    };

    wsClient.onmessage = (event) => {
      try {
        const msg = JSON.parse(event.data);
        if (msg.type === 'ALERT') {
          showFloatingAlert(msg.title, msg.message);
          refreshAllData(true);
        }
      } catch (err) {
        console.error('WS message parse error:', err);
      }
    };

    wsClient.onclose = () => {
      wsStatusEl.textContent = 'RECONNECTING';
      wsIndicatorEl.className = 'w-2.5 h-2.5 rounded-full bg-amber-500 animate-pulse';
      setTimeout(initWebSocket, 5000);
    };

    wsClient.onerror = () => {
      wsStatusEl.textContent = 'OFFLINE';
      wsIndicatorEl.className = 'w-2.5 h-2.5 rounded-full bg-red-500';
    };
  } catch (e) {
    wsStatusEl.textContent = 'OFFLINE';
  }
}

// 4. Tab Navigation
function switchTab(tabId) {
  currentTab = tabId;
  document.querySelectorAll('.tab-view').forEach(el => el.classList.add('hidden'));
  document.querySelectorAll('.tab-view').forEach(el => el.classList.remove('block'));

  const activeView = document.getElementById(`view-${tabId}`);
  if (activeView) {
    activeView.classList.remove('hidden');
    activeView.classList.add('block');
  }

  document.querySelectorAll('.nav-tab').forEach(btn => {
    btn.classList.toggle('active', btn.getAttribute('data-tab') === tabId);
  });

  // Re-invalidate map sizes when switching tabs
  if (tabId === 'live-map' && mainGisMap) {
    setTimeout(() => { mainGisMap.invalidateSize(); }, 200);
  }
  if (tabId === 'dashboard' && miniMap) {
    setTimeout(() => { miniMap.invalidateSize(); }, 200);
  }
  if (tabId === 'rainfall') {
    setTimeout(renderRainfallChart, 200);
  }

  lucide.createIcons();
}

// 5. Operational Mode Toggle: LIVE vs DEMO
function toggleOperationalMode() {
  operationalMode = operationalMode === 'LIVE' ? 'DEMO' : 'LIVE';
  const labelEl = document.getElementById('mode-label');
  const btnEl = document.getElementById('mode-toggle-btn');
  const pulseEl = document.getElementById('mode-pulse');

  if (operationalMode === 'LIVE') {
    labelEl.textContent = 'LIVE MODE';
    btnEl.className = 'flex items-center gap-1.5 text-xs px-2.5 py-0.5 rounded-full font-mono font-bold bg-emerald-950/80 text-emerald-400 border border-emerald-600/60 hover:bg-emerald-900 transition';
    pulseEl.className = 'live-pulse';
  } else {
    labelEl.textContent = 'DEMO MODE';
    btnEl.className = 'flex items-center gap-1.5 text-xs px-2.5 py-0.5 rounded-full font-mono font-bold bg-amber-950/80 text-amber-400 border border-amber-600/60 hover:bg-amber-900 transition';
    pulseEl.className = 'w-2.5 h-2.5 rounded-full bg-amber-400';
  }

  refreshAllData();
}

// 6. Refresh Data from Real APIs
async function refreshAllData(silent = false) {
  const icon = document.getElementById('refresh-icon');
  if (icon && !silent) icon.classList.add('animate-spin');

  try {
    await Promise.all([
      fetchDashboardSummary(),
      fetchGisLayers(),
      fetchRiskPredictions(),
      fetchWeatherObservations(),
      fetchRainfallData(),
      fetchOfficialWarnings(),
      fetchCitizenReports(),
      fetchFieldOperations(),
      fetchRoadNetwork(),
      fetchModelStatus(),
      fetchDataSources(),
      fetchAuditLogs(),
      fetchSatelliteTelemetry()
    ]);
  } catch (err) {
    console.error('Data refresh error:', err);
  } finally {
    if (icon) setTimeout(() => icon.classList.remove('animate-spin'), 600);
    lucide.createIcons();
  }
}

// 7. Dashboard Summary & KPI Cards
async function fetchDashboardSummary() {
  try {
    const res = await fetch(`${API_BASE}/dashboard/summary`);
    const data = await res.json();

    document.getElementById('kpi-risk-zones').textContent = data.kpis.active_risk_zones;
    document.getElementById('kpi-high-risk').textContent = data.kpis.high_risk_locations;
    document.getElementById('kpi-official-warnings').textContent = data.kpis.official_warnings;
    document.getElementById('kpi-rainfall-alerts').textContent = data.kpis.rainfall_alerts;
    document.getElementById('kpi-field-reports').textContent = data.kpis.pending_field_reports;
    document.getElementById('kpi-sources-online').textContent = data.kpis.data_sources_online;

    document.getElementById('active-model-tag').textContent = data.active_model_version;

    // Render Critical Escarpments list
    const critContainer = document.getElementById('top-critical-list');
    critContainer.innerHTML = '';
    if (!data.top_critical_locations || data.top_critical_locations.length === 0) {
      critContainer.innerHTML = '<div class="text-xs text-slate-500 py-3 text-center">No critical slopes currently active.</div>';
    } else {
      data.top_critical_locations.forEach(loc => {
        const badgeClass = loc.risk_class === 'CRITICAL' ? 'badge-critical' : 'badge-high';
        critContainer.innerHTML += `
          <div class="p-2.5 rounded bg-slate-900/80 border border-slate-800 flex items-center justify-between text-xs hover:border-cyan-800/80 transition cursor-pointer" onclick="focusMapLocation(${loc.location_id})">
            <div>
              <div class="font-bold text-slate-200">${loc.location_name}</div>
              <div class="text-[11px] text-slate-400 mt-0.5">Slope: ${loc.slope_deg}° | Elev: ${loc.elevation_m}m</div>
            </div>
            <div class="text-right">
              <span class="px-2 py-0.5 rounded text-[10px] font-mono font-bold ${badgeClass}">${loc.risk_class} (${(loc.risk_probability*100).toFixed(0)}%)</span>
              <div class="text-[10px] text-slate-500 font-mono mt-0.5">${loc.state_id}</div>
            </div>
          </div>
        `;
      });
    }

    // Render Warnings list
    const warnContainer = document.getElementById('dashboard-warnings-list');
    warnContainer.innerHTML = '';
    if (!data.active_warnings_feed || data.active_warnings_feed.length === 0) {
      warnContainer.innerHTML = '<div class="text-xs text-slate-500 py-3 text-center">No active official government alerts.</div>';
    } else {
      data.active_warnings_feed.forEach(w => {
        warnContainer.innerHTML += `
          <div class="p-2.5 rounded bg-slate-900/80 border border-amber-900/40 text-xs">
            <div class="flex items-center justify-between text-[10px] text-amber-400 font-mono font-bold mb-1">
              <span>${w.source} OFFICIAL BULLETIN</span>
              <span>${w.severity}</span>
            </div>
            <div class="font-semibold text-slate-200 line-clamp-1">${w.headline}</div>
            <div class="text-[10px] text-slate-400 mt-1 font-mono">Valid until: ${w.valid_until_ist}</div>
          </div>
        `;
      });
    }

  } catch (err) {
    console.error('Error fetching dashboard summary:', err);
  }
}

// 8. GIS Maps Initialization - Clean Free Tile Providers (No API Key Required)
const ESRI_DARK_BASE = 'https://server.arcgisonline.com/ArcGIS/rest/services/Canvas/World_Dark_Gray_Base/MapServer/tile/{z}/{y}/{x}';
const ESRI_DARK_LABELS = 'https://server.arcgisonline.com/ArcGIS/rest/services/Canvas/World_Dark_Gray_Reference/MapServer/tile/{z}/{y}/{x}';
const ESRI_SATELLITE = 'https://server.arcgisonline.com/ArcGIS/rest/services/World_Imagery/MapServer/tile/{z}/{y}/{x}';
const ESRI_TOPO = 'https://server.arcgisonline.com/ArcGIS/rest/services/World_Topo_Map/MapServer/tile/{z}/{y}/{x}';
const OSM_TILES = 'https://tile.openstreetmap.org/{z}/{x}/{y}.png';

let miniMapGroup = null;

function initMiniMap() {
  const container = document.getElementById('dashboard-mini-map');
  if (!container || miniMap) return;

  miniMap = L.map('dashboard-mini-map', {
    center: [26.20, 92.93],
    zoom: 7,
    zoomControl: true,
    attributionControl: false
  });

  // Base Dark Canvas (No watermark, No API key)
  L.tileLayer(ESRI_DARK_BASE, {
    maxZoom: 16,
    subdomains: ['server', 'services']
  }).addTo(miniMap);

  // High contrast reference labels & boundaries
  L.tileLayer(ESRI_DARK_LABELS, {
    maxZoom: 16,
    subdomains: ['server', 'services'],
    opacity: 0.85
  }).addTo(miniMap);

  miniMapGroup = L.layerGroup().addTo(miniMap);
}

function initMainGisMap() {
  const container = document.getElementById('main-gis-map');
  if (!container || mainGisMap) return;

  mainGisMap = L.map('main-gis-map', {
    center: [26.20, 92.93],
    zoom: 7,
    zoomControl: true
  });

  // Default: Dark Command Center Canvas (Official ESRI GIS)
  const darkBaseLayer = L.tileLayer(ESRI_DARK_BASE, { maxZoom: 16 });
  const darkLabelsLayer = L.tileLayer(ESRI_DARK_LABELS, { maxZoom: 16, opacity: 0.9 });
  const darkCanvasGroup = L.layerGroup([darkBaseLayer, darkLabelsLayer]).addTo(mainGisMap);

  // Satellite Imagery Layer
  const satelliteLayer = L.tileLayer(ESRI_SATELLITE, {
    maxZoom: 18,
    attribution: '&copy; Esri, Maxar, Earthstar Geographics'
  });

  // Mountain Topographic Terrain Layer
  const topoLayer = L.tileLayer(ESRI_TOPO, {
    maxZoom: 18,
    attribution: '&copy; Esri & USGS Topo'
  });

  // OpenStreetMap Layer
  const osmLayer = L.tileLayer(OSM_TILES, {
    maxZoom: 19,
    attribution: '&copy; OpenStreetMap contributors'
  });

  const baseMaps = {
    "Dark Command Canvas (Default)": darkCanvasGroup,
    "Satellite Imagery": satelliteLayer,
    "Himalayan Terrain Topo": topoLayer,
    "OpenStreetMap": osmLayer
  };

  gisLayerGroups = {
    hazards: L.layerGroup().addTo(mainGisMap),
    zones: L.layerGroup().addTo(mainGisMap),
    roads: L.layerGroup().addTo(mainGisMap),
    historical: L.layerGroup().addTo(mainGisMap),
    reports: L.layerGroup().addTo(mainGisMap)
  };

  const overlayMaps = {
    "Hazard Risk Escarpments": gisLayerGroups.hazards,
    "Active Risk Zones": gisLayerGroups.zones,
    "Highway Connectivity Network": gisLayerGroups.roads,
    "Historical Landslide Catalog": gisLayerGroups.historical,
    "Citizen / Field Reports": gisLayerGroups.reports
  };

  L.control.layers(baseMaps, overlayMaps, { position: 'topright', collapsed: true }).addTo(mainGisMap);
}

function toggleMapLayer(layerName, visible) {
  if (!gisLayerGroups[layerName] || !mainGisMap) return;
  if (visible) {
    mainGisMap.addLayer(gisLayerGroups[layerName]);
  } else {
    mainGisMap.removeLayer(gisLayerGroups[layerName]);
  }
}

async function fetchGisLayers() {
  try {
    const url = selectedState ? `${API_BASE}/map/layers?state_id=${selectedState}` : `${API_BASE}/map/layers`;
    const res = await fetch(url);
    const layers = await res.json();

    // Clear existing
    if (miniMapGroup) miniMapGroup.clearLayers();
    if (gisLayerGroups.hazards) gisLayerGroups.hazards.clearLayers();
    if (gisLayerGroups.zones) gisLayerGroups.zones.clearLayers();
    if (gisLayerGroups.roads) gisLayerGroups.roads.clearLayers();
    if (gisLayerGroups.historical) gisLayerGroups.historical.clearLayers();
    if (gisLayerGroups.reports) gisLayerGroups.reports.clearLayers();

    // 1. Hazards Points
    if (layers.hazard_locations && layers.hazard_locations.features) {
      layers.hazard_locations.features.forEach(f => {
        const props = f.properties;
        const coords = f.geometry.coordinates;
        
        let color = '#10b981'; // LOW
        let radius = 6;
        if (props.risk_class === 'CRITICAL') { color = '#e63946'; radius = 10; }
        else if (props.risk_class === 'HIGH') { color = '#fb8500'; radius = 8; }
        else if (props.risk_class === 'MODERATE') { color = '#ffb703'; radius = 7; }

        const marker = L.circleMarker([coords[1], coords[0]], {
          radius: radius,
          fillColor: color,
          color: '#ffffff',
          weight: 1.5,
          opacity: 0.9,
          fillOpacity: 0.85
        });

        const popupHtml = `
          <div class="text-xs space-y-1.5 p-1 min-w-[200px]">
            <div class="font-bold text-sm text-cyan-400">${props.name}</div>
            <div class="text-[11px] text-slate-300">District: ${props.district_name} (${props.state_id})</div>
            <div class="flex items-center justify-between pt-1 border-t border-slate-700">
              <span class="text-slate-400">Risk Probability:</span>
              <strong class="font-mono text-cyan-300">${(props.risk_probability*100).toFixed(1)}%</strong>
            </div>
            <div class="flex items-center justify-between">
              <span class="text-slate-400">Slope Angle:</span>
              <strong class="font-mono text-slate-200">${props.slope_deg}°</strong>
            </div>
            <div class="flex items-center justify-between">
              <span class="text-slate-400">Elevation:</span>
              <strong class="font-mono text-slate-200">${props.elevation_m}m</strong>
            </div>
            ${props.thresholds_exceeded && props.thresholds_exceeded.length ? `
              <div class="p-1 rounded bg-red-950/70 border border-red-800/80 text-[10px] text-red-300">
                ${props.thresholds_exceeded.join('<br>')}
              </div>
            ` : ''}
            <div class="text-[10px] text-slate-400 pt-1 font-mono border-t border-slate-800">
              Evaluated: ${props.last_update_ist}
            </div>
          </div>
        `;
        marker.bindPopup(popupHtml);

        if (gisLayerGroups.hazards) gisLayerGroups.hazards.addLayer(marker);

        // Also add to mini map if exists
        if (miniMapGroup) {
          L.circleMarker([coords[1], coords[0]], {
            radius: radius - 1,
            fillColor: color,
            color: '#fff',
            weight: 1,
            fillOpacity: 0.8
          }).bindPopup(popupHtml).addTo(miniMapGroup);
        }
      });
    }

    // 2. Risk Zones Polygons
    if (layers.risk_zones && layers.risk_zones.features) {
      layers.risk_zones.features.forEach(f => {
        const poly = L.geoJSON(f, {
          style: {
            color: f.properties.risk_level === 'CRITICAL' ? '#e63946' : '#fb8500',
            weight: 2,
            dashArray: '4, 4',
            fillColor: f.properties.risk_level === 'CRITICAL' ? '#e63946' : '#fb8500',
            fillOpacity: 0.2
          }
        });
        poly.bindPopup(`
          <div class="text-xs p-1">
            <div class="font-bold text-red-400">${f.properties.name}</div>
            <div>Level: <strong>${f.properties.risk_level}</strong></div>
            <div>Area: ${f.properties.area_sqkm} sq.km</div>
            <div class="text-[10px] text-slate-400 mt-1 font-mono">Expires: ${f.properties.valid_until_ist}</div>
          </div>
        `);
        if (gisLayerGroups.zones) gisLayerGroups.zones.addLayer(poly);
      });
    }

    // 3. Roads
    if (layers.road_network && layers.road_network.features) {
      layers.road_network.features.forEach(f => {
        const st = f.properties.status;
        const color = st === 'BLOCKED' ? '#e63946' : st === 'PARTIALLY_BLOCKED' ? '#ffb703' : '#10b981';
        const line = L.geoJSON(f, {
          style: { color: color, weight: 4, opacity: 0.85 }
        });
        line.bindPopup(`
          <div class="text-xs p-1">
            <div class="font-bold text-slate-200">${f.properties.name}</div>
            <div>Status: <strong style="color:${color}">${st}</strong></div>
            ${f.properties.cause ? `<div>Cause: ${f.properties.cause}</div>` : ''}
            <div class="text-[10px] text-slate-400 mt-1 font-mono">Source: ${f.properties.source_attribution}</div>
          </div>
        `);
        if (gisLayerGroups.roads) gisLayerGroups.roads.addLayer(line);
      });
    }

    // 4. Historical Landslides
    if (layers.historical_landslides && layers.historical_landslides.features) {
      layers.historical_landslides.features.forEach(f => {
        const coords = f.geometry.coordinates;
        const marker = L.circleMarker([coords[1], coords[0]], {
          radius: 5,
          fillColor: '#9333ea',
          color: '#ffffff',
          weight: 1,
          fillOpacity: 0.8
        });
        marker.bindPopup(`
          <div class="text-xs p-1">
            <div class="font-bold text-purple-400">${f.properties.location_name}</div>
            <div>Date: ${f.properties.event_date}</div>
            <div>Trigger: ${f.properties.trigger_cause}</div>
            <div>Casualties: ${f.properties.casualties}</div>
            <div class="text-[10px] text-slate-400 mt-1 font-mono">Source: ${f.properties.source}</div>
          </div>
        `);
        if (gisLayerGroups.historical) gisLayerGroups.historical.addLayer(marker);
      });
    }

    // 5. Citizen Reports
    if (layers.incident_reports && layers.incident_reports.features) {
      layers.incident_reports.features.forEach(f => {
        const coords = f.geometry.coordinates;
        const marker = L.circleMarker([coords[1], coords[0]], {
          radius: 6,
          fillColor: '#00f2fe',
          color: '#ffffff',
          weight: 1,
          fillOpacity: 0.9
        });
        marker.bindPopup(`
          <div class="text-xs p-1">
            <div class="font-bold text-cyan-300">${f.properties.report_number}: ${f.properties.report_type}</div>
            <div>${f.properties.description}</div>
            <div>Status: <strong>${f.properties.status}</strong></div>
            <div class="text-[10px] text-slate-400 mt-1 font-mono">Reported: ${f.properties.submitted_at_ist}</div>
          </div>
        `);
        if (gisLayerGroups.reports) gisLayerGroups.reports.addLayer(marker);
      });
    }

  } catch (err) {
    console.error('Error fetching GIS layers:', err);
  }
}

// 9. AI Risk Predictions Tab
async function fetchRiskPredictions() {
  try {
    const url = selectedState ? `${API_BASE}/risk/current?state_id=${selectedState}` : `${API_BASE}/risk/current`;
    const res = await fetch(url);
    const data = await res.json();

    const tbody = document.getElementById('risk-table-body');
    tbody.innerHTML = '';

    if (!data.predictions || !data.predictions.length) {
      tbody.innerHTML = '<tr><td colspan="8" class="text-center py-6 text-slate-500">No hazard spots match active filter.</td></tr>';
      return;
    }

    data.predictions.forEach(p => {
      let badgeClass = 'badge-low';
      if (p.risk_class === 'CRITICAL') badgeClass = 'badge-critical';
      else if (p.risk_class === 'HIGH') badgeClass = 'badge-high';
      else if (p.risk_class === 'MODERATE') badgeClass = 'badge-moderate';

      tbody.innerHTML += `
        <tr class="hover:bg-slate-800/40 transition">
          <td class="py-3 px-4 font-bold text-slate-100">${p.location_name}</td>
          <td class="py-3 px-4 text-slate-400">${p.district_name}, ${p.state_id}</td>
          <td class="py-3 px-4 font-mono">${p.elevation_m}m / <strong class="text-cyan-400">${p.slope_deg}°</strong></td>
          <td class="py-3 px-4 text-slate-400">${p.geology_type || 'Sedimentary'}</td>
          <td class="py-3 px-4 font-mono font-bold text-sm text-cyan-300">${(p.risk_probability*100).toFixed(1)}%</td>
          <td class="py-3 px-4"><span class="px-2 py-0.5 rounded text-[11px] font-mono font-bold ${badgeClass}">${p.risk_class}</span></td>
          <td class="py-3 px-4 text-[11px] text-slate-300">${p.thresholds_exceeded && p.thresholds_exceeded.length ? p.thresholds_exceeded.join(', ') : 'Within stability envelope'}</td>
          <td class="py-3 px-4 font-mono text-[11px] text-slate-400">${p.prediction_time_ist}</td>
        </tr>
      `;
    });
  } catch (err) {
    console.error('Error fetching risk predictions:', err);
  }
}

// 10. IMD Weather Tab
async function fetchWeatherObservations() {
  try {
    const url = selectedState ? `${API_BASE}/weather/current?state_id=${selectedState}` : `${API_BASE}/weather/current`;
    const res = await fetch(url);
    const data = await res.json();

    const grid = document.getElementById('weather-cards-grid');
    grid.innerHTML = '';

    if (!data.observations || !data.observations.length) {
      grid.innerHTML = '<div class="col-span-3 text-center py-8 text-slate-500">No current IMD observations available for selected region.</div>';
      return;
    }

    data.observations.forEach(o => {
      grid.innerHTML += `
        <div class="glass-panel p-4 flex flex-col justify-between">
          <div>
            <div class="flex items-center justify-between text-xs text-slate-400 pb-2 border-b border-slate-800">
              <span class="font-bold text-slate-300">${o.location_name}</span>
              <span class="font-mono text-cyan-400">${o.state_id}</span>
            </div>
            
            <div class="mt-3 flex items-baseline justify-between">
              <div>
                <span class="text-3xl font-bold font-mono text-slate-100">${o.temperature_c !== null ? o.temperature_c + '°C' : 'N/A'}</span>
                <div class="text-xs text-slate-400 mt-0.5">${o.weather_condition || 'Scattered Clouds'}</div>
              </div>
              <div class="text-right text-xs font-mono space-y-1 text-slate-300">
                <div>Humidity: <strong class="text-cyan-300">${o.humidity_pct || '--'}%</strong></div>
                <div>Wind: <strong>${o.wind_speed_kmh || '--'} km/h</strong></div>
                <div>Pressure: <strong>${o.pressure_hpa || '--'} hPa</strong></div>
              </div>
            </div>
          </div>

          <div class="mt-4 pt-2.5 border-t border-slate-800/80 flex items-center justify-between text-[10px] text-slate-500 font-mono">
            <span>Source: <strong>${o.provenance.source_name}</strong></span>
            <span>Updated: ${o.provenance.observed_at_ist}</span>
          </div>
        </div>
      `;
    });
  } catch (err) {
    console.error('Error fetching weather:', err);
  }
}

// 11. Rainfall Analytics Tab
async function fetchRainfallData() {
  try {
    const url = selectedState ? `${API_BASE}/rainfall/latest?state_id=${selectedState}` : `${API_BASE}/rainfall/latest`;
    const res = await fetch(url);
    const data = await res.json();

    const tbody = document.getElementById('rainfall-table-body');
    tbody.innerHTML = '';

    if (!data.observations || !data.observations.length) {
      tbody.innerHTML = '<tr><td colspan="9" class="text-center py-6 text-slate-500">No rainfall observations available.</td></tr>';
      return;
    }

    const labels = [];
    const rfValues = [];

    data.observations.forEach(r => {
      let statusColor = 'text-emerald-400';
      if (r.status === 'EXTREME') statusColor = 'text-red-500 font-bold';
      else if (r.status === 'HEAVY') statusColor = 'text-orange-400 font-bold';
      else if (r.status === 'MODERATE') statusColor = 'text-amber-400';

      tbody.innerHTML += `
        <tr class="hover:bg-slate-800/40 transition">
          <td class="py-3 px-4 font-bold text-slate-100">${r.location_name}</td>
          <td class="py-3 px-4 text-slate-400">${r.district_name}</td>
          <td class="py-3 px-4">${r.rainfall_1h_mm || 0} mm</td>
          <td class="py-3 px-4">${r.rainfall_3h_mm || 0} mm</td>
          <td class="py-3 px-4">${r.rainfall_6h_mm || 0} mm</td>
          <td class="py-3 px-4 font-bold text-cyan-300">${r.rainfall_24h_mm || 0} mm</td>
          <td class="py-3 px-4">${r.rainfall_72h_mm || 0} mm</td>
          <td class="py-3 px-4 font-bold">${r.cumulative_event_mm || 0} mm</td>
          <td class="py-3 px-4 ${statusColor}">${r.status}</td>
        </tr>
      `;

      labels.push(r.location_name.split(' ')[0]);
      rfValues.push(r.rainfall_24h_mm || 0);
    });

    renderRainfallChart(labels, rfValues);

  } catch (err) {
    console.error('Error fetching rainfall:', err);
  }
}

function renderRainfallChart(labels = [], dataValues = []) {
  const ctx = document.getElementById('rainfall-chart');
  if (!ctx) return;

  if (rainfallChartInstance) {
    rainfallChartInstance.destroy();
  }

  rainfallChartInstance = new Chart(ctx, {
    type: 'bar',
    data: {
      labels: labels.length ? labels : ['Haflong', 'Guwahati', 'Bhalukpong', 'Sohra', 'Tupul', 'Aizawl', 'Gangtok'],
      datasets: [{
        label: '24h Rainfall (mm)',
        data: dataValues.length ? dataValues : [124.5, 68.0, 145.0, 185.0, 110.0, 95.0, 88.0],
        backgroundColor: 'rgba(0, 242, 254, 0.6)',
        borderColor: '#00f2fe',
        borderWidth: 1.5,
        borderRadius: 4
      }]
    },
    options: {
      responsive: true,
      maintainAspectRatio: false,
      plugins: {
        legend: { display: false }
      },
      scales: {
        x: {
          grid: { color: 'rgba(255, 255, 255, 0.05)' },
          ticks: { color: '#94a3b8', font: { family: 'JetBrains Mono', size: 10 } }
        },
        y: {
          grid: { color: 'rgba(255, 255, 255, 0.05)' },
          ticks: { color: '#94a3b8', font: { family: 'JetBrains Mono', size: 10 } }
        }
      }
    }
  });
}

// 12. Official Government Warnings Tab
async function fetchOfficialWarnings() {
  try {
    const url = selectedState ? `${API_BASE}/warnings?state_id=${selectedState}` : `${API_BASE}/warnings`;
    const res = await fetch(url);
    const data = await res.json();

    const grid = document.getElementById('official-warnings-grid');
    grid.innerHTML = '';

    if (!data.warnings || !data.warnings.length) {
      grid.innerHTML = '<div class="text-center py-8 text-slate-500">No active official government alerts for selected state.</div>';
      return;
    }

    data.warnings.forEach(w => {
      const isRed = w.severity.toLowerCase().includes('red');
      const isOrange = w.severity.toLowerCase().includes('orange');
      const borderClass = isRed ? 'border-red-600/70 bg-red-950/20' : isOrange ? 'border-orange-500/70 bg-orange-950/20' : 'border-amber-500/70 bg-amber-950/20';

      grid.innerHTML += `
        <div class="glass-panel p-5 border-l-4 ${borderClass}">
          <div class="flex flex-wrap items-center justify-between gap-2 mb-2 font-mono text-xs">
            <span class="px-2.5 py-0.5 rounded font-bold ${isRed ? 'bg-red-950 text-red-400' : 'bg-orange-950 text-orange-400'}">${w.alert_source} OFFICIAL BULLETIN: ${w.severity}</span>
            <span class="text-slate-400">ID: ${w.official_alert_id}</span>
          </div>

          <h3 class="text-base font-bold text-slate-100 mb-2">${w.headline}</h3>
          <p class="text-xs text-slate-300 leading-relaxed mb-3">${w.description}</p>

          <div class="flex flex-wrap items-center justify-between text-[11px] text-slate-400 pt-3 border-t border-slate-800/80 font-mono">
            <div>Issued: <strong>${w.issued_at_ist}</strong> | Valid Until: <strong>${w.valid_until_ist}</strong></div>
            ${w.official_source_url ? `<a href="${w.official_source_url}" target="_blank" class="text-cyan-400 hover:underline">Official Government Portal &rarr;</a>` : ''}
          </div>
        </div>
      `;
    });
  } catch (err) {
    console.error('Error fetching warnings:', err);
  }
}

// 13. Citizen Reporting & Submission
async function submitReportForm(event) {
  event.preventDefault();
  const btn = document.getElementById('cr-submit-btn');
  btn.disabled = true;
  btn.innerHTML = 'Submitting...';

  const formData = new FormData();
  formData.append('reporter_name', document.getElementById('cr-name').value);
  formData.append('reporter_phone', document.getElementById('cr-phone').value);
  formData.append('report_type', document.getElementById('cr-type').value);
  formData.append('description', document.getElementById('cr-desc').value);
  formData.append('latitude', document.getElementById('cr-lat').value);
  formData.append('longitude', document.getElementById('cr-lon').value);
  formData.append('landmark', document.getElementById('cr-landmark').value);

  const fileInput = document.getElementById('cr-photo');
  if (fileInput.files.length > 0) {
    formData.append('photo', fileInput.files[0]);
  }

  try {
    const res = await fetch(`${API_BASE}/reports`, {
      method: 'POST',
      body: formData
    });
    const result = await res.json();

    if (res.ok) {
      alert(`Report Registered Successfully!\nReport ID: ${result.report_number}\nStatus: ${result.status}`);
      document.getElementById('citizen-report-form').reset();
      fetchCitizenReports();
    } else {
      alert(`Submission Error: ${result.detail || 'Failed to submit'}`);
    }
  } catch (err) {
    alert(`Network Error: ${err.message}`);
  } finally {
    btn.disabled = false;
    btn.innerHTML = '<i data-lucide="send" class="w-4 h-4"></i> Submit Geo-Report';
    lucide.createIcons();
  }
}

function autofillCurrentGPS() {
  if (navigator.geolocation) {
    navigator.geolocation.getCurrentPosition(
      pos => {
        document.getElementById('cr-lat').value = pos.coords.latitude.toFixed(4);
        document.getElementById('cr-lon').value = pos.coords.longitude.toFixed(4);
      },
      err => {
        // Fallback default coordinates (Guwahati/Haflong axis)
        document.getElementById('cr-lat').value = '25.1780';
        document.getElementById('cr-lon').value = '93.0230';
      }
    );
  }
}

async function fetchCitizenReports() {
  try {
    const res = await fetch(`${API_BASE}/reports`);
    const reports = await res.json();

    const feed = document.getElementById('citizen-reports-feed');
    feed.innerHTML = '';

    if (!reports.length) {
      feed.innerHTML = '<div class="text-center py-8 text-slate-500">No citizen reports registered yet.</div>';
      return;
    }

    reports.forEach(r => {
      let stBadge = 'bg-cyan-950 text-cyan-300 border-cyan-800';
      if (r.status === 'VERIFIED') stBadge = 'bg-emerald-950 text-emerald-300 border-emerald-800';
      else if (r.status === 'REJECTED') stBadge = 'bg-red-950 text-red-300 border-red-800';

      feed.innerHTML += `
        <div class="p-4 rounded-lg bg-slate-900/80 border border-slate-800 text-xs hover:border-cyan-800/80 transition">
          <div class="flex items-center justify-between mb-2">
            <span class="font-mono font-bold text-cyan-400">${r.report_number} &bull; ${r.report_type}</span>
            <span class="px-2 py-0.5 rounded text-[10px] font-mono border ${stBadge}">${r.status}</span>
          </div>
          <div class="text-slate-200 mb-2">${r.description}</div>
          <div class="flex flex-wrap items-center justify-between text-[11px] text-slate-400 font-mono pt-2 border-t border-slate-800">
            <div>GPS: ${r.latitude.toFixed(4)}, ${r.longitude.toFixed(4)} ${r.landmark ? `(${r.landmark})` : ''}</div>
            <div>Submitted: ${r.submitted_at_ist}</div>
          </div>
        </div>
      `;
    });
  } catch (err) {
    console.error('Error fetching citizen reports:', err);
  }
}

// 14. Field Officer Operations & Offline Queue
function loadOfflineQueue() {
  try {
    const saved = localStorage.getItem('ne_shield_offline_queue');
    if (saved) {
      offlineQueue = JSON.parse(saved);
      document.getElementById('offline-queue-count').textContent = offlineQueue.length;
    }
  } catch (e) {}
}

async function fetchFieldOperations() {
  try {
    const res = await fetch(`${API_BASE}/field/incidents`);
    if (!res.ok) return; // Might require officer role
    const data = await res.json();

    const pendingContainer = document.getElementById('field-pending-list');
    pendingContainer.innerHTML = '';
    if (!data.pending_ground_checks || !data.pending_ground_checks.length) {
      pendingContainer.innerHTML = '<div class="text-center py-6 text-slate-500">No pending checks.</div>';
    } else {
      data.pending_ground_checks.forEach(c => {
        pendingContainer.innerHTML += `
          <div class="p-3 rounded bg-slate-900 border border-slate-800">
            <div class="font-bold text-slate-200">${c.report_number}: ${c.type}</div>
            <div class="text-slate-400 mt-1">${c.description}</div>
            <div class="text-[10px] text-cyan-400 font-mono mt-2">GPS: ${c.latitude}, ${c.longitude}</div>
          </div>
        `;
      });
    }

    const verifiedContainer = document.getElementById('field-verified-list');
    verifiedContainer.innerHTML = '';
    if (!data.verified_field_reports || !data.verified_field_reports.length) {
      verifiedContainer.innerHTML = '<div class="text-center py-6 text-slate-500">No verified reports yet.</div>';
    } else {
      data.verified_field_reports.forEach(f => {
        verifiedContainer.innerHTML += `
          <div class="p-3 rounded bg-slate-900 border border-slate-800">
            <div class="font-bold text-emerald-400">${f.report_number} &bull; ${f.incident_type}</div>
            <div class="text-slate-300 mt-1">Movement: ${f.movement_active ? 'ACTIVE' : 'STABILIZED'} | Road Blocked: ${f.road_blocked ? 'YES' : 'NO'}</div>
            <div class="text-[10px] text-slate-400 font-mono mt-1">Verified: ${f.created_at_ist}</div>
          </div>
        `;
      });
    }
  } catch (err) {
    console.error('Error in field operations:', err);
  }
}

async function syncOfflineQueueManual() {
  if (!offlineQueue.length) {
    alert('No pending offline reports in local queue.');
    return;
  }
  try {
    const res = await fetch(`${API_BASE}/field/sync`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(offlineQueue)
    });
    const result = await res.json();
    alert(`Sync Complete! ${result.synced_count} reports synchronized.`);
    offlineQueue = [];
    localStorage.removeItem('ne_shield_offline_queue');
    document.getElementById('offline-queue-count').textContent = '0';
    fetchFieldOperations();
  } catch (e) {
    alert(`Sync failed: ${e.message}`);
  }
}

// 15. Road Connectivity
async function fetchRoadNetwork() {
  try {
    const res = await fetch(`${API_BASE}/roads`);
    const roads = await res.json();

    const tbody = document.getElementById('roads-table-body');
    tbody.innerHTML = '';

    roads.forEach(rd => {
      let stColor = 'text-emerald-400';
      if (rd.current_status === 'BLOCKED') stColor = 'text-red-500 font-bold';
      else if (rd.current_status === 'PARTIALLY_BLOCKED') stColor = 'text-amber-400 font-bold';

      tbody.innerHTML += `
        <tr class="hover:bg-slate-800/40 transition">
          <td class="py-3 px-4 font-bold text-slate-100">${rd.name} ${rd.highway_number ? `(${rd.highway_number})` : ''}</td>
          <td class="py-3 px-4 text-slate-400">${rd.state_id}</td>
          <td class="py-3 px-4 ${stColor}">${rd.current_status}</td>
          <td class="py-3 px-4 text-slate-300 text-[11px]">${rd.cause || 'Clear for transit'}</td>
          <td class="py-3 px-4 font-mono text-[11px] text-cyan-300">${rd.source_attribution}</td>
          <td class="py-3 px-4 font-mono text-[11px] text-slate-400">${rd.last_updated_ist}</td>
          <td class="py-3 px-4">
            <button onclick="toggleRoadStatusPrompt('${rd.id}', '${rd.current_status}')" class="px-2 py-1 rounded bg-slate-800 hover:bg-slate-700 text-cyan-400 font-mono text-[11px] border border-slate-700">
              Update
            </button>
          </td>
        </tr>
      `;
    });
  } catch (err) {
    console.error('Error fetching roads:', err);
  }
}

async function toggleRoadStatusPrompt(segmentId, currentStatus) {
  const newSt = prompt(`Update status for ${segmentId}\nOptions: OPEN, PARTIALLY_BLOCKED, BLOCKED:`, currentStatus);
  if (!newSt) return;
  const cause = prompt('Enter blockage reason / clearing ETA:', 'Clearance active');

  try {
    const res = await fetch(`${API_BASE}/roads/${segmentId}`, {
      method: 'PATCH',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        status: newSt.trim().toUpperCase(),
        cause: cause,
        source_attribution: 'FIELD_VERIFIED'
      })
    });
    if (res.ok) {
      alert('Road status updated successfully!');
      fetchRoadNetwork();
      fetchGisLayers();
    } else {
      alert('Failed to update road status.');
    }
  } catch (e) {
    alert(`Error: ${e.message}`);
  }
}

// 16. ML Model Governance Tab
async function fetchModelStatus() {
  try {
    const res = await fetch(`${API_BASE}/model/status`);
    const data = await res.json();

    document.getElementById('ml-stat-accuracy').textContent = (data.metrics.accuracy * 100).toFixed(1) + '%';
    document.getElementById('ml-stat-roc-auc').textContent = data.metrics.roc_auc.toFixed(4);
    document.getElementById('ml-stat-precision').textContent = (data.metrics.precision * 100).toFixed(1) + '%';
    document.getElementById('ml-stat-recall').textContent = (data.metrics.recall * 100).toFixed(1) + '%';
    document.getElementById('ml-stat-dataset-size').textContent = data.dataset_size;

    // Render Confusion Matrix
    const cm = data.metrics.confusion_matrix;
    const cmDiv = document.getElementById('confusion-matrix-display');
    cmDiv.innerHTML = `
      <div class="grid grid-cols-2 gap-3 text-center">
        <div class="p-3 rounded bg-slate-900 border border-slate-800">
          <div class="text-slate-400 text-[10px]">True Negative (Stable)</div>
          <div class="text-xl font-bold text-emerald-400 mt-1">${cm[0][0]}</div>
        </div>
        <div class="p-3 rounded bg-slate-900 border border-slate-800">
          <div class="text-slate-400 text-[10px]">False Positive (False Alarm)</div>
          <div class="text-xl font-bold text-amber-400 mt-1">${cm[0][1]}</div>
        </div>
        <div class="p-3 rounded bg-slate-900 border border-slate-800">
          <div class="text-slate-400 text-[10px]">False Negative (Missed Slide)</div>
          <div class="text-xl font-bold text-red-500 mt-1">${cm[1][0]}</div>
        </div>
        <div class="p-3 rounded bg-slate-900 border border-slate-800">
          <div class="text-slate-400 text-[10px]">True Positive (Detected Slide)</div>
          <div class="text-xl font-bold text-cyan-400 mt-1">${cm[1][1]}</div>
        </div>
      </div>
    `;

    // Render Feature Importances
    const fiList = document.getElementById('feature-importances-list');
    fiList.innerHTML = '';
    const sortedFeatures = Object.entries(data.metrics.feature_importances || {})
      .sort((a, b) => b[1] - a[1])
      .slice(0, 7);

    sortedFeatures.forEach(([feat, val]) => {
      const pct = (val * 100).toFixed(1);
      fiList.innerHTML += `
        <div>
          <div class="flex justify-between text-slate-300 mb-1">
            <span>${feat}</span>
            <span class="text-cyan-400 font-bold">${pct}%</span>
          </div>
          <div class="w-full h-1.5 rounded-full bg-slate-800 overflow-hidden">
            <div class="h-full bg-gradient-to-r from-cyan-500 to-blue-500" style="width: ${pct}%"></div>
          </div>
        </div>
      `;
    });

  } catch (err) {
    console.error('Error fetching model status:', err);
  }
}

// 16. Pipeline Terminal Logger
function appendPipelineLog(msg, type = 'info') {
  const logEl = document.getElementById('pipeline-terminal-log');
  if (!logEl) return;

  const now = new Date();
  const timeStr = now.toTimeString().split(' ')[0];
  let colorClass = 'text-slate-300';
  let prefix = '[INFO]';

  if (type === 'success') {
    colorClass = 'text-emerald-400 font-bold';
    prefix = '[SUCCESS]';
  } else if (type === 'warning') {
    colorClass = 'text-amber-400 font-bold';
    prefix = '[WARN]';
  } else if (type === 'error') {
    colorClass = 'text-red-400 font-bold';
    prefix = '[ERROR]';
  } else if (type === 'step') {
    colorClass = 'text-cyan-300 font-bold';
    prefix = '[PIPELINE]';
  }

  const line = document.createElement('div');
  line.className = colorClass;
  line.textContent = `[${timeStr}] ${prefix} ${msg}`;
  logEl.appendChild(line);
  logEl.scrollTop = logEl.scrollHeight;

  const timeIndicator = document.getElementById('pipeline-last-sync-time');
  if (timeIndicator) timeIndicator.textContent = `Last run: ${timeStr} IST`;
}

// Model Retraining with Government Geotechnical Data
async function triggerModelRetrain() {
  const btn = document.getElementById('train-model-btn');
  const pipeBtn = document.getElementById('btn-pipeline-train');
  if (btn) { btn.disabled = true; btn.innerHTML = '<span class="animate-spin inline-block">↻</span> Training...'; }
  if (pipeBtn) { pipeBtn.disabled = true; pipeBtn.innerHTML = '<span class="animate-spin inline-block">↻</span> Training...'; }

  appendPipelineLog('Initiating Model Training on GSI & IMD Government Geotechnical Data...', 'step');

  try {
    const res = await fetch(`${API_BASE}/model/train`, {
      method: 'POST',
      headers: getAuthHeaders(),
      body: JSON.stringify({ algorithm: 'GradientBoostingClassifier', n_estimators: 90 })
    });
    const result = await res.json();
    if (res.ok) {
      appendPipelineLog(`Model Trained Successfully! Version: ${result.version_tag}`, 'success');
      appendPipelineLog(`Accuracy: ${(result.metrics.accuracy * 100).toFixed(2)}% | ROC-AUC: ${result.metrics.roc_auc} | F1: ${result.metrics.f1_score}`, 'success');
      fetchModelStatus();
      fetchDashboardSummary();
    } else {
      appendPipelineLog(`Training failed: ${result.detail || 'Error'}`, 'error');
    }
  } catch (e) {
    appendPipelineLog(`Network error during training: ${e.message}`, 'error');
  } finally {
    if (btn) { btn.disabled = false; btn.innerHTML = '<i data-lucide="play" class="w-3.5 h-3.5"></i> Retrain Active Model'; }
    if (pipeBtn) { pipeBtn.disabled = false; pipeBtn.innerHTML = '<i data-lucide="database" class="w-3.5 h-3.5 text-indigo-300"></i> 1. Train on Gov Data'; }
    lucide.createIcons();
  }
}

// Ingest Live Satellite Telemetry
async function syncSatelliteData() {
  const btn = document.getElementById('btn-pipeline-satellite');
  if (btn) { btn.disabled = true; btn.innerHTML = '<span class="animate-spin inline-block">↻</span> Ingesting Satellite...'; }

  appendPipelineLog('Connecting to ISRO Bhuvan WMS & Live Earth Observation Satellites...', 'step');

  try {
    const res = await fetch(`${API_BASE}/satellite/sync`, {
      method: 'POST',
      headers: getAuthHeaders()
    });
    const result = await res.json();
    if (res.ok && result.success) {
      appendPipelineLog(`ISRO Bhuvan Service: ${result.bhuvan_wms_status} (${result.bhuvan_latency_ms}ms)`, 'info');
      appendPipelineLog(`Ingested live satellite data for ${result.locations_synced} Northeast locations! Avg latency: ${result.satellite_average_latency_ms}ms`, 'success');
      
      const latEl = document.getElementById('pipeline-satellite-latency');
      if (latEl) latEl.textContent = `${result.satellite_average_latency_ms} ms`;
      
      fetchSatelliteTelemetry();
      fetchDataSources();
    } else {
      appendPipelineLog(`Satellite sync error: ${result.detail || result.message || 'Unknown'}`, 'error');
    }
  } catch (e) {
    appendPipelineLog(`Satellite connection failed: ${e.message}`, 'error');
  } finally {
    if (btn) { btn.disabled = false; btn.innerHTML = '<i data-lucide="satellite" class="w-3.5 h-3.5 text-cyan-200"></i> 2. Fetch Live Satellite Data'; }
    lucide.createIcons();
  }
}

// Run AI Inference on Satellite Data
async function predictOnSatelliteData() {
  const btn = document.getElementById('btn-pipeline-predict');
  if (btn) { btn.disabled = true; btn.innerHTML = '<span class="animate-spin inline-block">↻</span> Predicting...'; }

  appendPipelineLog('Executing AI Inference on real-time Satellite inputs across all monitored spots...', 'step');

  try {
    const res = await fetch(`${API_BASE}/satellite/predict`, {
      method: 'POST',
      headers: getAuthHeaders()
    });
    const result = await res.json();
    if (res.ok && result.success) {
      appendPipelineLog(`Inference completed for ${result.count} locations using model ${result.model_version}!`, 'success');
      renderSatellitePredictionsTable(result.predictions);
      fetchDashboardSummary();
      fetchGisLayers();
    } else {
      appendPipelineLog(`Prediction error: ${result.detail || 'Error'}`, 'error');
    }
  } catch (e) {
    appendPipelineLog(`Prediction failed: ${e.message}`, 'error');
  } finally {
    if (btn) { btn.disabled = false; btn.innerHTML = '<i data-lucide="cpu" class="w-3.5 h-3.5 text-purple-200"></i> 3. Predict on Satellite Data'; }
    lucide.createIcons();
  }
}

// One-Click End-to-End Pipeline Execution
async function executeFullPipeline() {
  const btn = document.getElementById('btn-pipeline-full');
  if (btn) {
    btn.disabled = true;
    btn.innerHTML = '<span class="animate-spin inline-block mr-1">↻</span> Running Pipeline (Train → Satellite → Predict)...';
  }

  appendPipelineLog('================ STARTING END-TO-END PIPELINE ================', 'step');
  appendPipelineLog('Step 1: Retraining model on official Government geotechnical data...', 'info');

  try {
    const res = await fetch(`${API_BASE}/satellite/run-pipeline`, {
      method: 'POST',
      headers: getAuthHeaders()
    });
    const data = await res.json();

    if (res.ok && data.success) {
      const t = data.step1_training;
      appendPipelineLog(`[Step 1 OK] Model ${t.version_tag} trained! Accuracy: ${(t.metrics.accuracy * 100).toFixed(2)}%, ROC-AUC: ${t.metrics.roc_auc}`, 'success');

      const s = data.step2_satellite_sync;
      appendPipelineLog(`[Step 2 OK] Satellite Ingestion: ${s.locations_synced} locations synced via ISRO Bhuvan (Avg RTT: ${s.average_latency_ms}ms)`, 'success');

      const p = data.step3_ai_predictions;
      appendPipelineLog(`[Step 3 OK] AI Prediction Complete! Critical Hazards: ${p.critical_hazard_count}, High: ${p.high_hazard_count}`, 'success');
      appendPipelineLog('================ PIPELINE EXECUTED SUCCESSFULLY ================', 'step');

      renderSatellitePredictionsTable(p.predictions);

      const latEl = document.getElementById('pipeline-satellite-latency');
      if (latEl) latEl.textContent = `${s.average_latency_ms} ms`;

      fetchModelStatus();
      fetchDashboardSummary();
      fetchGisLayers();
      fetchDataSources();
    } else {
      appendPipelineLog(`Pipeline execution halted: ${data.detail || 'Unknown error'}`, 'error');
    }
  } catch (e) {
    appendPipelineLog(`Pipeline failed with exception: ${e.message}`, 'error');
  } finally {
    if (btn) {
      btn.disabled = false;
      btn.innerHTML = '<i data-lucide="zap" class="w-4 h-4 text-black"></i> Execute Full Live Pipeline';
    }
    lucide.createIcons();
  }
}

// Fetch & Render Latest Satellite Telemetry
async function fetchSatelliteTelemetry() {
  try {
    const res = await fetch(`${API_BASE}/satellite/latest`);
    const data = await res.json();
    if (!data || !data.satellite_telemetry) return;

    const tbody = document.getElementById('satellite-predictions-tbody');
    if (!tbody) return;

    // If predictions haven't run yet, populate with raw telemetry
    if (tbody.children.length <= 1) {
      tbody.innerHTML = '';
      data.satellite_telemetry.forEach(item => {
        tbody.innerHTML += `
          <tr class="hover:bg-slate-900/60 transition font-mono">
            <td class="p-2.5 font-bold text-slate-200">${item.location_name}</td>
            <td class="p-2.5 text-cyan-400 font-bold">${item.state_id}</td>
            <td class="p-2.5 text-slate-400 text-[11px]">${item.latitude.toFixed(2)}, ${item.longitude.toFixed(2)}</td>
            <td class="p-2.5 text-cyan-300 font-bold">${item.satellite_rainfall_24h_mm} mm</td>
            <td class="p-2.5 text-indigo-300 font-bold">${item.satellite_soil_moisture_pct}%</td>
            <td class="p-2.5 text-slate-300">--</td>
            <td class="p-2.5"><span class="px-2 py-0.5 rounded text-[10px] bg-slate-800 text-slate-400">READY</span></td>
            <td class="p-2.5 text-slate-400 text-xs">--</td>
            <td class="p-2.5 text-[11px] text-slate-500">Live Satellite Connected</td>
          </tr>
        `;
      });
    }
  } catch (err) {
    console.warn('Error fetching satellite telemetry:', err);
  }
}

// Render AI Predictions Table
function renderSatellitePredictionsTable(predictions) {
  const tbody = document.getElementById('satellite-predictions-tbody');
  if (!tbody || !predictions) return;

  tbody.innerHTML = '';
  let criticalCount = 0;
  let highCount = 0;

  predictions.forEach(p => {
    const probPct = (p.risk_probability * 100).toFixed(1);
    const rClass = p.risk_class;

    let badgeClass = 'bg-emerald-950 text-emerald-400 border border-emerald-800';
    if (rClass === 'CRITICAL') {
      badgeClass = 'bg-red-950 text-red-400 border border-red-800 animate-pulse';
      criticalCount++;
    } else if (rClass === 'HIGH') {
      badgeClass = 'bg-amber-950 text-amber-400 border border-amber-800';
      highCount++;
    } else if (rClass === 'MODERATE') {
      badgeClass = 'bg-cyan-950 text-cyan-400 border border-cyan-800';
    }

    const sat = p.satellite_telemetry || {};
    const rain24 = sat.rainfall_24h_mm !== undefined ? sat.rainfall_24h_mm : (p.features?.rainfall_24h_mm || 0);
    const sm = sat.soil_moisture_pct !== undefined ? sat.soil_moisture_pct : (p.features?.soil_moisture_pct || 45);
    const cloud = sat.cloud_cover_pct !== undefined ? sat.cloud_cover_pct : 85;

    const triggers = (p.thresholds_exceeded && p.thresholds_exceeded.length > 0)
      ? p.thresholds_exceeded.join('; ')
      : 'Slope stability verified within threshold';

    tbody.innerHTML += `
      <tr class="hover:bg-slate-900/80 transition font-mono">
        <td class="p-2.5 font-bold text-slate-100 flex items-center gap-1.5">
          <span class="w-1.5 h-1.5 rounded-full ${rClass === 'CRITICAL' ? 'bg-red-500' : rClass === 'HIGH' ? 'bg-amber-500' : 'bg-cyan-500'}"></span>
          ${p.location_name}
        </td>
        <td class="p-2.5 text-cyan-400 font-bold">${p.state_id}</td>
        <td class="p-2.5 text-slate-400 text-[11px]">${p.latitude.toFixed(2)}, ${p.longitude.toFixed(2)}</td>
        <td class="p-2.5 text-cyan-300 font-bold">${rain24} mm</td>
        <td class="p-2.5 text-indigo-300 font-bold">${sm}%</td>
        <td class="p-2.5 text-slate-300">${cloud}%</td>
        <td class="p-2.5">
          <span class="px-2 py-0.5 rounded text-[10px] font-bold ${badgeClass}">${rClass}</span>
        </td>
        <td class="p-2.5 font-bold ${rClass === 'CRITICAL' ? 'text-red-400' : rClass === 'HIGH' ? 'text-amber-400' : 'text-slate-300'}">${probPct}%</td>
        <td class="p-2.5 text-[11px] text-slate-400 max-w-xs truncate" title="${triggers}">${triggers}</td>
      </tr>
    `;
  });

  const critEl = document.getElementById('pipeline-critical-count');
  if (critEl) critEl.textContent = `${criticalCount} Critical / ${highCount} High`;
}

// 17. Data Provenance & Health Registry Tab
async function fetchDataSources() {
  try {
    const res = await fetch(`${API_BASE}/data-sources/status`);
    const data = await res.json();

    const grid = document.getElementById('data-sources-grid');
    grid.innerHTML = '';

    data.data_sources.forEach(ds => {
      const isOnline = ds.status === 'ONLINE';
      grid.innerHTML += `
        <div class="glass-panel p-4 flex flex-col justify-between">
          <div>
            <div class="flex items-center justify-between pb-2 border-b border-slate-800">
              <span class="font-bold text-sm text-slate-100">${ds.name}</span>
              <span class="px-2 py-0.5 rounded text-[10px] font-mono font-bold ${isOnline ? 'bg-emerald-950 text-emerald-400 border border-emerald-800' : 'bg-red-950 text-red-400 border border-red-800'}">${ds.status}</span>
            </div>

            <div class="mt-3 space-y-1.5 text-xs text-slate-300 font-mono">
              <div class="text-[11px] text-slate-400 truncate">Endpoint: ${ds.endpoint_url || 'N/A'}</div>
              <div>Category: <strong class="text-cyan-300">${ds.category}</strong></div>
              <div>Latency: <strong>${ds.latency_ms} ms</strong></div>
              <div>Records Ingested: <strong>${ds.records_synced_today}</strong></div>
            </div>
          </div>

          <div class="mt-4 pt-2.5 border-t border-slate-800 text-[10px] text-slate-500 font-mono">
            Last Successful Sync: ${ds.last_successful_sync_ist}
          </div>
        </div>
      `;
    });
  } catch (err) {
    console.error('Error fetching data sources:', err);
  }
}

// 18. Audit Logs Tab
async function fetchAuditLogs() {
  try {
    const res = await fetch(`${API_BASE}/audit-logs`);
    if (!res.ok) return;
    const logs = await res.json();

    const tbody = document.getElementById('audit-table-body');
    tbody.innerHTML = '';

    logs.forEach(l => {
      tbody.innerHTML += `
        <tr class="hover:bg-slate-800/40 transition">
          <td class="py-3 px-4 text-slate-400">${l.timestamp_ist}</td>
          <td class="py-3 px-4 font-bold text-cyan-400">${l.action}</td>
          <td class="py-3 px-4 text-slate-300">${l.user_email}</td>
          <td class="py-3 px-4 text-slate-400">${l.resource_type}: ${l.resource_id || '--'}</td>
          <td class="py-3 px-4 text-emerald-400">${l.result_status}</td>
          <td class="py-3 px-4 text-slate-400 text-[10px] max-w-[200px] truncate">${JSON.stringify(l.details || {})}</td>
        </tr>
      `;
    });
  } catch (err) {
    console.error('Error fetching audit logs:', err);
  }
}

// Filter Handlers
function onStateFilterChange(val) {
  selectedState = val;
  refreshAllData(true);
}
function onRiskFilterChange(val) {
  selectedRisk = val;
  fetchRiskPredictions();
}

function focusMapLocation(locId) {
  switchTab('live-map');
}

function showFloatingAlert(title, message) {
  alert(`[NE-SHIELD EMERGENCY ALERT]\n${title}\n${message}`);
}

function switchPersona(persona) {
  // Update UI context for testing roles
  refreshAllData(true);
}
