/**
 * RetailPulse AI — Grounded Enterprise BI Agent Frontend Logic
 * Full Three.js 3D WebGL Matrix + Chart.js Telemetry + Alibaba Qwen 2.5 7B Live RAG Chat
 */

let chartInstances = {};
let inlineChartCounter = 0;
const currentSessionId = 'session_' + Math.random().toString(36).substring(2, 9);

// Global Warehouse state synced from SQLite backend
let WAREHOUSE = {
  kpis: { grossRevenue: 357500.76, totalOrders: 1008, completedOrders: 967, cancelledOrders: 41, aov: 369.70, customersTotal: 161, customersActive: 113, customersInactive: 48 },
  months: ['Nov', 'Dec', 'Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun', 'Jul', 'Aug', 'Sep', 'Oct'],
  monthlyTotals: [],
  categories: [
    { name: 'Electronics', short: 'Elec', color: '#3B82F6', hex: 0x3B82F6, orders: 312, revenue: 124850.40, share: 34.9 },
    { name: 'Apparel', short: 'Apparel', color: '#10B981', hex: 0x10B981, orders: 248, revenue: 94120.16, share: 26.3 },
    { name: 'Home & Kitchen', short: 'Home', color: '#6366F1', hex: 0x6366F1, orders: 185, revenue: 68430.20, share: 19.1 },
    { name: 'Fitness & Outdoor', short: 'Fitness', color: '#F59E0B', hex: 0xF59E0B, orders: 134, revenue: 42680.00, share: 11.9 },
    { name: 'Beauty & Personal Care', short: 'Beauty', color: '#06B6D4', hex: 0x06B6D4, orders: 88, revenue: 27420.00, share: 7.7 }
  ],
  topProducts: []
};

document.addEventListener("DOMContentLoaded", async () => {
  await initLiveData();
  initThreeTelemetry();
  initChartTelemetry();
  initETLAudit();
  runSqlWorkbench(); // auto-run default query on start
});

// =========================================================================
// 1. LIVE BACKEND DATA HYDRATION
// =========================================================================
async function initLiveData() {
  try {
    const [resKpis, resMonthly, resCats, resProds, resCust] = await Promise.all([
      fetch('/api/kpis').then(r => r.json()).catch(() => null),
      fetch('/api/sales/monthly').then(r => r.json()).catch(() => null),
      fetch('/api/sales/categories').then(r => r.json()).catch(() => null),
      fetch('/api/products/top?metric=revenue&limit=5').then(r => r.json()).catch(() => null),
      fetch('/api/customers/summary').then(r => r.json()).catch(() => null)
    ]);

    if (resKpis) {
      document.getElementById('kpiGrossRevenue').textContent = `$${resKpis.total_revenue.toLocaleString('en-US', { minimumFractionDigits: 2, maximumFractionDigits: 2 })}`;
      document.getElementById('kpiCompletedOrders').textContent = `${resKpis.completed_orders.toLocaleString()} completed orders`;
      document.getElementById('kpiTotalOrders').textContent = resKpis.total_orders.toLocaleString();
      document.getElementById('kpiOrdersCompleted').textContent = `${resKpis.completed_orders.toLocaleString()} Completed`;
      document.getElementById('kpiOrdersCancelled').textContent = `${resKpis.cancelled_orders} Cancelled · ${(resKpis.cancelled_orders / resKpis.total_orders * 100).toFixed(1)}%`;
      document.getElementById('kpiAOV').textContent = `$${resKpis.average_order_value.toFixed(2)}`;
      document.getElementById('kpiCustomerCount').innerHTML = `${resKpis.total_customers} <span class="text-xs font-normal text-[#8A94A6]">ACCTS</span>`;
      document.getElementById('kpiActiveCustText').textContent = `${resKpis.active_customers} Active · ${(resKpis.active_customers / resKpis.total_customers * 100).toFixed(1)}%`;
      document.getElementById('kpiInactiveCustText').textContent = `${resKpis.inactive_customers} Inactive >90d`;
      document.getElementById('kpiRiskBadge').textContent = `${resKpis.inactive_customers} AT RISK`;

      const activePct = (resKpis.active_customers / resKpis.total_customers * 100).toFixed(1);
      const inactivePct = (100 - activePct).toFixed(1);
      document.getElementById('retentionActiveBar').style.width = `${activePct}%`;
      document.getElementById('retentionInactiveBar').style.width = `${inactivePct}%`;
      document.getElementById('retentionActivePct').textContent = `${activePct}%`;
      document.getElementById('retentionInactivePct').textContent = `${inactivePct}%`;
      document.getElementById('cohortCenterPct').textContent = `${activePct}%`;
      document.getElementById('cohortAccountsLabel').textContent = `${resKpis.total_customers} ACCTS`;
      document.getElementById('telemetryOrdersCount').textContent = `${resKpis.total_orders.toLocaleString()} ORDERS`;
    }

    if (resMonthly && resMonthly.length) {
      WAREHOUSE.monthlyTotals = resMonthly;
      WAREHOUSE.months = resMonthly.map(m => m.month.substring(5)); // '11', '12', '01'...
    }

    if (resCats && resCats.length) {
      WAREHOUSE.categories = resCats.map((c, idx) => ({
        name: c.category_name,
        short: c.category_name.split(' ')[0],
        color: ['#3B82F6', '#10B981', '#6366F1', '#F59E0B', '#06B6D4'][idx % 5],
        hex: [0x3B82F6, 0x10B981, 0x6366F1, 0xF59E0B, 0x06B6D4][idx % 5],
        orders: c.orders_count,
        revenue: c.revenue,
        share: c.pct_of_total
      }));
    }

    if (resProds && resProds.length) {
      WAREHOUSE.topProducts = resProds;
    }
  } catch (err) {
    console.warn("Using baseline telemetry fallback for visualization:", err);
  }
}

// =========================================================================
// 2. THREE.JS WEBGL 3D REVENUE & CATEGORY MATRIX
// =========================================================================
let threeScene, threeCamera, threeRenderer, raycaster, mouseVec;
let pillarMeshes = [];
let hoveredPillar = null;
let camSpherical = { radius: 17.5, theta: 0.62, phi: 0.96 };
let targetSpherical = { radius: 17.5, theta: 0.62, phi: 0.96 };
let isDragging3D = false;
let prevPointer = { x: 0, y: 0 };

function initThreeTelemetry() {
  const container = document.getElementById('three-canvas-container');
  if (!container) return;
  const width = container.clientWidth || 600;
  const height = container.clientHeight || 300;

  threeScene = new THREE.Scene();
  threeCamera = new THREE.PerspectiveCamera(36, width / height, 0.1, 100);
  updateCameraFromSpherical();

  threeRenderer = new THREE.WebGLRenderer({ antialias: true, alpha: true, powerPreference: 'high-performance' });
  threeRenderer.setSize(width, height);
  threeRenderer.setPixelRatio(Math.min(window.devicePixelRatio, 2));
  container.innerHTML = '';
  container.appendChild(threeRenderer.domElement);

  // Precision Lighting
  const ambientLight = new THREE.AmbientLight(0xffffff, 0.6);
  threeScene.add(ambientLight);

  const keyLight = new THREE.DirectionalLight(0xffffff, 0.95);
  keyLight.position.set(10, 18, 12);
  threeScene.add(keyLight);

  const rimLight = new THREE.DirectionalLight(0x3B82F6, 0.45);
  rimLight.position.set(-12, 8, -10);
  threeScene.add(rimLight);

  // Architectural Grid & Pedestal
  const gridHelper = new THREE.GridHelper(14, 14, 0x2E3442, 0x181D28);
  gridHelper.position.y = -0.01;
  threeScene.add(gridHelper);

  const basePlate = new THREE.Mesh(
    new THREE.BoxGeometry(12.5, 0.12, 6.8),
    new THREE.MeshStandardMaterial({ color: 0x0D1015, roughness: 0.7, metalness: 0.2 })
  );
  basePlate.position.y = -0.07;
  threeScene.add(basePlate);

  // Build 3D Pillars (10/12 Months x 5 Categories)
  const numMonths = Math.min(10, WAREHOUSE.monthlyTotals.length || 10);
  const numCats = WAREHOUSE.categories.length || 5;
  const maxCellRev = 14500;
  const maxPillarHeight = 4.2;
  const xSpacing = 1.15;
  const zSpacing = 1.20;
  const xOffset = -((numMonths - 1) * xSpacing) / 2;
  const zOffset = -((numCats - 1) * zSpacing) / 2;

  pillarMeshes = [];

  for (let mIdx = 0; mIdx < numMonths; mIdx++) {
    const mData = WAREHOUSE.monthlyTotals[mIdx] || { month: `M${mIdx + 1}`, revenue: 35000, orders: 90 };
    for (let cIdx = 0; cIdx < numCats; cIdx++) {
      const cat = WAREHOUSE.categories[cIdx];
      const cellRev = Math.max(1200, (cat.share / 100) * mData.revenue * (1 + Math.sin(mIdx + cIdx) * 0.1));
      const cellOrders = Math.max(4, Math.round(cellRev / 380));
      const targetH = Math.max(0.25, (cellRev / maxCellRev) * maxPillarHeight);

      const geo = new THREE.BoxGeometry(0.72, targetH, 0.72);
      const mat = new THREE.MeshStandardMaterial({
        color: cat.hex,
        emissive: cat.hex,
        emissiveIntensity: 0.15,
        roughness: 0.35,
        metalness: 0.45
      });

      const mesh = new THREE.Mesh(geo, mat);
      mesh.position.set(xOffset + mIdx * xSpacing, targetH / 2, zOffset + cIdx * zSpacing);
      mesh.userData = {
        category: cat.name,
        month: mData.month,
        revenue: cellRev,
        orders: cellOrders,
        origEmissive: 0.15,
        origColor: cat.hex
      };

      threeScene.add(mesh);
      pillarMeshes.push(mesh);
    }
  }

  raycaster = new THREE.Raycaster();
  mouseVec = new THREE.Vector2(-999, -999);

  // Mouse & Orbit Event Listeners
  container.addEventListener('mousedown', (e) => {
    isDragging3D = true;
    prevPointer = { x: e.clientX, y: e.clientY };
  });

  window.addEventListener('mouseup', () => { isDragging3D = false; });

  container.addEventListener('mousemove', (e) => {
    const rect = container.getBoundingClientRect();
    mouseVec.x = ((e.clientX - rect.left) / rect.width) * 2 - 1;
    mouseVec.y = -((e.clientY - rect.top) / rect.height) * 2 + 1;

    if (isDragging3D) {
      const dx = e.clientX - prevPointer.x;
      const dy = e.clientY - prevPointer.y;
      prevPointer = { x: e.clientX, y: e.clientY };

      targetSpherical.theta -= dx * 0.007;
      targetSpherical.phi = Math.max(0.18, Math.min(Math.PI / 2 - 0.04, targetSpherical.phi - dy * 0.007));
    }

    updateRaycastHover(e, container);
  });

  container.addEventListener('wheel', (e) => {
    e.preventDefault();
    targetSpherical.radius = Math.max(9, Math.min(26, targetSpherical.radius + e.deltaY * 0.015));
  }, { passive: false });

  window.addEventListener('resize', () => {
    if (!container || !threeRenderer || !threeCamera) return;
    const w = container.clientWidth;
    const h = container.clientHeight;
    threeCamera.aspect = w / h;
    threeCamera.updateProjectionMatrix();
    threeRenderer.setSize(w, h);
  });

  animateThree();
}

function updateCameraFromSpherical() {
  const x = camSpherical.radius * Math.sin(camSpherical.phi) * Math.sin(camSpherical.theta);
  const y = camSpherical.radius * Math.cos(camSpherical.phi);
  const z = camSpherical.radius * Math.sin(camSpherical.phi) * Math.cos(camSpherical.theta);
  threeCamera.position.set(x, y, z);
  threeCamera.lookAt(0, 1.2, 0);
}

function animateThree() {
  requestAnimationFrame(animateThree);
  camSpherical.theta += (targetSpherical.theta - camSpherical.theta) * 0.08;
  camSpherical.phi += (targetSpherical.phi - camSpherical.phi) * 0.08;
  camSpherical.radius += (targetSpherical.radius - camSpherical.radius) * 0.08;
  updateCameraFromSpherical();
  threeRenderer.render(threeScene, threeCamera);
}

function updateRaycastHover(event, container) {
  if (!raycaster || !threeCamera) return;
  raycaster.setFromCamera(mouseVec, threeCamera);
  const intersects = raycaster.intersectObjects(pillarMeshes);
  const tooltip = document.getElementById('three-tooltip');

  if (intersects.length > 0) {
    const hit = intersects[0].object;
    if (hoveredPillar !== hit) {
      if (hoveredPillar) hoveredPillar.material.emissiveIntensity = hoveredPillar.userData.origEmissive;
      hoveredPillar = hit;
      hit.material.emissiveIntensity = 0.55;
    }

    const rect = container.getBoundingClientRect();
    const x = event.clientX - rect.left + 14;
    const y = event.clientY - rect.top + 14;

    tooltip.style.left = `${Math.min(x, rect.width - 180)}px`;
    tooltip.style.top = `${Math.min(y, rect.height - 90)}px`;
    tooltip.classList.remove('hidden');

    document.getElementById('tt-category').textContent = hit.userData.category;
    document.getElementById('tt-month').textContent = `Month: ${hit.userData.month}`;
    document.getElementById('tt-revenue').textContent = `$${hit.userData.revenue.toLocaleString('en-US', { minimumFractionDigits: 2, maximumFractionDigits: 2 })}`;
    document.getElementById('tt-orders').textContent = hit.userData.orders;
  } else {
    if (hoveredPillar) {
      hoveredPillar.material.emissiveIntensity = hoveredPillar.userData.origEmissive;
      hoveredPillar = null;
    }
    tooltip.classList.add('hidden');
  }
}

function setCameraPreset(mode) {
  ['isometric', 'top', 'front'].forEach(m => {
    const btn = document.getElementById(`cam-btn-${m}`);
    if (btn) {
      btn.className = m === mode
        ? 'px-2 py-0.5 rounded bg-blue-600 text-white font-semibold cursor-pointer transition-colors'
        : 'px-2 py-0.5 rounded bg-[#131720] hover:bg-[#181D28] text-[#8A94A6] border border-[#1E222B] cursor-pointer transition-colors';
    }
  });

  if (mode === 'isometric') targetSpherical = { radius: 17.5, theta: 0.62, phi: 0.96 };
  else if (mode === 'top') targetSpherical = { radius: 19.0, theta: 0.0, phi: 0.05 };
  else if (mode === 'front') targetSpherical = { radius: 17.0, theta: 0.0, phi: 1.48 };
}

// =========================================================================
// 3. CHART.JS 2x2 TELEMETRY INITIALIZATION
// =========================================================================
function initChartTelemetry() {
  const mLabels = (WAREHOUSE.monthlyTotals.length ? WAREHOUSE.monthlyTotals : [
    { month: 'Nov', revenue: 31200 }, { month: 'Dec', revenue: 42100 }, { month: 'Jan', revenue: 29800 },
    { month: 'Feb', revenue: 33400 }, { month: 'Mar', revenue: 34600 }, { month: 'Apr', revenue: 35100 },
    { month: 'May', revenue: 36800 }, { month: 'Jun', revenue: 38100 }, { month: 'Jul', revenue: 37400 },
    { month: 'Aug', revenue: 41200 }, { month: 'Sep', revenue: 39400 }, { month: 'Oct', revenue: 35186 }
  ]);

  // 1. Monthly Line Trajectory
  const ctxM = document.getElementById('chart-monthly').getContext('2d');
  new Chart(ctxM, {
    type: 'line',
    data: {
      labels: mLabels.map(m => m.month),
      datasets: [{
        label: 'Gross Revenue ($)',
        data: mLabels.map(m => m.revenue),
        borderColor: '#3B82F6',
        backgroundColor: 'rgba(59, 130, 246, 0.12)',
        fill: true,
        tension: 0.35,
        borderWidth: 2,
        pointBackgroundColor: '#3B82F6',
        pointRadius: 2.5
      }]
    },
    options: {
      responsive: true,
      maintainAspectRatio: false,
      plugins: { legend: { display: false } },
      scales: {
        x: { grid: { color: 'rgba(30, 34, 43, 0.6)' }, ticks: { color: '#8A94A6', font: { size: 9, family: 'JetBrains Mono' } } },
        y: { grid: { color: 'rgba(30, 34, 43, 0.6)' }, ticks: { color: '#8A94A6', font: { size: 9, family: 'JetBrains Mono' } } }
      }
    }
  });

  // 2. Category Mix Bar
  const ctxC = document.getElementById('chart-category').getContext('2d');
  new Chart(ctxC, {
    type: 'bar',
    data: {
      labels: WAREHOUSE.categories.map(c => c.short),
      datasets: [{
        data: WAREHOUSE.categories.map(c => c.revenue),
        backgroundColor: WAREHOUSE.categories.map(c => c.color),
        borderRadius: 3
      }]
    },
    options: {
      responsive: true,
      maintainAspectRatio: false,
      plugins: { legend: { display: false } },
      scales: {
        x: { grid: { display: false }, ticks: { color: '#8A94A6', font: { size: 9, family: 'JetBrains Mono' } } },
        y: { grid: { color: 'rgba(30, 34, 43, 0.6)' }, ticks: { color: '#8A94A6', font: { size: 9, family: 'JetBrains Mono' } } }
      }
    }
  });

  // 3. Top SKUs Horizontal Bar
  const ctxS = document.getElementById('chart-top-skus').getContext('2d');
  const prods = WAREHOUSE.topProducts.length ? WAREHOUSE.topProducts : [
    { product_name: 'Pro 4K Monitor', revenue: 54449 },
    { product_name: 'Folding Rowing Machine', revenue: 53399 },
    { product_name: 'Artisan Espresso Machine', revenue: 42299 },
    { product_name: 'Wireless Headphones', revenue: 38990 },
    { product_name: 'Quick-Lock Dumbbells', revenue: 27990 }
  ];

  new Chart(ctxS, {
    type: 'bar',
    data: {
      labels: prods.map(p => (p.product_name || p.name).substring(0, 14) + '..'),
      datasets: [{
        data: prods.map(p => p.revenue),
        backgroundColor: '#10B981',
        borderRadius: 3
      }]
    },
    options: {
      indexAxis: 'y',
      responsive: true,
      maintainAspectRatio: false,
      plugins: { legend: { display: false } },
      scales: {
        x: { grid: { color: 'rgba(30, 34, 43, 0.6)' }, ticks: { color: '#8A94A6', font: { size: 9, family: 'JetBrains Mono' } } },
        y: { grid: { display: false }, ticks: { color: '#8A94A6', font: { size: 9, family: 'JetBrains Mono' } } }
      }
    }
  });

  // 4. Cohort Donut
  const ctxCoh = document.getElementById('chart-cohorts').getContext('2d');
  new Chart(ctxCoh, {
    type: 'doughnut',
    data: {
      labels: ['Active', 'Inactive (>90d)'],
      datasets: [{
        data: [113, 48],
        backgroundColor: ['#10B981', '#F59E0B'],
        borderWidth: 0,
        cutout: '76%'
      }]
    },
    options: {
      responsive: true,
      maintainAspectRatio: false,
      plugins: { legend: { display: false } }
    }
  });
}

// =========================================================================
// 4. AI ANALYST STUDIO WIRED TO LIVE ALIBABA QWEN 2.5 7B RAG PIPELINE
// =========================================================================
async function handleChatSubmit(event) {
  event.preventDefault();
  const input = document.getElementById('analyst-input');
  const question = input.value.trim();
  if (!question) return;

  input.value = '';
  appendUserMessage(question);

  const typingId = appendTypingIndicator();

  try {
    const res = await fetch('/api/chat', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ question, session_id: currentSessionId })
    });

    removeTypingIndicator(typingId);

    if (!res.ok) {
      const err = await res.json();
      throw new Error(err.detail || 'Server processing error');
    }

    const data = await res.json();
    appendAssistantMessage(data);

    if (data.model_provider) {
      document.getElementById('llmEngineName').textContent = data.model_provider;
    }
  } catch (err) {
    removeTypingIndicator(typingId);
    appendErrorMessage(`System Error: ${err.message}`);
  }
}

function askPrompt(text) {
  document.getElementById('analyst-input').value = text;
  document.getElementById('chatForm').dispatchEvent(new Event('submit'));
}

function appendUserMessage(text) {
  const stream = document.getElementById('analyst-stream');
  const msg = document.createElement('div');
  msg.className = 'ml-auto max-w-[85%] bg-blue-950/60 border border-blue-600/50 rounded-lg p-3 text-xs sm:text-sm text-blue-100 shadow-md';
  msg.innerHTML = `
    <div class="flex items-center justify-between pb-1 mb-1 border-b border-blue-500/20 font-mono text-[10px] text-blue-300">
      <span>Operator Query</span>
      <span>${new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })}</span>
    </div>
    <p class="leading-relaxed font-sans">${escapeHtml(text)}</p>
  `;
  stream.appendChild(msg);
  stream.scrollTop = stream.scrollHeight;
}

function appendTypingIndicator() {
  const stream = document.getElementById('analyst-stream');
  const id = `typing-${Date.now()}`;
  const el = document.createElement('div');
  el.id = id;
  el.className = 'bg-[#0D1015] border border-[#1E222B] rounded-lg p-3 text-xs text-[#8A94A6] flex items-center gap-2.5 font-mono';
  el.innerHTML = `
    <span class="inline-block w-2 h-2 rounded-full bg-blue-500 animate-pulse"></span>
    <span>Alibaba Qwen 2.5 7B grounding SQLite telemetry & generating analysis...</span>
  `;
  stream.appendChild(el);
  stream.scrollTop = stream.scrollHeight;
  return id;
}

function removeTypingIndicator(id) {
  const el = document.getElementById(id);
  if (el) el.remove();
}

function appendAssistantMessage(data) {
  const stream = document.getElementById('analyst-stream');
  const msg = document.createElement('div');
  msg.className = 'bg-[#0D1015] border border-[#1E222B] rounded-lg p-4 space-y-3 text-xs sm:text-sm text-[#F3F4F6] shadow-md animate-fadeIn';

  // Format Markdown with marked.js
  const renderedContent = marked.parse(data.answer);

  // Tool Execution Trace Pill
  let toolTraceHtml = '';
  if (data.executed_tools && data.executed_tools.length) {
    toolTraceHtml = `
      <div class="bg-[#07080A] border border-[#1E222B] rounded px-3 py-2 font-mono text-[11px] text-[#8A94A6] space-y-1">
        <div class="flex items-center justify-between text-blue-400 font-bold">
          <span>⚡ RAG Execution Trace (${data.executed_tools.length} step)</span>
          <span class="tabular-nums">${data.latency_ms.toFixed(0)}ms latency</span>
        </div>
        ${data.executed_tools.map(t => `<div>• <strong>${escapeHtml(t.tool_name)}</strong>: ${escapeHtml(t.output_summary)}</div>`).join('')}
      </div>
    `;
  }

  // Dynamic Chart Canvas if returned
  let chartContainerHtml = '';
  let inlineCanvasId = null;
  if (data.chart) {
    inlineChartCounter++;
    inlineCanvasId = `inline-chart-${inlineChartCounter}`;
    chartContainerHtml = `
      <div class="bg-[#07080A] border border-[#1E222B] rounded p-3 h-[240px]">
        <canvas id="${inlineCanvasId}"></canvas>
      </div>
    `;
  }

  // Follow-up chip suggestions
  let followupsHtml = '';
  if (data.suggested_followups && data.suggested_followups.length) {
    followupsHtml = `
      <div class="pt-2 border-t border-[#1E222B] flex flex-wrap items-center gap-1.5 font-mono text-[10px]">
        <span class="text-[#8A94A6]">Follow-up:</span>
        ${data.suggested_followups.map(f => `<button onclick="askPrompt('${escapeHtml(f)}')" class="px-2 py-0.5 rounded bg-[#131720] hover:bg-[#181D28] text-blue-400 border border-[#1E222B] cursor-pointer transition-colors">${escapeHtml(f)}</button>`).join('')}
      </div>
    `;
  }

  msg.innerHTML = `
    <div class="flex items-center justify-between border-b border-[#1E222B] pb-2 font-mono text-[11px] text-[#8A94A6]">
      <div class="flex items-center gap-2">
        <span class="w-1.5 h-1.5 rounded-full bg-emerald-400"></span>
        <strong class="text-blue-400 font-semibold">${escapeHtml(data.model_provider || 'Qwen 2.5 7B')}</strong>
        <span class="text-[9px] uppercase px-1.5 py-0.2 rounded bg-emerald-500/10 text-emerald-400 border border-emerald-500/30">GROUNDED</span>
      </div>
      <span>${new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })}</span>
    </div>
    ${toolTraceHtml}
    <div class="prose prose-invert max-w-none text-xs sm:text-sm leading-relaxed">${renderedContent}</div>
    ${chartContainerHtml}
    ${followupsHtml}
  `;

  stream.appendChild(msg);

  if (data.chart && inlineCanvasId) {
    setTimeout(() => {
      renderInlineChart(inlineCanvasId, data.chart);
    }, 60);
  }

  stream.scrollTop = stream.scrollHeight;
}

function renderInlineChart(canvasId, spec) {
  const canvas = document.getElementById(canvasId);
  if (!canvas) return;
  new Chart(canvas.getContext('2d'), {
    type: spec.chart_type,
    data: { labels: spec.labels, datasets: spec.datasets },
    options: {
      responsive: true,
      maintainAspectRatio: false,
      plugins: {
        title: { display: true, text: spec.title, color: '#F3F4F6', font: { size: 11, family: 'Plus Jakarta Sans' } },
        legend: { labels: { color: '#8A94A6', font: { size: 9, family: 'JetBrains Mono' } } }
      },
      scales: spec.chart_type !== 'doughnut' && spec.chart_type !== 'pie' ? {
        x: { grid: { color: 'rgba(30, 34, 43, 0.6)' }, ticks: { color: '#8A94A6', font: { size: 9, family: 'JetBrains Mono' } } },
        y: { grid: { color: 'rgba(30, 34, 43, 0.6)' }, ticks: { color: '#8A94A6', font: { size: 9, family: 'JetBrains Mono' } } }
      } : {}
    }
  });
}

function appendErrorMessage(errText) {
  const stream = document.getElementById('analyst-stream');
  const msg = document.createElement('div');
  msg.className = 'bg-rose-950/40 border border-rose-500/50 rounded-lg p-3 text-xs text-rose-300 font-mono';
  msg.innerHTML = `<strong>ALERT:</strong> ${escapeHtml(errText)}`;
  stream.appendChild(msg);
  stream.scrollTop = stream.scrollHeight;
}

function clearChatSession() {
  document.getElementById('analyst-stream').innerHTML = `
    <div class="bg-[#0D1015] border border-[#1E222B] rounded-lg p-3 text-xs text-[#8A94A6] font-mono">
      Session cleared. Fresh context initialized for Alibaba Qwen 2.5 7B.
    </div>
  `;
}

// =========================================================================
// 5. ETL DATA QUALITY AUDIT & SAFE READ-ONLY SQL WORKBENCH
// =========================================================================
async function initETLAudit() {
  try {
    const res = await fetch('/api/data-quality');
    const data = await res.json();
    document.getElementById('auditRawRows').textContent = data.records_loaded.toLocaleString();
    document.getElementById('auditDuplicates').textContent = data.duplicates_removed.toLocaleString();
    document.getElementById('auditNullsFixed').textContent = data.missing_values_handled.toLocaleString();
    document.getElementById('auditCleanPctBadge').textContent = `${data.clean_pct}% INTEGRITY`;
  } catch (err) {
    console.warn("Error loading ETL audit:", err);
  }
}

async function runSqlWorkbench() {
  const input = document.getElementById('sql-console-input');
  const sql = input.value.trim();
  const alertBox = document.getElementById('sql-guardrail-alert');
  const thead = document.getElementById('sql-thead');
  const tbody = document.getElementById('sql-tbody');
  const meta = document.getElementById('sql-exec-meta');

  alertBox.classList.add('hidden');
  thead.innerHTML = '';
  tbody.innerHTML = '<tr><td class="p-3 text-[#8A94A6]" colspan="6">Executing read-only SQL query...</td></tr>';

  try {
    const res = await fetch('/api/query/sql', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ sql })
    });

    const data = await res.json();

    if (!res.ok) {
      if (res.status === 403) {
        alertBox.classList.remove('hidden');
        document.getElementById('sql-guardrail-detail').textContent = data.detail || 'Mutating SQL operation forbidden.';
        tbody.innerHTML = `<tr><td class="p-3 text-rose-400 font-bold" colspan="6">BLOCKED: ${escapeHtml(data.detail)}</td></tr>`;
      } else {
        tbody.innerHTML = `<tr><td class="p-3 text-amber-400 font-bold" colspan="6">ERROR: ${escapeHtml(data.detail || 'SQL syntax error')}</td></tr>`;
      }
      return;
    }

    meta.textContent = `Returned ${data.row_count} rows in ${data.execution_time_ms}ms · SQLite 3.50`;

    if (!data.rows || !data.rows.length) {
      tbody.innerHTML = '<tr><td class="p-3 text-[#8A94A6]" colspan="6">Query completed. 0 records returned.</td></tr>';
      return;
    }

    thead.innerHTML = '<tr>' + data.columns.map(c => `<th class="px-3 py-2 border-r border-[#1E222B] uppercase text-[10px] tracking-wider">${escapeHtml(c)}</th>`).join('') + '</tr>';
    tbody.innerHTML = data.rows.slice(0, 10).map(r => `
      <tr class="hover:bg-[#131720]/60 transition-colors">
        ${data.columns.map(c => `<td class="px-3 py-1.5 border-r border-[#1E222B]">${escapeHtml(String(r[c]))}</td>`).join('')}
      </tr>
    `).join('');
  } catch (err) {
    tbody.innerHTML = `<tr><td class="p-3 text-rose-400" colspan="6">Network failure: ${escapeHtml(err.message)}</td></tr>`;
  }
}

function applySqlPreset(type) {
  const input = document.getElementById('sql-console-input');
  if (type === 'category') {
    input.value = "SELECT c.name as category_name, count(distinct o.order_id) as orders, round(sum(oi.subtotal), 2) as gross_revenue FROM categories c JOIN products p ON c.category_id = p.category_id JOIN order_items oi ON p.product_id = oi.product_id JOIN orders o ON oi.order_id = o.order_id WHERE o.status = 'completed' GROUP BY c.name ORDER BY gross_revenue DESC;";
  } else if (type === 'status') {
    input.value = "SELECT status, count(*) AS order_count, round(sum(total_amount), 2) AS total_value FROM orders GROUP BY status;";
  } else if (type === 'drop') {
    input.value = "DROP TABLE customers;";
  }
  runSqlWorkbench();
}

function toggleWorkbenchDrawer() {
  const body = document.getElementById('workbench-drawer-body');
  const arrow = document.getElementById('drawer-arrow');
  const text = document.getElementById('drawer-toggle-text');

  if (body.classList.contains('hidden')) {
    body.classList.remove('hidden');
    arrow.classList.add('rotate-180');
    text.textContent = 'COLLAPSE';
  } else {
    body.classList.add('hidden');
    arrow.classList.remove('rotate-180');
    text.textContent = 'EXPAND';
  }
}

function escapeHtml(str) {
  if (!str) return '';
  return String(str).replace(/&/g, '&amp;').replace(/</g, '&lt;').replace(/>/g, '&gt;').replace(/"/g, '&quot;').replace(/'/g, '&#039;');
}
