# TransitPulse AI: Public Transport Feedback Intelligence & Decision Support System

An end-to-end, AI and GIS-powered intelligence platform developed for public transport authorities. The system ingests passenger feedback across multiple channels (mobile applications, social media / microblogs, customer emails, web portals), performs natural language processing (NLP) classification, sentiment & emotion analysis, extracts transit routes and stations via Named Entity Recognition (NER), clusters operational bottlenecks, predicts passenger satisfaction trends, and provides interactive GIS maps with actionable decision-support recommendations.

---

## Key Capabilities & System Features

### 1. Multi-Platform Feedback Ingestion Layer
- **Multi-Channel Support**: Ingests passenger feedback from Mobile Apps, Social Media (Twitter/X style tweets), Customer Service Emails, and Public Web Portals.
- **Continuous Ingestion Pipeline**: Real-time enrichment pipeline parsing text, assigning transit modes, and routing issues to relevant departments.

### 2. NLP & AI Intelligence Pipeline
- **9-Class Service Categorization**:
  1. `Punctuality & Delays`
  2. `Overcrowding & Capacity`
  3. `Cleanliness & Hygiene`
  4. `Driver & Staff Behavior`
  5. `Ticketing, Smart Cards & Fares`
  6. `Safety, Security & Lighting`
  7. `Accessibility & Special Needs`
  8. `Route Frequency & Network Coverage`
  9. `HVAC & Vehicle Comfort`
- **Sentiment & Emotion Analysis**:
  - Polarity scoring (`[-1.0, 1.0]`) and sentiment classification (`Positive`, `Neutral`, `Negative`).
  - Multi-label emotion spectrum (`Anger`, `Frustration`, `Anxiety`, `Satisfaction`, `Gratitude`, `Neutral`).
- **Transit Named Entity Recognition (NER)**:
  - Extracts Stations / Terminals, Transit Lines / Bus numbers, Direction / Headings, Time references, and Physical equipment / Aspects.
  - Automatically resolves mentions to canonical GIS spatial nodes.
- **Topic Modeling & Bottleneck Clustering**:
  - TF-IDF vectorization + clustering to uncover recurring problem signatures and key phrases.
- **Predictive CSAT Forecasting & Anomaly Detection**:
  - Calculates daily CSAT (Customer Satisfaction Index) & Net Sentiment Score (NSS).
  - 7-Day linear predictive forecasting with confidence interval bands.
  - Z-Score anomaly detector for sudden operational spikes or service disruptions.

### 3. Interactive GIS Transit Map & Geospatial Analytics
- **Metropolis Spatial Network**: Metro Lines (Red, Blue, Green), Bus Routes (101, 204), and Tram Lines (T1) with 35+ geo-coded stations.
- **Dynamic Leaflet Map**:
  - Route health status and satisfaction color-coding.
  - Station pins with interactive popups showing real-time CSAT, feedback volume, and issue breakdowns.
  - Leaflet Heatmap layer highlighting operational complaint hotspots.
  - Mode filtering (Metro, Bus, Tram).

### 4. AI Decision Support & Action Recommendation Center
- **Automated Root-Cause Diagnosis**: Synthesizes category, emotion, location, and keywords to identify core operational failures.
- **Prescriptive Operational Directives**: Generates prioritized recommendations (Critical, High, Medium, Low) with estimated passenger reach, projected CSAT recovery impact, and assigned operational departments.
- **Incident Dispatch Workflow**: Status state-machine (`Open` ➔ `Approved` ➔ `Dispatched` ➔ `Completed`).

### 5. Interactive UI & Passenger Experience
- **Executive Operations Dashboard**: High-level KPIs, sentiment doughnuts, emotion radar charts, and category volume graphs.
- **Live NLP Lab**: Interactive sandbox to test arbitrary passenger feedback text with real-time entity and confidence visualizers.
- **Passenger Portal Simulator**: Citizen feedback submission form with instant AI classification preview.
- **Disruption & Scenario Simulator**: Real-time event injection for *Rush Hour Overcrowding*, *Rain & Signal Delays*, *Fare Gate Glitches*, and *Cleanliness Compliments*.

---

## Directory Structure

```
transit_feedback_intelligence/
├── app/
│   ├── config.py                   # App configuration & paths
│   ├── main.py                     # FastAPI server & REST API endpoints
│   ├── models/
│   │   └── schemas.py              # Pydantic data schemas
│   ├── nlp/
│   │   ├── classifier.py           # 9-class service categorization
│   │   ├── sentiment.py            # Polarity & emotion engine
│   │   ├── ner_extractor.py        # Transit NER & location resolution
│   │   ├── topic_clusterer.py      # Topic modeling & bottleneck clustering
│   │   └── forecaster.py           # CSAT forecasting & anomaly detector
│   ├── gis/
│   │   ├── network_data.py         # GIS network topology & GeoJSON
│   │   └── spatial_analytics.py    # Station hotspots & route health index
│   ├── recommender/
│   │   ├── root_cause.py           # Root cause diagnosis engine
│   │   └── action_engine.py        # Action recommendation & ticket dispatch
│   ├── ingestion/
│   │   ├── pipeline.py             # Data ingestion and persistence
│   │   └── mock_generator.py       # High-volume synthetic data generator
│   ├── static/
│   │   ├── css/custom.css          # Glassmorphism theme & animations
│   │   └── js/                     # Modular frontend JavaScript files
│   └── templates/
│       └── index.html              # Single-page dashboard template
├── data/
│   ├── transit_network.json        # GeoJSON transit network database
│   └── seed_feedback.json          # Preloaded realistic feedback records
├── tests/
│   ├── test_nlp.py                 # NLP classification, sentiment, NER tests
│   ├── test_gis.py                 # GIS network and spatial tests
│   ├── test_recommender.py         # Decision support & root cause tests
│   ├── test_api.py                 # REST API endpoints test suite
│   └── run_tests.py                # Comprehensive test runner script
├── run.py                          # Application startup script
├── requirements.txt                # Python dependencies
└── README.md                       # Documentation
```

---

## Quick Start Guide

### 1. Run Automated Test Suite
```powershell
python tests/run_tests.py
```

### 2. Launch the Application
```powershell
python run.py
```
Open your browser and navigate to:
- **Interactive Dashboard & GIS Portal**: [http://127.0.0.1:8000](http://127.0.0.1:8000)
- **Interactive Swagger REST API Docs**: [http://127.0.0.1:8000/docs](http://127.0.0.1:8000/docs)

---

## REST API Reference

| Endpoint | Method | Description |
|---|---|---|
| `GET /` | `GET` | Serves the interactive full-stack dashboard |
| `GET /api/analytics/summary` | `GET` | Returns executive KPIs, CSAT index, sentiment & emotion distribution |
| `GET /api/analytics/trends` | `GET` | Returns historical daily trends and 7-day predictive forecast |
| `POST /api/feedback` | `POST` | Ingests passenger feedback with automatic AI enrichment |
| `GET /api/feedback` | `GET` | Retrieves filtered feedback list (by mode, category, sentiment, severity, search) |
| `PATCH /api/feedback/{id}/status` | `PATCH` | Updates resolution ticket status (Open, In Review, Dispatched, Resolved) |
| `POST /api/nlp/analyze` | `POST` | Live real-time NLP analysis sandbox for arbitrary text |
| `GET /api/gis/network` | `GET` | Returns GeoJSON transit network lines and stations |
| `GET /api/gis/stations` | `GET` | Returns station sentiment, complaint volume, and bottleneck metrics |
| `GET /api/gis/routes` | `GET` | Returns route-level operational health and punctuality metrics |
| `GET /api/gis/heatmap` | `GET` | Returns coordinate-intensity points for Leaflet heatmap layer |
| `GET /api/recommendations` | `GET` | Returns prioritized AI actionable recommendations |
| `PATCH /api/recommendations/{id}/status` | `PATCH` | Updates recommendation workflow (Open -> Approved -> Dispatched -> Completed) |
| `GET /api/bottlenecks` | `GET` | Returns topic clusters and root-cause diagnoses |
| `POST /api/simulation/inject` | `POST` | Injects simulated real-time operational disruption scenarios |
| `POST /api/simulation/reset` | `POST` | Resets dataset to fresh baseline seed |
