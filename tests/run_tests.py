import os
import sys

# Ensure UTF-8 output encoding on Windows console
if sys.platform == "win32":
    sys.stdout.reconfigure(encoding="utf-8")

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if BASE_DIR not in sys.path:
    sys.path.insert(0, BASE_DIR)

from tests.test_nlp import (
    test_service_category_classification,
    test_sentiment_and_emotion_analysis,
    test_ner_and_location_resolution,
    test_satisfaction_forecaster
)
from tests.test_gis import (
    test_gis_network_structure,
    test_spatial_analytics_station_and_route_metrics
)
from tests.test_recommender import (
    test_root_cause_diagnosis,
    test_action_recommendation_generation_and_workflow
)
from tests.test_api import test_api

def run_all_tests():
    print("=" * 70)
    print("RUNNING FULL TEST SUITE FOR TRANSIT FEEDBACK INTELLIGENCE SYSTEM")
    print("=" * 70)

    tests = [
        ("NLP: Service Category 9-Class Classifier", test_service_category_classification),
        ("NLP: Sentiment Polarity & Emotion Analysis", test_sentiment_and_emotion_analysis),
        ("NLP: Transit Named Entity Recognition (NER)", test_ner_and_location_resolution),
        ("NLP: CSAT Satisfaction Trend Forecaster", test_satisfaction_forecaster),
        ("GIS: Network Topology & GeoJSON Features", test_gis_network_structure),
        ("GIS: Spatial Analytics, Station Hotspots & Routes", test_spatial_analytics_station_and_route_metrics),
        ("Decision Support: Root Cause Diagnoser", test_root_cause_diagnosis),
        ("Decision Support: Action Recommendations Workflow", test_action_recommendation_generation_and_workflow),
        ("REST API: Full Async Endpoints & Simulation", test_api),
    ]

    passed = 0
    failed = 0

    for name, test_func in tests:
        try:
            test_func()
            print(f"[PASS] {name}")
            passed += 1
        except Exception as e:
            print(f"[FAIL] {name} -> {e}")
            failed += 1

    print("=" * 70)
    print(f"RESULTS: {passed} PASSED | {failed} FAILED | TOTAL: {len(tests)}")
    print("=" * 70)

    if failed > 0:
        sys.exit(1)
    else:
        print("ALL TESTS PASSED SUCCESSFULLY!")

if __name__ == "__main__":
    run_all_tests()
