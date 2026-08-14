// Screen Watch dashboard — reads data/stocks.json (git-as-DB), renders a
// sortable value-ranked table. Two ranking modes: primary (Value 50, 4-factor)
// and alt (Enhanced, 3-factor).

let STOCKS = [];
let rankMode = 'primary'; // 'primary' | 'alt'
let sortKey = 'value_score';
let sortAsc = false;
let query = '';

const $ = (id) => document.getElementById(id);

function esc(s) {
  if (s == null) return '';
  return String(s).replace(/&/g, '&amp;').replace(/</g, '&lt;').replace(/>/g, '&gt;');
}
function fmt(v, nd = 2) {
  return (typeof v === 'number') ? v.toLocaleString('en-IN', { maximumFractionDigits: nd }) : '—';
}
function median(arr) {
  const a = arr.filter((x) => typeof x === 'number').sort((x, y) => x - y);
  if (!a.length) return null;
  const m = Math.floor(a.length / 2);
  return a.length % 2 ? a[m] : (a[m - 1] + a[m]) / 2;
}

async function load() {
  try {
    const r = await fetch('./data/stocks.json?_=' + Date.now());
    const data = await r.json();
    STOCKS = data.stocks || [];
    $('updated').textContent = data.ts
      ? 'updated ' + new Date(data.ts).toLocaleString('en-IN', {
          day: '2-digit', month: 'short', hour: '2-digit', minute: '2-digit' })
      : '';
    renderTiles();
    render();
  } catch (e) {
    $('updated').textContent = 'data load failed';
    $('empty').hidden = false;
    $('empty').textContent = 'Could not load data/stocks.json — ' + e.message;
  }
}

function activeRank(s) { return rankMode === 'alt' ? s.alt_rank : s.rank; }
function activeScore(s) { return rankMode === 'alt' ? s.alt_value_score : s.value_score; }

function renderTiles() {
  $('k-count').textContent = STOCKS.length || '—';
  const byRank = [...STOCKS].sort((a, b) => (a.rank || 1e9) - (b.rank || 1e9));
  $('k-cheap').textContent = byRank.length ? byRank[0].ticker : '—';
  const pe = median(STOCKS.map((s) => s.pe));
  const dy = median(STOCKS.map((s) => s.dividend_yield));
  $('k-pe').textContent = pe != null ? fmt(pe, 1) : '—';
  $('k-dy').textContent = dy != null ? fmt(dy, 2) + '%' : '—';
}

function render() {
  const q = query.trim().toLowerCase();
  let rows = STOCKS.filter((s) =>
    !q || (s.ticker || '').toLowerCase().includes(q) || (s.name || '').toLowerCase().includes(q));

  rows.sort((a, b) => {
    let va = sortKey === 'rank' ? activeRank(a) : (sortKey === 'value_score' ? activeScore(a) : a[sortKey]);
    let vb = sortKey === 'rank' ? activeRank(b) : (sortKey === 'value_score' ? activeScore(b) : b[sortKey]);
    if (va == null && vb == null) return 0;
    if (va == null) return 1;
    if (vb == null) return -1;
    if (typeof va === 'string') return sortAsc ? va.localeCompare(vb) : vb.localeCompare(va);
    return sortAsc ? va - vb : vb - va;
  });

  const tbody = $('rows');
  $('empty').hidden = rows.length > 0;
  tbody.innerHTML = rows.map((s) => {
    const rank = activeRank(s);
    const topCls = (rank && rank <= 10) ? ' top' : '';
    const url = 'https://www.screener.in/company/' + esc(s.ticker) + '/';
    const cell = (v, nd, unit = '') =>
      `<td class="num${v == null ? ' dim' : ''}">${v == null ? '—' : fmt(v, nd) + unit}</td>`;
    return `<tr>
      <td class="num td-rank${topCls}">${rank ?? '—'}</td>
      <td class="td-ticker"><a href="${url}" target="_blank" rel="noopener">${esc(s.ticker)}</a></td>
      <td class="name-col" title="${esc(s.name)}">${esc(s.name) || '—'}</td>
      ${cell(s.current_price, 0)}
      ${cell(s.pe, 2)}
      ${cell(s.pb, 2)}
      ${cell(s.dividend_yield, 2)}
      ${cell(s.roce, 1)}
      ${cell(s.roe, 1)}
      <td class="num"><span class="val-pill">${fmt(activeScore(s), 3)}</span></td>
    </tr>`;
  }).join('');

  document.querySelectorAll('.sortable').forEach((th) => {
    th.classList.toggle('sorted', th.dataset.sort === sortKey);
    th.classList.toggle('asc', th.dataset.sort === sortKey && sortAsc);
  });
}

function initSort() {
  document.querySelectorAll('.sortable').forEach((th) => {
    th.addEventListener('click', () => {
      const k = th.dataset.sort;
      if (sortKey === k) sortAsc = !sortAsc;
      else { sortKey = k; sortAsc = (k === 'rank' || k === 'ticker' || k === 'name'); }
      render();
    });
  });
}

function initRankToggle() {
  document.querySelectorAll('.rt').forEach((btn) => {
    btn.addEventListener('click', () => {
      document.querySelectorAll('.rt').forEach((b) => b.classList.remove('active'));
      btn.classList.add('active');
      rankMode = btn.dataset.rank;
      if (sortKey === 'value_score' || sortKey === 'rank') render();
      else render();
    });
  });
}

function initTheme() {
  const saved = localStorage.getItem('sw-theme');
  if (saved) document.documentElement.setAttribute('data-theme', saved);
  const btn = $('theme-btn');
  const sync = () => {
    btn.textContent = document.documentElement.getAttribute('data-theme') === 'dark' ? '☾' : '☀';
  };
  sync();
  btn.addEventListener('click', () => {
    const next = document.documentElement.getAttribute('data-theme') === 'dark' ? 'light' : 'dark';
    document.documentElement.setAttribute('data-theme', next);
    localStorage.setItem('sw-theme', next);
    sync();
  });
}

document.addEventListener('DOMContentLoaded', () => {
  initTheme();
  initSort();
  initRankToggle();
  $('q').addEventListener('input', (e) => { query = e.target.value; render(); });
  load();
});
