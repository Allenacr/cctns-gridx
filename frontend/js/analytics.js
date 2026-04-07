/* CCTNS-GridX — Analytics & AI Predictions */
async function loadAnalytics() {
    if (!initPage('analytics', 'AI Predictions & Analytics')) return;
    document.getElementById('page-content').innerHTML = `
    <div class="animate-fadeInUp">
        <div class="analytics-grid">
            <div class="prediction-card"><div class="chart-header"><div class="chart-title">🤖 Crime Prediction</div><div class="chart-subtitle">Predict crime type for a location</div></div>
                <div class="form-grid" style="margin-top:12px">
                    <div class="form-group"><label class="form-label">Latitude</label><input type="number" step="0.001" class="form-input" id="predLat" value="13.08" min="7" max="14"></div>
                    <div class="form-group"><label class="form-label">Longitude</label><input type="number" step="0.001" class="form-input" id="predLng" value="80.27" min="76" max="81"></div>
                    <div class="form-group"><label class="form-label">Hour (0-23)</label><input type="number" class="form-input" id="predHour" value="22" min="0" max="23"></div>
                    <div class="form-group"><label class="form-label">Month (1-12)</label><input type="number" class="form-input" id="predMonth" value="6" min="1" max="12"></div>
                </div>
                <button class="btn btn-primary mt-md" onclick="runPrediction()">🔮 Predict Crime</button>
                <div id="predResult"></div>
            </div>
            <div class="chart-container"><div class="chart-header"><div class="chart-title">📊 Feature Importance</div></div><div class="chart-body"><canvas id="featureChart"></canvas></div></div>
        </div>
        <div class="analytics-grid mt-lg">
            <div class="chart-container"><div class="chart-header"><div class="chart-title">📈 Crime Forecast (Next 6 Months)</div></div><div class="chart-body"><canvas id="forecastChart"></canvas></div></div>
            <div class="chart-container"><div class="chart-header"><div class="chart-title">📊 Crime Type Trends</div></div><div class="chart-body"><canvas id="trendsChart"></canvas></div></div>
        </div>
        <div class="analytics-grid mt-lg">
            <div class="prediction-card analytics-full"><div class="chart-header"><div class="chart-title">🗺️ Seasonal Risk Map</div><div><label>Month: <select class="select-styled" id="riskMonth" onchange="loadRiskMap()">
                <option value="1">January</option><option value="2">February</option><option value="3">March</option><option value="4" selected>April</option><option value="5">May</option><option value="6">June</option><option value="7">July</option><option value="8">August</option><option value="9">September</option><option value="10">October</option><option value="11">November</option><option value="12">December</option></select></label></div></div>
                <div id="riskMapData" style="margin-top:12px"></div>
            </div>
        </div>
    </div>`;
    loadFeatureImportance(); loadForecast(); loadTrends(); loadRiskMap();
}

async function runPrediction() {
    const lat = document.getElementById('predLat').value;
    const lng = document.getElementById('predLng').value;
    const hour = document.getElementById('predHour').value;
    const month = document.getElementById('predMonth').value;
    try {
        const r = await Utils.get(`/api/analytics/predict?latitude=${lat}&longitude=${lng}&hour=${hour}&day_of_week=2&month=${month}&district_id=1`);
        const probs = r.all_probabilities || [];
        document.getElementById('predResult').innerHTML = `
            <div class="prediction-result mt-md"><div><div class="pred-type">${r.prediction}</div><div class="text-secondary mt-sm">Most likely crime type at this location & time</div></div><div class="pred-confidence">${(r.confidence*100).toFixed(1)}%</div></div>
            <div class="probability-bars mt-md">${probs.map(p => `<div class="prob-bar-row"><div class="prob-bar-label">${p.crime_type}</div><div class="prob-bar-track"><div class="prob-bar-fill" style="width:${p.probability*100}%"></div></div><div class="prob-bar-value">${(p.probability*100).toFixed(1)}%</div></div>`).join('')}</div>`;
    } catch(e) { Utils.showToast('Prediction failed', 'error'); }
}

async function loadFeatureImportance() {
    try {
        const r = await Utils.get('/api/analytics/feature-importance');
        const features = r.features || [];
        if (!features.length) return;
        new Chart(document.getElementById('featureChart'), {
            type: 'bar', data: { labels: features.map(f => f.feature), datasets: [{ data: features.map(f => f.importance), backgroundColor: Utils.chartColorArray().slice(0, features.length), borderWidth: 0, borderRadius: 4 }] },
            options: { responsive: true, maintainAspectRatio: false, indexAxis: 'y', plugins: { legend: { display: false } }, scales: { x: { beginAtZero: true }, y: { grid: { display: false } } } }
        });
    } catch(e) {}
}

async function loadForecast() {
    try {
        const r = await Utils.get('/api/analytics/forecast?months_ahead=6');
        if (r.error) return;
        const hist = r.historical || {};
        const fore = r.forecasts || [];
        const labels = [...(hist.months||[]), ...fore.map(f => f.month)];
        const actual = [...(hist.counts||[]), ...fore.map(() => null)];
        const predicted = [...(hist.counts||[]).map(() => null), ...fore.map(f => f.predicted_count)];
        new Chart(document.getElementById('forecastChart'), {
            type: 'line', data: { labels, datasets: [
                { label: 'Actual', data: actual, borderColor: '#00e5ff', backgroundColor: 'rgba(0,229,255,0.1)', fill: true, tension: 0.3, pointRadius: 2 },
                { label: 'Forecast', data: predicted, borderColor: '#e040fb', backgroundColor: 'rgba(224,64,251,0.1)', fill: true, borderDash: [5,5], tension: 0.3, pointRadius: 3 }
            ] },
            options: { responsive: true, maintainAspectRatio: false, scales: { x: { grid: { display: false } }, y: { beginAtZero: true } } }
        });
    } catch(e) {}
}

async function loadTrends() {
    try {
        const r = await Utils.get('/api/analytics/crime-trends');
        const dist = r.crime_type_distribution || {};
        const labels = Object.keys(dist).slice(0, 8);
        const values = labels.map(l => dist[l]);
        new Chart(document.getElementById('trendsChart'), {
            type: 'polarArea', data: { labels, datasets: [{ data: values, backgroundColor: Utils.chartBgArray(), borderColor: Utils.chartColorArray(), borderWidth: 1 }] },
            options: { responsive: true, maintainAspectRatio: false, plugins: { legend: { position: 'right', labels: { font: { size: 10 }, boxWidth: 10 } } } }
        });
    } catch(e) {}
}

async function loadRiskMap() {
    const month = document.getElementById('riskMonth').value;
    try {
        const r = await Utils.get(`/api/analytics/seasonal-risk?month=${month}`);
        const risks = r.district_risks || [];
        document.getElementById('riskMapData').innerHTML = `<table class="data-table"><thead><tr><th>District</th><th>Crimes (Month)</th><th>Total Crimes</th><th>Risk Score</th><th>Risk Level</th></tr></thead><tbody>${
            risks.slice(0, 15).map(d => `<tr><td>${d.district_name}</td><td class="mono">${d.month_crimes}</td><td class="mono">${d.total_crimes}</td><td class="mono">${(d.risk_score*100).toFixed(0)}%</td><td>${Utils.riskBadge(d.risk_level)}</td></tr>`).join('')
        }</tbody></table>`;
    } catch(e) {}
}
document.addEventListener('DOMContentLoaded', loadAnalytics);
