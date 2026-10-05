import asyncio
import httpx
from app.main import app

async def run_api_tests():
    transport = httpx.ASGITransport(app=app)
    async with httpx.AsyncClient(transport=transport, base_url="http://testserver") as client:
        # Test 1: Health / Index
        res = await client.get("/")
        assert res.status_code == 200
        assert "TransitPulse AI" in res.text
        print("✓ API: Mumbai Index page served")

        # Test 2: Analytics Summary
        res = await client.get("/api/analytics/summary")
        assert res.status_code == 200
        data = res.json()
        assert "total_feedback" in data
        assert "csat_score" in data
        print("✓ API: Analytics summary returned Mumbai KPIs")

        # Test 3: Analytics Trends
        res = await client.get("/api/analytics/trends")
        assert res.status_code == 200
        data = res.json()
        assert "historical_trend" in data
        assert len(data["forecast_trend"]) == 7
        print("✓ API: Mumbai CSAT trends & 7-day forecast returned")

        # Test 4: Ingestion (Train, Bus, Metro, Monorail)
        payload = {
            "text": "Western Line AC local was 15 minutes late at Andheri Station Interchange. Very crowded!",
            "source": "Mobile App",
            "mode": "Train",
            "rating": 2
        }
        res = await client.post("/api/feedback", json=payload)
        assert res.status_code == 200
        item = res.json()
        assert item["sentiment"] == "Negative"
        assert item["mode"] == "Train"
        print("✓ API: Mumbai feedback ingestion with NLP enrichment")

        # Test 5: Live NLP Lab
        res = await client.post("/api/nlp/analyze", json={"text": "Clean train on Metro Line 3 at BKC station! Thank you."})
        assert res.status_code == 200
        data = res.json()
        assert data["sentiment"] == "Positive"
        assert any("BKC" in s for s in data["entities"]["stations"])
        print("✓ API: Mumbai live NLP analysis sandbox")

        # Test 6: GIS Network & Stations
        res = await client.get("/api/gis/network")
        assert res.status_code == 200
        assert res.json()["type"] == "FeatureCollection"

        res_st = await client.get("/api/gis/stations")
        assert res_st.status_code == 200
        assert len(res_st.json()) >= 20
        print("✓ API: Mumbai GIS network and station analytics")

        # Test 7: Recommendations Workflow, Custom Creation & Editing
        res = await client.get("/api/recommendations")
        assert res.status_code == 200
        assert len(res.json()) >= 1
        rec_id = res.json()[0]["id"]

        # Status patch
        patch_res = await client.patch(f"/api/recommendations/{rec_id}/status", json={"status": "Approved"})
        assert patch_res.status_code == 200
        assert patch_res.json()["status"] == "Approved"

        # Create custom action
        create_payload = {
            "title": "Deploy RPF Quick Reaction Team on Harbour Line at Vashi",
            "category": "Safety, Security & Lighting",
            "target_name": "Vashi Sector 17 / Station Hub",
            "priority": "Critical",
            "root_cause_summary": "Late night commuter safety concerns.",
            "recommended_action": "Roving security patrols between 21:00 and 01:30.",
            "operational_department": "Transit Police (GRP & RPF Security)",
            "supervisor_notes": "Immediate deployment approved."
        }
        post_rec_res = await client.post("/api/recommendations", json=create_payload)
        assert post_rec_res.status_code == 201
        new_rec = post_rec_res.json()
        assert new_rec["is_custom"] is True

        # Edit recommendation
        new_id = new_rec["id"]
        put_res = await client.put(f"/api/recommendations/{new_id}", json={
            "recommended_action": "Deploy 4 RPF officers with bodycams on Vashi platforms.",
            "supervisor_notes": "Updated with bodycam requirement."
        })
        assert put_res.status_code == 200
        assert "bodycam" in put_res.json()["recommended_action"]
        print("✓ API: Recommendation creation, editing & approval workflow")

        # Test 8: Simulation Injection
        res = await client.post("/api/simulation/inject?scenario_type=rush_hour")
        assert res.status_code == 200
        assert res.json()["status"] == "success"
        print("✓ API: Mumbai scenario disruption simulator")

def test_api():
    asyncio.run(run_api_tests())

if __name__ == "__main__":
    test_api()
