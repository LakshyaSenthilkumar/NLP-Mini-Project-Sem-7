import os
import json
import uuid
from typing import List, Dict, Any, Optional
from datetime import datetime

from app.nlp.classifier import category_classifier
from app.nlp.sentiment import sentiment_engine
from app.nlp.ner_extractor import ner_extractor
from app.models.schemas import FeedbackSubmission, FeedbackItem, ExtractedEntities

class IngestionPipeline:
    def __init__(self, data_path: Optional[str] = None):
        if not data_path:
            base_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
            data_path = os.path.join(base_dir, "data", "seed_feedback.json")
        self.data_path = data_path
        self.feedback_store: List[Dict[str, Any]] = []
        self.load_seed_data()

    def load_seed_data(self):
        if os.path.exists(self.data_path):
            try:
                with open(self.data_path, "r", encoding="utf-8") as f:
                    self.feedback_store = json.load(f)
            except Exception as e:
                print(f"Error loading seed feedback: {e}")
                self.feedback_store = []

    def save_data(self):
        try:
            os.makedirs(os.path.dirname(self.data_path), exist_ok=True)
            with open(self.data_path, "w", encoding="utf-8") as f:
                json.dump(self.feedback_store, f, indent=2)
        except Exception as e:
            print(f"Error saving feedback: {e}")

    def process_feedback(self, submission: FeedbackSubmission) -> Dict[str, Any]:
        """
        Runs full NLP & Geospatial enrichment pipeline on an incoming passenger feedback submission.
        """
        text = submission.text

        # 1. Classify Category
        category, confidence = category_classifier.classify(text)

        # 2. Sentiment & Emotion
        sentiment, polarity, primary_emotion, emotion_scores = sentiment_engine.analyze(text)

        # 3. Named Entity Recognition
        entities_raw = ner_extractor.extract(text)
        entities = ExtractedEntities(**entities_raw)

        # 4. Location Resolution (Line & Station)
        ln_id, ln_name, st_id, st_name = ner_extractor.resolve_location(
            entities_raw.get("stations", []),
            entities_raw.get("lines", [])
        )

        # User-provided overrides if available
        if submission.line_id:
            ln_id = submission.line_id
        if submission.station_id:
            st_id = submission.station_id

        # Determine mode
        mode = submission.mode
        if not mode:
            if ln_id and "BUS" in str(ln_id).upper():
                mode = "Bus"
            elif ln_id and "TRAM" in str(ln_id).upper():
                mode = "Tram"
            elif ln_id and "METRO" in str(ln_id).upper():
                mode = "Metro"
            elif any("Bus" in l for l in entities.lines) or any("route" in text.lower() for _ in [1]):
                mode = "Bus"
            elif any("Tram" in l for l in entities.lines):
                mode = "Tram"
            else:
                mode = "Metro"

        # 5. Severity Assessment
        if category == "Safety, Security & Lighting" or primary_emotion in ["Anger"] and polarity < -0.6:
            severity = "Critical"
        elif polarity < -0.3 or primary_emotion in ["Frustration", "Anxiety"]:
            severity = "High"
        elif sentiment == "Negative":
            severity = "Medium"
        else:
            severity = "Low"

        # 6. Assigned Department
        dept_map = {
            "Punctuality & Delays": "Operations Control Center (OCC)",
            "Overcrowding & Capacity": "Service Planning & Scheduling",
            "Cleanliness & Hygiene": "Station Facilities & Sanitation",
            "Driver & Staff Behavior": "HR & Operator Management",
            "Ticketing, Smart Cards & Fares": "Automated Fare Collection Tech",
            "Safety, Security & Lighting": "Transit Police & Security",
            "Accessibility & Special Needs": "ADA Compliance & Maintenance",
            "Route Frequency & Network Coverage": "Network Planning",
            "HVAC & Vehicle Comfort": "Rolling Stock Fleet Engineering"
        }
        assigned_dept = dept_map.get(category, "Customer Relations")

        # Create Item Record
        item_id = f"FB-{uuid.uuid4().hex[:8].upper()}"
        ts = submission.timestamp.strftime("%Y-%m-%d %H:%M:%S") if submission.timestamp else datetime.now().strftime("%Y-%m-%d %H:%M:%S")

        item_dict = {
            "id": item_id,
            "text": text,
            "source": submission.source,
            "mode": mode,
            "line_id": ln_id,
            "line_name": ln_name,
            "station_id": st_id,
            "station_name": st_name,
            "category": category,
            "category_confidence": confidence,
            "sentiment": sentiment,
            "polarity_score": polarity,
            "primary_emotion": primary_emotion,
            "emotion_scores": emotion_scores,
            "entities": entities.model_dump(),
            "rating": submission.rating,
            "severity": severity,
            "timestamp": ts,
            "status": "Open",
            "assigned_department": assigned_dept,
            "resolution_notes": None
        }

        # Insert at front of dataset
        self.feedback_store.insert(0, item_dict)
        self.save_data()
        return item_dict

    def get_all(self, filters: Optional[Dict[str, Any]] = None) -> List[Dict[str, Any]]:
        """
        Retrieves feedback items with optional filtering (by mode, category, sentiment, source, severity).
        """
        items = self.feedback_store
        if not filters:
            return items

        res = []
        for it in items:
            if filters.get("mode") and filters["mode"] != "All" and it.get("mode") != filters["mode"]:
                continue
            if filters.get("category") and filters["category"] != "All" and it.get("category") != filters["category"]:
                continue
            if filters.get("sentiment") and filters["sentiment"] != "All" and it.get("sentiment") != filters["sentiment"]:
                continue
            if filters.get("source") and filters["source"] != "All" and it.get("source") != filters["source"]:
                continue
            if filters.get("severity") and filters["severity"] != "All" and it.get("severity") != filters["severity"]:
                continue
            if filters.get("search"):
                term = filters["search"].lower()
                if term not in it.get("text", "").lower() and term not in str(it.get("station_name", "")).lower() and term not in str(it.get("line_name", "")).lower():
                    continue
            res.append(it)
        return res

    def update_item_status(self, item_id: str, status: str, notes: Optional[str] = None, department: Optional[str] = None) -> Optional[Dict[str, Any]]:
        for it in self.feedback_store:
            if it["id"] == item_id:
                it["status"] = status
                if notes:
                    it["resolution_notes"] = notes
                if department:
                    it["assigned_department"] = department
                self.save_data()
                return it
        return None

# Global singleton
ingestion_pipeline = IngestionPipeline()
