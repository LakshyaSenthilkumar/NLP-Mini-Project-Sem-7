// GIS Interactive Transit Map Logic for Mumbai & Navi Mumbai Region
let map, heatLayer, geoJsonLinesLayer, stationsLayerGroup;
let currentGisModeFilter = "All";
let showHeatmapToggle = true;

document.addEventListener("DOMContentLoaded", () => {
    initGisMap();
});

function initGisMap() {
    const mapEl = document.getElementById("gis-map");
    if (!mapEl) return;

    // Center on Mumbai Metropolitan Region
    map = L.map("gis-map", {
        center: [19.0760, 72.8777],
        zoom: 11,
        zoomControl: true
    });
    window.transitMap = map;

    // Dark Matter Carto Tile Layer
    L.tileLayer("https://{s}.basemaps.cartocdn.com/dark_all/{z}/{x}/{y}{r}.png", {
        attribution: '&copy; <a href="https://carto.com/">CARTO</a> | &copy; OpenStreetMap',
        maxZoom: 19,
        subdomains: "abcd"
    }).addTo(map);

    stationsLayerGroup = L.layerGroup().addTo(map);

    // Initial load
    renderMapLayers();

    // Setup map control listeners
    const modeSelect = document.getElementById("map-mode-filter");
    if (modeSelect) {
        modeSelect.addEventListener("change", (e) => {
            currentGisModeFilter = e.target.value;
            renderMapLayers();
        });
    }

    const heatToggle = document.getElementById("map-toggle-heatmap");
    if (heatToggle) {
        heatToggle.addEventListener("change", (e) => {
            showHeatmapToggle = e.target.checked;
            if (heatLayer) {
                if (showHeatmapToggle) map.addLayer(heatLayer);
                else map.removeLayer(heatLayer);
            }
        });
    }
}

async function renderMapLayers() {
    if (!map) return;

    try {
        const [networkRes, stationsRes, routesRes, heatRes] = await Promise.all([
            fetch("/api/gis/network"),
            fetch("/api/gis/stations"),
            fetch("/api/gis/routes"),
            fetch("/api/gis/heatmap")
        ]);

        const networkGeoJson = await networkRes.json();
        const stations = await stationsRes.json();
        const routes = await routesRes.json();
        const heatPoints = await heatRes.json();

        // 1. Render Lines
        if (geoJsonLinesLayer) {
            map.removeLayer(geoJsonLinesLayer);
        }

        const filteredLineFeatures = networkGeoJson.features.filter(f => {
            if (f.geometry.type !== "LineString") return false;
            if (currentGisModeFilter === "All") return true;
            return f.properties.mode === currentGisModeFilter;
        });

        geoJsonLinesLayer = L.geoJSON({ type: "FeatureCollection", features: filteredLineFeatures }, {
            style: (feature) => {
                return {
                    color: feature.properties.color || "#3B82F6",
                    weight: 5,
                    opacity: 0.85
                };
            },
            onEachFeature: (feature, layer) => {
                const routeInfo = routes.find(r => r.id === feature.properties.id) || {};
                layer.bindTooltip(`
                    <div class="text-xs font-bold">${feature.properties.name}</div>
                    <div class="text-[11px] text-slate-300">Mode: ${feature.properties.mode}</div>
                    <div class="text-[11px] text-emerald-400">CSAT: ${routeInfo.csat || 80}%</div>
                    <div class="text-[11px] text-amber-400">Health: ${routeInfo.health_status || 'Good'}</div>
                `, { sticky: true, className: "custom-map-tooltip" });
            }
        }).addTo(map);

        // 2. Render Station Pins with Mumbai transit icons
        stationsLayerGroup.clearLayers();

        stations.forEach(st => {
            if (currentGisModeFilter !== "All" && !st.modes.includes(currentGisModeFilter)) {
                return;
            }

            const isCritical = st.status === "Critical";
            const isBottleneck = st.status === "Bottleneck";
            const primaryMode = st.modes[0] || "Train";

            let markerClass = "station-pin-train";
            let pinIcon = "🚆";
            if (isCritical) {
                markerClass = "station-pin-critical";
                pinIcon = "⚠️";
            } else if (primaryMode === "Metro") {
                markerClass = "station-pin-metro";
                pinIcon = "🚇";
            } else if (primaryMode === "Monorail") {
                markerClass = "station-pin-monorail";
                pinIcon = "🚝";
            } else if (primaryMode === "Bus") {
                markerClass = "station-pin-bus";
                pinIcon = "🚌";
            }

            const customIcon = L.divIcon({
                className: "custom-div-icon",
                html: `<div class="custom-station-pin ${markerClass}">${pinIcon}</div>`,
                iconSize: [26, 26],
                iconAnchor: [13, 13]
            });

            const marker = L.marker([st.lat, st.lng], { icon: customIcon });

            const topCategory = Object.entries(st.top_categories || {}).sort((a,b) => b[1] - a[1])[0];
            const topCategoryStr = topCategory ? `${topCategory[0]} (${topCategory[1]})` : 'None';

            const popupContent = `
                <div class="p-2 min-w-[250px]">
                    <div class="flex items-center justify-between border-b border-slate-700 pb-2 mb-2">
                        <span class="font-bold text-sm text-white">${st.name}</span>
                        <span class="text-[11px] px-2 py-0.5 rounded ${
                            st.status === 'Critical' ? 'bg-red-900 text-red-300 font-bold' :
                            st.status === 'Bottleneck' ? 'bg-amber-900 text-amber-300' :
                            'bg-emerald-900 text-emerald-300'
                        }">${st.status}</span>
                    </div>
                    <div class="grid grid-cols-2 gap-2 text-xs mb-2">
                        <div class="bg-slate-800 p-1.5 rounded">
                            <span class="text-slate-400">CSAT Score:</span>
                            <div class="font-bold ${st.csat < 60 ? 'text-rose-400' : 'text-emerald-400'}">${st.csat}%</div>
                        </div>
                        <div class="bg-slate-800 p-1.5 rounded">
                            <span class="text-slate-400">Total Reports:</span>
                            <div class="font-bold text-blue-400">${st.total_feedback}</div>
                        </div>
                    </div>
                    <div class="text-xs text-slate-300 space-y-1">
                        <div><span class="text-slate-400">Region Zone:</span> <span class="text-indigo-300">${st.zone || 'Mumbai'}</span></div>
                        <div><span class="text-slate-400">Transit Modes:</span> ${st.modes.join(', ')}</div>
                        <div><span class="text-slate-400">Top Issue:</span> <span class="text-amber-300">${topCategoryStr}</span></div>
                        <div class="flex gap-2 text-[11px] mt-1 pt-1 border-t border-slate-800">
                            <span class="text-emerald-400">👍 ${st.positive}</span>
                            <span class="text-slate-400">😐 ${st.neutral}</span>
                            <span class="text-rose-400">👎 ${st.negative}</span>
                        </div>
                    </div>
                </div>
            `;

            marker.bindPopup(popupContent);
            stationsLayerGroup.addLayer(marker);
        });

        // 3. Render Leaflet Heatmap Layer
        if (heatLayer) {
            map.removeLayer(heatLayer);
        }

        if (window.L && window.L.heatLayer && heatPoints.length > 0) {
            heatLayer = L.heatLayer(heatPoints, {
                radius: 30,
                blur: 20,
                maxZoom: 14,
                gradient: { 0.2: '#3B82F6', 0.5: '#F59E0B', 0.8: '#EF4444', 1.0: '#991B1B' }
            });
            if (showHeatmapToggle) {
                heatLayer.addTo(map);
            }
        }

        renderRouteHealthCards(routes);

    } catch (err) {
        console.error("Error rendering GIS layers:", err);
    }
}

function renderRouteHealthCards(routes) {
    const container = document.getElementById("gis-routes-cards");
    if (!container) return;

    container.innerHTML = routes.map(r => {
        const healthBadge =
            r.health_status === "Severe" ? "bg-rose-950 text-rose-400 border-rose-800" :
            r.health_status === "Degraded" ? "bg-amber-950 text-amber-400 border-amber-800" :
            r.health_status === "Moderate" ? "bg-blue-950 text-blue-400 border-blue-800" :
            "bg-emerald-950 text-emerald-400 border-emerald-800";

        return `
            <div class="p-3 bg-slate-900/80 border border-slate-800 rounded-lg hover:border-slate-700 transition">
                <div class="flex items-center justify-between mb-1.5">
                    <div class="flex items-center gap-2">
                        <span class="w-3 h-3 rounded-full" style="background-color: ${r.color}"></span>
                        <span class="font-semibold text-xs text-white">${r.name}</span>
                    </div>
                    <span class="px-2 py-0.5 rounded text-[11px] border ${healthBadge}">${r.health_status}</span>
                </div>
                <div class="grid grid-cols-3 gap-1.5 text-center text-xs mt-2">
                    <div class="bg-slate-800/60 p-1 rounded">
                        <div class="text-[10px] text-slate-400">CSAT</div>
                        <div class="font-bold ${r.csat < 65 ? 'text-rose-400' : 'text-emerald-400'}">${r.csat}%</div>
                    </div>
                    <div class="bg-slate-800/60 p-1 rounded">
                        <div class="text-[10px] text-slate-400">Punctuality</div>
                        <div class="font-bold text-blue-400">${r.on_time_performance_est}%</div>
                    </div>
                    <div class="bg-slate-800/60 p-1 rounded">
                        <div class="text-[10px] text-slate-400">Crush Index</div>
                        <div class="font-bold ${r.overcrowding_index > 50 ? 'text-amber-400' : 'text-slate-300'}">${r.overcrowding_index}%</div>
                    </div>
                </div>
            </div>
        `;
    }).join("");
}

window.renderMapLayers = renderMapLayers;
