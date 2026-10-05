import os

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA_DIR = os.path.join(BASE_DIR, "data")
TRANSIT_NETWORK_PATH = os.path.join(DATA_DIR, "transit_network.json")
FEEDBACK_DATA_PATH = os.path.join(DATA_DIR, "seed_feedback.json")
STATIC_DIR = os.path.join(BASE_DIR, "app", "static")
TEMPLATES_DIR = os.path.join(BASE_DIR, "app", "templates")

APP_TITLE = "TransitPulse AI - Public Transport Feedback Intelligence & Decision Support"
APP_VERSION = "2.0.0"
