import pytest
from app.gis.network_data import gis_network
from app.gis.spatial_analytics import spatial_analytics

def test_gis_network_structure():
    stations = gis_network.get_all_stations()
    lines = gis_network.get_all_lines()
    assert len(stations) >= 20
    assert len(lines) >= 6

    # Verify modes include Bus, Train, Metro, Monorail
    all_modes = set()
    for ln in lines:
        all_modes.add(ln["mode"])
    assert "Train" in all_modes
    assert "Metro" in all_modes
    assert "Monorail" in all_modes
    assert "Bus" in all_modes

    geojson = gis_network.get_geojson()
    assert geojson["type"] == "FeatureCollection"
    assert len(geojson["features"]) >= 25

def test_spatial_analytics_station_and_route_metrics():
    mock_items = [
        {
            "station_id": "MUM-03",
            "station_name": "Dadar Junction (Western & Central)",
            "line_id": "LOCAL-WESTERN",
            "line_name": "Western Line Local (Churchgate - Virar)",
            "sentiment": "Negative",
            "category": "Overcrowding & Capacity",
            "primary_emotion": "Frustration"
        },
        {
            "station_id": "MUM-03",
            "station_name": "Dadar Junction (Western & Central)",
            "line_id": "LOCAL-WESTERN",
            "line_name": "Western Line Local (Churchgate - Virar)",
            "sentiment": "Negative",
            "category": "Punctuality & Delays",
            "primary_emotion": "Anger"
        },
        {
            "station_id": "MUM-01",
            "station_name": "Churchgate Station",
            "line_id": "LOCAL-WESTERN",
            "line_name": "Western Line Local (Churchgate - Virar)",
            "sentiment": "Positive",
            "category": "Cleanliness & Hygiene",
            "primary_emotion": "Satisfaction"
        }
    ]

    st_metrics = spatial_analytics.calculate_station_metrics(mock_items)
    assert len(st_metrics) >= 20
    dadar = next((s for s in st_metrics if "Dadar" in s["name"]), None)
    assert dadar is not None
    assert dadar["total_feedback"] == 2
    assert dadar["negative"] == 2
    assert dadar["issue_score"] > 0

    route_metrics = spatial_analytics.calculate_route_metrics(mock_items)
    assert len(route_metrics) >= 6
    western = next((r for r in route_metrics if "Western Line" in r["name"]), None)
    assert western is not None
    assert western["total_feedback"] == 3

    heat_pts = spatial_analytics.get_heat_points(mock_items)
    assert len(heat_pts) >= 2
