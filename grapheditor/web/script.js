/* ============================================================
   0. Проверка Chart.js
   ============================================================ */
if (typeof Chart === 'undefined') {
  document.body.insertAdjacentHTML('afterbegin',
    '<div style="background:#dc3545;color:#fff;padding:12px;margin:10px 0;border-radius:6px">' +
    '⚠️ Chart.js не загрузился. Проверьте соединение или подключите библиотеку локально.</div>');
}

/* ============================================================
   1. Константы и состояние
   ============================================================ */
const $ = id => document.getElementById(id);
const ctx = $('myChart').getContext('2d');

const CIRCULAR_TYPES = ['pie', 'doughnut', 'polarArea', 'radar'];
const SLICE_TYPES    = ['pie', 'doughnut', 'polarArea'];
const XY_TYPES       = ['line', 'scatter', 'bar'];

const isCircular = () => CIRCULAR_TYPES.includes($('chartType').value);
const isXY       = () => XY_TYPES.includes($('chartType').value);

let points = [
  { x: 1, y: 10 }, { x: 2, y: 20 }, { x: 3, y: 15 },
  { x: 4, y: 25 }, { x: 5, y: 18 }
];
let chart = null;
let dragging = null;

const viewState = {
  showX: true, showY: true, showDel: true,
  showLabels: true, showPresets: true, showAnims: true, showTable: true
};

/* ============================================================
   2. История (undo / redo)
   ============================================================ */
const history = { stack: [], pos: -1 };

function getState() {
  return {
    version: 1,
    points: JSON.parse(JSON.stringify(points)),
    chartType: $('chartType').value,
    title: $('chartTitle').value,
    xLabel: $('xLabel').value,
    yLabel: $('yLabel').value,
    xMin: $('xMin').value, xMax: $('xMax').value, xStep: $('xStep').value,
    yMin: $('yMin').value, yMax: $('yMax').value, yStep: $('yStep').value,
    showX: viewState.showX, showY: viewState.showY, showDel: viewState.showDel,
    showLabels: viewState.showLabels, showPresets: viewState.showPresets,
    showAnims: viewState.showAnims, showTable: viewState.showTable,
    fontFamily: $('fontFamily').value,
    fontSize: $('fontSize').value,
    animations: $('animationsEnabled').checked,
    animDuration: $('animDuration').value,
    animDelay: $('animDelay').value,
    animEasing: $('animEasing').value,
    animType: $('animType').value,
    animSpeed: $('animSpeed').value,
    animAmp: $('animAmp').value
  };
}

function getProjectState() {
  return { ...getState(), theme: document.body.classList.contains('dark') ? 'dark' : 'light' };
}

function setState(state) {
  if (!state) return;
  hardStopAnimation();

  points = Array.isArray(state.points) ? JSON.parse(JSON.stringify(state.points)) : [];
  $('chartType').value = state.chartType || 'line';
  $('chartTitle').value = state.title || 'Мой график';
  $('xLabel').value = state.xLabel || 'X';
  $('yLabel').value = state.yLabel || 'Y';
  $('xMin').value = state.xMin || '';
  $('xMax').value = state.xMax || '';
  $('xStep').value = state.xStep || '';
  $('yMin').value = state.yMin || '';
  $('yMax').value = state.yMax || '';
  $('yStep').value = state.yStep || '';

  viewState.showX = state.showX !== false;
  viewState.showY = state.showY !== false;
  viewState.showDel = state.showDel !== false;
  viewState.showLabels = state.showLabels !== false;
  viewState.showPresets = state.showPresets !== false;
  viewState.showAnims = state.showAnims !== false;
  viewState.showTable = state.showTable !== false;
  $('toggleColX').checked = viewState.showX;
  $('toggleColY').checked = viewState.showY;
  $('toggleColDel').checked = viewState.showDel;
  $('toggleBlockLabels').checked = viewState.showLabels;
  $('toggleBlockPresets').checked = viewState.showPresets;
  $('toggleBlockAnims').checked = viewState.showAnims;
  $('toggleBlockTable').checked = viewState.showTable;

  if (state.fontFamily) $('fontFamily').value = state.fontFamily;
  if (state.fontSize)   $('fontSize').value = state.fontSize;
  $('animationsEnabled').checked = state.animations !== false;
  if (state.animDuration !== undefined) $('animDuration').value = state.animDuration;
  if (state.animDelay !== undefined)    $('animDelay').value    = state.animDelay;
  if (state.animEasing)                 $('animEasing').value   = state.animEasing;
  if (state.animType)                   $('animType').value     = state.animType;
  if (state.animSpeed) {
    $('animSpeed').value = state.animSpeed;
    $('animSpeedVal').textContent = parseFloat(state.animSpeed).toFixed(1) + '×';
  }
  if (state.animAmp) {
    $('animAmp').value = state.animAmp;
    $('animAmpVal').textContent = parseFloat(state.animAmp).toFixed(2);
  }

  applyFont();
  renderChart();
}

function setProjectState(state) {
  setState(state);
  if (state.theme === 'dark') document.body.classList.add('dark');
  else if (state.theme === 'light') document.body.classList.remove('dark');
  applyThemeToChart();
}

function snapshot() {
  const state = getState();
  const json = JSON.stringify(state);
  if (history.pos >= 0 && JSON.stringify(history.stack[history.pos]) === json) return;
  history.stack = history.stack.slice(0, history.pos + 1);
  history.stack.push(state);
  history.pos = history.stack.length - 1;
  if (history.stack.length > 100) { history.stack.shift(); history.pos--; }
  updateUndoRedoUI();
}

let snapshotTimer = null;
function scheduleSnapshot() {
  clearTimeout(snapshotTimer);
  snapshotTimer = setTimeout(snapshot, 500);
}

function undo() {
  if (history.pos <= 0) return;
  history.pos--;
  setState(history.stack[history.pos]);
  updateUndoRedoUI();
}
function redo() {
  if (history.pos >= history.stack.length - 1) return;
  history.pos++;
  setState(history.stack[history.pos]);
  updateUndoRedoUI();
}
function updateUndoRedoUI() {
  $('undoBtn').disabled = history.pos <= 0;
  $('redoBtn').disabled = history.pos >= history.stack.length - 1;
}

/* ============================================================
   3. Утилиты
   ============================================================ */
function makeColors(n, alpha) {
  const arr = [];
  for (let i = 0; i < n; i++) {
    const hue = Math.round((360 / Math.max(n, 1)) * i);
    arr.push(`hsla(${hue}, 70%, 55%, ${alpha})`);
  }
  return arr;
}

function parseX(raw) {
  if (raw === '') return null;
  const num = Number(raw);
  return Number.isFinite(num) && /^-?\d+(\.\d+)?([eE][+-]?\d+)?$/.test(raw) ? num : raw;
}

function applyFont() {
  document.documentElement.style.setProperty('--ui-font-family', $('fontFamily').value);
  document.documentElement.style.setProperty('--ui-font-size', (parseInt($('fontSize').value, 10) || 14) + 'px');
}

function applyAxisRange(scales) {
  if (!scales) return;
  const check = (v) => { const n = parseFloat(v); return Number.isFinite(n) ? n : null; };
  const xMin = check($('xMin').value), xMax = check($('xMax').value), xStep = check($('xStep').value);
  const yMin = check($('yMin').value), yMax = check($('yMax').value), yStep = check($('yStep').value);

  if (scales.x) {
    if (xMin !== null) scales.x.min = xMin; else delete scales.x.min;
    if (xMax !== null) scales.x.max = xMax; else delete scales.x.max;
    if (xStep !== null && xStep > 0) scales.x.ticks = { ...(scales.x.ticks || {}), stepSize: xStep };
    else if (scales.x.ticks) delete scales.x.ticks.stepSize;
  }
  if (scales.y) {
    if (yMin !== null) scales.y.min = yMin; else delete scales.y.min;
    if (yMax !== null) scales.y.max = yMax; else delete scales.y.max;
    if (yStep !== null && yStep > 0) scales.y.ticks = { ...(scales.y.ticks || {}), stepSize: yStep };
    else if (scales.y.ticks) delete scales.y.ticks.stepSize;
  }
}

function getBuiltinAnimationOptions() {
  if (!$('animationsEnabled').checked) return false;
  const duration = parseInt($('animDuration').value, 10) || 0;
  if (duration <= 0) return false;
  return {
    duration,
    delay: parseInt($('animDelay').value, 10) || 0,
    easing: $('animEasing').value
  };
}

/* ============================================================
   4. Построение графика
   ============================================================ */
function buildConfig() {
  const type   = $('chartType').value;
  const circ   = isCircular();
  const slices = SLICE_TYPES.includes(type);

  const baseSize = parseInt($('fontSize').value, 10) || 14;
  const family   = $('fontFamily').value;

  let data, scales = {};

  if (circ) {
    data = {
      labels: points.map(p => String(p.x)),
      datasets: [{
        label: 'Данные',
        data: points.map(p => p.y),
        backgroundColor: slices ? makeColors(points.length, .6) : 'rgba(54,162,235,.3)',
        borderColor:     slices ? makeColors(points.length, 1)  : 'rgba(54,162,235,1)',
        borderWidth: 1,
        fill: type === 'radar'
      }]
    };
    if (type === 'radar' || type === 'polarArea') scales = { r: { beginAtZero: true } };
  } else {
    const nums = points
      .filter(p => typeof p.x === 'number' && Number.isFinite(p.y))
      .sort((a, b) => a.x - b.x);

    data = {
      datasets: [{
        label: 'Данные',
        data: nums,
        parsing: false,
        backgroundColor: type === 'bar' ? 'rgba(255,99,132,.5)' : 'rgba(54,162,235,.3)',
        borderColor:     type === 'bar' ? 'rgba(255,99,132,1)'  : 'rgba(54,162,235,1)',
        borderWidth: 1,
        tension: 0.2,
        pointRadius: 6,
        pointHoverRadius: 8,
        showLine: type === 'line'
      }]
    };
    scales = {
      x: { type: 'linear', position: 'bottom', title: { display: true, text: $('xLabel').value } },
      y: { beginAtZero: true, title: { display: true, text: $('yLabel').value } }
    };
  }

  applyAxisRange(scales);

  return {
    type,
    data,
    options: {
      responsive: true,
      maintainAspectRatio: false,
      animation: getBuiltinAnimationOptions(),
      font: { family, size: baseSize },
      scales,
      plugins: {
        title: { display: true, text: $('chartTitle').value, font: { size: baseSize + 4, family } },
        legend: { display: circ, labels: { font: { family, size: baseSize } } },
        tooltip: {
          callbacks: {
            label: c => circ ? `${c.label}: ${c.parsed}` : `X: ${c.parsed.x}, Y: ${c.parsed.y}`
          }
        }
      }
    }
  };
}

function renderChart() {
  // Жёстко останавливаем непрерывную анимацию (данные восстанавливаем из backup)
  hardStopAnimation();

  try {
    if (chart) { chart.destroy(); chart = null; }
    chart = new Chart(ctx, buildConfig());
    applyThemeToChart();
    renderTable();
    applyViewState();
    applyBlocksVisibility();
    syncFieldsWithType();
  } catch (err) {
    console.error('Ошибка построения графика:', err);
    alert('Не удалось построить график: ' + err.message);
  }
}

function refreshChart(animate = true) {
  if (!chart) return;
  const type   = $('chartType').value;
  const circ   = isCircular();
  const slices = SLICE_TYPES.includes(type);

  if (circ) {
    chart.data.labels = points.map(p => String(p.x));
    chart.data.datasets[0].data = points.map(p => p.y);
    if (slices) {
      chart.data.datasets[0].backgroundColor = makeColors(points.length, .6);
      chart.data.datasets[0].borderColor     = makeColors(points.length, 1);
    }
  } else {
    chart.data.datasets[0].data = points
      .filter(p => typeof p.x === 'number' && Number.isFinite(p.y))
      .sort((a, b) => a.x - b.x);
  }

  chart.options.plugins.title.text = $('chartTitle').value;
  if (chart.options.scales.x) chart.options.scales.x.title.text = $('xLabel').value;
  if (chart.options.scales.y) chart.options.scales.y.title.text = $('yLabel').value;
  applyAxisRange(chart.options.scales);

  const useAnim = animate && !anim.rafId;
  chart.options.animation = useAnim ? getBuiltinAnimationOptions() : false;
  chart.update(useAnim ? undefined : 'none');
}

/* ============================================================
   5. Таблица
   ============================================================ */
function renderTable() {
  const tbody = document.querySelector('#pointsTable tbody');
  tbody.innerHTML = '';
  points.forEach((p, i) => {
    const tr = document.createElement('tr');

    const tdX = document.createElement('td');
    const inX = document.createElement('input');
    inX.type = 'text'; inX.value = p.x;
    inX.dataset.index = i; inX.dataset.field = 'x';
    tdX.appendChild(inX);

    const tdY = document.createElement('td');
    const inY = document.createElement('input');
    inY.type = 'number'; inY.step = 'any'; inY.value = p.y;
    inY.dataset.index = i; inY.dataset.field = 'y';
    tdY.appendChild(inY);

    const tdDel = document.createElement('td');
    const del = document.createElement('button');
    del.type = 'button'; del.textContent = '×';
    del.className = 'danger'; del.title = 'Удалить точку';
    del.addEventListener('click', () => {
      hardStopAnimation();
      points.splice(i, 1);
      refreshChart(); renderTable(); snapshot();
    });
    tdDel.appendChild(del);

    tr.append(tdX, tdY, tdDel);
    tbody.appendChild(tr);
  });
  applyViewState();
}

function applyViewState() {
  document.querySelectorAll('#pointsTable tr').forEach(tr => {
    const cells = tr.children;
    if (cells[0]) cells[0].style.display = viewState.showX ? '' : 'none';
    if (cells[1]) cells[1].style.display = viewState.showY ? '' : 'none';
    if (cells[2]) cells[2].style.display = viewState.showDel ? '' : 'none';
  });
}

function applyBlocksVisibility() {
  $('fieldsetLabels').style.display     = viewState.showLabels  ? '' : 'none';
  $('fieldsetPresets').style.display    = viewState.showPresets ? '' : 'none';
  $('fieldsetAnimations').style.display = viewState.showAnims   ? '' : 'none';
  $('fieldsetTable').style.display      = viewState.showTable   ? '' : 'none';
  $('toggleBlockLabels').checked  = viewState.showLabels;
  $('toggleBlockPresets').checked = viewState.showPresets;
  $('toggleBlockAnims').checked   = viewState.showAnims;
  $('toggleBlockTable').checked   = viewState.showTable;
}

document.querySelector('#pointsTable').addEventListener('input', e => {
  const input = e.target;
  if (input.tagName !== 'INPUT') return;
  hardStopAnimation();
  const i = Number(input.dataset.index);
  if (!points[i]) return;
  const raw = input.value.trim();
  if (input.dataset.field === 'x') {
    const parsed = parseX(raw);
    points[i].x = parsed === null ? '' : parsed;
  } else {
    const num = parseFloat(raw);
    points[i].y = Number.isFinite(num) ? num : 0;
  }
  refreshChart(false);
  scheduleSnapshot();
});

/* ============================================================
   6. Перетаскивание точек
   ============================================================ */
function setupDrag() {
  chart.canvas.addEventListener('mousedown', onMouseDown);
  window.addEventListener('mousemove', onMouseMove);
  window.addEventListener('mouseup', onMouseUp);
}
function onMouseDown(e) {
  if (anim.rafId) hardStopAnimation();
  if (!isXY() || $('chartType').value === 'bar') return;
  const els = chart.getElementsAtEventForMode(e, 'nearest', { intersect: true }, true);
  if (!els.length) return;
  const obj = chart.data.datasets[0].data[els[0].index];
  const idx = points.indexOf(obj);
  if (idx === -1) return;
  dragging = { index: idx, obj };
  chart.options.animation = false;
  chart.canvas.style.cursor = 'grabbing';
  e.preventDefault();
}
function onMouseMove(e) {
  if (!dragging) return;
  const rect = chart.canvas.getBoundingClientRect();
  const px = e.clientX - rect.left, py = e.clientY - rect.top;
  const area = chart.chartArea;
  if (px < area.left || px > area.right || py < area.top || py > area.bottom) return;
  let nx = chart.scales.x.getValueForPixel(px);
  let ny = chart.scales.y.getValueForPixel(py);
  if (nx == null || ny == null) return;
  nx = Math.round(nx * 100) / 100;
  ny = Math.round(ny * 100) / 100;
  dragging.obj.x = nx; dragging.obj.y = ny;
  const row = document.querySelector('#pointsTable tbody').children[dragging.index];
  if (row) {
    row.children[0].querySelector('input').value = nx;
    row.children[1].querySelector('input').value = ny;
  }
  chart.data.datasets[0].data = points
    .filter(p => typeof p.x === 'number' && Number.isFinite(p.y))
    .sort((a, b) => a.x - b.x);
  chart.update('none');
}
function onMouseUp() {
  if (!dragging) return;
  dragging = null;
  chart.options.animation = getBuiltinAnimationOptions();
  chart.canvas.style.cursor = '';
  snapshot();
}

/* ============================================================
   7. Тема
   ============================================================ */
function applyThemeToChart() {
  if (!chart) return;
  const dark = document.body.classList.contains('dark');
  const text = dark ? '#e8e8e8' : '#333333';
  const tick = dark ? '#bbbbbb' : '#666666';
  const grid = dark ? 'rgba(255,255,255,0.08)' : 'rgba(0,0,0,0.08)';

  if (chart.options.plugins.title) chart.options.plugins.title.color = text;
  if (chart.options.plugins.legend && chart.options.plugins.legend.labels) {
    chart.options.plugins.legend.labels.color = text;
  }
  ['x', 'y', 'r'].forEach(axis => {
    const sc = chart.options.scales && chart.options.scales[axis];
    if (!sc) return;
    sc.ticks = { ...(sc.ticks || {}), color: tick };
    sc.grid  = { ...(sc.grid  || {}), color: grid };
    if (sc.title) sc.title.color = text;
  });
  chart.update('none');
}

function toggleTheme() {
  document.body.classList.toggle('dark');
  try { localStorage.setItem('chartTheme', document.body.classList.contains('dark') ? 'dark' : 'light'); } catch (_) {}
  applyThemeToChart();
}

try { if (localStorage.getItem('chartTheme') === 'dark') document.body.classList.add('dark'); } catch (_) {}

/* ============================================================
   8. Непрерывная анимация (RAF)
   ============================================================ */
const anim = {
  rafId: null,
  startTime: 0,
  backup: null,
  type: null
};

function snapshotForAnim() {
  return {
    points: JSON.parse(JSON.stringify(points)),
    datasetRadius: chart?.data?.datasets?.[0]?.pointRadius,
    datasetBg:     chart?.data?.datasets?.[0]?.backgroundColor,
    datasetBorder: chart?.data?.datasets?.[0]?.borderColor
  };
}

function restoreFromAnim(snap) {
  if (!snap) return;
  points = JSON.parse(JSON.stringify(snap.points));
  if (chart) {
    const ds = chart.data.datasets[0];
    if (ds) {
      if (snap.datasetRadius !== undefined) ds.pointRadius = snap.datasetRadius;
      if (snap.datasetBg     !== undefined) ds.backgroundColor = snap.datasetBg;
      if (snap.datasetBorder !== undefined) ds.borderColor     = snap.datasetBorder;
    }
  }
}

function startAnimation() {
  if (!chart) return;
  if (anim.rafId) return;            // уже идёт

  anim.type = $('animType').value;
  anim.backup = snapshotForAnim();
  anim.startTime = performance.now();
  document.body.classList.add('animating');
  $('animStartBtn').disabled = true;
  $('animStopBtn').disabled = false;

  // На время цикла выключаем встроенные переходы Chart.js
  chart._savedAnimation = chart.options.animation;
  chart.options.animation = false;

  const tick = (now) => {
    if (!chart) { stopAnimation(); return; }
    const elapsed = (now - anim.startTime) / 1000;
    const speed   = parseFloat($('animSpeed').value) || 1;
    const amp     = parseFloat($('animAmp').value) || 0.3;
    const t       = elapsed * speed;

    try {
      applyAnimationFrame(anim.type, t, amp);
    } catch (err) {
      console.error('Ошибка в кадре анимации:', err);
      stopAnimation();
      return;
    }
    chart.update('none');
    anim.rafId = requestAnimationFrame(tick);
  };
  anim.rafId = requestAnimationFrame(tick);
}

function hardStopAnimation() {
  if (anim.rafId) {
    cancelAnimationFrame(anim.rafId);
    anim.rafId = null;
  }
  document.body.classList.remove('animating');
  $('animStartBtn').disabled = false;
  $('animStopBtn').disabled = true;

  if (anim.backup) restoreFromAnim(anim.backup);
  if (chart && chart._savedAnimation !== undefined) {
    chart.options.animation = chart._savedAnimation;
    delete chart._savedAnimation;
  }
  anim.backup = null;
  anim.type = null;
}

function stopAnimation() {
  if (!anim.rafId && !anim.backup) return;
  hardStopAnimation();
  if (chart) {
    refreshChart(false);
    renderTable();
  }
}

function applyAnimationFrame(type, t, amp) {
  const ds = chart.data.datasets[0];
  if (!ds) return;
  const isCirc = CIRCULAR_TYPES.includes($('chartType').value);
  const basePoints = anim.backup.points;

  switch (type) {

    case 'pulse': {
      if (isCirc) break;
      const r = 4 + Math.abs(Math.sin(t * Math.PI * 2)) * 10 * (0.5 + amp);
      ds.pointRadius = r;
      ds.pointHoverRadius = r + 2;
      break;
    }

    case 'wave': {
      if (isCirc) break;
      points = basePoints.map((p, i) => {
        const phase = i * 0.7;
        const base = typeof p.y === 'number' && p.y !== 0 ? p.y : 1;
        return { x: p.x, y: p.y + Math.sin(t * 2 + phase) * Math.abs(base) * amp };
      });
      ds.data = points
        .filter(p => typeof p.x === 'number' && Number.isFinite(p.y))
        .sort((a, b) => a.x - b.x);
      break;
    }

    case 'rainbow': {
      const shift = (t * 60) % 360;
      const isSlice = isCirc && SLICE_TYPES.includes($('chartType').value);
      if (isSlice) {
        const n = points.length;
        const bgs = [], brs = [];
        for (let i = 0; i < n; i++) {
          const hue = (shift + (360 / Math.max(n, 1)) * i) % 360;
          bgs.push(`hsla(${hue}, 70%, 55%, 0.6)`);
          brs.push(`hsla(${hue}, 70%, 55%, 1)`);
        }
        ds.backgroundColor = bgs;
        ds.borderColor = brs;
      } else {
        const hue = shift;
        ds.borderColor = `hsla(${hue}, 70%, 55%, 1)`;
        ds.backgroundColor = `hsla(${hue}, 70%, 55%, 0.3)`;
      }
      break;
    }

    case 'breathe': {
      if (isCirc) break;
      const factor = 1 + Math.sin(t * Math.PI) * amp;
      points = basePoints.map(p => ({
        x: p.x,
        y: typeof p.y === 'number' ? p.y * factor : p.y
      }));
      ds.data = points
        .filter(p => typeof p.x === 'number' && Number.isFinite(p.y))
        .sort((a, b) => a.x - b.x);
      break;
    }

    case 'appear': {
      const alpha = 0.1 + (Math.sin(t * 2) * 0.5 + 0.5) * 0.9;
      const isSlice = isCirc && SLICE_TYPES.includes($('chartType').value);
      if (isSlice) {
        const n = points.length;
        const bgs = [], brs = [];
        for (let i = 0; i < n; i++) {
          const hue = Math.round((360 / Math.max(n, 1)) * i);
          bgs.push(`hsla(${hue}, 70%, 55%, ${alpha * 0.6})`);
          brs.push(`hsla(${hue}, 70%, 55%, ${alpha})`);
        }
        ds.backgroundColor = bgs;
        ds.borderColor = brs;
      } else {
        ds.borderColor = `rgba(54, 162, 235, ${alpha})`;
        ds.backgroundColor = `rgba(54, 162, 235, ${alpha * 0.3})`;
      }
      break;
    }

    case 'slide': {
      if (isCirc) break;
      const offset = Math.sin(t * Math.PI * 2) * amp * 5;
      points = basePoints.map(p => ({
        x: typeof p.x === 'number' ? p.x + offset : p.x,
        y: p.y
      }));
      ds.data = points
        .filter(p => typeof p.x === 'number' && Number.isFinite(p.y))
        .sort((a, b) => a.x - b.x);
      break;
    }

    case 'rotate': {
      if (!isCirc) break;
      const n = basePoints.length;
      if (n === 0) break;
      const shift = Math.floor(t * 2) % n;
      const rotated = basePoints.slice(shift).concat(basePoints.slice(0, shift));
      chart.data.labels = rotated.map(p => String(p.x));
      ds.data = rotated.map(p => p.y);
      if (SLICE_TYPES.includes($('chartType').value)) {
        const bgs = [], brs = [];
        for (let i = 0; i < n; i++) {
          const hue = Math.round((360 / n) * i);
          bgs.push(`hsla(${hue}, 70%, 55%, 0.6)`);
          brs.push(`hsla(${hue}, 70%, 55%, 1)`);
        }
        ds.backgroundColor = bgs;
        ds.borderColor = brs;
      }
      break;
    }
  }
}

/* ============================================================
   9. Меню-бар
   ============================================================ */
function closeAllMenus() {
  document.querySelectorAll('.menu').forEach(m => m.classList.remove('open'));
}

document.querySelectorAll('.menu > .menu-btn').forEach(btn => {
  btn.addEventListener('click', e => {
    e.stopPropagation();
    const parent = btn.parentElement;
    const wasOpen = parent.classList.contains('open');
    closeAllMenus();
    if (!wasOpen) parent.classList.add('open');
  });
});
document.addEventListener('click', closeAllMenus);
document.querySelectorAll('.dropdown').forEach(d => d.addEventListener('click', e => e.stopPropagation()));
document.addEventListener('keydown', e => { if (e.key === 'Escape') closeAllMenus(); });

/* ============================================================
   10. Действия меню
   ============================================================ */
function handleAction(action) {
  switch (action) {
    case 'new': {
      if (!confirm('Создать новый проект? Несохранённые изменения будут потеряны.')) return;
      hardStopAnimation();
      points = [];
      $('chartTitle').value = 'Мой график';
      $('xLabel').value = 'X'; $('yLabel').value = 'Y';
      $('xMin').value = ''; $('xMax').value = ''; $('xStep').value = '';
      $('yMin').value = ''; $('yMax').value = ''; $('yStep').value = '';
      renderChart();
      snapshot();
      break;
    }
    case 'import-project': $('importFile').click(); break;
    case 'export-project': exportProject(); break;
    case 'export-png': exportImage('png'); break;
    case 'export-jpg': exportImage('jpeg'); break;
    case 'undo': undo(); break;
    case 'redo': redo(); break;
    case 'toggle-theme': toggleTheme(); break;
    case 'show-all-blocks': {
      viewState.showLabels = viewState.showPresets = viewState.showAnims = viewState.showTable = true;
      applyBlocksVisibility();
      snapshot();
      break;
    }
  }
}

document.querySelectorAll('.dropdown button[data-action]').forEach(btn => {
  btn.addEventListener('click', e => {
    e.stopPropagation();
    handleAction(btn.dataset.action);
    closeAllMenus();
  });
});

/* ============================================================
   11. Экспорт / импорт
   ============================================================ */
function stampNow() {
  return new Date().toISOString().slice(0, 19).replace(/[:T]/g, '-');
}

function exportProject() {
  const state = getProjectState();
  const blob = new Blob([JSON.stringify(state, null, 2)], { type: 'application/json' });
  const a = document.createElement('a');
  a.href = URL.createObjectURL(blob);
  a.download = `graph-${stampNow()}.graphxw`;
  a.click();
  setTimeout(() => URL.revokeObjectURL(a.href), 1000);
}

$('importFile').addEventListener('change', async e => {
  const file = e.target.files[0];
  if (!file) return;
  try {
    const text = await file.text();
    const state = JSON.parse(text);
    setProjectState(state);
    snapshot();
  } catch (err) {
    alert('Не удалось прочитать файл: ' + err.message);
  }
  e.target.value = '';
});

async function exportImage(format) {
  if (!chart) return;
  const mime = format === 'jpeg' ? 'image/jpeg' : 'image/png';
  const dark = document.body.classList.contains('dark');
  const bg   = dark ? '#1b1b1f' : '#ffffff';
  const ext  = format === 'jpeg' ? 'jpg' : 'png';

  const origDPR = chart.options.devicePixelRatio;
  chart.options.devicePixelRatio = (origDPR || window.devicePixelRatio || 1) * 2;
  chart.resize();
  chart.update('none');
  await new Promise(r => requestAnimationFrame(() => requestAnimationFrame(r)));

  const src = chart.canvas;
  const tmp = document.createElement('canvas');
  tmp.width = src.width;
  tmp.height = src.height;
  const tctx = tmp.getContext('2d');
  tctx.fillStyle = bg;
  tctx.fillRect(0, 0, tmp.width, tmp.height);
  tctx.drawImage(src, 0, 0);

  const dataUrl = tmp.toDataURL(mime, 0.92);
  const a = document.createElement('a');
  a.href = dataUrl;
  a.download = `chart-${stampNow()}.${ext}`;
  a.click();

  chart.options.devicePixelRatio = origDPR;
  chart.resize();
  chart.update('none');
}

/* ============================================================
   12. Поля формы
   ============================================================ */
function syncFieldsWithType() {
  const circ = isCircular();
  $('axisOptions').style.display = circ ? 'none' : '';
  $('xFieldLabel').textContent = circ ? 'Подпись:' : 'X:';
}

$('addBtn').addEventListener('click', () => {
  hardStopAnimation();
  const rawX = $('xInput').value.trim();
  const y = parseFloat($('yInput').value);
  if (rawX === '' || !Number.isFinite(y)) {
    alert('Введите X (или подпись) и числовой Y');
    return;
  }
  const x = parseX(rawX);
  if (x === null) { alert('Некорректное значение X'); return; }
  points.push({ x, y });
  if (typeof x === 'number') $('xInput').value = x + 1;
  else $('xInput').value = '';
  refreshChart();
  renderTable();
  snapshot();
});
['xInput', 'yInput'].forEach(id => $(id).addEventListener('keypress', e => {
  if (e.key === 'Enter') $('addBtn').click();
}));

$('clearBtn').addEventListener('click', () => {
  if (!confirm('Удалить все точки?')) return;
  hardStopAnimation();
  points = [];
  refreshChart(); renderTable(); snapshot();
});

$('applyBtn').addEventListener('click', () => { refreshChart(); snapshot(); });
$('chartType').addEventListener('change', () => { renderChart(); snapshot(); });

['chartTitle', 'xLabel', 'yLabel'].forEach(id => {
  $(id).addEventListener('input', () => { refreshChart(false); scheduleSnapshot(); });
});
['xMin', 'xMax', 'xStep', 'yMin', 'yMax', 'yStep'].forEach(id => {
  $(id).addEventListener('input', () => { refreshChart(false); scheduleSnapshot(); });
});

['fontFamily', 'fontSize'].forEach(id => {
  $(id).addEventListener('change', () => { applyFont(); renderChart(); snapshot(); });
});

/* Встроенные переходы */
['animationsEnabled', 'animDelay', 'animEasing'].forEach(id => {
  $(id).addEventListener('change', () => { refreshChart(); snapshot(); });
});
$('animDuration').addEventListener('change', () => { refreshChart(); snapshot(); });

/* Непрерывная анимация — настройки */
['animType', 'animSpeed', 'animAmp'].forEach(id => {
  $(id).addEventListener('input', () => {
    if (id === 'animSpeed') $('animSpeedVal').textContent = parseFloat($('animSpeed').value).toFixed(1) + '×';
    if (id === 'animAmp')   $('animAmpVal').textContent   = parseFloat($('animAmp').value).toFixed(2);
    scheduleSnapshot();
  });
});

$('animStartBtn').addEventListener('click', startAnimation);
$('animStopBtn').addEventListener('click', stopAnimation);

/* Вид: колонки */
$('toggleColX').addEventListener('change', e => { viewState.showX = e.target.checked; applyViewState(); snapshot(); });
$('toggleColY').addEventListener('change', e => { viewState.showY = e.target.checked; applyViewState(); snapshot(); });
$('toggleColDel').addEventListener('change', e => { viewState.showDel = e.target.checked; applyViewState(); snapshot(); });

/* Вид: блоки */
$('toggleBlockLabels').addEventListener('change',  e => { viewState.showLabels  = e.target.checked; applyBlocksVisibility(); snapshot(); });
$('toggleBlockPresets').addEventListener('change', e => { viewState.showPresets = e.target.checked; applyBlocksVisibility(); snapshot(); });
$('toggleBlockAnims').addEventListener('change',   e => { viewState.showAnims   = e.target.checked; applyBlocksVisibility(); snapshot(); });
$('toggleBlockTable').addEventListener('change',   e => { viewState.showTable   = e.target.checked; applyBlocksVisibility(); snapshot(); });

/* ============================================================
   13. Горячие клавиши
   ============================================================ */
document.addEventListener('keydown', e => {
  const mod = e.ctrlKey || e.metaKey;
  if (!mod) return;
  const key = e.key.toLowerCase();
  if (key === 'z' && !e.shiftKey) { e.preventDefault(); undo(); }
  else if (key === 'y' || (e.shiftKey && key === 'z')) { e.preventDefault(); redo(); }
  else if (key === 's') { e.preventDefault(); exportProject(); }
});

/* ============================================================
   14. Старт
   ============================================================ */
if (typeof Chart !== 'undefined') {
  applyFont();
  renderChart();
  setupDrag();
  snapshot();
}
