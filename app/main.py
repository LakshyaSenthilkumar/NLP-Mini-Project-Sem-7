from fastapi import FastAPI, Request, HTTPException, Query
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse, JSONResponse
from typing import Optional, List, Dict, Any
from datetime import datetime

from app.config import APP_TITLE, APP_VERSION, STATIC_DIR, TEMPLATES_DIR
from app.models.schemas import (
    FeedbackSubmission, FeedbackItem, LiveAnalysisRequest,
    StatusUpdateRequest, ActionRecommendation, AnalyticsSummary,
    CreateCustomRecommendationRequest, UpdateRecommendationDetailsRequest
)
from app.nlp.classifier import category_classifier
from app.nlp.sentiment import sentiment_engine
from app.nlp.ner_extractor import ner_extractor
from app.nlp.topic_clusterer import topic_clusterer
from app.nlp.forecaster import satisfaction_forecaster
from app.gis.network_data import gis_network
from app.gis.spatial_analytics import spatial_analytics
from app.recommender.action_engine import recommendation_engine
from app.recommender.root_cause import root_cause_diagnoser
from app.ingestion.pipeline import ingestion_pipeline
from app.ingestion.mock_generator import synthetic_generator

app = FastAPI(title=APP_TITLE, version=APP_VERSION)

# Enable CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Mount Static Files & Templates
app.mount("/static", StaticFiles(directory=STATIC_DIR), name="static")
templates = Jinja2Templates(directory=TEMPLATES_DIR)

# ----------------- Web UI Route -----------------
@app.get("/", response_class=HTMLResponse)
async def serve_dashboard(request: Request):
    return templates.TemplateResponse(
        request=request,
        name="index.html",
        context={
            "app_title": "TransitPulse AI - Mumbai Metropolitan Transport Feedback Intelligence",
            "app_version": APP_VERSION
        }
    )

# ----------------- Feedback Ingestion & Retrieval API -----------------
@app.post("/api/feedback", response_model=Dict[str, Any])
async def submit_feedback(submission: FeedbackSubmission):
    """
    Ingests passenger feedback, runs full NLP (Category, Sentiment, NER, Severity) and persists record.
    """
    result = ingestion_pipeline.process_feedback(submission)
    recommendation_engine.generate_recommendations(ingestion_pipeline.feedback_store)
    return result

@app.get("/api/feedback", response_model=List[Dict[str, Any]])
async def get_feedback_list(
    mode: Optional[str] = Query(None),
    category: Optional[str] = Query(None),
    sentiment: Optional[str] = Query(None),
    source: Optional[str] = Query(None),
    severity: Optional[str] = Query(None),
    search: Optional[str] = Query(None),
    limit: Optional[int] = Query(150)
):
    """
    Retrieves filtered list of passenger feedback items.
    """
    filters = {
        "mode": mode,
        "category": category,
        "sentiment": sentiment,
        "source": source,
        "severity": severity,
        "search": search
    }
    items = ingestion_pipeline.get_all(filters)
    return items[:limit]

@app.get("/api/feedback/{feedback_id}")
async def get_feedback_item(feedback_id: str):
    items = [it for it in ingestion_pipeline.feedback_store if it["id"] == feedback_id]
    if not items:
        raise HTTPException(status_code=404, detail="Feedback item not found")
    return items[0]

@app.patch("/api/feedback/{feedback_id}/status")
async def update_feedback_status(feedback_id: str, req: StatusUpdateRequest):
    updated = ingestion_pipeline.update_item_status(feedback_id, req.status, req.notes, req.department)
    if not updated:
        raise HTTPException(status_code=404, detail="Feedback item not found")
    return updated

# ----------------- Live NLP Lab -----------------
@app.post("/api/nlp/analyze")
async def live_nlp_analysis(req: LiveAnalysisRequest):
    """
    Real-time interactive NLP analysis of arbitrary passenger statement in Mumbai transit context.
    """
    text = req.text
    category, confidence = category_classifier.classify(text)
    all_category_scores = category_classifier.get_all_category_scores(text)
    sentiment, polarity, primary_emotion, emotion_scores = sentiment_engine.analyze(text)
    entities = ner_extractor.extract(text)
    ln_id, ln_name, st_id, st_name = ner_extractor.resolve_location(
        entities.get("stations", []),
        entities.get("lines", [])
    )

    return {
        "text": text,
        "category": category,
        "category_confidence": confidence,
        "category_scores": all_category_scores,
        "sentiment": sentiment,
        "polarity_score": polarity,
        "primary_emotion": primary_emotion,
        "emotion_scores": emotion_scores,
        "entities": entities,
        "resolved_location": {
            "line_id": ln_id,
            "line_name": ln_name,
            "station_id": st_id,
            "station_name": st_name
        }
    }

# ----------------- GIS & Geospatial API -----------------
@app.get("/api/gis/network")
async def get_gis_network():
    return gis_network.get_geojson()

@app.get("/api/gis/stations")
async def get_gis_stations():
    items = ingestion_pipeline.feedback_store
    return spatial_analytics.calculate_station_metrics(items)

@app.get("/api/gis/routes")
async def get_gis_routes():
    items = ingestion_pipeline.feedback_store
    return spatial_analytics.calculate_route_metrics(items)

@app.get("/api/gis/heatmap")
async def get_gis_heatmap():
    items = ingestion_pipeline.feedback_store
    return spatial_analytics.get_heat_points(items)

# ----------------- Decision Support & Recommendations API -----------------
@app.get("/api/recommendations")
async def get_recommendations():
    items = ingestion_pipeline.feedback_store
    recs = recommendation_engine.generate_recommendations(items)
    return recs

@app.post("/api/recommendations", status_code=201)
async def create_custom_recommendation(req: CreateCustomRecommendationRequest):
    """
    Allows authorities / operators to submit a new custom operational directive or suggestion.
    """
    new_rec = recommendation_engine.create_custom_recommendation(req.model_dump())
    return new_rec

@app.put("/api/recommendations/{rec_id}")
async def update_recommendation_details(rec_id: str, req: UpdateRecommendationDetailsRequest):
    """
    Updates the text, suggestions, priority, department, or notes of an existing recommendation.
    """
    updated = recommendation_engine.update_recommendation(rec_id, req.model_dump(exclude_unset=True))
    if not updated:
        raise HTTPException(status_code=404, detail="Recommendation not found")
    return updated

@app.patch("/api/recommendations/{rec_id}/status")
async def update_rec_status(rec_id: str, req: StatusUpdateRequest):
    updated = recommendation_engine.update_recommendation_status(rec_id, req.status, req.notes)
    if not updated:
        raise HTTPException(status_code=404, detail="Recommendation not found")
    return updated

@app.get("/api/bottlenecks")
async def get_bottlenecks():
    items = ingestion_pipeline.feedback_store
    clusters = topic_clusterer.cluster_issues(items)
    key_phrases = topic_clusterer.extract_key_phrases([it["text"] for it in items if it.get("sentiment") == "Negative"], top_n=10)
    root_causes = root_cause_diagnoser.diagnose(items)
    return {
        "clusters": clusters,
        "key_phrases": key_phrases,
        "root_causes": root_causes
    }

# ----------------- Analytics & Trends API -----------------
@app.get("/api/analytics/summary")
async def get_analytics_summary():
    items = ingestion_pipeline.feedback_store
    total = len(items)
    if total == 0:
        return {
            "total_feedback": 0,
            "csat_score": 0.0,
            "net_sentiment_score": 0.0,
            "open_tickets_count": 0,
            "critical_alerts_count": 0,
            "sentiment_distribution": {"Positive": 0, "Neutral": 0, "Negative": 0},
            "emotion_distribution": {},
            "category_distribution": {},
            "channel_breakdown": {}
        }

    sentiments = {"Positive": 0, "Neutral": 0, "Negative": 0}
    emotions: Dict[str, int] = {}
    categories: Dict[str, int] = {}
    channels: Dict[str, int] = {}
    open_tickets = 0
    critical_alerts = 0

    for it in items:
        sent = it.get("sentiment", "Neutral")
        sentiments[sent] = sentiments.get(sent, 0) + 1

        emo = it.get("primary_emotion", "Neutral")
        emotions[emo] = emotions.get(emo, 0) + 1

        cat = it.get("category", "General")
        categories[cat] = categories.get(cat, 0) + 1

        ch = it.get("source", "Web Portal")
        channels[ch] = channels.get(ch, 0) + 1

        if it.get("status") in ["Open", "In Review"]:
            open_tickets += 1
        if it.get("severity") == "Critical":
            critical_alerts += 1

    csat = round(((sentiments["Positive"] + 0.5 * sentiments["Neutral"]) / total) * 100, 1)
    nss = round(((sentiments["Positive"] - sentiments["Negative"]) / total) * 100, 1)

    return {
        "total_feedback": total,
        "csat_score": csat,
        "net_sentiment_score": nss,
        "open_tickets_count": open_tickets,
        "critical_alerts_count": critical_alerts,
        "sentiment_distribution": sentiments,
        "emotion_distribution": emotions,
        "category_distribution": categories,
        "channel_breakdown": channels
    }

@app.get("/api/analytics/trends")
async def get_analytics_trends():
    items = ingestion_pipeline.feedback_store
    return satisfaction_forecaster.compute_trends_and_forecast(items)

# ----------------- Mumbai Scenario Simulator API -----------------
@app.post("/api/simulation/inject")
async def inject_scenario(scenario_type: str = Query(..., description="rush_hour | monsoon_delay | faregate_glitch | positive_wave")):
    """
    Simulates real-time Mumbai transit disruptions or service praise.
    """
    now = datetime.now()
    injected_count = 0

    if scenario_type == "rush_hour":
        # Dadar & Andheri rush hour crush
        templates = [
            ("Extreme crowd crush on Dadar Junction platform 3! Commuters cannot alight and pushing on footboard.", "Overcrowding & Capacity", "Social Media", "Train"),
            ("Metro Line 1 at Ghatkopar Station Interchange is overflowing with 4-metro wait times during peak rush.", "Overcrowding & Capacity", "Mobile App", "Metro"),
            ("BEST Bus Route 302 packed to maximum capacity at BKC Diamond Bourse. Bypassed the bus stop!", "Overcrowding & Capacity", "Web Portal", "Bus"),
            ("Mumbai Monorail headway gap reached 45 minutes at Wadala Bridge Monorail. Platform overflowing.", "Route Frequency & Network Coverage", "Social Media", "Monorail")
        ]
    elif scenario_type == "monsoon_delay":
        # Monsoon waterlogging & signal cascade
        templates = [
            ("Heavy waterlogging and track circuit failure at Kurla Junction Interchange. Central line locals delayed by 45 minutes!", "Punctuality & Delays", "Social Media", "Train"),
            ("Harbour Line local stranded between Wadala and Chembur Station due to signal trip.", "Punctuality & Delays", "Mobile App", "Train"),
            ("NMMT AC Bus 105 stuck in 2-hour jam on Vashi Highway Creek Bridge in heavy downpour.", "Punctuality & Delays", "Web Portal", "Bus"),
            ("Monorail coach window leaking water near Jacob Circle Sant Gadge Maharaj Chowk.", "HVAC & Vehicle Comfort", "Email", "Monorail")
        ]
    elif scenario_type == "faregate_glitch":
        # UTS app & Chalo card server timeout
        templates = [
            ("UTS mobile app ticketing GPS location failing across CSMT and Churchgate Station booking zones!", "Ticketing, Smart Cards & Fares", "Mobile App", "Train"),
            ("Metro QR scanner gates not reading WhatsApp tickets at Andheri Station Interchange. Massive queue.", "Ticketing, Smart Cards & Fares", "Social Media", "Metro"),
            ("BEST Bus Chalo card electronic machines showing network error on Route A-115 at Nariman Point.", "Ticketing, Smart Cards & Fares", "Web Portal", "Bus"),
            ("Monorail token vending kiosk out of order at Chembur Station Interchange.", "Ticketing, Smart Cards & Fares", "Mobile App", "Monorail")
        ]
    elif scenario_type == "positive_wave":
        # AC local & new Metro Line 3 praise
        templates = [
            ("The new underground Metro Line 3 Aqua Line from Aarey JVLR to BKC is ultra-clean, peaceful, and lightning fast!", "Punctuality & Delays", "Social Media", "Metro"),
            ("Western Line AC local on Churchgate to Borivali arrived sharp on time. Great air conditioning relief in humid weather!", "HVAC & Vehicle Comfort", "Mobile App", "Train"),
            ("Driver on BEST Electric Bus 302 helped a disabled passenger board smoothly with wheelchair ramp at Bandra Station.", "Driver & Staff Behavior", "Web Portal", "Bus"),
            ("Spotless platforms and quick automated token counters at Versova Metro Station today!", "Cleanliness & Hygiene", "Social Media", "Metro")
        ]
    else:
        raise HTTPException(status_code=400, detail="Unknown scenario type")

    for text, exp_cat, src, mode in templates:
        sub = FeedbackSubmission(
            text=text,
            source=src,
            mode=mode,
            timestamp=now
        )
        ingestion_pipeline.process_feedback(sub)
        injected_count += 1

    recommendation_engine.generate_recommendations(ingestion_pipeline.feedback_store)

    return {
        "status": "success",
        "scenario": scenario_type,
        "injected_feedback_count": injected_count,
        "total_feedback_now": len(ingestion_pipeline.feedback_store)
    }

@app.post("/api/simulation/reset")
async def reset_simulation():
    fresh_ds = synthetic_generator.generate_seed_dataset(150)
    ingestion_pipeline.feedback_store = fresh_ds
    ingestion_pipeline.save_data()
    recommendation_engine.recommendations.clear()
    recommendation_engine.generate_recommendations(fresh_ds)
    return {"status": "reset_completed", "count": len(fresh_ds)}
