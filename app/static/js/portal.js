// Passenger Public Feedback Portal Logic
let currentSelectedRating = 5;

document.addEventListener("DOMContentLoaded", () => {
    initPortal();
});

function initPortal() {
    const starBtns = document.querySelectorAll(".portal-star-btn");
    starBtns.forEach(btn => {
        btn.addEventListener("click", () => {
            const val = parseInt(btn.getAttribute("data-value"));
            currentSelectedRating = val;
            updateStarDisplay(val);
        });
    });

    const form = document.getElementById("passenger-feedback-form");
    if (form) {
        form.addEventListener("submit", async (e) => {
            e.preventDefault();
            await submitPassengerFeedback();
        });
    }

    // Live typing preview
    const textarea = document.getElementById("portal-feedback-text");
    let debounceTimer;
    if (textarea) {
        textarea.addEventListener("input", () => {
            clearTimeout(debounceTimer);
            debounceTimer = setTimeout(() => {
                updatePortalLivePreview(textarea.value.trim());
            }, 400);
        });
    }
}

function updateStarDisplay(val) {
    const starBtns = document.querySelectorAll(".portal-star-btn");
    starBtns.forEach(b => {
        const btnVal = parseInt(b.getAttribute("data-value"));
        if (btnVal <= val) {
            b.classList.remove("text-slate-600");
            b.classList.add("text-amber-400");
        } else {
            b.classList.remove("text-amber-400");
            b.classList.add("text-slate-600");
        }
    });
}

async function updatePortalLivePreview(text) {
    const previewBox = document.getElementById("portal-ai-preview");
    if (!previewBox) return;

    if (!text || text.length < 5) {
        previewBox.classList.add("hidden");
        return;
    }

    try {
        const res = await fetch("/api/nlp/analyze", {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({ text })
        });
        const data = await res.json();
        previewBox.classList.remove("hidden");

        document.getElementById("preview-category").innerText = data.category;
        document.getElementById("preview-sentiment").innerText = data.sentiment;
        document.getElementById("preview-emotion").innerText = data.primary_emotion;

        const sentBadge = document.getElementById("preview-sentiment-badge");
        if (sentBadge) {
            sentBadge.className = `px-2 py-0.5 rounded text-xs font-bold ${
                data.sentiment === 'Positive' ? 'bg-emerald-950 text-emerald-300 border border-emerald-700' :
                data.sentiment === 'Negative' ? 'bg-rose-950 text-rose-300 border border-rose-700' :
                'bg-slate-800 text-slate-300'
            }`;
        }
    } catch (err) {
        // silent fail on preview
    }
}

async function submitPassengerFeedback() {
    const textEl = document.getElementById("portal-feedback-text");
    const sourceEl = document.getElementById("portal-channel-select");
    const modeEl = document.getElementById("portal-mode-select");
    const lineEl = document.getElementById("portal-line-select");
    const stationEl = document.getElementById("portal-station-select");

    const text = textEl.value.trim();
    if (!text) {
        showToast("Please enter your feedback comments.", "warning");
        return;
    }

    const payload = {
        text: text,
        source: sourceEl?.value || "Mobile App",
        mode: modeEl?.value || "Metro",
        line_id: lineEl?.value || null,
        station_id: stationEl?.value || null,
        rating: currentSelectedRating
    };

    const submitBtn = document.getElementById("btn-submit-feedback");
    if (submitBtn) {
        submitBtn.disabled = true;
        submitBtn.innerText = "Submitting with AI Triage...";
    }

    try {
        const res = await fetch("/api/feedback", {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify(payload)
        });

        if (res.ok) {
            const result = await res.json();
            showToast(`Thank you! Feedback #${result.id} submitted & classified as "${result.category}"`, "success");

            // Reset form
            textEl.value = "";
            document.getElementById("portal-ai-preview")?.classList.add("hidden");
            currentSelectedRating = 5;
            updateStarDisplay(5);

            // Refresh global dashboard in background
            loadDashboardData();
        } else {
            showToast("Error submitting feedback. Please try again.", "error");
        }
    } catch (err) {
        showToast("Network error submitting feedback.", "error");
    } finally {
        if (submitBtn) {
            submitBtn.disabled = false;
            submitBtn.innerText = "Submit Passenger Feedback";
        }
    }
}
