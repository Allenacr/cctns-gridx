/* CCTNS-GridX — Shared Utilities */
const API_BASE = '';

const Utils = {
    getToken() { return sessionStorage.getItem('cctns_token'); },
    setToken(t) { sessionStorage.setItem('cctns_token', t); },
    getUser() { try { return JSON.parse(sessionStorage.getItem('cctns_user')); } catch { return null; } },
    setUser(u) { sessionStorage.setItem('cctns_user', JSON.stringify(u)); },
    logout() { sessionStorage.removeItem('cctns_token'); sessionStorage.removeItem('cctns_user'); window.location.href = '/'; },
    isLoggedIn() { return !!this.getToken(); },

    async api(endpoint, options = {}) {
        const token = this.getToken();
        const headers = { 'Content-Type': 'application/json', ...(options.headers || {}) };
        if (token) headers['Authorization'] = `Bearer ${token}`;
        try {
            const res = await fetch(`${API_BASE}${endpoint}`, { ...options, headers });
            if (res.status === 401) { this.logout(); return null; }
            const data = await res.json();
            if (!res.ok) {
                if (Array.isArray(data.detail) && data.detail.length > 0) {
                    throw new Error(`${data.detail[0].loc[data.detail[0].loc.length - 1]}: ${data.detail[0].msg}`);
                }
                throw new Error(data.detail || 'API Error');
            }
            return data;
        } catch (err) {
            console.error(`API Error [${endpoint}]:`, err);
            throw err;
        }
    },

    async get(endpoint) { return this.api(endpoint); },
    async post(endpoint, body) { return this.api(endpoint, { method: 'POST', body: JSON.stringify(body) }); },
    async put(endpoint, body) { return this.api(endpoint, { method: 'PUT', body: JSON.stringify(body) }); },

    showToast(message, type = 'info') {
        let container = document.getElementById('toast-container');
        if (!container) {
            container = document.createElement('div');
            container.id = 'toast-container';
            container.className = 'toast-container';
            document.body.appendChild(container);
        }
        const icons = { success: '✅', error: '❌', info: 'ℹ️', warning: '⚠️' };
        const toast = document.createElement('div');
        toast.className = `toast toast-${type}`;
        toast.innerHTML = `<span>${icons[type] || ''}</span><span>${message}</span>`;
        container.appendChild(toast);
        setTimeout(() => { toast.style.opacity = '0'; setTimeout(() => toast.remove(), 300); }, 4000);
    },

    formatNumber(n) {
        if (n >= 1000000) return (n / 1000000).toFixed(1) + 'M';
        if (n >= 1000) return (n / 1000).toFixed(1) + 'K';
        return n.toString();
    },

    formatDate(d) {
        if (!d) return 'N/A';
        try { return new Date(d).toLocaleDateString('en-IN', { day: '2-digit', month: 'short', year: 'numeric' }); }
        catch { return d; }
    },

    riskBadge(level) {
        const cls = { Critical: 'badge-critical', High: 'badge-high', Medium: 'badge-medium', Low: 'badge-low' };
        return `<span class="badge ${cls[level] || 'badge-info'}">${level}</span>`;
    },

    statusBadge(status) {
        const colors = {
            'Registered': 'badge-info', 'Under Investigation': 'badge-medium',
            'Charge Sheet Filed': 'badge-high', 'Closed': 'badge-low', 'Undetected': 'badge-critical'
        };
        return `<span class="badge ${colors[status] || 'badge-info'}">${status}</span>`;
    },

    chartColors: {
        cyan: '#00e5ff', magenta: '#e040fb', orange: '#ff6d00', green: '#00e676',
        red: '#ff1744', yellow: '#ffd600', blue: '#2979ff', purple: '#7c4dff',
        teal: '#1de9b6', pink: '#f50057', lime: '#76ff03', amber: '#ffab00',
    },
    chartColorArray() { return Object.values(this.chartColors); },
    chartBgArray() { return Object.values(this.chartColors).map(c => c + '22'); },

    createChartDefaults() {
        if (typeof Chart === 'undefined') return;
        Chart.defaults.color = '#a0a0b8';
        Chart.defaults.borderColor = 'rgba(255,255,255,0.06)';
        Chart.defaults.font.family = "'Inter', sans-serif";
        Chart.defaults.font.size = 12;
        Chart.defaults.plugins.legend.labels.usePointStyle = true;
        Chart.defaults.plugins.legend.labels.pointStyleWidth = 10;
        Chart.defaults.plugins.tooltip.backgroundColor = 'rgba(13,13,20,0.95)';
        Chart.defaults.plugins.tooltip.borderColor = 'rgba(0,229,255,0.2)';
        Chart.defaults.plugins.tooltip.borderWidth = 1;
        Chart.defaults.plugins.tooltip.cornerRadius = 8;
        Chart.defaults.plugins.tooltip.padding = 12;
    }
};
