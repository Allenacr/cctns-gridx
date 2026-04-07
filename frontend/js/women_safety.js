/* CCTNS-GridX — Women Safety Analysis */
let womenMap;
async function loadWomenSafety() {
    if (!initPage('women_safety', 'Women Safety Analysis')) return;
    document.getElementById('page-content').innerHTML = `
    <div class="animate-fadeInUp">
        <div class="stats-grid" id="womenStats"></div>
        <div class="dashboard-grid">
            <div class="map-wrapper"><div class="chart-header" style="padding:12px 16px"><div class="chart-title">🛡️ Women Safety Zones</div>
                <select class="select-styled" id="wsRiskFilter" onchange="filterWomenZones()"><option value="">All Risk Levels</option><option>Critical</option><option>High</option><option>Medium</option><option>Low</option></select>
            </div><div id="womenMapDiv" style="height:500px"></div></div>
            <div>
                <div class="chart-container mb-md"><div class="chart-header"><div class="chart-title">Top Districts — Crimes Against Women</div></div><div class="chart-body"><canvas id="womenDistChart"></canvas></div></div>
                <div class="chart-container"><div class="chart-header"><div class="chart-title">Hourly Distribution</div></div><div class="chart-body"><canvas id="womenHourChart"></canvas></div></div>
            </div>
        </div>
        <div class="chart-container mt-lg"><div class="chart-header"><div class="chart-title">Monthly Trend — Crimes Against Women</div></div><div class="chart-body"><canvas id="womenTrendChart"></canvas></div></div>
    </div>`;
    womenMap = L.map('womenMapDiv').setView([10.85, 78.65], 7);
    L.tileLayer('https://{s}.basemaps.cartocdn.com/dark_all/{z}/{x}/{y}{r}.png', { maxZoom: 19 }).addTo(womenMap);
    loadWomenStats(); loadWomenZones();
}

async function loadWomenStats() {
    try {
        const s = await Utils.get('/api/safety/women-stats');
        const risk = s.by_risk_level || {};
        document.getElementById('womenStats').innerHTML = `
            <div class="stat-card"><div class="stat-icon magenta">🛡️</div><div class="stat-info"><div class="stat-value">${s.total_safety_zones}</div><div class="stat-label">Safety Zones</div></div></div>
            <div class="stat-card"><div class="stat-icon red">🔴</div><div class="stat-info"><div class="stat-value">${risk['Critical']||0}</div><div class="stat-label">Critical Zones</div></div></div>
            <div class="stat-card"><div class="stat-icon orange">🟡</div><div class="stat-info"><div class="stat-value">${risk['High']||0}</div><div class="stat-label">High Risk Zones</div></div></div>
            <div class="stat-card"><div class="stat-icon green">🟢</div><div class="stat-info"><div class="stat-value">${risk['Low']||0}</div><div class="stat-label">Low Risk Zones</div></div></div>`;
        // Charts
        const dists = s.top_districts || [];
        if (dists.length) new Chart(document.getElementById('womenDistChart'), {
            type: 'bar', data: { labels: dists.map(d=>d.name), datasets: [{ data: dists.map(d=>d.count), backgroundColor: 'rgba(233,30,99,0.3)', borderColor: '#e91e63', borderWidth: 1, borderRadius: 4 }] },
            options: { responsive: true, maintainAspectRatio: false, indexAxis: 'y', plugins: { legend: { display: false } }, scales: { x: { beginAtZero: true }, y: { grid: { display: false } } } }
        });
        const hourly = s.hourly_distribution || {};
        const hours = Array.from({length:24}, (_,i)=>i);
        const hData = hours.map(h => hourly[h]||0);
        new Chart(document.getElementById('womenHourChart'), {
            type: 'bar', data: { labels: hours.map(h=>`${h}:00`), datasets: [{ data: hData, backgroundColor: hours.map(h => h>=18||h<=5 ? 'rgba(255,23,68,0.4)' : 'rgba(0,229,255,0.2)'), borderWidth: 0, borderRadius: 2 }] },
            options: { responsive: true, maintainAspectRatio: false, plugins: { legend: { display: false } }, scales: { x: { grid: { display: false } }, y: { beginAtZero: true } } }
        });
        const monthly = s.monthly_trend || [];
        if (monthly.length) new Chart(document.getElementById('womenTrendChart'), {
            type: 'line', data: { labels: monthly.map(m=>m.month), datasets: [{ label: 'Incidents', data: monthly.map(m=>m.count), borderColor: '#e91e63', backgroundColor: 'rgba(233,30,99,0.1)', fill: true, tension: 0.4, pointRadius: 2 }] },
            options: { responsive: true, maintainAspectRatio: false, plugins: { legend: { display: false } }, scales: { x: { grid: { display: false } }, y: { beginAtZero: true } } }
        });
    } catch(e) {}
}

async function loadWomenZones() { filterWomenZones(); }
async function filterWomenZones() {
    const risk = document.getElementById('wsRiskFilter').value;
    const params = new URLSearchParams(); if (risk) params.set('risk_level', risk);
    try {
        const data = await Utils.get(`/api/safety/women-zones?${params}`);
        womenMap.eachLayer(l => { if (l instanceof L.Circle || l instanceof L.Marker) womenMap.removeLayer(l); });
        const riskColors = { Critical: '#ff1744', High: '#ff6d00', Medium: '#ffd600', Low: '#00e676' };
        (data.zones||[]).forEach(z => {
            const color = riskColors[z.risk_level] || '#95a5a6';
            L.circle([z.lat, z.lng], { radius: z.radius_meters, color, fillColor: color, fillOpacity: 0.2, weight: 2 }).addTo(womenMap)
            .bindPopup(`<div class="popup-title">${z.name}</div><div class="popup-row"><span class="popup-label">Type:</span><span class="popup-value">${z.zone_type}</span></div><div class="popup-row"><span class="popup-label">Risk:</span><span class="popup-value">${z.risk_level}</span></div><div class="popup-row"><span class="popup-label">Patrol:</span><span class="popup-value">${z.patrol_frequency}</span></div><div class="popup-row"><span class="popup-label">Incidents:</span><span class="popup-value">${z.total_incidents}</span></div><div class="popup-row"><span class="popup-label">CCTV:</span><span class="popup-value">${z.has_cctv?'Yes':'No'}</span></div>`);
        });
    } catch(e) {}
}
document.addEventListener('DOMContentLoaded', loadWomenSafety);
