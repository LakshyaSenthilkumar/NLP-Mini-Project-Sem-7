import re
from typing import Tuple, Dict, List

# 9 Standard Transit Service Categories
CATEGORIES = [
    "Punctuality & Delays",
    "Overcrowding & Capacity",
    "Cleanliness & Hygiene",
    "Driver & Staff Behavior",
    "Ticketing, Smart Cards & Fares",
    "Safety, Security & Lighting",
    "Accessibility & Special Needs",
    "Route Frequency & Network Coverage",
    "HVAC & Vehicle Comfort"
]

CATEGORY_KEYWORDS: Dict[str, Dict[str, float]] = {
    "Punctuality & Delays": {
        "delay": 2.5, "delayed": 2.5, "late": 2.2, "on time": 2.0, "punctual": 2.0,
        "schedule": 1.5, "wait": 1.5, "waiting": 1.5, "stuck": 1.8, "breakdown": 2.0,
        "held": 1.5, "standing": 1.0, "minutes late": 2.5, "hours late": 2.8, "cancelled": 2.5,
        "cancellation": 2.5, "slow": 1.2, "behind time": 2.0, "headway": 1.8, "signal failure": 2.5
    },
    "Overcrowding & Capacity": {
        "crowded": 2.5, "overcrowded": 3.0, "packed": 2.5, "full": 1.8, "no seats": 2.2,
        "sardines": 2.8, "crushed": 2.5, "capacity": 2.0, "squeeze": 2.0, "standing room": 2.2,
        "cannot board": 2.8, "passed by": 2.5, "skipped": 2.0, "congestion": 1.8, "platform crowd": 2.5,
        "rush hour crush": 2.5, "space": 1.2, "jammed": 2.0, "overflowing": 2.5
    },
    "Cleanliness & Hygiene": {
        "dirty": 2.8, "clean": 2.0, "smell": 2.5, "stink": 2.8, "trash": 2.5, "garbage": 2.5,
        "litter": 2.2, "filthy": 3.0, "spill": 2.2, "stain": 2.0, "urine": 3.0, "vomit": 3.0,
        "disgusting": 2.5, "sanitary": 2.0, "hygiene": 2.2, "restroom": 2.0, "toilet": 2.2,
        "graffiti": 2.0, "sticky": 2.0, "dusty": 1.8, "fresh": 1.5, "spotless": 2.5
    },
    "Driver & Staff Behavior": {
        "driver": 2.0, "staff": 2.0, "operator": 2.0, "conductor": 2.0, "rude": 2.8,
        "polite": 2.2, "helpful": 2.2, "aggressive": 2.8, "reckless": 3.0, "harsh braking": 2.5,
        "ignored": 2.0, "shouted": 2.8, "attitude": 2.2, "courteous": 2.2, "friendly": 2.0,
        "customer service": 2.0, "unprofessional": 2.5, "slammed door": 2.8, "drove off": 2.8
    },
    "Ticketing, Smart Cards & Fares": {
        "ticket": 2.5, "fare": 2.5, "card": 2.0, "tap": 2.2, "turnstile": 2.5, "gate": 2.0,
        "kiosk": 2.2, "machine": 1.8, "overcharged": 2.8, "refund": 2.5, "validator": 2.5,
        "scanner": 2.0, "app payment": 2.2, "balance": 1.8, "top up": 2.2, "metrocard": 2.5,
        "transit pass": 2.2, "fare increase": 2.0, "payment error": 2.8, "contactless": 2.0
    },
    "Safety, Security & Lighting": {
        "safety": 2.5, "safe": 2.0, "security": 2.5, "guard": 2.0, "police": 2.2,
        "harassment": 3.2, "threat": 3.0, "fight": 3.0, "dark": 2.0, "lighting": 2.2,
        "scary": 2.2, "pickpocket": 3.0, "theft": 3.0, "stolen": 2.8, "emergency": 3.0,
        "sos": 3.0, "unsafe": 2.8, "danger": 2.8, "cctv": 2.0, "slip hazard": 2.8,
        "assault": 3.5, "suspicious": 2.5
    },
    "Accessibility & Special Needs": {
        "wheelchair": 3.0, "ramp": 2.8, "elevator": 2.8, "lift": 2.5, "escalator": 2.5,
        "accessible": 2.5, "disabled": 2.5, "stroller": 2.2, "elderly": 2.2, "blind": 2.5,
        "audio announcement": 2.2, "braille": 2.8, "broken elevator": 3.0, "step free": 2.5,
        "mobility": 2.5, "special needs": 2.8, "tactile paving": 2.8
    },
    "Route Frequency & Network Coverage": {
        "frequency": 2.5, "frequent": 2.0, "headway": 2.2, "every 30 mins": 2.5, "route": 1.8,
        "bus line": 2.0, "missing stop": 2.2, "connect": 1.8, "connection": 2.0, "transfer": 1.8,
        "more buses": 2.5, "more trains": 2.5, "weekend service": 2.2, "night service": 2.2,
        "coverage": 2.2, "extend route": 2.5, "gap": 1.8, "irregular": 2.2
    },
    "HVAC & Vehicle Comfort": {
        "ac": 2.8, "air conditioning": 3.0, "heater": 2.8, "heating": 2.8, "hot": 2.2,
        "cold": 2.2, "freezing": 2.5, "boiling": 2.5, "stuffy": 2.5, "ventilation": 2.5,
        "noisy": 2.0, "vibration": 2.0, "bumpy": 2.0, "seats uncomfortable": 2.2, "leaking": 2.5,
        "temperature": 2.2, "air quality": 2.5, "windows": 1.8, "ac broken": 3.0
    }
}

class ServiceCategoryClassifier:
    def __init__(self):
        self.categories = CATEGORIES
        self.keywords = CATEGORY_KEYWORDS

    def classify(self, text: str) -> Tuple[str, float]:
        """
        Classifies feedback text into one of 9 transit service categories.
        Returns: (category_name, confidence_score [0.0 - 1.0])
        """
        if not text or not text.strip():
            return "Punctuality & Delays", 0.50

        clean_text = text.lower()
        scores: Dict[str, float] = {cat: 0.0 for cat in self.categories}

        for cat, kw_dict in self.keywords.items():
            for kw, weight in kw_dict.items():
                # Word boundary match for single words, direct substring for multi-words
                if " " in kw:
                    if kw in clean_text:
                        scores[cat] += weight * 1.5
                else:
                    matches = len(re.findall(r'\b' + re.escape(kw) + r'\b', clean_text))
                    if matches > 0:
                        scores[cat] += weight * matches

        # Check top score
        sorted_scores = sorted(scores.items(), key=lambda x: x[1], reverse=True)
        top_cat, top_score = sorted_scores[0]

        if top_score == 0.0:
            # Fallback heuristic based on generic mentions
            if any(w in clean_text for w in ["bus", "train", "metro", "tram"]):
                return "Route Frequency & Network Coverage", 0.45
            return "Punctuality & Delays", 0.40

        # Normalize confidence to 0.55 - 0.98 range
        total_positive_scores = sum(s for s in scores.values() if s > 0)
        confidence = min(0.98, max(0.55, top_score / (total_positive_scores + 1.0) * 0.8 + 0.35))
        return top_cat, round(confidence, 2)

    def get_all_category_scores(self, text: str) -> Dict[str, float]:
        clean_text = text.lower()
        scores: Dict[str, float] = {}
        for cat, kw_dict in self.keywords.items():
            cat_score = 0.0
            for kw, weight in kw_dict.items():
                if " " in kw:
                    if kw in clean_text:
                        cat_score += weight * 1.5
                else:
                    matches = len(re.findall(r'\b' + re.escape(kw) + r'\b', clean_text))
                    if matches > 0:
                        cat_score += weight * matches
            scores[cat] = cat_score
        
        total = sum(scores.values()) or 1.0
        return {cat: round(s / total, 3) for cat, s in scores.items()}

# Global singleton
category_classifier = ServiceCategoryClassifier()
