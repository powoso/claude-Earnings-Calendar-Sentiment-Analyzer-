/* ================================================================
   Dashboard page logic — calendar scanning and display.
   ================================================================ */

const WATCHLISTS = {
    top30: '',  // empty = server default
    mag7: 'AAPL,MSFT,GOOGL,AMZN,META,NVDA,TSLA',
    faang: 'AAPL,AMZN,META,GOOGL,NFLX,MSFT,NVDA,TSLA',
    semis: 'NVDA,AMD,INTC,AVGO,QCOM,MU,AMAT,LRCX',
    finance: 'JPM,GS,MS,BAC,WFC,C,BLK,SCHW',
    custom: '',
};

/* ---------- Init ---------- */
document.addEventListener('DOMContentLoaded', () => {
    const select = document.getElementById('watchlist-select');
    select.addEventListener('change', () => {
        document.getElementById('custom-tickers-wrap').classList.toggle('hidden', select.value !== 'custom');
    });
});


/* ---------- Scan ---------- */
async function scanCalendar() {
    const select = document.getElementById('watchlist-select');
    const days = document.getElementById('days-ahead').value;
    let tickers = WATCHLISTS[select.value] || '';

    if (select.value === 'custom') {
        tickers = document.getElementById('custom-tickers').value;
    }

    // Show loading
    showEl('loading');
    hideEl('empty-state');
    hideEl('calendar-section');
    hideEl('kpi-row');

    try {
        const params = new URLSearchParams({ days });
        if (tickers) params.set('tickers', tickers);

        const resp = await fetch('/api/calendar?' + params.toString());
        if (!resp.ok) throw new Error(`HTTP ${resp.status}`);
        const events = await resp.json();

        hideEl('loading');
        if (!events.length) {
            showEl('empty-state');
            document.querySelector('#empty-state h3').textContent = 'No Upcoming Earnings';
            document.querySelector('#empty-state p').textContent =
                'No earnings found in the specified window. Try a longer date range or different watchlist.';
            return;
        }

        renderKpis(events);
        renderTable(events);
        showEl('kpi-row');
        showEl('calendar-section');
    } catch (err) {
        hideEl('loading');
        showEl('empty-state');
        document.querySelector('#empty-state h3').textContent = 'Error';
        document.querySelector('#empty-state p').textContent = 'Failed to fetch earnings data: ' + err.message;
    }
}


/* ---------- Render KPIs ---------- */
function renderKpis(events) {
    const container = document.getElementById('kpi-row');
    const next = events[0];
    const today = new Date().toISOString().slice(0, 10);
    const daysUntil = Math.ceil((new Date(next.earnings_date) - new Date(today)) / 86400000);

    container.innerHTML = `
        <div class="metric-card">
            <div class="metric-label">Upcoming Earnings</div>
            <div class="metric-value">${events.length}</div>
        </div>
        <div class="metric-card">
            <div class="metric-label">Next Report</div>
            <div class="metric-value" style="font-size:1.25rem">${next.ticker}</div>
            <div class="metric-delta neutral">${next.earnings_date}</div>
        </div>
        <div class="metric-card">
            <div class="metric-label">Days Until Next</div>
            <div class="metric-value">${daysUntil}</div>
        </div>
        <div class="metric-card">
            <div class="metric-label">Companies</div>
            <div class="metric-value">${new Set(events.map(e => e.ticker)).size}</div>
        </div>
    `;
}


/* ---------- Render table ---------- */
function renderTable(events) {
    const body = document.getElementById('calendar-body');
    document.getElementById('event-count').textContent = `${events.length} events`;

    body.innerHTML = events.map(e => `
        <tr>
            <td class="font-medium text-gray-300">${e.earnings_date}</td>
            <td>
                <a href="/ticker/${encodeURIComponent(e.ticker)}" class="ticker-cell">${escHtml(e.ticker)}</a>
            </td>
            <td class="text-gray-400">${escHtml(e.company_name)}</td>
            <td class="text-right font-mono text-gray-300">${e.eps_estimate != null ? '$' + e.eps_estimate.toFixed(2) : '—'}</td>
            <td class="text-right font-mono text-gray-300">${fmtRev(e.revenue_estimate)}</td>
            <td class="text-gray-500 text-sm">${(e.time_of_day || 'unknown').replace(/_/g, ' ')}</td>
        </tr>
    `).join('');
}


/* ---------- Helpers ---------- */
function showEl(id) { document.getElementById(id).classList.remove('hidden'); }
function hideEl(id) { document.getElementById(id).classList.add('hidden'); }

function fmtRev(val) {
    if (val == null) return '—';
    if (Math.abs(val) >= 1e9) return '$' + (val / 1e9).toFixed(2) + 'B';
    if (Math.abs(val) >= 1e6) return '$' + (val / 1e6).toFixed(1) + 'M';
    return '$' + val.toLocaleString();
}

function escHtml(str) {
    const d = document.createElement('div');
    d.textContent = str;
    return d.innerHTML;
}
