/* CCTNS-GridX — Dashboard Logic */
async function loadDashboard() {
    if (!initPage('dashboard', 'Command Center')) return;
    const content = document.getElementById('page-content');
    content.innerHTML = '<div class="spinner"></div>';
    try {
        const stats = await Utils.get('/api/fir/stats');
        const s = stats.by_status || {};
        content.innerHTML = `
        <div class="stats-grid animate-fadeInUp">
            <div class="stat-card"><div class="stat-icon cyan">📋</div><div class="stat-info"><div class="stat-value">${Utils.formatNumber(stats.total_firs)}</div><div class="stat-label">Total FIRs</div></div></div>
            <div class="stat-card"><div class="stat-icon orange">🔍</div><div class="stat-info"><div class="stat-value">${Utils.formatNumber(s['Under Investigation']||0)}</div><div class="stat-label">Under Investigation</div></div></div>
            <div class="stat-card"><div class="stat-icon green">✅</div><div class="stat-info"><div class="stat-value">${Utils.formatNumber(s['Closed']||0)}</div><div class="stat-label">Cases Closed</div></div></div>
            <div class="stat-card"><div class="stat-icon red">🔴</div><div class="stat-info"><div class="stat-value">${Utils.formatNumber(s['Registered']||0)}</div><div class="stat-label">Pending Registration</div></div></div>
            <div class="stat-card"><div class="stat-icon magenta">📄</div><div class="stat-info"><div class="stat-value">${Utils.formatNumber(s['Charge Sheet Filed']||0)}</div><div class="stat-label">Charge Sheets</div></div></div>
            <div class="stat-card"><div class="stat-icon blue">❓</div><div class="stat-info"><div class="stat-value">${Utils.formatNumber(s['Undetected']||0)}</div><div class="stat-label">Undetected</div></div></div>
        </div>
        <div class="dashboard-grid">
            <div class="chart-container"><div class="chart-header"><div class="chart-title">Monthly Crime Trend</div></div><div class="chart-body"><canvas id="trendChart"></canvas></div></div>
            <div class="chart-container"><div class="chart-header"><div class="chart-title">Crime Type Distribution</div></div><div class="chart-body"><canvas id="typeChart"></canvas></div></div>
        </div>
        <div class="dashboard-grid">
            <div class="chart-container"><div class="chart-header"><div class="chart-title">Top 10 Districts by Crime</div></div><div class="chart-body"><canvas id="districtChart"></canvas></div></div>
            <div class="recent-fir-card"><div class="card-header"><h3>Recent FIRs</h3><a href="/fir_entry" class="btn btn-sm btn-primary">+ New FIR</a></div><div class="table-scroll" id="recentTable"></div></div>
        </div>`;
        renderTrendChart(stats.monthly_trend);
        renderTypeChart(stats.by_crime_type);
        renderDistrictChart(stats.top_districts);
        renderRecentTable(stats.recent_firs);
    } catch(e) { content.innerHTML = `<p class="text-red">Error loading dashboard: ${e.message}</p>`; }
}
function renderTrendChart(data) {
    if (!data || !data.length) return;
    new Chart(document.getElementById('trendChart'), {
        type: 'line', data: { labels: data.map(d => d.month), datasets: [{ label: 'FIRs', data: data.map(d => d.count), borderColor: '#00e5ff', backgroundColor: 'rgba(0,229,255,0.08)', fill: true, tension: 0.4, pointRadius: 2, pointHoverRadius: 5 }] },
        options: { responsive: true, maintainAspectRatio: false, scales: { x: { grid: { display: false } }, y: { beginAtZero: true } }, plugins: { legend: { display: false } } }
    });
}
function renderTypeChart(data) {
    if (!data || !data.length) return;
    const colors = Utils.chartColorArray();
    new Chart(document.getElementById('typeChart'), {
        type: 'doughnut', data: { labels: data.map(d => d.type), datasets: [{ data: data.map(d => d.count), backgroundColor: colors.slice(0, data.length), borderWidth: 0 }] },
        options: { responsive: true, maintainAspectRatio: false, cutout: '65%', plugins: { legend: { position: 'right', labels: { boxWidth: 10, padding: 8, font: { size: 11 } } } } }
    });
}
function renderDistrictChart(data) {
    if (!data || !data.length) return;
    new Chart(document.getElementById('districtChart'), {
        type: 'bar', data: { labels: data.map(d => d.name), datasets: [{ label: 'FIRs', data: data.map(d => d.count), backgroundColor: 'rgba(0,229,255,0.3)', borderColor: '#00e5ff', borderWidth: 1, borderRadius: 4 }] },
        options: { responsive: true, maintainAspectRatio: false, indexAxis: 'y', scales: { x: { beginAtZero: true, grid: { color: 'rgba(255,255,255,0.03)' } }, y: { grid: { display: false } } }, plugins: { legend: { display: false } } }
    });
}
function renderRecentTable(firs) {
    const el = document.getElementById('recentTable');
    if (!firs || !firs.length) { el.innerHTML = '<p class="text-muted" style="padding:16px">No recent FIRs</p>'; return; }
    el.innerHTML = `<table class="data-table"><thead><tr><th>FIR No.</th><th>Crime</th><th>District</th><th>Status</th><th>Date</th></tr></thead><tbody>${
        firs.map(f => `<tr><td class="mono text-cyan">${f.fir_number}</td><td>${f.crime_type}</td><td>${f.district_name}</td><td>${Utils.statusBadge(f.status)}</td><td>${Utils.formatDate(f.date_reported)}</td></tr>`).join('')
    }</tbody></table>`;
}
document.addEventListener('DOMContentLoaded', loadDashboard);
