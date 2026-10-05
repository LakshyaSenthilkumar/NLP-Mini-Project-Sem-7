// Disruption & Scenario Simulation Controller
document.addEventListener("DOMContentLoaded", () => {
    initSimulator();
});

function initSimulator() {
    const scenarioBtns = document.querySelectorAll(".btn-trigger-scenario");
    scenarioBtns.forEach(btn => {
        btn.addEventListener("click", async () => {
            const scenario = btn.getAttribute("data-scenario");
            await triggerScenario(scenario, btn);
        });
    });

    const resetBtn = document.getElementById("btn-reset-simulation");
    if (resetBtn) {
        resetBtn.addEventListener("click", async () => {
            await resetSimulationData(resetBtn);
        });
    }
}

async function triggerScenario(scenarioType, buttonEl) {
    const originalText = buttonEl.innerText;
    buttonEl.disabled = true;
    buttonEl.innerText = "Simulating Events...";

    try {
        const res = await fetch(`/api/simulation/inject?scenario_type=${scenarioType}`, {
            method: "POST"
        });
        const data = await res.json();

        if (res.ok) {
            showToast(`⚡ Injected ${data.injected_feedback_count} feedback reports for scenario: ${scenarioType.replace('_', ' ').toUpperCase()}`, "success");
            // Refresh entire dashboard & map
            await loadDashboardData();
        } else {
            showToast("Failed to simulate scenario", "error");
        }
    } catch (err) {
        showToast("Error triggering simulation", "error");
    } finally {
        buttonEl.disabled = false;
        buttonEl.innerText = originalText;
    }
}

async function resetSimulationData(buttonEl) {
    const originalText = buttonEl.innerText;
    buttonEl.disabled = true;
    buttonEl.innerText = "Resetting System...";

    try {
        const res = await fetch("/api/simulation/reset", {
            method: "POST"
        });
        const data = await res.json();

        if (res.ok) {
            showToast(`System reset to baseline with ${data.count} fresh records.`, "info");
            await loadDashboardData();
        } else {
            showToast("Failed to reset system", "error");
        }
    } catch (err) {
        showToast("Error resetting simulation", "error");
    } finally {
        buttonEl.disabled = false;
        buttonEl.innerText = originalText;
    }
}
