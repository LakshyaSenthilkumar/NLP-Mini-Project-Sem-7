import re
from typing import List, Dict, Any
from collections import Counter
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.cluster import MiniBatchKMeans

STOP_WORDS = {
    "the", "a", "an", "and", "or", "but", "in", "on", "at", "to", "for", "with",
    "by", "about", "against", "between", "into", "through", "during", "before",
    "after", "above", "below", "from", "up", "down", "of", "off", "over", "under",
    "again", "further", "then", "once", "here", "there", "when", "where", "why",
    "how", "all", "any", "both", "each", "few", "more", "most", "other", "some",
    "such", "no", "nor", "not", "only", "own", "same", "so", "than", "too", "very",
    "s", "t", "can", "will", "just", "don", "should", "now", "it", "is", "was",
    "are", "were", "been", "being", "have", "has", "had", "having", "do", "does",
    "did", "doing", "i", "me", "my", "myself", "we", "our", "ours", "ourselves",
    "you", "your", "yours", "yourself", "yourselves", "he", "him", "his", "himself",
    "she", "her", "hers", "herself", "they", "them", "their", "theirs", "themselves",
    "what", "which", "who", "whom", "this", "that", "these", "those", "am"
}

class TopicAndBottleneckClusterer:
    def __init__(self, n_clusters: int = 5):
        self.n_clusters = n_clusters

    def extract_key_phrases(self, texts: List[str], top_n: int = 10) -> List[Dict[str, Any]]:
        """
        Extracts trending bigrams and high-frequency issue phrases.
        """
        if not texts:
            return []

        phrases = []
        for text in texts:
            words = [w.lower() for w in re.findall(r'\b[a-zA-Z]{3,}\b', text) if w.lower() not in STOP_WORDS]
            # Bi-grams
            for i in range(len(words) - 1):
                phrases.append(f"{words[i]} {words[i+1]}")
            # Uni-grams
            phrases.extend(words)

        counts = Counter(phrases)
        total = len(phrases) or 1
        return [{"phrase": phrase, "count": count, "frequency": round(count / total * 100, 2)}
                for phrase, count in counts.most_common(top_n)]

    def cluster_issues(self, feedback_items: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        Clusters negative and recurring feedback into operational bottleneck themes.
        """
        if len(feedback_items) < 3:
            return []

        texts = [item.get("text", "") for item in feedback_items]
        
        # TF-IDF
        try:
            vectorizer = TfidfVectorizer(max_features=200, stop_words="english", ngram_range=(1, 2))
            X = vectorizer.fit_transform(texts)
            feature_names = vectorizer.get_feature_names_out()

            k = min(self.n_clusters, len(feedback_items))
            kmeans = MiniBatchKMeans(n_clusters=k, random_state=42, n_init=3, batch_size=64)
            labels = kmeans.fit_predict(X)

            clusters = []
            for i in range(k):
                cluster_indices = [idx for idx, label in enumerate(labels) if label == i]
                if not cluster_indices:
                    continue

                cluster_items = [feedback_items[idx] for idx in cluster_indices]
                cluster_texts = [texts[idx] for idx in cluster_indices]

                # Top terms in cluster center
                center = kmeans.cluster_centers_[i]
                top_term_indices = center.argsort()[::-1][:5]
                top_terms = [feature_names[term_idx] for term_idx in top_term_indices if term_idx < len(feature_names)]

                # Find dominant category and station/line
                categories = Counter([it.get("category", "General") for it in cluster_items])
                stations = Counter([it.get("station_name") for it in cluster_items if it.get("station_name")])
                lines = Counter([it.get("line_name") for it in cluster_items if it.get("line_name")])
                emotions = Counter([it.get("primary_emotion", "Frustration") for it in cluster_items])
                
                dominant_cat = categories.most_common(1)[0][0] if categories else "Service Operations"
                dominant_st = stations.most_common(1)[0][0] if stations else "Transit Network"
                dominant_ln = lines.most_common(1)[0][0] if lines else "Multi-Route"
                dominant_emo = emotions.most_common(1)[0][0] if emotions else "Frustration"

                # Calculate bottleneck severity score
                neg_count = sum(1 for it in cluster_items if it.get("sentiment") == "Negative")
                neg_ratio = neg_count / len(cluster_items) if cluster_items else 0
                severity_score = min(100.0, round((len(cluster_items) * 4.0) + (neg_ratio * 40.0), 1))

                clusters.append({
                    "cluster_id": i + 1,
                    "title": f"{dominant_cat} @ {dominant_st}",
                    "category": dominant_cat,
                    "primary_location": dominant_st,
                    "primary_line": dominant_ln,
                    "dominant_emotion": dominant_emo,
                    "item_count": len(cluster_items),
                    "negative_ratio": round(neg_ratio * 100, 1),
                    "severity_score": severity_score,
                    "top_keywords": top_terms,
                    "sample_complaints": [it.get("text") for it in cluster_items[:2]]
                })

            clusters.sort(key=lambda x: x["severity_score"], reverse=True)
            return clusters

        except Exception as e:
            # Fallback simple group-by category
            cat_groups = {}
            for item in feedback_items:
                cat = item.get("category", "General")
                cat_groups.setdefault(cat, []).append(item)

            fallback_clusters = []
            for idx, (cat, items) in enumerate(cat_groups.items()):
                fallback_clusters.append({
                    "cluster_id": idx + 1,
                    "title": f"Recurring {cat} Issues",
                    "category": cat,
                    "primary_location": "Network-wide",
                    "primary_line": "All Lines",
                    "dominant_emotion": "Frustration",
                    "item_count": len(items),
                    "negative_ratio": 75.0,
                    "severity_score": min(100.0, float(len(items) * 8.0)),
                    "top_keywords": [cat.lower(), "delay", "service", "transit"],
                    "sample_complaints": [it.get("text", "") for it in items[:2]]
                })
            return fallback_clusters

# Global singleton
topic_clusterer = TopicAndBottleneckClusterer()
