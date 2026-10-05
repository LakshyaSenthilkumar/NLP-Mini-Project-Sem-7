// Live NLP & AI Intelligence Lab Logic
document.addEventListener("DOMContentLoaded", () => {
    initNlpLab();
});

function initNlpLab() {
    const analyzeBtn = document.getElementById("btn-analyze-live");
    const inputEl = document.getElementById("nlp-input-text");

    if (analyzeBtn && inputEl) {
        analyzeBtn.addEventListener("click", () => {
            const text = inputEl.value.trim();
            if (text) {
                runLiveNlpAnalysis(text);
            }
        });
    }

    // Quick sample chips
    const sampleChips = document.querySelectorAll(".sample-nlp-prompt");
    sampleChips.forEach(chip => {
        chip.addEventListener("click", () => {
            const sampleText = chip.getAttribute("data-sample");
            if (inputEl) {
                inputEl.value = sampleText;
                runLiveNlpAnalysis(sampleText);
            }
        });
    });
}

async function runLiveNlpAnalysis(text) {
    const resultBox = document.getElementById("nlp-analysis-results");
    if (!resultBox) return;

    try {
        const res = await fetch("/api/nlp/analyze", {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({ text })
        });

        const data = await res.json();
        resultBox.classList.remove("hidden");

        // 1. Render Category & Confidence
        document.getElementById("res-category").innerText = data.category;
        const confPct = Math.round(data.category_confidence * 100);
        document.getElementById("res-confidence").innerText = `${confPct}%`;
        document.getElementById("res-confidence-bar").style.width = `${confPct}%`;

        // 2. Render Sentiment & Polarity
        const sentEl = document.getElementById("res-sentiment");
        const polEl = document.getElementById("res-polarity");
        sentEl.innerText = data.sentiment;
        sentEl.className = `text-lg font-bold ${
            data.sentiment === 'Positive' ? 'text-emerald-400' :
            data.sentiment === 'Negative' ? 'text-rose-400' : 'text-slate-300'
        }`;
        polEl.innerText = `Polarity Score: ${data.polarity_score > 0 ? '+' : ''}${data.polarity_score}`;

        // 3. Render Emotion Breakdown
        const emoContainer = document.getElementById("res-emotions-breakdown");
        if (emoContainer && data.emotion_scores) {
            emoContainer.innerHTML = Object.entries(data.emotion_scores).map(([emo, score]) => {
                const pct = Math.round(score * 100);
                const isPrimary = emo === data.primary_emotion;
                return `
                    <div class="space-y-1">
                        <div class="flex justify-between text-xs">
                            <span class="${isPrimary ? 'text-purple-300 font-bold' : 'text-slate-400'}">${emo} ${isPrimary ? '⭐' : ''}</span>
                            <span class="text-slate-400">${pct}%</span>
                        </div>
                        <div class="w-full bg-slate-800 rounded-full h-1.5">
                            <div class="h-1.5 rounded-full ${isPrimary ? 'bg-purple-500' : 'bg-slate-600'}" style="width: ${pct}%"></div>
                        </div>
                    </div>
                `;
            }).join("");
        }

        // 4. Render Extracted Named Entities (NER)
        const nerStations = document.getElementById("ner-stations");
        const nerLines = document.getElementById("ner-lines");
        const nerAspects = document.getElementById("ner-aspects");
        const nerDirections = document.getElementById("ner-directions");
        const nerTimes = document.getElementById("ner-times");

        renderChips(nerStations, data.entities.stations, "bg-cyan-950 text-cyan-300 border border-cyan-800", "📍");
        renderChips(nerLines, data.entities.lines, "bg-blue-950 text-blue-300 border border-blue-800", "🚆");
        renderChips(nerAspects, data.entities.aspects, "bg-amber-950 text-amber-300 border border-amber-800", "⚙️");
        renderChips(nerDirections, data.entities.directions, "bg-purple-950 text-purple-300 border border-purple-800", "🧭");
        renderChips(nerTimes, data.entities.time_mentions, "bg-slate-800 text-slate-300 border border-slate-700", "⏰");

        // 5. Render Resolved Location
        const locBadge = document.getElementById("ner-resolved-location");
        if (locBadge) {
            const loc = data.resolved_location;
            const locText = [loc.line_name, loc.station_name].filter(Boolean).join(" • ") || "Network-wide / Unspecified";
            locBadge.innerText = locText;
        }

    } catch (err) {
        console.error("Error in live NLP analysis:", err);
    }
}

function renderChips(container, items, styleClass, icon) {
    if (!container) return;
    if (!items || items.length === 0) {
        container.innerHTML = `<span class="text-xs text-slate-500 italic">None detected</span>`;
        return;
    }
    container.innerHTML = items.map(it => `
        <span class="inline-flex items-center gap-1 px-2.5 py-1 rounded-md text-xs font-semibold ${styleClass}">
            <span>${icon}</span> <span>${escapeHtml(it)}</span>
        </span>
    `).join("");
}
