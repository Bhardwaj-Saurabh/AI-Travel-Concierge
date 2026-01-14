# app/models.py
from pydantic import BaseModel
from typing import List, Optional


class Weather(BaseModel):
    temperature_c: Optional[float] = None
    conditions: Optional[str] = None
    recommendation: Optional[str] = None


class SearchResult(BaseModel):
    title: str
    snippet: Optional[str] = None
    url: Optional[str] = None
    price_range: Optional[str] = None
    rating: Optional[float] = None
    category: Optional[str] = None   # e.g., "restaurant", "hotel", "event", "general"


class CardRecommendation(BaseModel):
    card: str
    benefit: str
    fx_fee: str
    source: str


class CurrencyInfo(BaseModel):
    usd_to_eur: Optional[float] = None
    sample_meal_usd: Optional[float] = None
    sample_meal_eur: Optional[float] = None
    points_earned: Optional[int] = None


class TripPlan(BaseModel):
    destination: str
    travel_dates: str
    weather: Optional[Weather] = None
    results: Optional[List[SearchResult]] = None
    card_recommendation: CardRecommendation
    currency_info: CurrencyInfo
    citations: Optional[List[str]] = None
    next_steps: List[str]
