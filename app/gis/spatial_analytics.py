from typing import List, Dict, Any
from app.gis.network_data import gis_network

class SpatialAnalyticsEngine:
    def __init__(self):
        self.network = gis_network

    def calculate_station_metrics(self, feedback_items: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        Calculates sentiment scores, complaint volumes, and bottleneck ratings for all stations.
        """
        station_data = {}
        for st in self.network.get_all_stations():
            station_data[st["id"]] = {
                "id": st["id"],
                "name": st["name"],
                "lat": st["lat"],
                "lng": st["lng"],
                "modes": st["modes"],
                "is_interchange": st["is_interchange"],
                "zone": st.get("zone", "Zone 1"),
                "total_feedback": 0,
                "positive": 0,
                "neutral": 0,
                "negative": 0,
                "emotions": {},
                "top_categories": {},
                "avg_polarity": 0.0,
                "csat": 75.0,
                "issue_score": 0.0,  # 0 to 100 hotspot index
                "status": "Normal"  # Normal, Watchlist, Bottleneck, Critical
            }

        # Aggregate feedback
        for item in feedback_items:
            st_id = item.get("station_id")
            st_name = item.get("station_name")
            
            # Find station matching id or name
            target_st = None
            if st_id and st_id in station_data:
                target_st = station_data[st_id]
            elif st_name:
                for s in station_data.values():
                    if s["name"].lower() == st_name.lower():
                        target_st = s
                        break

            if target_st:
                target_st["total_feedback"] += 1
                sentiment = item.get("sentiment", "Neutral")
                if sentiment == "Positive":
                    target_st["positive"] += 1
                elif sentiment == "Negative":
                    target_st["negative"] += 1
                else:
                    target_st["neutral"] += 1

                emo = item.get("primary_emotion", "Neutral")
                target_st["emotions"][emo] = target_st["emotions"].get(emo, 0) + 1

                cat = item.get("category", "General")
                target_st["top_categories"][cat] = target_st["top_categories"].get(cat, 0) + 1

        # Calculate final metrics & hotspot intensity
        results = []
        for st_id, st in station_data.items():
            tot = st["total_feedback"]
            if tot > 0:
                st["csat"] = round(((st["positive"] + 0.5 * st["neutral"]) / tot) * 100, 1)
                neg_rate = (st["negative"] / tot)
                # Hotspot issue score: volume * negative weight
                st["issue_score"] = min(100.0, round((tot * 3.0) + (neg_rate * 60.0), 1))
            else:
                st["csat"] = 80.0
                st["issue_score"] = 10.0

            # Assign operational status
            if st["issue_score"] >= 75.0:
                st["status"] = "Critical"
            elif st["issue_score"] >= 50.0:
                st["status"] = "Bottleneck"
            elif st["issue_score"] >= 25.0:
                st["status"] = "Watchlist"
            else:
                st["status"] = "Normal"

            results.append(st)

        results.sort(key=lambda x: x["issue_score"], reverse=True)
        return results

    def calculate_route_metrics(self, feedback_items: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        Calculates health, punctuality, satisfaction score for each transit line/route.
        """
        line_data = {}
        for ln in self.network.get_all_lines():
            line_data[ln["id"]] = {
                "id": ln["id"],
                "name": ln["name"],
                "mode": ln["mode"],
                "color": ln["color"],
                "coordinates": ln["coordinates"],
                "stations": ln["stations"],
                "total_feedback": 0,
                "positive": 0,
                "neutral": 0,
                "negative": 0,
                "csat": 78.0,
                "on_time_performance_est": 88.0,
                "overcrowding_index": 20.0,
                "top_issues": [],
                "health_status": "Good"  # Good, Moderate, Degraded, Severe
            }

        # Aggregate feedback
        for item in feedback_items:
            ln_id = item.get("line_id")
            ln_name = item.get("line_name")

            target_ln = None
            if ln_id and ln_id in line_data:
                target_ln = line_data[ln_id]
            elif ln_name:
                for l in line_data.values():
                    if l["name"].lower() == ln_name.lower():
                        target_ln = l
                        break

            if target_ln:
                target_ln["total_feedback"] += 1
                sentiment = item.get("sentiment", "Neutral")
                if sentiment == "Positive":
                    target_ln["positive"] += 1
                elif sentiment == "Negative":
                    target_ln["negative"] += 1
                else:
                    target_ln["neutral"] += 1

                cat = item.get("category", "")
                if cat:
                    target_ln["top_issues"].append(cat)

        results = []
        for ln_id, ln in line_data.items():
            tot = ln["total_feedback"]
            if tot > 0:
                ln["csat"] = round(((ln["positive"] + 0.5 * ln["neutral"]) / tot) * 100, 1)
                
                # Estimate OTP and overcrowding from category occurrences
                delay_count = sum(1 for c in ln["top_issues"] if "Punctuality" in c or "Delay" in c)
                crowd_count = sum(1 for c in ln["top_issues"] if "Overcrowding" in c or "Capacity" in c)
                
                ln["on_time_performance_est"] = max(45.0, round(92.0 - (delay_count * 4.5), 1))
                ln["overcrowding_index"] = min(98.0, round(15.0 + (crowd_count * 8.0), 1))
            else:
                ln["csat"] = 82.0
                ln["on_time_performance_est"] = 92.0
                ln["overcrowding_index"] = 18.0

            if ln["csat"] < 50.0 or ln["on_time_performance_est"] < 65.0:
                ln["health_status"] = "Severe"
            elif ln["csat"] < 68.0 or ln["overcrowding_index"] > 60.0:
                ln["health_status"] = "Degraded"
            elif ln["csat"] < 80.0:
                ln["health_status"] = "Moderate"
            else:
                ln["health_status"] = "Good"

            results.append(ln)

        results.sort(key=lambda x: x["csat"])
        return results

    def get_heat_points(self, feedback_items: List[Dict[str, Any]]) -> List[List[float]]:
        """
        Returns list of [lat, lng, intensity] points for Leaflet Heatmap layer.
        Intensity is higher for negative feedback, anger/frustration emotions, and high complaint count.
        """
        points = []
        st_metrics = self.calculate_station_metrics(feedback_items)
        for st in st_metrics:
            if st["total_feedback"] > 0:
                # Intensity between 0.2 and 1.0
                intensity = min(1.0, max(0.2, st["issue_score"] / 100.0))
                points.append([st["lat"], st["lng"], intensity])

        # Also add coordinates for any specific geo-tagged feedback
        return points

# Global singleton
spatial_analytics = SpatialAnalyticsEngine()
