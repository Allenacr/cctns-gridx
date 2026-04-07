/* CCTNS-GridX — Behavioral Analysis */
async function loadBehavioral() {
    if (!initPage('behavioral', 'Behavioral Analysis')) return;
    document.getElementById('page-content').innerHTML = `
    <div class="animate-fadeInUp">
        <div class="map-controls mb-lg">
            <label>Crime Type: <select class="select-styled" id="behCrimeType" onchange="refreshBehavioral()"><option value="">All Types</option></select></label>
            <label>District: <select class="select-styled" id="behDistrict" onchange="refreshBehavioral()"><option value="">All Districts</option></select></label>
        </div>
        <div class="analytics-grid">
            <div class="chart-container"><div class="chart-header"><div class="chart-title">⏰ Hourly Crime Distribution</div></div><div class="chart-body"><canvas id="hourlyChart"></canvas></div></div>
            <div class="chart-container"><div class="chart-header"><div class="chart-title">📅 Day of Week Pattern</div></div><div class="chart-body"><canvas id="dailyChart"></canvas></div></div>
        </div>
        <div class="analytics-grid mt-lg">
            <div class="chart-container"><div class="chart-header"><div class="chart-title">📆 Monthly Pattern</div></div><div class="chart-body"><canvas id="monthlyChart"></canvas></div></div>
            <div class="chart-container"><div class="chart-header"><div class="chart-title">🌡️ Seasonal Analysis</div></div><div class="chart-body"><canvas id="seasonalChart"></canvas></div></div>
        </div>
        <div class="analytics-grid mt-lg">
            <div class="chart-container"><div class="chart-header"><div class="chart-title">👤 Accused Age Distribution</div></div><div class="chart-body"><canvas id="ageChart"></canvas></div></div>
            <div class="chart-container"><div class="chart-header"><div class="chart-title">🔁 Repeat Offenders</div></div><div class="table-scroll" id="repeatTable"></div></div>
        </div>
        <div class="prediction-card mt-lg" id="insights"><div class="chart-title mb-md">🧠 Key Behavioral Insights</div><div id="insightsContent"></div></div>
    </div>`;
    const [types, districts] = await Promise.all([Utils.get('/api/maps/crime-types'), Utils.get('/api/fir/districts/all')]);
    const tSel = document.getElementById('behCrimeType');
    (types.crime_types||[]).forEach(t => { const o = document.createElement('option'); o.value = t; o.textContent = t; tSel.appendChild(o); });
    const dSel = document.getElementById('behDistrict');
    (districts.districts||[]).forEach(d => { const o = document.createElement('option'); o.value = d.id; o.textContent = d.name; dSel.appendChild(o); });
    refreshBehavioral();
}

const behCharts = {};
async function refreshBehavioral() {
    const ct = document.getElementById('behCrimeType').value;
    const did = document.getElementById('behDistrict').value;
    Object.values(behCharts).forEach(c => c.destroy());
    try {
        const [temporal, seasonal, demo, repeat] = await Promise.all([
            Utils.get(`/api/analytics/temporal-patterns?${new URLSearchParams({...(ct?{crime_type:ct}:{}), ...(did?{district_id:did}:{})})}`),
            Utils.get(`/api/analytics/seasonal-analysis?${did?`district_id=${did}`:''}`),
            Utils.get(`/api/analytics/demographics?${ct?`crime_type=${ct}`:''}`),
            Utils.get('/api/analytics/repeat-offenders')
        ]);
        // Hourly
        const hours = Array.from({length:24},(_,i)=>`${i}:00`);
        behCharts.hourly = new Chart(document.getElementById('hourlyChart'), {
            type: 'bar', data: { labels: hours, datasets: [{ data: temporal.hourly_distribution, backgroundColor: temporal.hourly_distribution.map((_,i)=>i>=22||i<=5?'rgba(255,23,68,0.4)':'rgba(0,229,255,0.3)'), borderWidth: 0, borderRadius: 2 }] },
            options: { responsive: true, maintainAspectRatio: false, plugins: { legend: { display: false } }, scales: { x: { grid: { display: false } }, y: { beginAtZero: true } } }
        });
        // Daily
        const days = ['Mon','Tue','Wed','Thu','Fri','Sat','Sun'];
        behCharts.daily = new Chart(document.getElementById('dailyChart'), {
            type: 'radar', data: { labels: days, datasets: [{ data: temporal.daily_distribution, borderColor: '#00e5ff', backgroundColor: 'rgba(0,229,255,0.15)', pointBackgroundColor: '#00e5ff', pointRadius: 4 }] },
            options: { responsive: true, maintainAspectRatio: false, plugins: { legend: { display: false } }, scales: { r: { grid: { color: 'rgba(255,255,255,0.06)' }, pointLabels: { color: '#a0a0b8' }, ticks: { display: false } } } }
        });
        // Monthly
        const months = ['Jan','Feb','Mar','Apr','May','Jun','Jul','Aug','Sep','Oct','Nov','Dec'];
        behCharts.monthly = new Chart(document.getElementById('monthlyChart'), {
            type: 'line', data: { labels: months, datasets: [{ data: temporal.monthly_distribution, borderColor: '#e040fb', backgroundColor: 'rgba(224,64,251,0.1)', fill: true, tension: 0.4, pointRadius: 3 }] },
            options: { responsive: true, maintainAspectRatio: false, plugins: { legend: { display: false } }, scales: { x: { grid: { display: false } }, y: { beginAtZero: true } } }
        });
        // Seasonal
        const sd = seasonal.seasonal_data || {};
        const sLabels = Object.keys(sd);
        behCharts.seasonal = new Chart(document.getElementById('seasonalChart'), {
            type: 'bar', data: { labels: sLabels, datasets: [{ data: sLabels.map(s => sd[s].total_crimes), backgroundColor: ['#ff6d00','#2979ff','#00e676','#e040fb','#ffd600'], borderWidth: 0, borderRadius: 6 }] },
            options: { responsive: true, maintainAspectRatio: false, plugins: { legend: { display: false } }, scales: { x: { grid: { display: false } }, y: { beginAtZero: true } } }
        });
        // Age
        const ageGroups = demo.accused?.age_groups || {};
        behCharts.age = new Chart(document.getElementById('ageChart'), {
            type: 'doughnut', data: { labels: Object.keys(ageGroups), datasets: [{ data: Object.values(ageGroups), backgroundColor: Utils.chartColorArray(), borderWidth: 0 }] },
            options: { responsive: true, maintainAspectRatio: false, cutout: '55%', plugins: { legend: { position: 'right', labels: { boxWidth: 10, font: { size: 11 } } } } }
        });
        // Repeat offenders
        const reps = repeat.repeat_offenders || [];
        document.getElementById('repeatTable').innerHTML = `<table class="data-table"><thead><tr><th>Name</th><th>Crimes</th><th>Types</th><th>Districts</th></tr></thead><tbody>${
            reps.slice(0,10).map(r => `<tr><td>${r.name}</td><td class="mono text-red">${r.crime_count}</td><td>${(r.crime_types||[]).join(', ')}</td><td>${(r.districts||[]).join(', ')}</td></tr>`).join('')
        }</tbody></table>`;
        // Insights
        document.getElementById('insightsContent').innerHTML = `
            <div class="flex gap-lg flex-wrap">
                <div class="map-stat"><div class="stat-label">Peak Hour</div><div class="stat-value text-cyan">${temporal.peak_hour_label}</div></div>
                <div class="map-stat"><div class="stat-label">Peak Day</div><div class="stat-value text-magenta">${temporal.peak_day}</div></div>
                <div class="map-stat"><div class="stat-label">Peak Month</div><div class="stat-value text-orange">${temporal.peak_month}</div></div>
                <div class="map-stat"><div class="stat-label">Night Crime</div><div class="stat-value text-red">${temporal.night_crime_pct}%</div></div>
                <div class="map-stat"><div class="stat-label">Weekend Crime</div><div class="stat-value text-yellow">${temporal.weekend_crime_pct}%</div></div>
                <div class="map-stat"><div class="stat-label">Most Dangerous</div><div class="stat-value text-red">${seasonal.most_dangerous_season}</div></div>
                <div class="map-stat"><div class="stat-label">Accused Avg Age</div><div class="stat-value">${demo.accused?.avg_age || 'N/A'}</div></div>
                <div class="map-stat"><div class="stat-label">Repeat Offenders</div><div class="stat-value text-red">${repeat.total_repeat_offenders}</div></div>
            </div>`;
    } catch(e) { console.error(e); }
}
document.addEventListener('DOMContentLoaded', loadBehavioral);
