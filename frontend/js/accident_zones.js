/* CCTNS-GridX — Accident Zones */
let accidentMap;
async function loadAccidentZones() {
    if (!initPage('accident_zones', 'Accident-Prone Areas')) return;
    document.getElementById('page-content').innerHTML = `
    <div class="animate-fadeInUp">
        <div class="stats-grid" id="accidentStats"></div>
        <div class="dashboard-grid">
            <div class="map-wrapper"><div class="chart-header" style="padding:12px 16px"><div class="chart-title">⚠️ Accident-Prone Areas (IRAD Data)</div>
                <select class="select-styled" id="accSeverity" onchange="filterAccidents()"><option value="">All Severity</option><option>Critical</option><option>High</option><option>Medium</option><option>Low</option></select>
            </div><div id="accidentMapDiv" style="height:500px"></div></div>
            <div>
                <div class="chart-container mb-md"><div class="chart-header"><div class="chart-title">By Road Type</div></div><div class="chart-body"><canvas id="roadTypeChart"></canvas></div></div>
                <div class="chart-container"><div class="chart-header"><div class="chart-title">By Primary Cause</div></div><div class="chart-body"><canvas id="causeChart"></canvas></div></div>
            </div>
        </div>
        <div class="chart-container mt-lg"><div class="chart-header"><div class="chart-title">📊 All Accident Zones</div></div><div class="table-scroll" id="accidentTable"></div></div>
    </div>`;
    accidentMap = L.map('accidentMapDiv').setView([10.85, 78.65], 7);
    L.tileLayer('https://{s}.basemaps.cartocdn.com/dark_all/{z}/{x}/{y}{r}.png', { maxZoom: 19 }).addTo(accidentMap);
    loadAccidentStats(); filterAccidents();
}

async function loadAccidentStats() {
    try {
        const s = await Utils.get('/api/safety/accident-stats');
        document.getElementById('accidentStats').innerHTML = `
            <div class="stat-card"><div class="stat-icon red">⚠️</div><div class="stat-info"><div class="stat-value">${s.total_zones}</div><div class="stat-label">Accident Zones</div></div></div>
            <div class="stat-card"><div class="stat-icon orange">💥</div><div class="stat-info"><div class="stat-value">${s.total_accidents}</div><div class="stat-label">Total Accidents</div></div></div>
            <div class="stat-card"><div class="stat-icon red">💀</div><div class="stat-info"><div class="stat-value">${s.total_fatalities}</div><div class="stat-label">Fatalities</div></div></div>
            <div class="stat-card"><div class="stat-icon orange">🤕</div><div class="stat-info"><div class="stat-value">${s.total_injuries}</div><div class="stat-label">Injuries</div></div></div>`;
        const byRoad = s.by_road_type || [];
        if (byRoad.length) new Chart(document.getElementById('roadTypeChart'), {
            type: 'doughnut', data: { labels: byRoad.map(r=>r.type), datasets: [{ data: byRoad.map(r=>r.accidents), backgroundColor: Utils.chartColorArray(), borderWidth: 0 }] },
            options: { responsive: true, maintainAspectRatio: false, cutout: '55%', plugins: { legend: { position: 'bottom', labels: { boxWidth: 10, font: { size: 10 } } } } }
        });
        const byCause = s.by_cause || [];
        if (byCause.length) new Chart(document.getElementById('causeChart'), {
            type: 'bar', data: { labels: byCause.map(c=>c.cause), datasets: [{ data: byCause.map(c=>c.count), backgroundColor: 'rgba(255,109,0,0.3)', borderColor: '#ff6d00', borderWidth: 1, borderRadius: 4 }] },
            options: { responsive: true, maintainAspectRatio: false, indexAxis: 'y', plugins: { legend: { display: false } }, scales: { x: { beginAtZero: true }, y: { grid: { display: false } } } }
        });
    } catch(e) {}
}

async function filterAccidents() {
    const severity = document.getElementById('accSeverity').value;
    const params = new URLSearchParams(); if (severity) params.set('severity', severity);
    try {
        const data = await Utils.get(`/api/safety/accident-zones?${params}`);
        accidentMap.eachLayer(l => { if (l instanceof L.Circle || l instanceof L.Marker) accidentMap.removeLayer(l); });
        const sevColors = { Critical: '#ff1744', High: '#ff6d00', Medium: '#ffd600', Low: '#00e676' };
        const zones = data.zones || [];
        zones.forEach(z => {
            const color = sevColors[z.severity] || '#95a5a6';
            const radius = Math.max(z.accident_count * 50, 300);
            L.circle([z.lat, z.lng], { radius, color, fillColor: color, fillOpacity: 0.25, weight: 2 }).addTo(accidentMap)
            .bindPopup(`<div class="popup-title">${z.location_name}</div><div class="popup-row"><span class="popup-label">Road:</span><span class="popup-value">${z.road_name||''} (${z.road_type})</span></div><div class="popup-row"><span class="popup-label">Accidents:</span><span class="popup-value">${z.accident_count}</span></div><div class="popup-row"><span class="popup-label">Fatalities:</span><span class="popup-value">${z.fatality_count}</span></div><div class="popup-row"><span class="popup-label">Cause:</span><span class="popup-value">${z.primary_cause}</span></div><div class="popup-row"><span class="popup-label">Speed Limit:</span><span class="popup-value">${z.speed_limit} km/h</span></div>`);
        });
        document.getElementById('accidentTable').innerHTML = `<table class="data-table"><thead><tr><th>Location</th><th>Road</th><th>Accidents</th><th>Fatalities</th><th>Cause</th><th>Severity</th></tr></thead><tbody>${
            zones.map(z => `<tr><td>${z.location_name}</td><td>${z.road_type}</td><td class="mono">${z.accident_count}</td><td class="mono text-red">${z.fatality_count}</td><td>${z.primary_cause}</td><td>${Utils.riskBadge(z.severity)}</td></tr>`).join('')
        }</tbody></table>`;
    } catch(e) {}
}
document.addEventListener('DOMContentLoaded', loadAccidentZones);
