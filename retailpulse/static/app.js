/**
 * RetailPulse AI Frontend Application Logic.
 * Manages KPI updates, Chart.js instances, Chat streaming, and Safe SQL playground.
 */

let chartInstances = {};
let inlineChartCounter = 0;
const currentSessionId = 'session_' + Math.random().toString(36).substring(2, 9);

document.addEventListener("DOMContentLoaded", () => {
    initDashboard();
});

async function initDashboard() {
    await Promise.all([
        loadKPIs(),
        loadCharts(),
        loadDataQualityReport()
    ]);
}

// 1. Load Executive KPIs
async function loadKPIs() {
    try {
        const res = await fetch("/api/kpis");
        if (!res.ok) throw new Error("Failed to fetch KPIs");
        const data = await res.json();

        document.getElementById("kpiRevenue").textContent = `$${data.total_revenue.toLocaleString('en-US', { minimumFractionDigits: 2, maximumFractionDigits: 2 })}`;
        document.getElementById("kpiCompletedOrders").textContent = `${data.completed_orders.toLocaleString()} completed of ${data.total_orders.toLocaleString()} total orders`;
        
        document.getElementById("kpiOrders").textContent = data.total_orders.toLocaleString();
        document.getElementById("kpiOrdersSubtext").textContent = `${data.cancelled_orders} cancelled (${((data.cancelled_orders / data.total_orders) * 100).toFixed(1)}% drop rate)`;

        document.getElementById("kpiAOV").textContent = `$${data.average_order_value.toFixed(2)}`;
        
        document.getElementById("kpiCustomers").textContent = data.total_customers.toLocaleString();
        document.getElementById("kpiCustomersSubtext").textContent = `${data.active_customers} active • ${data.inactive_customers} inactive (>90d)`;
    } catch (err) {
        console.error("Error loading KPIs:", err);
    }
}

// 2. Load Visual Studio Charts (Chart.js)
async function loadCharts() {
    try {
        // Chart 1: Monthly Revenue Trend
        const resMonthly = await fetch("/api/sales/monthly");
        const monthlyData = await resMonthly.json();
        renderMonthlyRevenueChart(monthlyData);

        // Chart 2: Revenue by Category
        const resCat = await fetch("/api/sales/categories");
        const catData = await resCat.json();
        renderCategoryRevenueChart(catData);

        // Chart 3: Top Products
        const resProd = await fetch("/api/products/top?metric=revenue&limit=5");
        const prodData = await resProd.json();
        renderTopProductsChart(prodData);

        // Chart 4: Customer Segmentation
        const resCust = await fetch("/api/customers/summary");
        const custData = await resCust.json();
        renderCustomerSegmentationChart(custData);
    } catch (err) {
        console.error("Error loading charts:", err);
    }
}

function renderMonthlyRevenueChart(data) {
    const ctx = document.getElementById("monthlyRevenueCanvas").getContext("2d");
    if (chartInstances["monthly"]) chartInstances["monthly"].destroy();

    chartInstances["monthly"] = new Chart(ctx, {
        type: "line",
        data: {
            labels: data.map(d => d.month),
            datasets: [{
                label: "Monthly Revenue ($)",
                data: data.map(d => d.revenue),
                borderColor: "#3b82f6",
                backgroundColor: "rgba(59, 130, 246, 0.15)",
                fill: true,
                tension: 0.35,
                borderWidth: 2,
                pointBackgroundColor: "#3b82f6"
            }]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            plugins: {
                legend: { display: false },
                tooltip: {
                    callbacks: {
                        label: (ctx) => ` Revenue: $${ctx.raw.toLocaleString('en-US', { minimumFractionDigits: 2 })}`
                    }
                }
            },
            scales: {
                x: { grid: { color: "rgba(55, 65, 81, 0.3)" }, ticks: { color: "#9ca3af", font: { size: 10 } } },
                y: { grid: { color: "rgba(55, 65, 81, 0.3)" }, ticks: { color: "#9ca3af", font: { size: 10 } } }
            }
        }
    });
}

function renderCategoryRevenueChart(data) {
    const ctx = document.getElementById("categoryRevenueCanvas").getContext("2d");
    if (chartInstances["category"]) chartInstances["category"].destroy();

    chartInstances["category"] = new Chart(ctx, {
        type: "bar",
        data: {
            labels: data.map(d => d.category_name),
            datasets: [{
                label: "Revenue ($)",
                data: data.map(d => d.revenue),
                backgroundColor: ["#3b82f6", "#10b981", "#f59e0b", "#8b5cf6", "#ec4899"],
                borderRadius: 4
            }]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            plugins: {
                legend: { display: false },
                tooltip: {
                    callbacks: {
                        label: (ctx) => ` $${ctx.raw.toLocaleString('en-US', { minimumFractionDigits: 2 })}`
                    }
                }
            },
            scales: {
                x: { grid: { display: false }, ticks: { color: "#9ca3af", font: { size: 10 } } },
                y: { grid: { color: "rgba(55, 65, 81, 0.3)" }, ticks: { color: "#9ca3af", font: { size: 10 } } }
            }
        }
    });
}

function renderTopProductsChart(data) {
    const ctx = document.getElementById("topProductsCanvas").getContext("2d");
    if (chartInstances["top_products"]) chartInstances["top_products"].destroy();

    chartInstances["top_products"] = new Chart(ctx, {
        type: "bar",
        data: {
            labels: data.map(d => d.product_name.length > 20 ? d.product_name.substring(0, 20) + "..." : d.product_name),
            datasets: [{
                label: "Revenue ($)",
                data: data.map(d => d.revenue),
                backgroundColor: "#10b981",
                borderRadius: 4
            }]
        },
        options: {
            indexAxis: 'y',
            responsive: true,
            maintainAspectRatio: false,
            plugins: {
                legend: { display: false }
            },
            scales: {
                x: { grid: { color: "rgba(55, 65, 81, 0.3)" }, ticks: { color: "#9ca3af", font: { size: 10 } } },
                y: { grid: { display: false }, ticks: { color: "#9ca3af", font: { size: 10 } } }
            }
        }
    });
}

function renderCustomerSegmentationChart(data) {
    const ctx = document.getElementById("customerSegmentsCanvas").getContext("2d");
    if (chartInstances["customer_segments"]) chartInstances["customer_segments"].destroy();

    const activeCount = data.total_customers - data.inactive_customers;
    chartInstances["customer_segments"] = new Chart(ctx, {
        type: "doughnut",
        data: {
            labels: ["Active", "Inactive (>90d)", "New Signups (90d)"],
            datasets: [{
                data: [activeCount, data.inactive_customers, data.new_customers_last_90d],
                backgroundColor: ["#10b981", "#ef4444", "#3b82f6"],
                borderWidth: 0
            }]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            plugins: {
                legend: {
                    position: "bottom",
                    labels: { color: "#9ca3af", boxWidth: 12, font: { size: 10 } }
                }
            }
        }
    });
}

// 3. AI Chat Execution
async function handleChatSubmit(event) {
    event.preventDefault();
    const input = document.getElementById("chatInput");
    const question = input.value.trim();
    if (!question) return;

    input.value = "";
    appendUserMessage(question);

    const typingId = appendTypingIndicator();

    try {
        const res = await fetch("/api/chat", {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({ question, session_id: currentSessionId })
        });
        removeTypingIndicator(typingId);

        if (!res.ok) {
            const err = await res.json();
            throw new Error(err.detail || "Server error");
        }

        const data = await res.json();
        appendAssistantMessage(data);

        // Update model pill in header if present
        if (data.model_provider) {
            document.getElementById("modelStatusPill").textContent = `Engine: ${data.model_provider}`;
        }
    } catch (err) {
        removeTypingIndicator(typingId);
        appendErrorMessage(`Error: ${err.message}`);
    }
}

function askPreset(promptText) {
    document.getElementById("chatInput").value = promptText;
    document.getElementById("chatForm").dispatchEvent(new Event("submit"));
}

function appendUserMessage(text) {
    const container = document.getElementById("chatMessages");
    const msg = document.createElement("div");
    msg.className = "message user-message";
    msg.innerHTML = `
        <div class="message-sender">
            <strong>You</strong>
            <span class="timestamp">${new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })}</span>
        </div>
        <div class="message-content"><p>${escapeHtml(text)}</p></div>
    `;
    container.appendChild(msg);
    container.scrollTop = container.scrollHeight;
}

function appendTypingIndicator() {
    const container = document.getElementById("chatMessages");
    const id = `typing-${Date.now()}`;
    const msg = document.createElement("div");
    msg.id = id;
    msg.className = "message assistant-message";
    msg.innerHTML = `
        <div class="message-sender"><strong>RetailPulse AI</strong></div>
        <div class="message-content"><p>Analyzing data & calculating metrics...</p></div>
    `;
    container.appendChild(msg);
    container.scrollTop = container.scrollHeight;
    return id;
}

function removeTypingIndicator(id) {
    const el = document.getElementById(id);
    if (el) el.remove();
}

function appendAssistantMessage(data) {
    const container = document.getElementById("chatMessages");
    const msg = document.createElement("div");
    msg.className = "message assistant-message";

    // Format markdown text with marked.js
    const renderedHtml = marked.parse(data.answer);

    // Build Tool Execution Trace HTML
    let toolTraceHtml = "";
    if (data.executed_tools && data.executed_tools.length > 0) {
        toolTraceHtml = `
            <div class="tool-trace-card">
                <div class="tool-trace-title">
                    <span>⚡ Executed Tools (${data.executed_tools.length})</span>
                    <span>${data.latency_ms.toFixed(0)}ms</span>
                </div>
                <div class="tool-trace-body">
                    ${data.executed_tools.map(t => `<div>• <strong>${t.tool_name}()</strong>: ${escapeHtml(t.output_summary)} (${t.execution_time_ms}ms)</div>`).join("")}
                </div>
            </div>
        `;
    }

    // Dynamic Chart container
    let chartHtml = "";
    let inlineChartId = null;
    if (data.chart) {
        inlineChartCounter++;
        inlineChartId = `chat-chart-${inlineChartCounter}`;
        chartHtml = `
            <div class="chat-chart-box">
                <canvas id="${inlineChartId}"></canvas>
            </div>
        `;
    }

    // Follow-up suggestion chips
    let followupsHtml = "";
    if (data.suggested_followups && data.suggested_followups.length > 0) {
        followupsHtml = `
            <div style="margin-top: 0.75rem; display: flex; flex-wrap: wrap; gap: 0.4rem;">
                ${data.suggested_followups.map(f => `<button class="chip" onclick="askPreset('${escapeHtml(f)}')">${escapeHtml(f)}</button>`).join("")}
            </div>
        `;
    }

    msg.innerHTML = `
        <div class="message-sender">
            <strong>RetailPulse AI</strong>
            <span class="timestamp">${new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })}</span>
        </div>
        ${toolTraceHtml}
        <div class="message-content">${renderedHtml}</div>
        ${chartHtml}
        ${followupsHtml}
    `;

    container.appendChild(msg);

    // If dynamic chart was returned, render it inside the message
    if (data.chart && inlineChartId) {
        setTimeout(() => {
            renderDynamicChatChart(inlineChartId, data.chart);
        }, 50);
    }

    container.scrollTop = container.scrollHeight;
}

function renderDynamicChatChart(canvasId, chartSpec) {
    const canvas = document.getElementById(canvasId);
    if (!canvas) return;
    const ctx = canvas.getContext("2d");

    new Chart(ctx, {
        type: chartSpec.chart_type,
        data: {
            labels: chartSpec.labels,
            datasets: chartSpec.datasets
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            plugins: {
                title: { display: true, text: chartSpec.title, color: "#fff", font: { size: 12 } },
                legend: { labels: { color: "#9ca3af", font: { size: 10 } } }
            },
            scales: chartSpec.chart_type !== 'pie' && chartSpec.chart_type !== 'doughnut' ? {
                x: { grid: { color: "rgba(55, 65, 81, 0.3)" }, ticks: { color: "#9ca3af", font: { size: 9 } } },
                y: { grid: { color: "rgba(55, 65, 81, 0.3)" }, ticks: { color: "#9ca3af", font: { size: 9 } } }
            } : {}
        }
    });
}

function appendErrorMessage(errorText) {
    const container = document.getElementById("chatMessages");
    const msg = document.createElement("div");
    msg.className = "message assistant-message";
    msg.style.borderColor = "var(--accent-rose)";
    msg.innerHTML = `
        <div class="message-sender" style="color: var(--accent-rose);"><strong>System Warning</strong></div>
        <div class="message-content"><p>${escapeHtml(errorText)}</p></div>
    `;
    container.appendChild(msg);
    container.scrollTop = container.scrollHeight;
}

function clearChat() {
    document.getElementById("chatMessages").innerHTML = "";
}

// 4. Data Quality Audit & Safe SQL Tool
async function loadDataQualityReport() {
    try {
        const res = await fetch("/api/data-quality");
        const data = await res.json();
        
        document.getElementById("statLoaded").textContent = data.records_loaded.toLocaleString();
        document.getElementById("statDups").textContent = data.duplicates_removed.toLocaleString();
        document.getElementById("statMissing").textContent = data.missing_values_handled.toLocaleString();
        document.getElementById("statCleanPct").textContent = `${data.clean_pct}%`;

        const list = document.getElementById("auditIssuesList");
        list.innerHTML = data.issues_detected.map(issue => `<li>✅ ${escapeHtml(issue)}</li>`).join("");
    } catch (err) {
        console.error("Error loading quality audit:", err);
    }
}

async function runSafeSQL() {
    const sql = document.getElementById("sqlInput").value.trim();
    if (!sql) return;

    const resultBox = document.getElementById("sqlResults");
    resultBox.innerHTML = "Executing safe query...";

    try {
        const res = await fetch("/api/query/sql", {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({ sql })
        });
        const data = await res.json();
        
        if (!res.ok) {
            resultBox.innerHTML = `<span style="color: var(--accent-rose);">❌ ${escapeHtml(data.detail)}</span>`;
            return;
        }

        if (data.rows.length === 0) {
            resultBox.innerHTML = "Query executed successfully. 0 rows returned.";
            return;
        }

        let tableHtml = `<div style="color: #60a5fa; margin-bottom: 0.4rem;">Query returned ${data.row_count} rows in ${data.execution_time_ms}ms:</div>`;
        tableHtml += '<table style="width: 100%; border-collapse: collapse;">';
        tableHtml += '<tr>' + data.columns.map(c => `<th style="border: 1px solid #374151; padding: 4px; background: #1f2937;">${escapeHtml(c)}</th>`).join('') + '</tr>';
        tableHtml += data.rows.slice(0, 10).map(row => 
            '<tr>' + data.columns.map(c => `<td style="border: 1px solid #374151; padding: 4px;">${escapeHtml(String(row[c]))}</td>`).join('') + '</tr>'
        ).join('');
        tableHtml += '</table>';
        if (data.row_count > 10) tableHtml += `<div style="color: #9ca3af; margin-top: 4px;">... showing first 10 of ${data.row_count} rows.</div>`;

        resultBox.innerHTML = tableHtml;
    } catch (err) {
        resultBox.innerHTML = `<span style="color: var(--accent-rose);">❌ Network error: ${escapeHtml(err.message)}</span>`;
    }
}

async function triggerETL() {
    if (!confirm("Are you sure you want to re-run the ETL cleaning pipeline and re-seed the SQLite database?")) return;
    try {
        const res = await fetch("/api/etl/re-ingest", { method: "POST" });
        if (res.ok) {
            alert("ETL cleaning and database re-seeding completed successfully!");
            await initDashboard();
        }
    } catch (err) {
        alert(`Error triggering ETL: ${err.message}`);
    }
}

function setSqlPreset(sqlText) {
    document.getElementById("sqlInput").value = sqlText;
    runSafeSQL();
}

function escapeHtml(str) {
    if (!str) return "";
    return str.replace(/&/g, "&amp;").replace(/</g, "&lt;").replace(/>/g, "&gt;").replace(/"/g, "&quot;").replace(/'/g, "&#039;");
}
