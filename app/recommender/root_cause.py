from typing import List, Dict, Any
from collections import Counter

class RootCauseDiagnoser:
    def __init__(self):
        pass

    def diagnose(self, items: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        Analyzes negative feedback clusters to diagnose underlying Mumbai transit operational root causes.
        """
        if not items:
            return []

        # Filter negative / low rating complaints
        complaints = [it for it in items if it.get("sentiment") == "Negative" or (it.get("rating") is not None and it["rating"] <= 2)]
        if not complaints:
            return []

        # Group by (Category, Line/Station)
        grouped = {}
        for c in complaints:
            cat = c.get("category", "General Operations")
            loc = c.get("station_name") or c.get("line_name") or "Mumbai Metropolitan Transit"
            key = (cat, loc)
            grouped.setdefault(key, []).append(c)

        diagnoses = []
        for (cat, loc), group in grouped.items():
            if len(group) < 2 and len(complaints) > 10:
                continue

            emotions = Counter([g.get("primary_emotion", "Frustration") for g in group])
            top_emo = emotions.most_common(1)[0][0] if emotions else "Frustration"

            # Check modes involved
            modes = list(set([g.get("mode", "Train") for g in group]))
            mode = modes[0] if modes else "Train"

            aspects = []
            for g in group:
                ents = g.get("entities", {})
                if isinstance(ents, dict):
                    aspects.extend(ents.get("aspects", []))
            top_aspects = [a for a, _ in Counter(aspects).most_common(2)]

            # Root Cause synthesis logic tailored to Mumbai
            if mode == "Train":
                department = "Central / Western Railway Divisional Operations"
                if cat == "Punctuality & Delays":
                    diagnosis_summary = f"Signaling, track circuit failure, or overhead equipment (OHE) trip on {loc}"
                    probable_cause = "Signal cascade failure during peak hours, slow line bottleneck, or monsoon waterlogging."
                elif cat == "Overcrowding & Capacity":
                    diagnosis_summary = f"Severe platform and footboard crush load at {loc}"
                    probable_cause = "High commuter volume bottleneck; inadequate 15-car or AC local rake frequency."
                elif cat == "Safety, Security & Lighting":
                    diagnosis_summary = f"Foot Over Bridge (FOB) choke or platform gap hazard at {loc}"
                    probable_cause = "Commuter stampede hazard on narrow staircases and inadequate RPF/GRP police presence."
                elif cat == "Ticketing, Smart Cards & Fares":
                    diagnosis_summary = f"UTS mobile QR / ATVM ticketing machine failure at {loc}"
                    probable_cause = "CRIS server gateway latency or GPS geofence boundary mismatch on UTS app."
                else:
                    diagnosis_summary = f"Railway service degradation at {loc}"
                    probable_cause = "Station facility maintenance backlog and heavy passenger footfall."

            elif mode == "Metro":
                department = "MMRDA / Maha Mumbai Metro Operations (MMMOCL)"
                if cat == "Overcrowding & Capacity":
                    diagnosis_summary = f"Peak-hour platform crowding and interchange choke at {loc}"
                    probable_cause = "3-minute headway bottleneck; high interchange influx from local train stations."
                elif cat == "Ticketing, Smart Cards & Fares":
                    diagnosis_summary = f"NCMC / Mumbai 1 Smart Card / QR AFC gate validation error at {loc}"
                    probable_cause = "Optical QR barcode scanner firmware latency during high-speed passenger flow."
                else:
                    diagnosis_summary = f"Metro service issue at {loc}"
                    probable_cause = "Rolling stock HVAC filter saturation or escalator mechanical fault."

            elif mode == "Monorail":
                department = "Mumbai Monorail Operations Division"
                if cat == "Route Frequency & Network Coverage":
                    diagnosis_summary = f"Extended 40-minute headway gap on Mumbai Monorail at {loc}"
                    probable_cause = "Limited operational rake fleet availability and depot turnaround maintenance."
                elif cat == "HVAC & Vehicle Comfort":
                    diagnosis_summary = f"Monorail cabin HVAC climate failure at {loc}"
                    probable_cause = "Inverter compressor fault on rolling stock under heavy thermal load."
                else:
                    diagnosis_summary = f"Monorail infrastructure issue at {loc}"
                    probable_cause = "Guideway power rail insulation check required."

            else:  # Bus
                department = "BEST Undertaking / NMMT Bus Operations"
                if cat == "Punctuality & Delays":
                    diagnosis_summary = f"Bus headway bunching and corridor congestion near {loc}"
                    probable_cause = "Mixed-traffic congestion on WEH / SCLR / Palm Beach Road without bus priority lane."
                elif cat == "Driver & Staff Behavior":
                    diagnosis_summary = f"Bus crew conduct or change denomination dispute at {loc}"
                    probable_cause = "Cash handling friction or aggressive overtaking in crowded street lanes."
                elif cat == "Ticketing, Smart Cards & Fares":
                    diagnosis_summary = f"Chalo Card / ETM electronic ticketing machine error near {loc}"
                    probable_cause = "ETM network SIM connectivity blackout or contactless NFC timeout."
                else:
                    diagnosis_summary = f"Bus service issue near {loc}"
                    probable_cause = "Electric bus charger queueing or fleet maintenance backlog."

            if top_aspects:
                probable_cause += f" Specifically reported on {', '.join(top_aspects)}."

            diagnoses.append({
                "category": cat,
                "location": loc,
                "complaint_count": len(group),
                "dominant_emotion": top_emo,
                "diagnosis_summary": diagnosis_summary,
                "probable_cause": probable_cause,
                "department": department,
                "sample_feedback": [g.get("text") for g in group[:2]]
            })

        diagnoses.sort(key=lambda x: x["complaint_count"], reverse=True)
        return diagnoses

# Global singleton
root_cause_diagnoser = RootCauseDiagnoser()
