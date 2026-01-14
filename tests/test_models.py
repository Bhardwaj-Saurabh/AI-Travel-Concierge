"""
Unit tests for Pydantic models
"""

import pytest
from pydantic import ValidationError
from app.models import TripPlan, Weather, SearchResult, CardRecommendation, CurrencyInfo


class TestWeather:
    """Test cases for Weather model"""
    
    def test_valid_weather(self):
        """Test valid weather data"""
        weather = Weather(
            temperature_c=25.0,
            conditions="Clear",
            recommendation="Perfect weather for outdoor activities"
        )
        
        assert weather.temperature_c == 25.0
        assert weather.conditions == "Clear"
        assert weather.recommendation == "Perfect weather for outdoor activities"
    
    def test_invalid_weather_types(self):
        """Test that invalid types raise ValidationError"""
        with pytest.raises(ValidationError):
            Weather(
                temperature_c="not_a_number",
                conditions="Clear",
                recommendation="Good weather"
            )


class TestCardRecommendation:
    """Test cases for CardRecommendation model"""
    
    def test_valid_card_recommendation_required_only(self):
        """Test card recommendation with only required fields"""
        card = CardRecommendation(
            card="BankGold",
            benefit="4x dining worldwide",
            fx_fee="None",
            source="knowledge_base"
        )
        
        assert card.card == "BankGold"
        assert card.benefit == "4x dining worldwide"
        assert card.fx_fee == "None"
        assert card.source == "knowledge_base"
    
    def test_valid_card_recommendation_all_fields(self):
        """Test card recommendation with all fields"""
        card = CardRecommendation(
            card="BankGold",
            benefit="4x dining worldwide",
            fx_fee="None",
            source="knowledge_base"
        )
        
        assert card.card == "BankGold"
        assert card.benefit == "4x dining worldwide"
        assert card.fx_fee == "None"
        assert card.source == "knowledge_base"


class TestCurrencyInfo:
    """Test cases for CurrencyInfo model"""
    
    def test_valid_currency_info_required_only(self):
        """Test currency info with only required fields"""
        currency_info = CurrencyInfo(
            sample_meal_usd=100.0,
            points_earned=400
        )
        
        assert currency_info.sample_meal_usd == 100.0
        assert currency_info.points_earned == 400
        assert currency_info.usd_to_eur is None
        assert currency_info.sample_meal_eur is None
    
    def test_valid_currency_info_all_fields(self):
        """Test currency info with all fields"""
        currency_info = CurrencyInfo(
            usd_to_eur=0.8581,
            sample_meal_usd=100.0,
            sample_meal_eur=85.81,
            points_earned=400
        )
        
        assert currency_info.usd_to_eur == 0.8581
        assert currency_info.sample_meal_usd == 100.0
        assert currency_info.sample_meal_eur == 85.81
        assert currency_info.points_earned == 400



class TestTripPlan:
    """Test cases for TripPlan model"""
    
    def test_valid_trip_plan_minimal(self):
        """Test trip plan with minimal required fields"""
        plan = TripPlan(
            destination="Paris",
            travel_dates="2026-06-01 to 2026-06-08",
            card_recommendation=CardRecommendation(
                card="BankGold",
                benefit="4x dining worldwide",
                fx_fee="None",
                source="knowledge_base"
            ),
            currency_info=CurrencyInfo(
                usd_to_eur=0.8581,
                sample_meal_usd=100.0,
                sample_meal_eur=85.81,
                points_earned=400
            ),
            next_steps=["Book flights", "Reserve hotel"]
        )
        
        assert plan.destination == "Paris"
        assert plan.travel_dates == "2026-06-01 to 2026-06-08"
        assert plan.weather is None
        assert plan.results is None
        assert plan.citations is None
        assert len(plan.next_steps) == 2
    
    def test_valid_trip_plan_complete(self):
        """Test trip plan with all fields"""
        weather = Weather(
            temperature_c=25.0,
            conditions="Clear",
            recommendation="Perfect weather for sightseeing"
        )
        
        result = SearchResult(
            title="Test Result",
            snippet="Test snippet",
            url="https://example.com",
            price_range="$$",
            rating=4.5
        )
        
        plan = TripPlan(
            destination="Paris",
            travel_dates="2026-06-01 to 2026-06-08",
            weather=weather,
            results=[result],
            card_recommendation=CardRecommendation(
                card="BankGold",
                benefit="4x dining worldwide",
                fx_fee="None",
                source="knowledge_base"
            ),
            currency_info=CurrencyInfo(
                usd_to_eur=0.8581,
                sample_meal_usd=100.0,
                sample_meal_eur=85.81,
                points_earned=400
            ),
            citations=["https://example.com"],
            next_steps=["Book flights", "Reserve hotel"]
        )
        
        assert plan.destination == "Paris"
        assert plan.weather is not None
        assert plan.results is not None
        assert len(plan.results) == 1
        assert plan.citations is not None
        assert len(plan.citations) == 1
    
    def test_invalid_trip_plan_missing_required(self):
        """Test that missing required fields raise ValidationError"""
        with pytest.raises(ValidationError):
            TripPlan(
                destination="Paris"
                # Missing travel_dates, card_recommendation, currency_info, next_steps
            )
