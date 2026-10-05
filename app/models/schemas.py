from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any
from datetime import datetime

class FeedbackSubmission(BaseModel):
    text: str = Field(..., description="Passenger feedback comment or complaint text")
    source: str = Field(default="Web Portal", description="Channel: Mobile App, Social Media, Email, Web Portal")
    mode: Optional[str] = Field(default=None, description="Train, Metro, Monorail, Bus")
    line_id: Optional[str] = Field(default=None, description="Line/Route ID if selected")
    station_id: Optional[str] = Field(default=None, description="Station/Stop ID if selected")
    rating: Optional[int] = Field(default=None, ge=1, le=5, description="Optional 1-5 passenger star rating")
    timestamp: Optional[datetime] = Field(default_factory=datetime.now)

class ExtractedEntities(BaseModel):
    stations: List[str] = []
    lines: List[str] = []
    directions: List[str] = []
    time_mentions: List[str] = []
    aspects: List[str] = []

class SentimentEmotionResult(BaseModel):
    sentiment: str  # Positive, Neutral, Negative
    polarity_score: float  # -1.0 to 1.0
    primary_emotion: str  # Anger, Frustration, Anxiety, Satisfaction, Gratitude, Neutral
    emotion_scores: Dict[str, float]

class FeedbackItem(BaseModel):
    id: str
    text: str
    source: str
    mode: str
    line_id: Optional[str] = None
    line_name: Optional[str] = None
    station_id: Optional[str] = None
    station_name: Optional[str] = None
    category: str
    category_confidence: float
    sentiment: str
    polarity_score: float
    primary_emotion: str
    emotion_scores: Dict[str, float]
    entities: ExtractedEntities
    rating: Optional[int] = None
    severity: str  # Low, Medium, High, Critical
    timestamp: str
    status: str = "Open"  # Open, In Review, Dispatched, Resolved
    assigned_department: Optional[str] = None
    resolution_notes: Optional[str] = None

class ActionRecommendation(BaseModel):
    id: str
    title: str
    category: str
    target_type: str  # Line, Station, Fleet, Policy
    target_id: Optional[str] = None
    target_name: str
    priority: str  # Critical, High, Medium, Low
    severity_score: float  # 0 to 100
    root_cause_summary: str
    recommended_action: str
    operational_department: str
    estimated_impact: str
    status: str = "Open"  # Open, Approved, Dispatched, Completed
    affected_passenger_count: int
    created_at: str
    is_custom: bool = False
    supervisor_notes: Optional[str] = None

class CreateCustomRecommendationRequest(BaseModel):
    title: str
    category: str
    target_name: str
    target_type: Optional[str] = "Station"
    priority: str = "High"
    root_cause_summary: str
    recommended_action: str
    operational_department: str
    estimated_impact: Optional[str] = "Immediate service improvement across affected corridor"
    affected_passenger_count: Optional[int] = 500
    supervisor_notes: Optional[str] = None

class UpdateRecommendationDetailsRequest(BaseModel):
    title: Optional[str] = None
    category: Optional[str] = None
    target_name: Optional[str] = None
    priority: Optional[str] = None
    root_cause_summary: Optional[str] = None
    recommended_action: Optional[str] = None
    operational_department: Optional[str] = None
    estimated_impact: Optional[str] = None
    status: Optional[str] = None
    supervisor_notes: Optional[str] = None

class AnalyticsSummary(BaseModel):
    total_feedback: int
    sentiment_distribution: Dict[str, int]
    emotion_distribution: Dict[str, int]
    category_distribution: Dict[str, int]
    csat_score: float  # 0 to 100
    net_sentiment_score: float  # -100 to 100
    open_tickets_count: int
    critical_alerts_count: int
    top_bottlenecks: List[Dict[str, Any]]
    sentiment_trend: List[Dict[str, Any]]
    channel_breakdown: Dict[str, int]

class LiveAnalysisRequest(BaseModel):
    text: str

class StatusUpdateRequest(BaseModel):
    status: str
    notes: Optional[str] = None
    department: Optional[str] = None
