import math
from typing import List, Dict, Any
from datetime import datetime, timedelta

class SatisfactionForecaster:
    def __init__(self):
        pass

    def compute_trends_and_forecast(self, feedback_items: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Computes historical satisfaction index (CSAT & Net Sentiment Score) and forecasts future 7 periods.
        Detects statistical anomalies (Z-score spikes).
        """
        if not feedback_items:
            # Default empty trend
            return {
                "historical_trend": [],
                "forecast_trend": [],
                "anomalies": [],
                "current_csat": 75.0,
                "csat_change_pct": 0.0,
                "projected_csat_7d": 75.0
            }

        # Group feedback by date
        date_buckets: Dict[str, List[Dict[str, Any]]] = {}
        for item in feedback_items:
            ts_str = item.get("timestamp", "")
            # Extract YYYY-MM-DD or default
            dt_key = ts_str[:10] if len(ts_str) >= 10 else datetime.now().strftime("%Y-%m-%d")
            date_buckets.setdefault(dt_key, []).append(item)

        sorted_dates = sorted(date_buckets.keys())

        # If less than 5 days, expand synthetic dates for smooth visual presentation
        if len(sorted_dates) < 7:
            # Generate 7 recent days
            today = datetime.now()
            all_dates = [(today - timedelta(days=6-i)).strftime("%Y-%m-%d") for i in range(7)]
            for d in all_dates:
                if d not in date_buckets:
                    date_buckets[d] = []
            sorted_dates = sorted(date_buckets.keys())

        historical_trend = []
        sentiment_scores = []

        for d in sorted_dates:
            items = date_buckets[d]
            count = len(items)
            pos = sum(1 for it in items if it.get("sentiment") == "Positive")
            neg = sum(1 for it in items if it.get("sentiment") == "Negative")
            neu = sum(1 for it in items if it.get("sentiment") == "Neutral")

            if count > 0:
                # CSAT: (Positive + 0.5 * Neutral) / Total * 100
                csat = round(((pos + 0.5 * neu) / count) * 100, 1)
                # Net Sentiment Score (NSS): %Pos - %Neg (-100 to +100)
                nss = round(((pos - neg) / count) * 100, 1)
                avg_polarity = round(sum(it.get("polarity_score", 0.0) for it in items) / count, 2)
            else:
                # Baseline default
                csat = 72.0
                nss = 24.0
                avg_polarity = 0.15

            historical_trend.append({
                "date": d,
                "volume": count,
                "positive": pos,
                "neutral": neu,
                "negative": neg,
                "csat": csat,
                "nss": nss,
                "avg_polarity": avg_polarity
            })
            sentiment_scores.append(csat)

        # Anomaly Detection using Z-Score on Negative feedback volume / CSAT drops
        anomalies = []
        volumes = [h["volume"] for h in historical_trend if h["volume"] > 0]
        if len(volumes) >= 3:
            mean_vol = sum(volumes) / len(volumes)
            variance = sum((v - mean_vol) ** 2 for v in volumes) / len(volumes)
            std_vol = math.sqrt(variance) or 1.0

            for h in historical_trend:
                if h["volume"] > 0:
                    z_score = (h["volume"] - mean_vol) / std_vol
                    # Anomaly if volume spike or severe CSAT drop below 50
                    if z_score > 1.8 or (h["csat"] < 48 and h["volume"] >= 5):
                        anomalies.append({
                            "date": h["date"],
                            "volume": h["volume"],
                            "csat": h["csat"],
                            "z_score": round(z_score, 2),
                            "alert_type": "Complaint Surge Spike" if z_score > 1.8 else "Severe CSAT Degradation",
                            "severity": "Critical" if z_score > 2.2 else "High"
                        })

        # Linear Regression Forecast for Next 7 Days
        forecast_trend = []
        n = len(historical_trend)
        x_vals = list(range(n))
        y_vals = [h["csat"] for h in historical_trend]

        # Calculate slope & intercept
        x_mean = sum(x_vals) / n
        y_mean = sum(y_vals) / n
        denom = sum((x - x_mean) ** 2 for x in x_vals)
        if denom > 0:
            slope = sum((x_vals[i] - x_mean) * (y_vals[i] - y_mean) for i in range(n)) / denom
        else:
            slope = 0.0
        intercept = y_mean - (slope * x_mean)

        last_dt = datetime.strptime(sorted_dates[-1], "%Y-%m-%d")
        for i in range(1, 8):
            next_dt = (last_dt + timedelta(days=i)).strftime("%Y-%m-%d")
            x_future = n - 1 + i
            projected_csat = max(15.0, min(95.0, round(intercept + (slope * x_future), 1)))
            upper_bound = min(100.0, round(projected_csat + (1.5 * i), 1))
            lower_bound = max(0.0, round(projected_csat - (1.5 * i), 1))

            forecast_trend.append({
                "date": next_dt,
                "projected_csat": projected_csat,
                "upper_confidence": upper_bound,
                "lower_confidence": lower_bound
            })

        current_csat = historical_trend[-1]["csat"] if historical_trend else 75.0
        prev_csat = historical_trend[-2]["csat"] if len(historical_trend) >= 2 else current_csat
        csat_change = round(current_csat - prev_csat, 1)
        projected_7d = forecast_trend[-1]["projected_csat"] if forecast_trend else current_csat

        return {
            "historical_trend": historical_trend,
            "forecast_trend": forecast_trend,
            "anomalies": anomalies,
            "current_csat": current_csat,
            "csat_change_pct": csat_change,
            "projected_csat_7d": projected_7d
        }

# Global singleton
satisfaction_forecaster = SatisfactionForecaster()
