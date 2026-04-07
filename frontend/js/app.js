/* CCTNS-GridX — App Core: Sidebar + Auth Guard */
function buildSidebar(activePage) {
    const user = Utils.getUser() || {};
    const initials = (user.full_name || 'U').split(' ').map(w => w[0]).join('').slice(0, 2);
    return `
    <aside class="sidebar" id="sidebar">
        <div class="sidebar-brand">
            <div class="brand-icon">GX</div>
            <div class="brand-text">
                <div class="brand-name">CCTNS GridX</div>
                <div class="brand-sub">Tamil Nadu Police</div>
            </div>
        </div>
        <nav class="sidebar-nav">
            <div class="nav-section">
                <div class="nav-section-title">Overview</div>
                <a href="/dashboard" class="nav-item ${activePage==='dashboard'?'active':''}"><span class="nav-icon">📊</span><span>Dashboard</span></a>
                <a href="/fir_entry" class="nav-item ${activePage==='fir_entry'?'active':''}"><span class="nav-icon">📝</span><span>Register FIR</span></a>
            </div>
            <div class="nav-section">
                <div class="nav-section-title">Mapping</div>
                <a href="/hotspot_map" class="nav-item ${activePage==='hotspot_map'?'active':''}"><span class="nav-icon">🔥</span><span>Crime Hotspots</span></a>
                <a href="/women_safety" class="nav-item ${activePage==='women_safety'?'active':''}"><span class="nav-icon">🛡️</span><span>Women Safety</span></a>
                <a href="/accident_zones" class="nav-item ${activePage==='accident_zones'?'active':''}"><span class="nav-icon">⚠️</span><span>Accident Zones</span></a>
            </div>
            <div class="nav-section">
                <div class="nav-section-title">Intelligence</div>
                <a href="/analytics" class="nav-item ${activePage==='analytics'?'active':''}"><span class="nav-icon">🤖</span><span>AI Predictions</span></a>
                <a href="/behavioral" class="nav-item ${activePage==='behavioral'?'active':''}"><span class="nav-icon">🧠</span><span>Behavioral Analysis</span></a>
                <a href="/patrol" class="nav-item ${activePage==='patrol'?'active':''}"><span class="nav-icon">🚔</span><span>Patrol Routes</span></a>
            </div>
        </nav>
        <div class="sidebar-footer">
            <div class="user-avatar">${initials}</div>
            <div class="user-info">
                <div class="user-name">${user.full_name || 'Officer'}</div>
                <div class="user-rank">${user.rank || ''} • ${user.role || ''}</div>
            </div>
            <button class="logout-btn" onclick="Utils.logout()" title="Logout">⏻</button>
        </div>
    </aside>`;
}

function buildHeader(title, breadcrumb) {
    return `
    <header class="top-header">
        <div class="header-left">
            <div>
                <div class="page-title">${title}</div>
                <div class="breadcrumb">CCTNS GridX / <span>${breadcrumb || title}</span></div>
            </div>
        </div>
        <div class="header-right">
            <div class="cctns-status"><span class="status-dot"></span> CCTNS Linked</div>
        </div>
    </header>`;
}

function initPage(pageName, pageTitle) {
    if (!Utils.isLoggedIn()) { window.location.href = '/'; return false; }
    document.getElementById('sidebar-root').innerHTML = buildSidebar(pageName);
    document.getElementById('header-root').innerHTML = buildHeader(pageTitle);
    Utils.createChartDefaults();
    return true;
}
