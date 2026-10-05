// Decision Support & Action Center Logic (with Custom Creation & Suggestion Editing)
let currentRecommendations = [];
let activeRecPriorityFilter = "All";
let currentlyEditingRecId = null;

document.addEventListener("DOMContentLoaded", () => {
    initActionListeners();
    loadBottlenecksAndRootCauses();
});

function initActionListeners() {
    // Priority filter buttons
    const filterBtns = document.querySelectorAll(".rec-priority-filter");
    filterBtns.forEach(btn => {
        btn.addEventListener("click", () => {
            filterBtns.forEach(b => b.classList.remove("bg-blue-600", "text-white"));
            btn.classList.add("bg-blue-600", "text-white");
            activeRecPriorityFilter = btn.getAttribute("data-priority");
            renderActionRecommendations(currentRecommendations);
        });
    });

    // Create custom action button
    const btnOpenCreate = document.getElementById("btn-open-create-action");
    if (btnOpenCreate) {
        btnOpenCreate.addEventListener("click", () => {
            openCreateActionModal();
        });
    }

    // Create form submission
    const formCreate = document.getElementById("form-create-custom-action");
    if (formCreate) {
        formCreate.addEventListener("submit", async (e) => {
            e.preventDefault();
            await submitCustomAction();
        });
    }

    // Edit form submission
    const formEdit = document.getElementById("form-edit-action");
    if (formEdit) {
        formEdit.addEventListener("submit", async (e) => {
            e.preventDefault();
            await submitEditAction(false);
        });
    }

    const btnSaveAndApprove = document.getElementById("btn-edit-save-and-approve");
    if (btnSaveAndApprove) {
        btnSaveAndApprove.addEventListener("click", async () => {
            await submitEditAction(true);
        });
    }
}

function renderActionRecommendations(recs) {
    currentRecommendations = recs || [];
    const container = document.getElementById("recommendations-container");
    if (!container) return;

    const filtered = currentRecommendations.filter(r => {
        if (activeRecPriorityFilter === "All") return true;
        return r.priority === activeRecPriorityFilter;
    });

    if (filtered.length === 0) {
        container.innerHTML = `
            <div class="col-span-full text-center py-12 glass-card rounded-xl">
                <div class="text-4xl mb-2">🎉</div>
                <div class="text-lg font-bold text-slate-200">No Pending Directives in this Category</div>
                <p class="text-sm text-slate-400 mt-1">Click the <strong>"+ Add Custom Action / Suggestion"</strong> button above to submit an operational directive.</p>
            </div>
        `;
        return;
    }

    container.innerHTML = filtered.map(r => {
        const priorityBadge =
            r.priority === "Critical" ? "bg-rose-500/20 text-rose-400 border-rose-500/40 glow-danger" :
            r.priority === "High" ? "bg-orange-500/20 text-orange-400 border-orange-500/40" :
            r.priority === "Medium" ? "bg-amber-500/20 text-amber-400 border-amber-500/40" :
            "bg-blue-500/20 text-blue-400 border-blue-500/40";

        const statusBadge =
            r.status === "Completed" ? "bg-emerald-500/20 text-emerald-400 border-emerald-500/30" :
            r.status === "Dispatched" ? "bg-purple-500/20 text-purple-400 border-purple-500/30" :
            r.status === "Approved" ? "bg-blue-500/20 text-blue-400 border-blue-500/30" :
            "bg-amber-500/20 text-amber-400 border-amber-500/30";

        const isCustom = r.is_custom;
        const hasSupervisorNotes = Boolean(r.supervisor_notes);

        return `
            <div class="glass-card rounded-xl p-5 border border-slate-700/60 flex flex-col justify-between transition hover:border-slate-500">
                <div>
                    <!-- Header Badges -->
                    <div class="flex items-start justify-between gap-3 mb-3">
                        <div class="flex flex-wrap items-center gap-2">
                            <span class="px-2.5 py-0.5 rounded-full text-xs font-bold border ${priorityBadge}">
                                ${r.priority} Priority (${r.severity_score}/100)
                            </span>
                            <span class="px-2 py-0.5 rounded-md text-xs font-medium border ${statusBadge}">
                                ${r.status}
                            </span>
                            ${isCustom ? `
                                <span class="px-2 py-0.5 rounded-md text-[11px] font-semibold bg-indigo-950 text-indigo-300 border border-indigo-700 flex items-center gap-1">
                                    <span>👤</span> Custom Directive
                                </span>
                            ` : ''}
                        </div>
                        <span class="text-xs font-mono text-slate-500">${r.id}</span>
                    </div>

                    <!-- Title & Category -->
                    <h3 class="text-base font-bold text-white mb-1.5 leading-snug">${escapeHtml(r.title)}</h3>
                    <div class="flex flex-wrap items-center gap-2 text-xs text-slate-400 mb-3">
                        <span class="bg-slate-800 px-2 py-0.5 rounded text-blue-300">🏷️ ${r.category}</span>
                        <span class="bg-slate-800 px-2 py-0.5 rounded text-cyan-300">📍 ${r.target_name}</span>
                        <span class="bg-slate-800 px-2 py-0.5 rounded text-indigo-300">👥 ~${r.affected_passenger_count} Affected</span>
                    </div>

                    <!-- Root Cause Diagnosis -->
                    <div class="bg-slate-900/90 rounded-lg p-3 border border-slate-800 mb-3">
                        <div class="text-[11px] font-semibold text-rose-400 uppercase tracking-wider mb-1 flex items-center gap-1">
                            <span>🔍</span> Root Cause Diagnosis
                        </div>
                        <p class="text-xs text-slate-300 leading-relaxed">${escapeHtml(r.root_cause_summary)}</p>
                    </div>

                    <!-- Prescriptive Action / Directive -->
                    <div class="bg-blue-950/30 rounded-lg p-3 border border-blue-900/50 mb-3">
                        <div class="text-[11px] font-semibold text-blue-400 uppercase tracking-wider mb-1 flex items-center gap-1">
                            <span>⚡</span> Prescriptive Action / Suggestion
                        </div>
                        <p class="text-xs text-slate-200 font-medium leading-relaxed">${escapeHtml(r.recommended_action)}</p>
                    </div>

                    <!-- Supervisor Remarks / Custom Notes if present -->
                    ${hasSupervisorNotes ? `
                        <div class="bg-purple-950/30 rounded-lg p-3 border border-purple-900/50 mb-3">
                            <div class="text-[11px] font-semibold text-purple-400 uppercase tracking-wider mb-1 flex items-center gap-1">
                                <span>📝</span> Authority Remarks & Suggestions
                            </div>
                            <p class="text-xs text-purple-200 italic leading-relaxed">${escapeHtml(r.supervisor_notes)}</p>
                        </div>
                    ` : ''}

                    <!-- Impact & Department -->
                    <div class="space-y-1.5 text-xs text-slate-400 mb-4">
                        <div class="flex items-center gap-1.5">
                            <span class="text-emerald-400 font-semibold">📈 Projected Impact:</span>
                            <span class="text-slate-300">${escapeHtml(r.estimated_impact)}</span>
                        </div>
                        <div class="flex items-center gap-1.5">
                            <span class="text-purple-400 font-semibold">🏢 Assigned Dept:</span>
                            <span class="text-slate-300">${r.operational_department}</span>
                        </div>
                    </div>
                </div>

                <!-- Action Workflow Buttons & Edit Suggestion Button -->
                <div class="pt-3 border-t border-slate-800/80 flex flex-wrap items-center justify-between gap-2">
                    <span class="text-[11px] text-slate-500">${r.created_at.slice(5, 16)}</span>
                    <div class="flex flex-wrap items-center gap-2">
                        <!-- Edit / Add Suggestion Button -->
                        <button onclick="openEditActionModal('${r.id}')" class="px-2.5 py-1.5 bg-slate-800 hover:bg-slate-700 text-slate-200 text-xs font-semibold rounded-lg border border-slate-700 transition flex items-center gap-1">
                            <span>✏️</span> Edit / Suggest
                        </button>

                        ${r.status === 'Open' ? `
                            <button onclick="updateRecStatus('${r.id}', 'Approved')" class="px-3 py-1.5 bg-blue-600 hover:bg-blue-500 text-white text-xs font-semibold rounded-lg transition shadow">
                                Approve Action
                            </button>
                        ` : ''}
                        ${r.status === 'Approved' ? `
                            <button onclick="updateRecStatus('${r.id}', 'Dispatched')" class="px-3 py-1.5 bg-purple-600 hover:bg-purple-500 text-white text-xs font-semibold rounded-lg transition shadow">
                                🚀 Dispatch Crew
                            </button>
                        ` : ''}
                        ${r.status === 'Dispatched' ? `
                            <button onclick="updateRecStatus('${r.id}', 'Completed')" class="px-3 py-1.5 bg-emerald-600 hover:bg-emerald-500 text-white text-xs font-semibold rounded-lg transition shadow">
                                ✅ Mark Completed
                            </button>
                        ` : ''}
                        ${r.status === 'Completed' ? `
                            <span class="text-xs text-emerald-400 font-semibold flex items-center gap-1">
                                <span>✓</span> Executed
                            </span>
                        ` : ''}
                    </div>
                </div>
            </div>
        `;
    }).join("");
}

// ----------------- Modal 1: Create Custom Action -----------------
function openCreateActionModal() {
    const modal = document.getElementById("modal-create-action");
    if (modal) {
        modal.classList.remove("hidden");
    }
}

function closeCreateActionModal() {
    const modal = document.getElementById("modal-create-action");
    if (modal) {
        modal.classList.add("hidden");
    }
}

async function submitCustomAction() {
    const title = document.getElementById("create-act-title").value.trim();
    const category = document.getElementById("create-act-category").value;
    const targetName = document.getElementById("create-act-location").value.trim();
    const priority = document.getElementById("create-act-priority").value;
    const rootCause = document.getElementById("create-act-root-cause").value.trim();
    const action = document.getElementById("create-act-action").value.trim();
    const dept = document.getElementById("create-act-dept").value;
    const impact = document.getElementById("create-act-impact").value.trim();
    const notes = document.getElementById("create-act-notes").value.trim();

    if (!title || !action || !targetName) {
        showToast("Please fill in title, target location, and action directive.", "warning");
        return;
    }

    const payload = {
        title: title,
        category: category,
        target_name: targetName,
        priority: priority,
        root_cause_summary: rootCause || "Authority identified operational bottleneck.",
        recommended_action: action,
        operational_department: dept,
        estimated_impact: impact || "Immediate service reliability recovery across corridor.",
        supervisor_notes: notes || null
    };

    try {
        const res = await fetch("/api/recommendations", {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify(payload)
        });

        if (res.ok) {
            const created = await res.json();
            showToast(`Custom action directive "${created.id}" created successfully!`, "success");
            closeCreateActionModal();
            document.getElementById("form-create-custom-action").reset();
            await loadDashboardData();
        } else {
            showToast("Failed to create custom action directive", "error");
        }
    } catch (err) {
        showToast("Network error creating action directive", "error");
    }
}

// ----------------- Modal 2: Edit Existing Action / Add Suggestion -----------------
function openEditActionModal(recId) {
    const rec = currentRecommendations.find(r => r.id === recId);
    if (!rec) return;

    currentlyEditingRecId = recId;
    document.getElementById("edit-modal-rec-id").innerText = rec.id;
    document.getElementById("edit-act-title").value = rec.title;
    document.getElementById("edit-act-priority").value = rec.priority;
    document.getElementById("edit-act-action").value = rec.recommended_action;
    document.getElementById("edit-act-notes").value = rec.supervisor_notes || "";
    document.getElementById("edit-act-dept").value = rec.operational_department;
    document.getElementById("edit-act-impact").value = rec.estimated_impact;

    const modal = document.getElementById("modal-edit-action");
    if (modal) {
        modal.classList.remove("hidden");
    }
}

function closeEditActionModal() {
    const modal = document.getElementById("modal-edit-action");
    if (modal) {
        modal.classList.add("hidden");
    }
    currentlyEditingRecId = null;
}

async function submitEditAction(shouldApprove = false) {
    if (!currentlyEditingRecId) return;

    const title = document.getElementById("edit-act-title").value.trim();
    const priority = document.getElementById("edit-act-priority").value;
    const action = document.getElementById("edit-act-action").value.trim();
    const notes = document.getElementById("edit-act-notes").value.trim();
    const dept = document.getElementById("edit-act-dept").value;
    const impact = document.getElementById("edit-act-impact").value.trim();

    const payload = {
        title: title,
        priority: priority,
        recommended_action: action,
        supervisor_notes: notes || null,
        operational_department: dept,
        estimated_impact: impact,
        status: shouldApprove ? "Approved" : undefined
    };

    try {
        const res = await fetch(`/api/recommendations/${currentlyEditingRecId}`, {
            method: "PUT",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify(payload)
        });

        if (res.ok) {
            showToast(shouldApprove ? `Action updated and Approved!` : `Suggestions & changes saved for ${currentlyEditingRecId}!`, "success");
            closeEditActionModal();
            await loadDashboardData();
        } else {
            showToast("Failed to update recommendation", "error");
        }
    } catch (err) {
        showToast("Error updating recommendation", "error");
    }
}

async function updateRecStatus(recId, newStatus) {
    try {
        const res = await fetch(`/api/recommendations/${recId}/status`, {
            method: "PATCH",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({ status: newStatus })
        });
        if (res.ok) {
            showToast(`Action ${recId} changed to ${newStatus}`, "success");
            await loadDashboardData();
        }
    } catch (err) {
        showToast("Error updating recommendation status", "error");
    }
}

// Load Topic Clusters and Recurring Bottlenecks
async function loadBottlenecksAndRootCauses() {
    try {
        const res = await fetch("/api/bottlenecks");
        const data = await res.json();

        // Render Trending Key Phrases
        const phrasesContainer = document.getElementById("trending-phrases-container");
        if (phrasesContainer && data.key_phrases) {
            phrasesContainer.innerHTML = data.key_phrases.map(p => `
                <div class="bg-slate-800/80 px-3 py-1.5 rounded-lg border border-slate-700 flex items-center justify-between text-xs">
                    <span class="font-medium text-slate-300">"${escapeHtml(p.phrase)}"</span>
                    <span class="bg-rose-950 text-rose-300 px-2 py-0.5 rounded-full text-[11px] font-bold">${p.count} mentions</span>
                </div>
            `).join("");
        }

        // Render Topic Clusters
        const clustersContainer = document.getElementById("topic-clusters-container");
        if (clustersContainer && data.clusters) {
            clustersContainer.innerHTML = data.clusters.map(c => `
                <div class="bg-slate-900/60 p-3.5 rounded-xl border border-slate-800 hover:border-slate-700 transition">
                    <div class="flex items-center justify-between mb-2">
                        <span class="font-bold text-sm text-white">${escapeHtml(c.title)}</span>
                        <span class="text-xs font-bold text-rose-400">Severity: ${c.severity_score}</span>
                    </div>
                    <div class="flex flex-wrap gap-1.5 mb-2">
                        ${c.top_keywords.map(kw => `<span class="bg-slate-800 px-2 py-0.5 rounded text-[11px] text-blue-300">#${escapeHtml(kw)}</span>`).join("")}
                    </div>
                    <div class="text-xs text-slate-400">
                        <span class="text-slate-300 font-medium">${c.item_count} feedback reports</span> • <span class="text-amber-400">${c.dominant_emotion}</span>
                    </div>
                </div>
            `).join("");
        }

    } catch (err) {
        console.error("Error loading bottlenecks:", err);
    }
}

window.renderActionRecommendations = renderActionRecommendations;
window.openCreateActionModal = openCreateActionModal;
window.closeCreateActionModal = closeCreateActionModal;
window.openEditActionModal = openEditActionModal;
window.closeEditActionModal = closeEditActionModal;
