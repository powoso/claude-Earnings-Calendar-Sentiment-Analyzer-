/* ================================================================
   Ticker deep-dive page logic — research + brief generation.
   ================================================================ */

let _research = null;
let _briefData = null;
const _plotlyDark = {
    paper_bgcolor: 'rgba(0,0,0,0)',
    plot_bgcolor: 'rgba(0,0,0,0)',
    font: { color: '#9ca3af' },
    xaxis: { gridcolor: 'rgba(255,255,255,0.04)', color: '#9ca3af' },
    yaxis: { gridcolor: 'rgba(255,255,255,0.06)', color: '#9ca3af', zerolinecolor: 'rgba(255,255,255,0.1)' },
    margin: { t: 30, b: 40, l: 50, r: 20 },
};

/* ---------- Init ---------- */
async function initTickerPage(ticker) {
    try {
        const resp = await fetch('/api/research/' + encodeURIComponent(ticker));
        if (!resp.ok) throw new Error(`HTTP ${resp.status}`);
        _research = await resp.json();

        document.getElementById('research-loading').classList.add('hidden');
        document.getElementById('research-content').classList.remove('hidden');

        populateHeader(_research);
        populateKpis(_research);
        renderSentiment(_research.sentiment);
        renderHistorical(_research.historical_reactions);
        renderNews(_research.headlines);
    } catch (err) {
        document.getElementById('loading-text').textContent = 'Failed to load research: ' + err.message;
    }
}


/* ---------- Header ---------- */
function populateHeader(data) {
    const ev = data.event;
    document.getElementById('company-name').textContent = ev.company_name;
    document.getElementById('earnings-date').textContent =
        'Earnings Date: ' + ev.earnings_date + (ev.time_of_day !== 'unknown' ? ' · ' + ev.time_of_day.replace(/_/g, ' ') : '');

    if (data.sentiment && data.sentiment.sources.length) {
        const score = data.sentiment.overall_score;
        const badge = document.getElementById('sentiment-badge');
        badge.classList.remove('hidden');
        if (score > 0.1) {
            badge.textContent = 'BULLISH';
            badge.className = 'badge badge-bullish';
        } else if (score < -0.1) {
            badge.textContent = 'BEARISH';
            badge.className = 'badge badge-bearish';
        } else {
            badge.textContent = 'NEUTRAL';
            badge.className = 'badge badge-neutral';
        }
    }
}


/* ---------- KPIs ---------- */
function populateKpis(data) {
    const ev = data.event;
    document.getElementById('kpi-eps').textContent = ev.eps_estimate != null ? '$' + ev.eps_estimate.toFixed(2) : '—';
    document.getElementById('kpi-rev').textContent = ev.revenue_estimate != null ? fmtRev(ev.revenue_estimate) : '—';

    if (data.sentiment && data.sentiment.sources.length) {
        const score = data.sentiment.overall_score;
        document.getElementById('kpi-sentiment').textContent = (score >= 0 ? '+' : '') + score.toFixed(3);
        const label = document.getElementById('kpi-sentiment-label');
        if (score > 0.1) { label.textContent = 'Bullish'; label.className = 'metric-delta positive'; }
        else if (score < -0.1) { label.textContent = 'Bearish'; label.className = 'metric-delta negative'; }
        else { label.textContent = 'Neutral'; label.className = 'metric-delta neutral'; }
    }

    const moves = data.historical_reactions
        .filter(r => r.next_day_move_pct != null)
        .map(r => Math.abs(r.next_day_move_pct));
    if (moves.length) {
        const avg = (moves.reduce((a, b) => a + b, 0) / moves.length).toFixed(1);
        document.getElementById('kpi-avg-move').textContent = '±' + avg + '%';
    }
}


/* ---------- Tabs ---------- */
function switchTab(name) {
    document.querySelectorAll('.tab-panel').forEach(p => p.classList.add('hidden'));
    document.querySelectorAll('.tab-btn').forEach(b => b.classList.remove('active'));
    document.getElementById('tab-' + name).classList.remove('hidden');
    event.currentTarget.classList.add('active');
}


/* ---------- Sentiment ---------- */
function renderSentiment(sentiment) {
    if (!sentiment || !sentiment.sources.length) {
        document.getElementById('tab-sentiment').innerHTML =
            '<div class="glass-card p-8 text-center text-gray-500">No sentiment data available. Configure Reddit or StockTwits API keys for social data.</div>';
        return;
    }

    const donut = [{
        labels: ['Bullish', 'Bearish', 'Neutral'],
        values: [sentiment.bullish_count, sentiment.bearish_count, sentiment.neutral_count],
        type: 'pie',
        hole: 0.55,
        marker: { colors: ['#00cc96', '#ef553b', '#636efa'] },
        textinfo: 'label+percent',
        textfont: { size: 13, color: '#e5e7eb' },
        hoverlabel: { bgcolor: '#1f2937', font: { color: '#e5e7eb' } },
    }];
    Plotly.newPlot('chart-sentiment-donut', donut, {
        ..._plotlyDark,
        showlegend: false,
        margin: { t: 10, b: 10, l: 10, r: 10 },
    }, { responsive: true, displayModeBar: false });

    const bar = [{
        x: ['Bullish', 'Bearish', 'Neutral'],
        y: [sentiment.bullish_count, sentiment.bearish_count, sentiment.neutral_count],
        type: 'bar',
        marker: { color: ['#00cc96', '#ef553b', '#636efa'], opacity: 0.9 },
        text: [sentiment.bullish_count, sentiment.bearish_count, sentiment.neutral_count],
        textposition: 'auto',
        textfont: { color: '#e5e7eb' },
        hoverlabel: { bgcolor: '#1f2937', font: { color: '#e5e7eb' } },
    }];
    Plotly.newPlot('chart-sentiment-bar', bar, {
        ..._plotlyDark,
        yaxis: { ..._plotlyDark.yaxis, title: 'Posts' },
    }, { responsive: true, displayModeBar: false });

    document.getElementById('sentiment-sources').textContent = 'Sources: ' + sentiment.sources.join(', ');

    if (sentiment.sample_posts && sentiment.sample_posts.length) {
        document.getElementById('sample-posts').classList.remove('hidden');
        document.getElementById('sample-posts-list').innerHTML = sentiment.sample_posts.slice(0, 8).map(post =>
            `<div class="glass-card p-3 text-sm text-gray-400 leading-relaxed">${escHtml(post.substring(0, 300))}</div>`
        ).join('');
    }
}


/* ---------- Historical ---------- */
function renderHistorical(reactions) {
    if (!reactions || !reactions.length) {
        document.getElementById('tab-historical').innerHTML =
            '<div class="glass-card p-8 text-center text-gray-500">No historical earnings reaction data available.</div>';
        return;
    }

    const rev = [...reactions].reverse();
    const quarters = rev.map(r => r.quarter);
    const surprises = rev.map(r => r.surprise_pct ?? 0);
    const moves = rev.map(r => r.next_day_move_pct ?? 0);
    const moveColors = moves.map(m => m >= 0 ? '#00cc96' : '#ef553b');

    const traces = [
        {
            name: 'EPS Surprise %',
            x: quarters, y: surprises,
            type: 'bar',
            marker: { color: '#636efa', opacity: 0.85 },
            hoverlabel: { bgcolor: '#1f2937', font: { color: '#e5e7eb' } },
        },
        {
            name: 'Next-Day Move %',
            x: quarters, y: moves,
            type: 'bar',
            marker: { color: moveColors, opacity: 0.85 },
            hoverlabel: { bgcolor: '#1f2937', font: { color: '#e5e7eb' } },
        },
    ];

    Plotly.newPlot('chart-historical', traces, {
        ..._plotlyDark,
        barmode: 'group',
        yaxis: { ..._plotlyDark.yaxis, title: 'Percentage (%)' },
        legend: { orientation: 'h', yanchor: 'bottom', y: 1.05, xanchor: 'right', x: 1, font: { color: '#9ca3af' } },
        shapes: [{ type: 'line', x0: 0, x1: 1, xref: 'paper', y0: 0, y1: 0, line: { color: 'rgba(255,255,255,0.1)', dash: 'dot' } }],
    }, { responsive: true, displayModeBar: false });

    // Stats
    const validMoves = reactions.filter(r => r.next_day_move_pct != null).map(r => r.next_day_move_pct);
    const beats = reactions.filter(r => r.surprise_pct != null && r.surprise_pct > 0).length;
    const total = reactions.filter(r => r.surprise_pct != null).length;
    const avg = validMoves.length ? (validMoves.reduce((a, b) => a + Math.abs(b), 0) / validMoves.length).toFixed(1) : '—';

    document.getElementById('historical-stats').innerHTML = `
        <div class="metric-card">
            <div class="metric-label">Avg Absolute Move</div>
            <div class="metric-value">${avg}%</div>
        </div>
        <div class="metric-card">
            <div class="metric-label">Beat Rate</div>
            <div class="metric-value">${total ? beats + '/' + total : '—'}</div>
        </div>
        <div class="metric-card">
            <div class="metric-label">Last Move</div>
            <div class="metric-value ${validMoves.length && validMoves[0] >= 0 ? 'text-green-400' : 'text-red-400'}">
                ${validMoves.length ? (validMoves[0] >= 0 ? '+' : '') + validMoves[0].toFixed(1) + '%' : '—'}
            </div>
        </div>
    `;

    // Table
    document.getElementById('historical-body').innerHTML = reactions.map(r => `
        <tr>
            <td class="font-medium text-gray-300">${escHtml(r.quarter)}</td>
            <td class="text-right font-mono text-gray-300">${r.eps_estimate != null ? '$' + r.eps_estimate.toFixed(2) : '—'}</td>
            <td class="text-right font-mono text-gray-300">${r.eps_actual != null ? '$' + r.eps_actual.toFixed(2) : '—'}</td>
            <td class="text-right font-mono ${r.surprise_pct != null && r.surprise_pct >= 0 ? 'text-green-400' : 'text-red-400'}">
                ${r.surprise_pct != null ? (r.surprise_pct >= 0 ? '+' : '') + r.surprise_pct.toFixed(1) + '%' : '—'}
            </td>
            <td class="text-right font-mono ${r.next_day_move_pct != null && r.next_day_move_pct >= 0 ? 'text-green-400' : 'text-red-400'}">
                ${r.next_day_move_pct != null ? (r.next_day_move_pct >= 0 ? '+' : '') + r.next_day_move_pct.toFixed(1) + '%' : '—'}
            </td>
        </tr>
    `).join('');
}


/* ---------- News ---------- */
function renderNews(headlines) {
    if (!headlines || !headlines.length) {
        document.getElementById('news-list').classList.add('hidden');
        document.getElementById('news-empty').classList.remove('hidden');
        return;
    }

    document.getElementById('news-list').innerHTML = headlines.map(h => {
        const pubStr = h.published ? new Date(h.published).toLocaleDateString('en-US', { month: 'short', day: 'numeric', year: 'numeric' }) : '';
        return `
            <div class="news-item">
                <a href="${escAttr(h.url)}" target="_blank" rel="noopener">${escHtml(h.title)}</a>
                <div class="news-meta">${escHtml(h.source)}${pubStr ? ' · ' + pubStr : ''}</div>
                ${h.snippet ? '<div class="news-snippet">' + escHtml(h.snippet.substring(0, 250)) + '</div>' : ''}
            </div>
        `;
    }).join('');
}


/* ---------- Brief generation ---------- */
async function generateBrief(ticker) {
    const placeholder = document.getElementById('brief-placeholder');
    const loading = document.getElementById('brief-loading');
    const result = document.getElementById('brief-result');

    if (placeholder) placeholder.classList.add('hidden');
    result.classList.add('hidden');
    loading.classList.remove('hidden');

    try {
        const resp = await fetch('/api/brief/' + encodeURIComponent(ticker), { method: 'POST' });
        if (!resp.ok) throw new Error(`HTTP ${resp.status}`);
        _briefData = await resp.json();

        loading.classList.add('hidden');
        result.classList.remove('hidden');

        // Render markdown
        document.getElementById('brief-content').innerHTML = marked.parse(_briefData.full_brief || '');
    } catch (err) {
        loading.classList.add('hidden');
        if (placeholder) {
            placeholder.classList.remove('hidden');
            placeholder.innerHTML = `
                <div class="text-red-400 mb-4">&#x26a0;&#xfe0f; Failed to generate brief: ${escHtml(err.message)}</div>
                <p class="text-gray-500 text-sm mb-6">Make sure <code>ANTHROPIC_API_KEY</code> is set in your environment.</p>
                <button onclick="generateBrief('${escAttr(ticker)}')" class="btn-primary">Try Again</button>
            `;
        }
    }
}

function downloadBrief(ticker) {
    if (!_briefData) return;
    const md = `# ${_briefData.ticker} — ${_briefData.company_name}\n\n**Earnings Date:** ${_briefData.earnings_date}\n\n${_briefData.full_brief}`;
    const blob = new Blob([md], { type: 'text/markdown' });
    const a = document.createElement('a');
    a.href = URL.createObjectURL(blob);
    a.download = ticker + '_earnings_brief.md';
    a.click();
    URL.revokeObjectURL(a.href);
}


/* ---------- Helpers ---------- */
function fmtRev(val) {
    if (val == null) return '—';
    if (Math.abs(val) >= 1e9) return '$' + (val / 1e9).toFixed(2) + 'B';
    if (Math.abs(val) >= 1e6) return '$' + (val / 1e6).toFixed(1) + 'M';
    return '$' + val.toLocaleString();
}

function escHtml(str) {
    const d = document.createElement('div');
    d.textContent = str || '';
    return d.innerHTML;
}

function escAttr(str) {
    return (str || '').replace(/&/g, '&amp;').replace(/"/g, '&quot;').replace(/'/g, '&#39;').replace(/</g, '&lt;').replace(/>/g, '&gt;');
}
