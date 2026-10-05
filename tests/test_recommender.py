import pytest
from app.recommender.root_cause import root_cause_diagnoser
from app.recommender.action_engine import recommendation_engine

def test_root_cause_diagnosis():
    mock_complaints = [
        {
            "category": "Punctuality & Delays",
            "station_name": "Kurla Junction Interchange",
            "line_name": "Central Main Line Local (CSMT - Kalyan)",
            "mode": "Train",
            "sentiment": "Negative",
            "primary_emotion": "Anger",
            "entities": {"aspects": ["Signal"]}
        },
        {
            "category": "Punctuality & Delays",
            "station_name": "Kurla Junction Interchange",
            "line_name": "Central Main Line Local (CSMT - Kalyan)",
            "mode": "Train",
            "sentiment": "Negative",
            "primary_emotion": "Frustration",
            "entities": {"aspects": []}
        }
    ]

    diagnoses = root_cause_diagnoser.diagnose(mock_complaints)
    assert len(diagnoses) >= 1
    d = diagnoses[0]
    assert d["category"] == "Punctuality & Delays"
    assert "Railway" in d["department"]

def test_action_recommendation_generation_and_workflow():
    mock_items = [
        {
            "category": "Safety, Security & Lighting",
            "station_name": "Dadar Junction (Western & Central)",
            "line_name": "Western Line Local (Churchgate - Virar)",
            "mode": "Train",
            "sentiment": "Negative",
            "primary_emotion": "Anxiety",
            "entities": {"aspects": ["FOB", "Foot Over Bridge"]}
        },
        {
            "category": "Safety, Security & Lighting",
            "station_name": "Dadar Junction (Western & Central)",
            "line_name": "Western Line Local (Churchgate - Virar)",
            "mode": "Train",
            "sentiment": "Negative",
            "primary_emotion": "Anxiety",
            "entities": {"aspects": ["RPF"]}
        }
    ]

    recs = recommendation_engine.generate_recommendations(mock_items)
    assert len(recs) >= 1
    rec = recs[0]
    assert rec["priority"] in ["Critical", "High"]
    assert rec["status"] == "Open"

    rec_id = rec["id"]
    updated = recommendation_engine.update_recommendation_status(rec_id, "Approved", "CR/WR joint sign-off")
    assert updated["status"] == "Approved"

    dispatched = recommendation_engine.update_recommendation_status(rec_id, "Dispatched")
    assert dispatched["status"] == "Dispatched"

def test_custom_action_creation_and_editing():
    # Test creating custom action
    custom_data = {
        "title": "Install Extra Fans & Water Coolers on Platform 4 at Thane",
        "category": "HVAC & Vehicle Comfort",
        "target_name": "Thane Junction",
        "priority": "High",
        "root_cause_summary": "Commuters reported excessive heat on non-AC suburban platforms.",
        "recommended_action": "Procure 12 heavy-duty mist fans and 2 chilled drinking water kiosks.",
        "operational_department": "Central Railway Facilities & Station Sanitation",
        "estimated_impact": "Significantly improves passenger waiting comfort during peak afternoons.",
        "supervisor_notes": "Fast-track under station amenity modernization funds."
    }

    created = recommendation_engine.create_custom_recommendation(custom_data)
    assert created["id"].startswith("REC-MUM-USR-")
    assert created["is_custom"] is True
    assert created["supervisor_notes"] is not None

    # Test editing existing recommendation
    rec_id = created["id"]
    modified = recommendation_engine.update_recommendation(rec_id, {
        "priority": "Critical",
        "recommended_action": "Deploy 16 heavy-duty mist fans immediately.",
        "supervisor_notes": "Approved by Divisional Railway Manager."
    })
    assert modified["priority"] == "Critical"
    assert "16 heavy-duty" in modified["recommended_action"]
    assert "Divisional Railway Manager" in modified["supervisor_notes"]
