import re
from typing import Dict, Tuple

POSITIVE_LEXICON = {
    "great": 1.5, "excellent": 2.0, "amazing": 2.0, "good": 1.0, "helpful": 1.5,
    "clean": 1.5, "fast": 1.2, "smooth": 1.5, "on time": 2.0, "friendly": 1.8,
    "courteous": 1.8, "love": 1.5, "thanks": 1.5, "thank you": 2.0, "appreciate": 1.8,
    "efficient": 1.8, "comfortable": 1.5, "safe": 1.5, "improved": 1.2, "wonderful": 2.0,
    "polite": 1.5, "perfect": 2.0, "best": 1.5, "spotless": 2.0, "happy": 1.5, "kudos": 2.0
}

NEGATIVE_LEXICON = {
    "terrible": -2.0, "horrible": -2.2, "awful": -2.0, "bad": -1.0, "worst": -2.5,
    "delayed": -1.5, "late": -1.2, "dirty": -1.8, "filthy": -2.2, "stink": -2.0,
    "rude": -2.0, "angry": -2.0, "broken": -1.5, "useless": -2.0, "hate": -2.0,
    "crowded": -1.2, "overcrowded": -1.8, "stuck": -1.5, "reckless": -2.2, "unsafe": -2.5,
    "danger": -2.5, "disaster": -2.2, "disgusted": -2.2, "unacceptable": -2.2, "annoying": -1.5,
    "frustrating": -1.8, "ridiculous": -1.8, "pain": -1.2, "scam": -2.5, "furious": -2.5,
    "screaming": -1.8, "shame": -1.5, "never again": -2.0, "nightmare": -2.5, "crap": -2.0
}

INTENSIFIERS = {
    "very": 1.5, "extremely": 2.0, "super": 1.5, "so": 1.3, "really": 1.4,
    "absolutely": 1.8, "completely": 1.6, "total": 1.5, "totally": 1.5
}

NEGATIONS = {"not", "no", "never", "hardly", "barely", "scarcely", "cannot", "can't", "won't", "didn't", "doesn't", "isn't"}

EMOTION_KEYWORDS = {
    "Anger": [
        "furious", "angry", "rage", "outraged", "mad", "ridiculous", "incompetent",
        "unacceptable", "disaster", "screaming", "rude", "shouted", "reckless",
        "disgusting", "crap", "garbage", "trash", "lawsuit", "sue", "terrible", "worst"
    ],
    "Frustration": [
        "frustrated", "frustrating", "delayed", "late again", "waiting forever", "stuck",
        "tired of", "annoying", "annoyed", "waste of time", "broken again", "every single day",
        "why is it always", "no communication", "hopeless", "fed up", "packed like sardines", "no space"
    ],
    "Anxiety": [
        "scared", "scary", "unsafe", "danger", "dangerous", "worried", "fear", "dark",
        "harassment", "threat", "alone", "panic", "creepy", "suspicious", "fight",
        "emergency", "miss my flight", "late for work", "missed interview", "anxious"
    ],
    "Satisfaction": [
        "smooth", "on time", "clean", "comfortable", "efficient", "good service", "easy",
        "pleasant", "peaceful", "prompt", "reliable", "convenient", "seated", "working well",
        "organized", "nice ride", "relaxed"
    ],
    "Gratitude": [
        "thank you", "thanks", "grateful", "appreciated", "kudos", "shoutout", "bless",
        "helpful staff", "kind driver", "returned my lost", "hero", "saved my day", "wonderful driver"
    ]
}

class SentimentEmotionEngine:
    def __init__(self):
        self.pos_lex = POSITIVE_LEXICON
        self.neg_lex = NEGATIVE_LEXICON
        self.emotion_kw = EMOTION_KEYWORDS

    def analyze(self, text: str) -> Tuple[str, float, str, Dict[str, float]]:
        """
        Analyzes sentiment and emotions.
        Returns:
            - sentiment: "Positive" | "Neutral" | "Negative"
            - polarity_score: float in [-1.0, 1.0]
            - primary_emotion: str
            - emotion_scores: Dict[str, float]
        """
        if not text or not text.strip():
            return "Neutral", 0.0, "Neutral", {"Neutral": 1.0, "Anger": 0.0, "Frustration": 0.0, "Anxiety": 0.0, "Satisfaction": 0.0, "Gratitude": 0.0}

        words = re.findall(r'\b\w+\b', text.lower())
        total_score = 0.0
        word_count = max(len(words), 1)

        i = 0
        while i < len(words):
            w = words[i]
            # Check 2-word phrase first
            phrase_2 = f"{w} {words[i+1]}" if i + 1 < len(words) else ""
            
            val = 0.0
            step = 1
            if phrase_2 in self.pos_lex:
                val = self.pos_lex[phrase_2]
                step = 2
            elif phrase_2 in self.neg_lex:
                val = self.neg_lex[phrase_2]
                step = 2
            elif w in self.pos_lex:
                val = self.pos_lex[w]
            elif w in self.neg_lex:
                val = self.neg_lex[w]

            if val != 0.0:
                # Check for negation in preceding 2 words
                is_negated = False
                for prev_idx in range(max(0, i-2), i):
                    if words[prev_idx] in NEGATIONS:
                        is_negated = True
                        break
                
                # Check intensifier
                multiplier = 1.0
                if i > 0 and words[i-1] in INTENSIFIERS:
                    multiplier = INTENSIFIERS[words[i-1]]

                if is_negated:
                    val = -val * 0.8
                
                total_score += (val * multiplier)
                i += step
            else:
                i += 1

        # Normalize polarity to [-1.0, 1.0]
        polarity = total_score / (min(word_count, 10) * 0.8 + 1.0)
        polarity = max(-1.0, min(1.0, round(polarity, 2)))

        if polarity >= 0.15:
            sentiment = "Positive"
        elif polarity <= -0.15:
            sentiment = "Negative"
        else:
            sentiment = "Neutral"

        # Emotion Analysis
        emotion_raw: Dict[str, float] = {
            "Anger": 0.05,
            "Frustration": 0.05,
            "Anxiety": 0.05,
            "Satisfaction": 0.05,
            "Gratitude": 0.05,
            "Neutral": 0.20
        }

        clean_text = text.lower()
        for emotion, kws in self.emotion_kw.items():
            for kw in kws:
                if kw in clean_text:
                    emotion_raw[emotion] += 2.0

        if sentiment == "Negative":
            emotion_raw["Neutral"] = max(0.0, emotion_raw["Neutral"] - 0.15)
            if polarity < -0.5:
                emotion_raw["Anger"] += 1.5
                emotion_raw["Frustration"] += 1.2
            else:
                emotion_raw["Frustration"] += 1.5
        elif sentiment == "Positive":
            emotion_raw["Neutral"] = max(0.0, emotion_raw["Neutral"] - 0.15)
            emotion_raw["Satisfaction"] += 1.5
            if any(w in clean_text for w in ["thank", "kudos", "appreciat", "bless"]):
                emotion_raw["Gratitude"] += 2.0
        else:
            emotion_raw["Neutral"] += 1.5

        # Normalize emotions to probability distribution (sums to 1.0)
        total_emo = sum(emotion_raw.values())
        emotion_scores = {k: round(v / total_emo, 3) for k, v in emotion_raw.items()}
        primary_emotion = max(emotion_scores.items(), key=lambda x: x[1])[0]

        return sentiment, polarity, primary_emotion, emotion_scores

# Global singleton
sentiment_engine = SentimentEmotionEngine()
