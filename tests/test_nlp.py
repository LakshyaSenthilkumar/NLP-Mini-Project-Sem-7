import pytest
from app.nlp.classifier import category_classifier
from app.nlp.sentiment import sentiment_engine
from app.nlp.ner_extractor import ner_extractor
from app.nlp.forecaster import satisfaction_forecaster

def test_service_category_classification():
    cat, conf = category_classifier.classify("The local train is 35 minutes late and delayed again near Kurla.")
    assert cat == "Punctuality & Delays"
    assert conf > 0.5

    cat, conf = category_classifier.classify("Dadar platform is dangerously overcrowded and packed like sardines, cannot board.")
    assert cat == "Overcrowding & Capacity"

    cat, conf = category_classifier.classify("Dirty floors, smelly trash and pan stains all over the bus.")
    assert cat == "Cleanliness & Hygiene"

    cat, conf = category_classifier.classify("Conductor was very rude, shouted at passengers and refused change.")
    assert cat == "Driver & Staff Behavior"

    cat, conf = category_classifier.classify("UTS mobile app smart card card reader overcharged my balance.")
    assert cat == "Ticketing, Smart Cards & Fares"

    cat, conf = category_classifier.classify("Dark scary FOB bridge at night, felt unsafe and saw a pickpocket.")
    assert cat == "Safety, Security & Lighting"

    cat, conf = category_classifier.classify("Wheelchair ramp and elevator broken for disabled passengers at station.")
    assert cat == "Accessibility & Special Needs"

    cat, conf = category_classifier.classify("AC in the local train coach is completely broken and boiling hot.")
    assert cat == "HVAC & Vehicle Comfort"

def test_sentiment_and_emotion_analysis():
    sentiment, pol, emo, emo_scores = sentiment_engine.analyze("Amazing clean Metro 3 train, on time and friendly staff! Thank you so much.")
    assert sentiment == "Positive"
    assert pol > 0.3
    assert emo in ["Satisfaction", "Gratitude"]

    sentiment, pol, emo, emo_scores = sentiment_engine.analyze("Furious and angry! Terrible delay at Kurla, worst local train service ever, total disaster.")
    assert sentiment == "Negative"
    assert pol < -0.3
    assert emo in ["Anger", "Frustration"]

def test_ner_and_location_resolution():
    text = "Delayed 25 mins on Western Line at Dadar Junction heading Churchgate-bound with broken escalator"
    entities = ner_extractor.extract(text)
    
    assert any("Dadar" in s for s in entities["stations"])
    assert any("Western Line" in l for l in entities["lines"])
    assert any("Churchgate" in d for d in entities["directions"])
    assert "Escalator" in entities["aspects"]

    ln_id, ln_name, st_id, st_name = ner_extractor.resolve_location(entities["stations"], entities["lines"])
    assert "Dadar" in st_name
    assert "Western Line" in ln_name

def test_satisfaction_forecaster():
    mock_items = [
        {"timestamp": "2026-10-01 08:00:00", "sentiment": "Positive", "polarity_score": 0.8},
        {"timestamp": "2026-10-01 09:00:00", "sentiment": "Positive", "polarity_score": 0.6},
        {"timestamp": "2026-10-01 10:00:00", "sentiment": "Negative", "polarity_score": -0.8},
        {"timestamp": "2026-10-02 08:00:00", "sentiment": "Positive", "polarity_score": 0.7},
    ]
    res = satisfaction_forecaster.compute_trends_and_forecast(mock_items)
    assert "historical_trend" in res
    assert "forecast_trend" in res
    assert len(res["forecast_trend"]) == 7
    assert 0.0 <= res["current_csat"] <= 100.0
