/* CCTNS-GridX — Patrol Route Management */
let patrolMap;
async function loadPatrol() {
    if (!initPage('patrol', 'Patrol Route Management')) return;
    document.getElementById('page-content').innerHTML = `
    <div class="animate-fadeInUp">
        <div class="stats-grid" id="patrolStats"></div>
        <div class="dashboard-grid">
            <div class="map-wrapper"><div class="chart-header" style="padding:12px 16px"><div class="chart-title">🚔 Patrol Routes</div>
                <div class="flex gap-sm">
                    <select class="select-styled" id="patrolDistrict" onchange="loadPatrolRoutes()"><option value="">All Districts</option></select>
                    <select class="select-styled" id="patrolSeason"><option value="">All Seasons</option><option>Summer</option><option>Monsoon</option><option>Winter</option><option>Festival</option><option>General</option></select>
                    <button class="btn btn-sm btn-primary" onclick="generateRoute()">⚡ AI Generate</button>
                </div>
            </div><div id="patrolMapDiv" style="height:500px"></div></div>
            <div>
                <div class="chart-container mb-md"><div class="chart-header"><div class="chart-title">📊 Route Types</div></div><div class="chart-body"><canvas id="routeTypeChart"></canvas></div></div>
                <div class="route-info-panel" id="routeInfo"><p class="text-muted">Select a route to view details</p></div>
            </div>
        </div>
        <div class="chart-container mt-lg"><div class="chart-header"><div class="chart-title">🚓 Patrol Units</div></div><div class="table-scroll" id="unitTable"></div></div>
    </div>`;
    patrolMap = L.map('patrolMapDiv').setView([10.85, 78.65], 7);
    L.tileLayer('https://{s}.basemaps.cartocdn.com/dark_all/{z}/{x}/{y}{r}.png', { maxZoom: 19 }).addTo(patrolMap);
    const districts = await Utils.get('/api/fir/districts/all');
    const sel = document.getElementById('patrolDistrict');
    (districts.districts||[]).forEach(d => { const o = document.createElement('option'); o.value = d.id; o.textContent = d.name; sel.appendChild(o); });
    loadPatrolStats(); loadPatrolRoutes(); loadPatrolUnits();
}

async function loadPatrolStats() {
    try {
        const s = await Utils.get('/api/patrol/stats');
        document.getElementById('patrolStats').innerHTML = `
            <div class="stat-card"><div class="stat-icon cyan">🛣️</div><div class="stat-info"><div class="stat-value">${s.total_routes}</div><div class="stat-label">Active Routes</div></div></div>
            <div class="stat-card"><div class="stat-icon green">🚔</div><div class="stat-info"><div class="stat-value">${s.active_units}</div><div class="stat-label">Active Units</div></div></div>
            <div class="stat-card"><div class="stat-icon orange">💤</div><div class="stat-info"><div class="stat-value">${s.idle_units}</div><div class="stat-label">Idle Units</div></div></div>
            <div class="stat-card"><div class="stat-icon magenta">📊</div><div class="stat-info"><div class="stat-value">${s.total_units}</div><div class="stat-label">Total Units</div></div></div>`;
    } catch(e) {}
}

async function loadPatrolRoutes() {
    const did = document.getElementById('patrolDistrict').value;
    const params = new URLSearchParams(); if (did) params.set('district_id', did);
    try {
        const data = await Utils.get(`/api/patrol/routes?${params}`);
        patrolMap.eachLayer(l => { if (l instanceof L.Polyline || l instanceof L.Marker) patrolMap.removeLayer(l); });
        const routeColors = ['#00e5ff','#e040fb','#00e676','#ff6d00','#ffd600','#2979ff','#ff1744'];
        (data.routes||[]).forEach((r, i) => {
            const color = routeColors[i % routeColors.length];
            const wps = r.waypoints || [];
            if (wps.length < 2) return;
            const latlngs = wps.map(w => [w.lat, w.lng]);
            L.polyline(latlngs, { color, weight: 3, opacity: 0.8, dashArray: '8 4' }).addTo(patrolMap).on('click', () => showRouteInfo(r));
            wps.forEach((w, j) => {
                const icon = L.divIcon({ className: '', html: `<div style="background:${color};width:10px;height:10px;border-radius:50%;border:2px solid #fff"></div>`, iconSize: [14, 14] });
                L.marker([w.lat, w.lng], { icon }).addTo(patrolMap).bindPopup(`<b>${w.name}</b><br>${r.name}`);
            });
        });
        renderRouteTypeChart(data.routes||[]);
    } catch(e) {}
}

function showRouteInfo(r) {
    document.getElementById('routeInfo').innerHTML = `
        <h4 class="text-cyan">${r.name}</h4>
        <div class="route-stats mt-md">
            <div class="map-stat"><div class="stat-label">Distance</div><div class="stat-value">${r.total_distance_km} km</div></div>
            <div class="map-stat"><div class="stat-label">Est. Time</div><div class="stat-value">${r.estimated_time_mins} min</div></div>
            <div class="map-stat"><div class="stat-label">Season</div><div class="stat-value">${r.season}</div></div>
            <div class="map-stat"><div class="stat-label">Type</div><div class="stat-value">${r.route_type}</div></div>
        </div>
        <ul class="waypoint-list">${(r.waypoints||[]).map(w => `<li>${w.name}</li>`).join('')}</ul>`;
}

function renderRouteTypeChart(routes) {
    const types = {}; routes.forEach(r => { types[r.route_type] = (types[r.route_type]||0) + 1; });
    const canvas = document.getElementById('routeTypeChart');
    if (!canvas) return;
    new Chart(canvas, {
        type: 'doughnut', data: { labels: Object.keys(types), datasets: [{ data: Object.values(types), backgroundColor: Utils.chartColorArray(), borderWidth: 0 }] },
        options: { responsive: true, maintainAspectRatio: false, cutout: '60%', plugins: { legend: { position: 'bottom', labels: { boxWidth: 10, font: { size: 11 } } } } }
    });
}

async function generateRoute() {
    const did = document.getElementById('patrolDistrict').value || 1;
    const season = document.getElementById('patrolSeason').value || 'General';
    try {
        const r = await Utils.get(`/api/patrol/generate?district_id=${did}&season=${season}`);
        if (r.error) { Utils.showToast(r.error, 'warning'); return; }
        showRouteInfo(r);
        const wps = r.waypoints || [];
        if (wps.length > 1) {
            const latlngs = wps.map(w => [w.lat, w.lng]);
            L.polyline(latlngs, { color: '#00e5ff', weight: 4, opacity: 1 }).addTo(patrolMap);
            patrolMap.fitBounds(latlngs);
        }
        Utils.showToast('AI route generated!', 'success');
    } catch(e) { Utils.showToast('Route generation failed', 'error'); }
}

async function loadPatrolUnits() {
    try {
        const data = await Utils.get('/api/patrol/units');
        const units = data.units || [];
        document.getElementById('unitTable').innerHTML = `<table class="data-table"><thead><tr><th>Unit</th><th>Type</th><th>Station</th><th>District</th><th>Status</th><th>Officers</th></tr></thead><tbody>${
            units.map(u => `<tr><td class="mono text-cyan">${u.unit_name}</td><td>${u.unit_type}</td><td>${u.station_name}</td><td>${u.district_name}</td><td><span class="badge ${u.status==='Active'?'badge-low':u.status==='Idle'?'badge-info':'badge-medium'}">${u.status}</span></td><td>${u.officers_count}</td></tr>`).join('')
        }</tbody></table>`;
        units.forEach(u => {
            if (u.current_lat && u.current_lng) {
                const icon = L.divIcon({ className: '', html: `<div style="background:${u.status==='Active'?'#00e676':'#ffd600'};width:8px;height:8px;border-radius:50%;border:2px solid #fff;box-shadow:0 0 6px ${u.status==='Active'?'#00e676':'#ffd600'}"></div>`, iconSize: [12, 12] });
                L.marker([u.current_lat, u.current_lng], { icon }).addTo(patrolMap).bindPopup(`<b>${u.unit_name}</b><br>${u.status}`);
            }
        });
    } catch(e) {}
}
document.addEventListener('DOMContentLoaded', loadPatrol);
