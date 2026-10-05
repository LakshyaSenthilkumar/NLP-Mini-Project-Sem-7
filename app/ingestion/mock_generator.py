import random
import uuid
from datetime import datetime, timedelta
from typing import List, Dict, Any

from app.nlp.classifier import category_classifier
from app.nlp.sentiment import sentiment_engine
from app.nlp.ner_extractor import ner_extractor

MUMBAI_FEEDBACK_TEMPLATES = [
    # Train (Western, Central, Harbour local trains)
    ("The fast local on {line} was delayed by 35 minutes at {station} due to signal failure near Kurla. Overcrowded platforms!", "Punctuality & Delays", -0.85, "Anger", "Mobile App", 1, "Train"),
    ("Dangerous crowd crush on platform 1 at {station} during morning peak hours. People hanging out of the local train footboard!", "Overcrowding & Capacity", -0.90, "Anxiety", "Social Media", 1, "Train"),
    ("The new AC local train on {line} arriving at {station} was very cool, punctual, and comfortable commute.", "Punctuality & Delays", 0.90, "Satisfaction", "Mobile App", 5, "Train"),
    ("UTS mobile app GPS geolocation not working near {station} booking counter. Could not book local ticket on time.", "Ticketing, Smart Cards & Fares", -0.75, "Frustration", "Web Portal", 2, "Train"),
    ("FOB (Foot Over Bridge) at {station} is extremely narrow and packed. Serious stampede risk during evening rush hour.", "Safety, Security & Lighting", -0.95, "Anxiety", "Social Media", 1, "Train"),
    ("Cleanliness at {station} concourse and platforms has visibly improved. Dustbins emptied regularly.", "Cleanliness & Hygiene", 0.85, "Satisfaction", "Social Media", 5, "Train"),
    ("Ladies special train on {line} reached {station} right on schedule. Much safer and convenient commute for women.", "Safety, Security & Lighting", 0.95, "Satisfaction", "Mobile App", 5, "Train"),
    ("Wheelchair ramp and elevator at {station} platform 4 is locked and out of order. Disabled passengers struggling.", "Accessibility & Special Needs", -0.95, "Anger", "Web Portal", 1, "Train"),

    # Metro (Line 1 Versova-Ghatkopar, Line 2A, Line 7, Line 3 Aqua line)
    ("Metro Line 1 at {station} was completely packed like sardines. 3 metros passed without anyone able to board!", "Overcrowding & Capacity", -0.80, "Frustration", "Social Media", 1, "Metro"),
    ("Metro Line 3 Aqua Line from {station} to BKC is super fast, quiet, and spotless. World-class underground transit for Mumbai!", "Punctuality & Delays", 0.95, "Gratitude", "Mobile App", 5, "Metro"),
    ("Automatic AFC QR gate at {station} metro station failed to scan mobile ticket. Created huge queue behind me.", "Ticketing, Smart Cards & Fares", -0.80, "Frustration", "Mobile App", 2, "Metro"),
    ("Air conditioning in coach 2 of Metro arriving at {station} was not working properly. Very stuffy inside.", "HVAC & Vehicle Comfort", -0.70, "Frustration", "Web Portal", 2, "Metro"),
    ("Clear bilingual audio announcements and digital route displays inside metro at {station}. Very helpful!", "Accessibility & Special Needs", 0.90, "Satisfaction", "Mobile App", 5, "Metro"),

    # Monorail (Chembur - Wadala - Jacob Circle)
    ("Mumbai Monorail between {station} and Wadala arrived with a 45 minute headway gap. Frequency needs to be doubled!", "Route Frequency & Network Coverage", -0.85, "Frustration", "Social Media", 1, "Monorail"),
    ("Monorail coach AC failed while traveling near {station}. Glass windows don't open and suffocating heat!", "HVAC & Vehicle Comfort", -0.90, "Anger", "Email", 1, "Monorail"),
    ("Scenic and peaceful ride on Mumbai Monorail passing {station}. Great alternative to road traffic!", "Punctuality & Delays", 0.85, "Satisfaction", "Mobile App", 5, "Monorail"),
    ("Monorail station ticket counter at {station} was unstaffed and only accepting cash.", "Ticketing, Smart Cards & Fares", -0.70, "Frustration", "Web Portal", 2, "Monorail"),

    # Bus (BEST & NMMT buses in Mumbai & Navi Mumbai)
    ("BEST AC Bus on {bus_line} was stuck in traffic jam near {station} for 50 minutes. Need dedicated bus priority lanes.", "Punctuality & Delays", -0.75, "Frustration", "Web Portal", 2, "Bus"),
    ("Driver of BEST bus {bus_line} at {station} stopped with great care for a senior citizen and drove very smoothly.", "Driver & Staff Behavior", 0.95, "Gratitude", "Social Media", 5, "Bus"),
    ("NMMT AC Bus 105 from {station} to Panvel has great frequency and Chalo card tap-in tap-out is effortless.", "Ticketing, Smart Cards & Fares", 0.90, "Satisfaction", "Mobile App", 5, "Bus"),
    ("Conductor on bus {bus_line} near {station} refused to give change for 20 rupees and was very rude.", "Driver & Staff Behavior", -0.80, "Anger", "Mobile App", 1, "Bus"),
    ("Litter and empty gutkha packets found on the floor of bus {bus_line} at {station}. Deep cleaning needed.", "Cleanliness & Hygiene", -0.75, "Frustration", "Email", 2, "Bus")
]

MUMBAI_STATIONS = [
    "Churchgate Station", "Mumbai Central", "Dadar Junction (Western & Central)",
    "Bandra Terminus / Station", "Andheri Station Interchange", "Borivali Station",
    "CSMT (Chhatrapati Shivaji Maharaj Terminus)", "Kurla Junction Interchange",
    "Ghatkopar Station Interchange", "Thane Junction", "Kalyan Junction",
    "Wadala Bridge Monorail & Harbour", "Chembur Station Interchange",
    "Vashi Sector 17 / Station Hub", "Nerul LP / Station", "CBD Belapur Terminal",
    "Panvel Terminus", "Versova Metro Station", "D.N. Nagar Metro Interchange",
    "BKC (Bandra Kurla Complex) Hub", "Jacob Circle (Sant Gadge Maharaj Chowk)",
    "Lower Parel Monorail / Commercial Hub", "Aarey JVLR Metro 3"
]

MUMBAI_LINES = [
    ("Western Line Local (Churchgate - Virar)", "Train"),
    ("Central Main Line Local (CSMT - Kalyan)", "Train"),
    ("Harbour Line Local (CSMT - Panvel)", "Train"),
    ("Metro Line 1 (Versova - Ghatkopar Blue Line)", "Metro"),
    ("Metro Line 2A & 7 (Dahisar - Andheri West / Gundavali)", "Metro"),
    ("Metro Line 3 Aqua Line (Aarey JVLR - BKC - Cuffe Parade)", "Metro"),
    ("Mumbai Monorail (Chembur - Wadala - Jacob Circle)", "Monorail"),
    ("BEST Bus Route 302 (Kurla Stn - BKC - Bandra Stn)", "Bus"),
    ("BEST AC Bus A-115 (CSMT - Churchgate - Nariman Point)", "Bus"),
    ("NMMT AC Bus 105 (Vashi - Nerul - CBD Belapur - Panvel)", "Bus")
]

BUS_LINES = ["BEST Bus 302", "BEST AC Bus A-115", "NMMT AC Bus 105", "BEST Bus Route 415", "BEST Electric Bus 302"]

class SyntheticDataGenerator:
    def __init__(self):
        pass

    def generate_seed_dataset(self, count: int = 150) -> List[Dict[str, Any]]:
        """
        Generates realistic multi-channel feedback dataset for Mumbai Metropolitan Region across Train, Metro, Monorail, Bus.
        """
        dataset = []
        now = datetime.now()

        for i in range(count):
            template, exp_cat, base_pol, exp_emo, default_source, base_rating, template_mode = random.choice(MUMBAI_FEEDBACK_TEMPLATES)
            station = random.choice(MUMBAI_STATIONS)
            line_tuple = random.choice([l for l in MUMBAI_LINES if l[1] == template_mode] or MUMBAI_LINES)
            line_name, mode = line_tuple
            bus_line = random.choice(BUS_LINES)

            text = template.format(station=station, line=line_name, bus_line=bus_line)

            # Assign timestamp across recent 7 days with peak rush hour weighting (08:00-10:30 & 17:30-20:30)
            days_ago = random.randint(0, 6)
            if random.random() < 0.70:
                hour = random.choice([8, 9, 10, 17, 18, 19, 20])
            else:
                hour = random.randint(6, 23)
            minute = random.randint(0, 59)
            second = random.randint(0, 59)
            dt = now - timedelta(days=days_ago, hours=now.hour - hour, minutes=now.minute - minute, seconds=second)

            sources = ["Mobile App", "Social Media", "Email", "Web Portal"]
            source = random.choices(sources, weights=[0.45, 0.30, 0.10, 0.15])[0]

            # Category classification
            category, conf = category_classifier.classify(text)

            # Sentiment & Emotion
            sentiment, pol, emo, emo_scores = sentiment_engine.analyze(text)

            # Entities & location resolution
            entities_raw = ner_extractor.extract(text)
            ln_id, resolved_ln_name, st_id, resolved_st_name = ner_extractor.resolve_location(
                entities_raw.get("stations", []),
                entities_raw.get("lines", [])
            )

            # Severity
            if category == "Safety, Security & Lighting" or pol < -0.65:
                severity = "Critical"
            elif pol < -0.25:
                severity = "High"
            elif sentiment == "Negative":
                severity = "Medium"
            else:
                severity = "Low"

            # Rating
            rating = base_rating
            if sentiment == "Positive" and rating < 4:
                rating = 5
            elif sentiment == "Negative" and rating > 2:
                rating = 1

            status = random.choices(["Open", "In Review", "Dispatched", "Resolved"], weights=[0.40, 0.25, 0.15, 0.20])[0]

            # Department assignment based on Mumbai transport agencies
            if mode == "Train":
                dept = "Central & Western Railway Operations Desk"
            elif mode == "Metro":
                dept = "MMRDA / Maha Mumbai Metro OCC"
            elif mode == "Monorail":
                dept = "Mumbai Monorail Operations Division"
            else:
                dept = "BEST / NMMT City Bus Control"

            item_dict = {
                "id": f"MUM-{uuid.uuid4().hex[:7].upper()}",
                "text": text,
                "source": source,
                "mode": mode,
                "line_id": ln_id,
                "line_name": resolved_ln_name or line_name,
                "station_id": st_id,
                "station_name": resolved_st_name or station,
                "category": category,
                "category_confidence": conf,
                "sentiment": sentiment,
                "polarity_score": pol,
                "primary_emotion": emo,
                "emotion_scores": emo_scores,
                "entities": entities_raw,
                "rating": rating,
                "severity": severity,
                "timestamp": dt.strftime("%Y-%m-%d %H:%M:%S"),
                "status": status,
                "assigned_department": dept,
                "resolution_notes": "Acknowledged by Mumbai transit control desk." if status in ["Dispatched", "Resolved"] else None
            }
            dataset.append(item_dict)

        dataset.sort(key=lambda x: x["timestamp"], reverse=True)
        return dataset

# Global singleton
synthetic_generator = SyntheticDataGenerator()
