/* CCTNS-GridX — Hotspot Map */
let map, heatLayer, markerGroup;

async function loadHotspotMap() {
    if (!initPage('hotspot_map', 'Crime Hotspot Map')) return;
    document.getElementById('page-content').innerHTML = `
    <div class="map-page animate-fadeInUp">
        <div class="map-controls" id="mapControls">
            <label>Crime Type: <select class="select-styled" id="filterCrimeType" onchange="refreshMap()"><option value="">All Types</option></select></label>
            <label>District: <select class="select-styled" id="filterDistrict" onchange="refreshMap()"><option value="">All Districts</option></select></label>
            <label>View: <select class="select-styled" id="mapView" onchange="refreshMap()"><option value="heatmap">Heatmap</option><option value="clusters">Clusters</option><option value="points">Points</option><option value="zones">Zone Map</option><option value="stations">Station Map</option></select></label>
            <button class="btn btn-sm btn-primary" onclick="refreshMap()">Refresh</button>
        </div>
        <div class="map-stats-bar" id="mapStats"></div>
        <div class="map-wrapper"><div id="crimeMap" class="map-container"></div></div>
    </div>`;
    map = L.map('crimeMap', { zoomControl: true }).setView([10.85, 78.65], 7);
    L.tileLayer('https://{s}.basemaps.cartocdn.com/dark_all/{z}/{x}/{y}{r}.png', { attribution: '&copy; CartoDB', maxZoom: 19 }).addTo(map);
    markerGroup = L.layerGroup().addTo(map);
    try {
        const [types, districts] = await Promise.all([Utils.get('/api/maps/crime-types'), Utils.get('/api/fir/districts/all')]);
        const typeSelect = document.getElementById('filterCrimeType');
        (types.crime_types||[]).forEach(t => { const o = document.createElement('option'); o.value = t; o.textContent = t; typeSelect.appendChild(o); });
        const distSelect = document.getElementById('filterDistrict');
        (districts.districts||[]).forEach(d => { const o = document.createElement('option'); o.value = d.id; o.textContent = d.name; distSelect.appendChild(o); });
    } catch(e) {}
    refreshMap();
}

async function refreshMap() {
    const crimeType = document.getElementById('filterCrimeType').value;
    const districtId = document.getElementById('filterDistrict').value;
    const view = document.getElementById('mapView').value;
    markerGroup.clearLayers();
    if (heatLayer) { map.removeLayer(heatLayer); heatLayer = null; }
    try {
        if (view === 'heatmap') await loadHeatmap(crimeType, districtId);
        else if (view === 'clusters') await loadClusters(crimeType, districtId);
        else if (view === 'points') await loadPoints(crimeType, districtId);
        else if (view === 'zones') await loadZones();
        else if (view === 'stations') await loadStations();
    } catch(e) { Utils.showToast('Map load error', 'error'); console.error(e); }
}

async function loadHeatmap(ct, did) {
    const params = new URLSearchParams(); if (ct) params.set('crime_type', ct); if (did) params.set('district_id', did);
    const data = await Utils.get(`/api/maps/heatmap?${params}`);
    if (data.points && data.points.length) {
        const pts = data.points.map(p => [p.lat, p.lng, p.intensity]);
        heatLayer = L.heatLayer(pts, { radius: 25, blur: 15, maxZoom: 17, gradient: { 0.0: '#00e5ff', 0.3: '#00e676', 0.5: '#ffd600', 0.7: '#ff6d00', 1.0: '#ff1744' } }).addTo(map);
    }
    updateStats({ 'Heat Points': data.total || 0, 'Filter': ct || 'All', 'View': 'Heatmap' });
}

async function loadClusters(ct, did) {
    const params = new URLSearchParams(); if (ct) params.set('crime_type', ct); if (did) params.set('district_id', did);
    const data = await Utils.get(`/api/maps/hotspots?${params}`);
    const clusters = data.clusters || [];

    // Color palette for clusters — distinct colors per cluster to differentiate them
    const clusterColors = [
        '#ff1744', '#00e5ff', '#e040fb', '#00e676', '#ff6d00',
        '#ffd600', '#3d5afe', '#1de9b6', '#f50057', '#76ff03',
        '#ff9100', '#00b0ff', '#d500f9', '#64dd17', '#ff3d00',
        '#40c4ff', '#ea80fc', '#b2ff59', '#ff6e40', '#18ffff'
    ];

    clusters.forEach((c, idx) => {
        // Cap radius: min 200m, max 10km so clusters are visible but not huge blobs
        const radiusMeters = Math.min(Math.max(c.radius_km * 1000, 200), 10000);
        const color = clusterColors[idx % clusterColors.length];
        const opacity = Math.min(0.15 + c.intensity * 0.3, 0.45);

        const circle = L.circle([c.center.lat, c.center.lng], {
            radius: radiusMeters,
            color: color,
            fillColor: color,
            fillOpacity: opacity,
            weight: 2,
            dashArray: '5, 5'
        }).addTo(markerGroup);

        // Add a label at the center
        const label = L.divIcon({
            className: '',
            html: `<div style="color:${color};font-size:12px;font-weight:700;text-shadow:0 0 6px #000,0 0 3px #000;white-space:nowrap;text-align:center;transform:translate(-50%,-50%)">${c.crime_count} crimes<br><span style="font-size:10px;opacity:0.8">${c.dominant_crime_type}</span></div>`,
            iconSize: [100, 30],
            iconAnchor: [50, 15]
        });
        L.marker([c.center.lat, c.center.lng], { icon: label }).addTo(markerGroup);

        circle.bindPopup(`<div class="popup-title">Hotspot #${idx + 1}</div>
            <div class="popup-row"><span class="popup-label">Crimes:</span><span class="popup-value">${c.crime_count}</span></div>
            <div class="popup-row"><span class="popup-label">Type:</span><span class="popup-value">${c.dominant_crime_type}</span></div>
            <div class="popup-row"><span class="popup-label">Intensity:</span><span class="popup-value">${(c.intensity*100).toFixed(0)}%</span></div>
            <div class="popup-row"><span class="popup-label">Radius:</span><span class="popup-value">${c.radius_km.toFixed(1)} km</span></div>
            <div class="popup-row"><span class="popup-label">Districts:</span><span class="popup-value">${(c.districts||[]).join(', ')}</span></div>`);
    });
    updateStats({ 'Clusters': clusters.length, 'Total Crimes': data.total_crimes || 0, 'Noise Points': data.noise_points || 0 });
}

async function loadPoints(ct, did) {
    const params = new URLSearchParams(); if (ct) params.set('crime_type', ct); if (did) params.set('district_id', did); params.set('limit', '1000');
    const data = await Utils.get(`/api/maps/crime-points?${params}`);
    const colors = {
        'Property Crime': '#e74c3c', 'Violent Crime': '#ff1744', 'Crime Against Women': '#e91e63',
        'Economic Crime': '#f39c12', 'Public Order': '#3498db', 'Narcotics': '#9b59b6',
        'Excise': '#1abc9c', 'Kidnapping': '#e67e22', 'Communal': '#ff6d00',
        'Vice Crime': '#8e44ad', 'Arms': '#78909c', 'Mining': '#2ecc71',
        'Animal Protection': '#16a085', 'Atrocity': '#d35400', 'Anti-National': '#546e7a'
    };
    (data.points||[]).forEach(p => {
        const col = colors[p.crime_type] || '#95a5a6';
        L.circleMarker([p.latitude, p.longitude], { radius: 4, color: col, fillColor: col, fillOpacity: 0.7, weight: 1 }).addTo(markerGroup)
        .bindPopup(`<div class="popup-title">${p.fir_number}</div>
            <div class="popup-row"><span class="popup-label">Type:</span><span class="popup-value">${p.crime_type}</span></div>
            <div class="popup-row"><span class="popup-label">Section:</span><span class="popup-value">${p.act_name} ${p.section}</span></div>
            <div class="popup-row"><span class="popup-label">Station:</span><span class="popup-value">${p.station_name}</span></div>
            <div class="popup-row"><span class="popup-label">Date:</span><span class="popup-value">${p.date_of_crime}</span></div>`);
    });
    updateStats({ 'Crime Points': data.total || 0, 'Filter': ct || 'All' });
}

async function loadZones() {
    const data = await Utils.get('/api/maps/zones');
    const zones = data.zones || [];

    // Use RISK LEVEL for circle border color + DOMINANT CRIME for fill color
    const RISK_COLORS = {
        'Critical': '#ff1744',
        'High': '#ff6d00',
        'Medium': '#ffd600',
        'Low': '#00e676'
    };

    const CRIME_FILL_COLORS = {
        'Property Crime': '#e74c3c',
        'Violent Crime': '#ff1744',
        'Crime Against Women': '#e91e63',
        'Economic Crime': '#f39c12',
        'Public Order': '#3498db',
        'Narcotics': '#9b59b6',
        'Excise': '#1abc9c',
        'Kidnapping': '#e67e22',
        'Communal': '#ff6d00',
        'Vice Crime': '#8e44ad',
        'Arms': '#78909c',
        'Mining': '#2ecc71',
        'Animal Protection': '#16a085',
        'Atrocity': '#d35400',
        'Anti-National': '#546e7a'
    };

    zones.forEach(z => {
        const riskColor = RISK_COLORS[z.risk_level] || '#ffd600';
        const fillColor = CRIME_FILL_COLORS[z.dominant_crime] || '#95a5a6';
        const radiusMeters = Math.max(Math.sqrt(z.area_sq_km) * 400, 8000);

        const circle = L.circle([z.lat, z.lng], {
            radius: radiusMeters,
            color: riskColor,
            fillColor: fillColor,
            fillOpacity: 0.25,
            weight: 3,
            dashArray: z.risk_level === 'Critical' ? '' : '6, 4'
        }).addTo(markerGroup);

        // Label
        const labelColor = riskColor;
        const label = L.divIcon({
            className: '',
            html: `<div style="color:${labelColor};font-size:11px;font-weight:700;text-shadow:0 0 6px #000,0 0 3px #000;text-align:center;white-space:nowrap;transform:translate(-50%,-50%)">${z.name}<br><span style="font-size:9px;opacity:0.8">${z.total_crimes} crimes | ${z.risk_level}</span></div>`,
            iconSize: [120, 30],
            iconAnchor: [60, 15]
        });
        L.marker([z.lat, z.lng], { icon: label }).addTo(markerGroup);

        circle.bindPopup(`<div class="popup-title">${z.name}</div>
            <div class="popup-row"><span class="popup-label">Crimes:</span><span class="popup-value">${z.total_crimes}</span></div>
            <div class="popup-row"><span class="popup-label">Density:</span><span class="popup-value">${z.crime_density}/sq km</span></div>
            <div class="popup-row"><span class="popup-label">Dominant:</span><span class="popup-value">${z.dominant_crime}</span></div>
            <div class="popup-row"><span class="popup-label">Risk:</span><span class="popup-value" style="color:${riskColor};font-weight:700">${z.risk_level} (${(z.risk_score*100).toFixed(0)}%)</span></div>
            <div class="popup-row"><span class="popup-label">Population:</span><span class="popup-value">${(z.population/1000).toFixed(0)}K</span></div>`);
    });
    updateStats({ 'Zones': zones.length, 'View': 'Zonal Mapping' });
}

async function loadStations() {
    const data = await Utils.get('/api/maps/station-mapping');
    const TYPE_COLORS = { 'Regular': '#00e5ff', 'Women': '#e91e63', 'Cyber': '#7c4dff', 'Railway': '#ff6d00', 'Traffic': '#ffd600' };
    (data.stations||[]).forEach(s => {
        const col = TYPE_COLORS[s.station_type] || '#00e5ff';
        const icon = L.divIcon({ className: '', html: `<div style="background:${col};width:12px;height:12px;border-radius:50%;border:2px solid #fff;box-shadow:0 0 6px ${col}"></div>`, iconSize: [16, 16] });
        L.marker([s.lat, s.lng], { icon }).addTo(markerGroup)
        .bindPopup(`<div class="popup-title">${s.name}</div>
            <div class="popup-row"><span class="popup-label">District:</span><span class="popup-value">${s.district_name}</span></div>
            <div class="popup-row"><span class="popup-label">Type:</span><span class="popup-value">${s.station_type}</span></div>
            <div class="popup-row"><span class="popup-label">FIRs:</span><span class="popup-value">${s.total_crimes}</span></div>
            <div class="popup-row"><span class="popup-label">Pending:</span><span class="popup-value">${s.pending||0}</span></div>`);
    });
    updateStats({ 'Stations': (data.stations||[]).length, 'View': 'Station Mapping' });
}

function updateStats(obj) {
    document.getElementById('mapStats').innerHTML = Object.entries(obj).map(([k,v]) => `<div class="map-stat"><div class="stat-label">${k}</div><div class="stat-value">${v}</div></div>`).join('');
}
document.addEventListener('DOMContentLoaded', loadHotspotMap);
