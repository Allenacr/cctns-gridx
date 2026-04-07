/* CCTNS-GridX — FIR Entry Form Logic */
let districts = [], stations = [], categories = [];

async function loadFIRPage() {
    if (!initPage('fir_entry', 'Register FIR')) return;
    try {
        const [dRes, cRes] = await Promise.all([Utils.get('/api/fir/districts/all'), Utils.get('/api/fir/categories/all')]);
        districts = dRes.districts || [];
        categories = cRes.categories || [];
        renderFIRForm();
    } catch(e) { Utils.showToast('Failed to load form data', 'error'); }
}

function renderFIRForm() {
    const distOpts = districts.map(d => `<option value="${d.id}">${d.name}</option>`).join('');
    const grouped = {};
    categories.forEach(c => { if (!grouped[c.act_name]) grouped[c.act_name] = []; grouped[c.act_name].push(c); });
    let catOpts = '';
    for (const [act, cats] of Object.entries(grouped)) {
        catOpts += `<optgroup label="${act}">${cats.map(c => `<option value="${c.id}">Sec. ${c.section} — ${c.description}</option>`).join('')}</optgroup>`;
    }
    document.getElementById('page-content').innerHTML = `
    <div class="form-page animate-fadeInUp">
        <div id="fir-form-container">
            <form id="firForm" onsubmit="submitFIR(event)">
                <div class="form-section"><div class="form-section-title">📍 Crime Details</div><div class="form-grid">
                    <div class="form-group"><label class="form-label">District <span class="required">*</span></label><select class="form-select" id="district_id" required onchange="loadStations()">${distOpts}</select></div>
                    <div class="form-group"><label class="form-label">Police Station <span class="required">*</span></label><select class="form-select" id="police_station_id" required><option>Select district first</option></select></div>
                    <div class="form-group"><label class="form-label">Crime Category <span class="required">*</span></label><select class="form-select" id="crime_category_id" required>${catOpts}</select></div>
                    <div class="form-group"><label class="form-label">Date of Crime <span class="required">*</span></label><input type="date" class="form-input" id="date_of_crime" required></div>
                    <div class="form-group"><label class="form-label">Time of Crime</label><input type="time" class="form-input" id="time_of_crime"></div>
                </div></div>
                <div class="form-section"><div class="form-section-title">📍 Location</div><div class="form-grid">
                    <div class="form-group"><label class="form-label">Latitude <span class="required">*</span></label><input type="number" step="0.000001" class="form-input" id="latitude" required min="7" max="14" placeholder="e.g. 13.0827"></div>
                    <div class="form-group"><label class="form-label">Longitude <span class="required">*</span></label><input type="number" step="0.000001" class="form-input" id="longitude" required min="76" max="81" placeholder="e.g. 80.2707"></div>
                    <div class="form-group full-width"><label class="form-label">Address</label><input type="text" class="form-input" id="location_address" placeholder="Street, Area, City"></div>
                </div></div>
                <div class="form-section"><div class="form-section-title">👤 Complainant</div><div class="form-grid">
                    <div class="form-group"><label class="form-label">Name <span class="required">*</span></label><input type="text" class="form-input" id="complainant_name" required minlength="2"></div>
                    <div class="form-group"><label class="form-label">Age</label><input type="number" class="form-input" id="complainant_age" min="1" max="120"></div>
                    <div class="form-group"><label class="form-label">Gender</label><select class="form-select" id="complainant_gender"><option value="">-</option><option>Male</option><option>Female</option><option>Other</option></select></div>
                    <div class="form-group"><label class="form-label">Contact</label><input type="tel" class="form-input" id="complainant_contact"></div>
                </div></div>
                <div class="form-section"><div class="form-section-title">🔍 Accused</div><div class="form-grid">
                    <div class="form-group"><label class="form-label">Name</label><input type="text" class="form-input" id="accused_name"></div>
                    <div class="form-group"><label class="form-label">Age</label><input type="number" class="form-input" id="accused_age" min="1" max="120"></div>
                    <div class="form-group"><label class="form-label">Gender</label><select class="form-select" id="accused_gender"><option value="">-</option><option>Male</option><option>Female</option><option>Other</option></select></div>
                </div></div>
                <div class="form-section"><div class="form-section-title">📝 Description</div><div class="form-grid">
                    <div class="form-group full-width"><label class="form-label">Incident Description <span class="required">*</span></label><textarea class="form-textarea" id="description" required minlength="10" placeholder="Detailed account of the incident..."></textarea></div>
                    <div class="form-group full-width"><label class="form-label">Modus Operandi</label><input type="text" class="form-input" id="modus_operandi" placeholder="How was the crime committed?"></div>
                </div></div>
                <div class="form-actions"><button type="reset" class="btn btn-secondary">Clear</button><button type="submit" class="btn btn-primary" id="submitBtn">📋 Register FIR</button></div>
            </form>
        </div>
    </div>`;
    loadStations();
}

async function loadStations() {
    const did = document.getElementById('district_id').value;
    try {
        const res = await Utils.get(`/api/fir/stations/all?district_id=${did}`);
        stations = res.stations || [];
        document.getElementById('police_station_id').innerHTML = stations.map(s => `<option value="${s.id}">${s.name}</option>`).join('');
    } catch(e) {}
}

async function submitFIR(e) {
    e.preventDefault();
    const btn = document.getElementById('submitBtn');
    btn.disabled = true; btn.textContent = 'Submitting...';
    const fields = ['district_id','police_station_id','crime_category_id','date_of_crime','time_of_crime','latitude','longitude','location_address','complainant_name','complainant_age','complainant_gender','complainant_contact','accused_name','accused_age','accused_gender','description','modus_operandi'];
    const body = {};
    fields.forEach(f => {
        const el = document.getElementById(f);
        if (!el) return;
        let v = el.value;
        if (['district_id','police_station_id','crime_category_id','complainant_age','accused_age'].includes(f)) v = v ? parseInt(v) : null;
        if (['latitude','longitude'].includes(f)) v = v ? parseFloat(v) : null;
        if (v !== null && v !== '' && v !== undefined) body[f] = v;
    });
    try {
        const res = await Utils.post('/api/fir/', body);
        document.getElementById('fir-form-container').innerHTML = `
            <div class="form-success animate-fadeInUp">
                <div class="success-icon">✅</div>
                <h2>FIR Registered Successfully!</h2>
                <p class="text-secondary mt-sm">The FIR has been registered and synced with CCTNS</p>
                <div class="fir-number">${res.fir_number}</div>
                <div class="mt-lg"><button onclick="renderFIRForm()" class="btn btn-primary">Register Another FIR</button>
                <a href="/hotspot_map" class="btn btn-secondary mt-sm">View on Map</a></div>
            </div>`;
        Utils.showToast('FIR registered successfully!', 'success');
    } catch(err) { Utils.showToast(err.message, 'error'); btn.disabled = false; btn.textContent = '📋 Register FIR'; }
}
document.addEventListener('DOMContentLoaded', loadFIRPage);
