import uuid
from typing import List, Dict, Any, Optional
from datetime import datetime
from app.recommender.root_cause import root_cause_diagnoser

class ActionableRecommendationEngine:
    def __init__(self):
        self.recommendations: Dict[str, Dict[str, Any]] = {}
        self.diagnoser = root_cause_diagnoser

    def generate_recommendations(self, feedback_items: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        Generates actionable, prioritized operational directives tailored for Mumbai transit networks.
        Preserves existing custom and approved recommendations.
        """
        diagnoses = self.diagnoser.diagnose(feedback_items)

        for diag in diagnoses:
            cat = diag["category"]
            loc = diag["location"]
            count = diag["complaint_count"]
            dept = diag["department"]
            emo = diag["dominant_emotion"]

            # Severity Score (0 to 100)
            base_score = min(50.0, float(count * 6.0))
            if cat in ["Safety, Security & Lighting", "Accessibility & Special Needs"]:
                base_score += 35.0
            elif emo in ["Anger", "Anxiety"]:
                base_score += 20.0
            elif emo == "Frustration":
                base_score += 10.0

            severity_score = min(100.0, round(base_score, 1))

            # Priority Level
            if severity_score >= 80.0 or cat == "Safety, Security & Lighting":
                priority = "Critical"
            elif severity_score >= 60.0:
                priority = "High"
            elif severity_score >= 40.0:
                priority = "Medium"
            else:
                priority = "Low"

            # Prescriptive Action and Estimated Impact tailored to Mumbai context
            if cat == "Punctuality & Delays":
                title = f"Clear Signaling Interlock & Dispatch Fast Corridor Standby at {loc}"
                action = f"Instruct Control Office to resolve Kurla/Dadar cascade delay, deploy reserve suburban rake from Kurla/Bandra Car Shed, and coordinate signal green-wave."
                impact = "Estimated 28% reduction in local train / bus delay and +15 pts recovery in Mumbai CSAT."
            elif cat == "Overcrowding & Capacity":
                title = f"Inject Peak AC/15-Car Rakes & Deploy RPF Marshals at {loc}"
                action = f"Convert 2 slow services to 15-car rakes, reduce Metro Line 1 headway to 2.5 mins, and deploy 6 RPF marshals on FOB staircases to manage boarding flow."
                impact = "Eliminates dangerous platform crowd crush and improves boarding clearance by 35%."
            elif cat == "Cleanliness & Hygiene":
                title = f"Intensive Station Sanitation Blitz & Bio-Toilet Overhaul at {loc}"
                action = f"Deploy mechanized scrubbing contractors for concourse & FOBs, clean track beds, and ensure continuous water refill for station washrooms."
                impact = "Restores high hygiene standards across station platforms within 3 hours."
            elif cat == "Ticketing, Smart Cards & Fares":
                title = f"Emergency UTS QR & NCMC Gate Calibration at {loc}"
                action = f"Dispatch CRIS / AFC technical team to reboot QR optical turnstiles and open extra manual validation gates to clear ticketing concourse queues."
                impact = "Recovers 99.7% gate throughput and cuts commuter wait times from 15m to 2m."
            elif cat == "Safety, Security & Lighting":
                title = f"RPF/GRP Security Bandobast & FOB Lighting Overhaul at {loc}"
                action = f"Deploy uniformed GRP & RPF officers for platform footboard monitoring, inspect FOB structural flow, and replace high-mast LED fixtures."
                impact = "Immediate deterrence of anti-social incidents and significant reduction in commuter anxiety."
            elif cat == "Accessibility & Special Needs":
                title = f"Priority FOB Lift Repair & Divyang Sahayak Deployment at {loc}"
                action = f"Issue emergency contractor work order for elevator/lift restoration and station wheelchair mobility assistants at station booking hall."
                impact = "Ensures seamless, barrier-free access for elderly and disabled passengers across platforms."
            elif cat == "HVAC & Vehicle Comfort":
                title = f"AC Local & Monorail Thermal Overhaul at {loc}"
                action = f"Direct affected EMU / Monorail rakes to Kurla / Wadala Shed for HVAC gas pressure check and filter replacements."
                impact = "Maintains onboard cabin climate at comfortable 21-23°C during humid Mumbai weather."
            elif cat == "Driver & Staff Behavior":
                title = f"BEST / NMMT Crew Customer Courtesy & Digital Fare Briefing for {loc}"
                action = f"Conduct depot-level customer service training and enforce 100% acceptance of Chalo UPI / digital payments."
                impact = "Eliminates denomination disputes and improves passenger trust."
            else:
                title = f"Operational Audit & Service Optimization for {loc}"
                action = f"Review headway logs and dispatch standby vehicles to balance transit load."
                impact = "Improves overall Mumbai transit reliability."

            rec_id = f"REC-MUM-{abs(hash(cat + loc)) % 10000:04d}"
            
            # If already exists, preserve modified status and custom fields
            if rec_id in self.recommendations:
                continue

            rec_data = {
                "id": rec_id,
                "title": title,
                "category": cat,
                "target_type": "Line" if "Line" in loc or "Route" in loc or "Bus" in loc or "Monorail" in loc else "Station",
                "target_id": None,
                "target_name": loc,
                "priority": priority,
                "severity_score": severity_score,
                "root_cause_summary": diag["probable_cause"],
                "recommended_action": action,
                "operational_department": dept,
                "estimated_impact": impact,
                "status": "Open",
                "affected_passenger_count": count * 35,
                "created_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                "is_custom": False,
                "supervisor_notes": None
            }

            self.recommendations[rec_id] = rec_data

        all_recs = list(self.recommendations.values())
        all_recs.sort(key=lambda x: (x["priority"] == "Critical", x["severity_score"]), reverse=True)
        return all_recs

    def create_custom_recommendation(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Creates a new user-defined/authority-defined action recommendation or operational suggestion.
        """
        rec_id = f"REC-MUM-USR-{uuid.uuid4().hex[:4].upper()}"
        priority = data.get("priority", "High")
        
        severity_map = {"Critical": 90.0, "High": 70.0, "Medium": 45.0, "Low": 25.0}
        severity_score = severity_map.get(priority, 65.0)

        rec_data = {
            "id": rec_id,
            "title": data.get("title", "Custom Operational Directive"),
            "category": data.get("category", "General Operations"),
            "target_type": data.get("target_type", "Station"),
            "target_id": None,
            "target_name": data.get("target_name", "Mumbai Metropolitan Region"),
            "priority": priority,
            "severity_score": severity_score,
            "root_cause_summary": data.get("root_cause_summary", "Authority identified operational bottleneck / service improvement proposal."),
            "recommended_action": data.get("recommended_action", ""),
            "operational_department": data.get("operational_department", "Central / Western Railway Divisional Operations"),
            "estimated_impact": data.get("estimated_impact", "Projected reduction in commuter friction and improved service quality."),
            "status": "Open",
            "affected_passenger_count": data.get("affected_passenger_count", 500),
            "created_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "is_custom": True,
            "supervisor_notes": data.get("supervisor_notes")
        }

        self.recommendations[rec_id] = rec_data
        return rec_data

    def update_recommendation(self, rec_id: str, updates: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """
        Updates full details of a recommendation (custom suggestions, modified actions, department, priority, etc.).
        """
        if rec_id in self.recommendations:
            rec = self.recommendations[rec_id]
            for key, val in updates.items():
                if val is not None and key != "id":
                    rec[key] = val

            rec["updated_at"] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            return rec
        return None

    def update_recommendation_status(self, rec_id: str, new_status: str, notes: Optional[str] = None) -> Optional[Dict[str, Any]]:
        if rec_id in self.recommendations:
            self.recommendations[rec_id]["status"] = new_status
            if notes:
                self.recommendations[rec_id]["resolution_notes"] = notes
            self.recommendations[rec_id]["updated_at"] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            return self.recommendations[rec_id]
        return None

    def get_all_recommendations(self) -> List[Dict[str, Any]]:
        return list(self.recommendations.values())

# Global singleton
recommendation_engine = ActionableRecommendationEngine()
