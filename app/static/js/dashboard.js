// Dashboard Logic and Charts for TransitPulse AI
let sentimentChart, emotionChart, categoryChart, channelChart, forecastChart;
let currentFeedbackList = [];

document.addEventListener("DOMContentLoaded", () => {
    initTabs();
    initFilterListeners();
    loadDashboardData();
    // Auto-refresh every 45 seconds
    setInterval(loadDashboardData, 45000);
});

// Toast notification helper
function showToast(message, type = "info") {
    const container = document.getElementById("toast-container");
    if (!container) return;

    const toast = document.createElement("div");
    toast.className = `toast border-l-4 ${
        type === "success" ? "border-emerald-500" :
        type === "error" ? "border-rose-500" :
        type === "warning" ? "border-amber-500" : "border-blue-500"
    }`;

    const icon = type === "success" ? "✅" : type === "error" ? "❌" : type === "warning" ? "⚠️" : "ℹ️";
    toast.innerHTML = `<span class="text-lg">${icon}</span> <span class="text-sm font-medium">${message}</span>`;

    container.appendChild(toast);
    setTimeout(() => {
        toast.style.opacity = "0";
        toast.style.transition = "opacity 0.3s ease";
        setTimeout(() => toast.remove(), 300);
    }, 3500);
}

// Tab navigation handler
function initTabs() {
    const tabButtons = document.querySelectorAll(".tab-btn");
    const tabContents = document.querySelectorAll(".tab-content");

    tabButtons.forEach(btn => {
        btn.addEventListener("click", () => {
            const target = btn.getAttribute("data-tab");

            tabButtons.forEach(b => {
                b.classList.remove("text-blue-400", "border-blue-500", "bg-blue-950/40");
                b.classList.add("text-slate-400", "border-transparent");
            });

            btn.classList.add("text-blue-400", "border-blue-500", "bg-blue-950/40");
            btn.classList.remove("text-slate-400", "border-transparent");

            tabContents.forEach(content => {
                content.classList.add("hidden");
            });

            const activeContent = document.getElementById(`tab-${target}`);
            if (activeContent) {
                activeContent.classList.remove("hidden");
            }

            // Invalidate Leaflet map size if switching to map tab
            if (target === "gis" && window.transitMap) {
                setTimeout(() => window.transitMap.invalidateSize(), 200);
            }
        });
    });
}

// Load main dashboard metrics and charts
async function loadDashboardData() {
    try {
        const [summaryRes, trendsRes, feedbackRes, recsRes] = await Promise.all([
            fetch("/api/analytics/summary"),
            fetch("/api/analytics/trends"),
            fetch("/api/feedback?limit=150"),
            fetch("/api/recommendations")
        ]);

        const summary = await summaryRes.json();
        const trends = await trendsRes.json();
        const feedback = await feedbackRes.json();
        const recs = await recsRes.json();

        currentFeedbackList = feedback;

        // Render KPI Counters
        document.getElementById("kpi-total-feedback").innerText = summary.total_feedback.toLocaleString();
        document.getElementById("kpi-csat-score").innerText = `${summary.csat_score}%`;
        document.getElementById("kpi-nss-score").innerText = `${summary.net_sentiment_score > 0 ? '+' : ''}${summary.net_sentiment_score}`;
        document.getElementById("kpi-open-tickets").innerText = summary.open_tickets_count;
        document.getElementById("kpi-critical-alerts").innerText = summary.critical_alerts_count;
        
        // Header Quick Pulse
        const headerPulse = document.getElementById("header-csat-badge");
        if (headerPulse) {
            headerPulse.innerText = `CSAT: ${summary.csat_score}%`;
            headerPulse.className = `px-2.5 py-1 rounded-full text-xs font-semibold ${
                summary.csat_score >= 75 ? "bg-emerald-950 text-emerald-300 border border-emerald-700" :
                summary.csat_score >= 55 ? "bg-amber-950 text-amber-300 border border-amber-700" :
                "bg-rose-950 text-rose-300 border border-rose-700"
            }`;
        }

        // Render Charts
        renderSentimentChart(summary.sentiment_distribution);
        renderEmotionChart(summary.emotion_distribution);
        renderCategoryChart(summary.category_distribution);
        renderChannelChart(summary.channel_breakdown);
        renderForecastChart(trends);

        // Render Feedback Explorer Table
        renderFeedbackTable(currentFeedbackList);

        // Refresh Map & Action Engine if initialized
        if (window.renderMapLayers) {
            window.renderMapLayers();
        }
        if (window.renderActionRecommendations) {
            window.renderActionRecommendations(recs);
        }

    } catch (err) {
        console.error("Error loading dashboard data:", err);
    }
}

// Chart 1: Sentiment Distribution Doughnut
function renderSentimentChart(dist) {
    const ctx = document.getElementById("chart-sentiment");
    if (!ctx) return;

    const data = {
        labels: ["Positive", "Neutral", "Negative"],
        datasets: [{
            data: [dist["Positive"] || 0, dist["Neutral"] || 0, dist["Negative"] || 0],
            backgroundColor: ["#10B981", "#64748B", "#EF4444"],
            borderColor: "#0F172A",
            borderWidth: 2,
            hoverOffset: 6
        }]
    };

    if (sentimentChart) {
        sentimentChart.data = data;
        sentimentChart.update();
    } else {
        sentimentChart = new Chart(ctx, {
            type: "doughnut",
            data: data,
            options: {
                responsive: true,
                maintainAspectRatio: false,
                plugins: {
                    legend: { position: "bottom", labels: { color: "#CBD5E1", boxWidth: 12 } }
                },
                cutout: "68%"
            }
        });
    }
}

// Chart 2: Emotion Radar Chart
function renderEmotionChart(emotions) {
    const ctx = document.getElementById("chart-emotion");
    if (!ctx) return;

    const labels = ["Anger", "Frustration", "Anxiety", "Satisfaction", "Gratitude", "Neutral"];
    const values = labels.map(l => emotions[l] || 0);

    const data = {
        labels: labels,
        datasets: [{
            label: "Emotion Volume",
            data: values,
            backgroundColor: "rgba(139, 92, 246, 0.25)",
            borderColor: "#8B5CF6",
            pointBackgroundColor: "#A855F7",
            pointBorderColor: "#fff",
            pointHoverBackgroundColor: "#fff",
            pointHoverBorderColor: "#A855F7",
            borderWidth: 2
        }]
    };

    if (emotionChart) {
        emotionChart.data = data;
        emotionChart.update();
    } else {
        emotionChart = new Chart(ctx, {
            type: "radar",
            data: data,
            options: {
                responsive: true,
                maintainAspectRatio: false,
                scales: {
                    r: {
                        angleLines: { color: "#334155" },
                        grid: { color: "#334155" },
                        pointLabels: { color: "#94A3B8", font: { size: 11 } },
                        ticks: { display: false }
                    }
                },
                plugins: {
                    legend: { display: false }
                }
            }
        });
    }
}

// Chart 3: Service Category Volume (Horizontal Bar)
function renderCategoryChart(categories) {
    const ctx = document.getElementById("chart-category");
    if (!ctx) return;

    const sortedCats = Object.entries(categories).sort((a, b) => b[1] - a[1]);
    const labels = sortedCats.map(c => c[0]);
    const values = sortedCats.map(c => c[1]);

    const data = {
        labels: labels,
        datasets: [{
            label: "Complaints / Mentions",
            data: values,
            backgroundColor: [
                "#3B82F6", "#F59E0B", "#10B981", "#8B5CF6", "#EC4899",
                "#14B8A6", "#6366F1", "#F97316", "#06B6D4"
            ],
            borderRadius: 6
        }]
    };

    if (categoryChart) {
        categoryChart.data = data;
        categoryChart.update();
    } else {
        categoryChart = new Chart(ctx, {
            type: "bar",
            data: data,
            options: {
                indexAxis: "y",
                responsive: true,
                maintainAspectRatio: false,
                scales: {
                    x: { grid: { color: "#334155" }, ticks: { color: "#94A3B8" } },
                    y: { grid: { display: false }, ticks: { color: "#CBD5E1", font: { size: 11 } } }
                },
                plugins: {
                    legend: { display: false }
                }
            }
        });
    }
}

// Chart 4: Channels Breakdown (Pie)
function renderChannelChart(channels) {
    const ctx = document.getElementById("chart-channel");
    if (!ctx) return;

    const labels = Object.keys(channels);
    const values = Object.values(channels);

    const data = {
        labels: labels,
        datasets: [{
            data: values,
            backgroundColor: ["#3B82F6", "#10B981", "#F59E0B", "#8B5CF6"],
            borderColor: "#0F172A",
            borderWidth: 2
        }]
    };

    if (channelChart) {
        channelChart.data = data;
        channelChart.update();
    } else {
        channelChart = new Chart(ctx, {
            type: "pie",
            data: data,
            options: {
                responsive: true,
                maintainAspectRatio: false,
                plugins: {
                    legend: { position: "bottom", labels: { color: "#CBD5E1", boxWidth: 10 } }
                }
            }
        });
    }
}

// Chart 5: 7-Day CSAT Trend & Linear Forecast
function renderForecastChart(trendsData) {
    const ctx = document.getElementById("chart-forecast");
    if (!ctx) return;

    const hist = trendsData.historical_trend || [];
    const fc = trendsData.forecast_trend || [];

    const labels = [...hist.map(h => h.date.slice(5)), ...fc.map(f => f.date.slice(5))];
    
    // Historical CSAT line
    const histData = [...hist.map(h => h.csat), ...fc.map(() => null)];
    // Forecast CSAT line (connected from last historical point)
    const lastHistVal = hist.length ? hist[hist.length - 1].csat : 75;
    const fcData = [...hist.slice(0, -1).map(() => null), lastHistVal, ...fc.map(f => f.projected_csat)];

    const upperBand = [...hist.slice(0, -1).map(() => null), lastHistVal, ...fc.map(f => f.upper_confidence)];
    const lowerBand = [...hist.slice(0, -1).map(() => null), lastHistVal, ...fc.map(f => f.lower_confidence)];

    const data = {
        labels: labels,
        datasets: [
            {
                label: "Actual CSAT (%)",
                data: histData,
                borderColor: "#3B82F6",
                backgroundColor: "rgba(59, 130, 246, 0.1)",
                borderWidth: 3,
                tension: 0.3,
                fill: true,
                pointRadius: 4,
                pointBackgroundColor: "#3B82F6"
            },
            {
                label: "AI Projected CSAT (%)",
                data: fcData,
                borderColor: "#10B981",
                borderDash: [6, 4],
                borderWidth: 2.5,
                tension: 0.3,
                pointRadius: 4,
                pointBackgroundColor: "#10B981"
            },
            {
                label: "Upper Confidence Bound",
                data: upperBand,
                borderColor: "transparent",
                backgroundColor: "rgba(16, 185, 129, 0.08)",
                fill: "+1",
                pointRadius: 0
            },
            {
                label: "Lower Confidence Bound",
                data: lowerBand,
                borderColor: "transparent",
                pointRadius: 0
            }
        ]
    };

    if (forecastChart) {
        forecastChart.data = data;
        forecastChart.update();
    } else {
        forecastChart = new Chart(ctx, {
            type: "line",
            data: data,
            options: {
                responsive: true,
                maintainAspectRatio: false,
                scales: {
                    x: { grid: { color: "#334155" }, ticks: { color: "#94A3B8" } },
                    y: { min: 20, max: 100, grid: { color: "#334155" }, ticks: { color: "#94A3B8" } }
                },
                plugins: {
                    legend: { labels: { color: "#CBD5E1", filter: item => !item.text.includes("Bound") } }
                }
            }
        });
    }
}

// Render Feedback Explorer Table
function renderFeedbackTable(items) {
    const tbody = document.getElementById("feedback-table-body");
    const countBadge = document.getElementById("feedback-count-badge");
    if (!tbody) return;

    if (countBadge) countBadge.innerText = `${items.length} records`;

    if (items.length === 0) {
        tbody.innerHTML = `<tr><td colspan="7" class="text-center py-8 text-slate-400">No feedback matching the selected filters.</td></tr>`;
        return;
    }

    tbody.innerHTML = items.map(item => {
        const sentimentColor = 
            item.sentiment === "Positive" ? "bg-emerald-950 text-emerald-400 border-emerald-700" :
            item.sentiment === "Negative" ? "bg-rose-950 text-rose-400 border-rose-700" :
            "bg-slate-800 text-slate-300 border-slate-600";

        const severityBadge =
            item.severity === "Critical" ? "bg-red-500/20 text-red-400 border-red-500/40" :
            item.severity === "High" ? "bg-orange-500/20 text-orange-400 border-orange-500/40" :
            item.severity === "Medium" ? "bg-amber-500/20 text-amber-400 border-amber-500/40" :
            "bg-slate-500/20 text-slate-400 border-slate-500/40";

        const statusBadge =
            item.status === "Resolved" ? "bg-emerald-500/20 text-emerald-400" :
            item.status === "Dispatched" ? "bg-purple-500/20 text-purple-400" :
            item.status === "In Review" ? "bg-blue-500/20 text-blue-400" :
            "bg-amber-500/20 text-amber-400";

        return `
        <tr class="border-b border-slate-800 hover:bg-slate-800/40 transition">
            <td class="py-3 px-4 font-mono text-xs text-slate-400">${item.id}</td>
            <td class="py-3 px-4">
                <p class="text-sm text-slate-200 line-clamp-2">${escapeHtml(item.text)}</p>
                <div class="flex flex-wrap gap-1.5 mt-1.5 text-xs text-slate-400">
                    <span class="bg-slate-800 px-1.5 py-0.5 rounded text-blue-400">${item.mode || 'Transit'}</span>
                    ${item.line_name ? `<span class="bg-slate-800 px-1.5 py-0.5 rounded text-indigo-300">🚆 ${item.line_name}</span>` : ''}
                    ${item.station_name ? `<span class="bg-slate-800 px-1.5 py-0.5 rounded text-cyan-300">📍 ${item.station_name}</span>` : ''}
                    <span class="bg-slate-800 px-1.5 py-0.5 rounded">📱 ${item.source}</span>
                </div>
            </td>
            <td class="py-3 px-4 text-xs whitespace-nowrap">
                <span class="px-2 py-1 rounded-md border text-xs font-medium bg-slate-800 text-slate-300 border-slate-700">
                    ${item.category}
                </span>
            </td>
            <td class="py-3 px-4 whitespace-nowrap">
                <span class="px-2 py-1 rounded-full border text-xs font-semibold ${sentimentColor}">
                    ${item.sentiment} (${item.polarity_score > 0 ? '+' : ''}${item.polarity_score})
                </span>
                <div class="text-[11px] text-slate-400 mt-1">Emotion: <span class="text-purple-300 font-medium">${item.primary_emotion}</span></div>
            </td>
            <td class="py-3 px-4 whitespace-nowrap">
                <span class="px-2 py-0.5 rounded border text-[11px] font-semibold ${severityBadge}">
                    ${item.severity}
                </span>
            </td>
            <td class="py-3 px-4 whitespace-nowrap">
                <select onchange="updateTicketStatus('${item.id}', this.value)" class="text-xs bg-slate-900 border border-slate-700 rounded px-2 py-1 text-slate-300 focus:outline-none focus:border-blue-500">
                    <option value="Open" ${item.status === 'Open' ? 'selected' : ''}>Open</option>
                    <option value="In Review" ${item.status === 'In Review' ? 'selected' : ''}>In Review</option>
                    <option value="Dispatched" ${item.status === 'Dispatched' ? 'selected' : ''}>Dispatched</option>
                    <option value="Resolved" ${item.status === 'Resolved' ? 'selected' : ''}>Resolved</option>
                </select>
            </td>
            <td class="py-3 px-4 text-xs text-slate-400 whitespace-nowrap">${item.timestamp.slice(5, 16)}</td>
        </tr>
        `;
    }).join("");
}

// Filter listeners
function initFilterListeners() {
    const filters = ["filter-mode", "filter-category", "filter-sentiment", "filter-severity", "filter-source", "filter-search"];
    filters.forEach(id => {
        const el = document.getElementById(id);
        if (el) {
            el.addEventListener("input", applyFilters);
        }
    });
}

function applyFilters() {
    const mode = document.getElementById("filter-mode")?.value || "All";
    const category = document.getElementById("filter-category")?.value || "All";
    const sentiment = document.getElementById("filter-sentiment")?.value || "All";
    const severity = document.getElementById("filter-severity")?.value || "All";
    const source = document.getElementById("filter-source")?.value || "All";
    const search = document.getElementById("filter-search")?.value.toLowerCase() || "";

    const filtered = currentFeedbackList.filter(item => {
        if (mode !== "All" && item.mode !== mode) return false;
        if (category !== "All" && item.category !== category) return false;
        if (sentiment !== "All" && item.sentiment !== sentiment) return false;
        if (severity !== "All" && item.severity !== severity) return false;
        if (source !== "All" && item.source !== source) return false;
        if (search) {
            const txt = (item.text || "").toLowerCase();
            const st = (item.station_name || "").toLowerCase();
            const ln = (item.line_name || "").toLowerCase();
            if (!txt.includes(search) && !st.includes(search) && !ln.includes(search)) return false;
        }
        return true;
    });

    renderFeedbackTable(filtered);
}

// Update feedback ticket status
async function updateTicketStatus(id, newStatus) {
    try {
        const res = await fetch(`/api/feedback/${id}/status`, {
            method: "PATCH",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({ status: newStatus })
        });
        if (res.ok) {
            showToast(`Ticket ${id} status set to ${newStatus}`, "success");
            loadDashboardData();
        }
    } catch (err) {
        showToast("Failed to update ticket status", "error");
    }
}

function escapeHtml(text) {
    if (!text) return "";
    return text.replace(/&/g, "&amp;").replace(/</g, "&lt;").replace(/>/g, "&gt;").replace(/"/g, "&quot;");
}
