# app/synthesis.py
import json
from typing import Dict, Any, List, Optional
from app.models import TripPlan, Weather, SearchResult, CardRecommendation, CurrencyInfo


def _extract_weather_data(weather_result: Dict[str, Any]) -> Optional[Weather]:
    """Extract and format weather data."""
    if not weather_result or "error" in weather_result:
        return None

    try:
        daily = weather_result.get("daily", {})
        if not daily:
            return None

        # Get first day's weather
        temps_max = daily.get("temperature_2m_max", [])
        temps_min = daily.get("temperature_2m_min", [])
        weather_codes = daily.get("weathercode", [])

        if temps_max and temps_min:
            avg_temp = (temps_max[0] + temps_min[0]) / 2

            # Map weather code to conditions
            conditions_map = {
                0: "Clear sky",
                1: "Mainly clear",
                2: "Partly cloudy",
                3: "Overcast",
                45: "Foggy",
                48: "Foggy",
                51: "Light drizzle",
                61: "Slight rain",
                63: "Moderate rain",
                65: "Heavy rain",
                71: "Slight snow",
                80: "Rain showers"
            }

            code = weather_codes[0] if weather_codes else 0
            conditions = conditions_map.get(code, "Partly cloudy")

            # Generate recommendation
            if code in [0, 1, 2]:
                recommendation = "Great weather for sightseeing!"
            elif code in [51, 61, 80]:
                recommendation = "Bring an umbrella, rain expected"
            else:
                recommendation = "Check weather updates before heading out"

            return Weather(
                temperature_c=round(avg_temp, 1),
                conditions=conditions,
                recommendation=recommendation
            )
    except Exception:
        pass

    return None


def _extract_search_results(search_result: List[Dict[str, Any]]) -> Optional[List[SearchResult]]:
    """Extract and format search results."""
    if not search_result or "error" in search_result[0]:
        return None

    results = []
    for item in search_result[:5]:  # Limit to 5 results
        if "error" in item or "info" in item:
            continue

        results.append(SearchResult(
            title=item.get("title", ""),
            snippet=item.get("snippet", ""),
            url=item.get("url", ""),
            category="restaurant"  # Assume restaurant for now
        ))

    return results if results else None


def _extract_card_recommendation(card_result: Dict[str, Any]) -> CardRecommendation:
    """Extract and format card recommendation."""
    if not card_result or "error" in card_result:
        return CardRecommendation(
            card="No recommendation available",
            benefit="Unable to determine best card",
            fx_fee="Unknown",
            source="CardTools"
        )

    best = card_result.get("best", {})
    user_found = card_result.get("user_card_found", False)
    if user_found:
        source = f"Your card — {best.get('card', 'N/A')}"
    else:
        source = "CardTools - Rules-based recommendation"
    return CardRecommendation(
        card=best.get("card", "BankGold"),
        benefit=best.get("perk", "Standard rewards"),
        fx_fee=best.get("fx_fee", "Unknown"),
        source=source
    )


def _extract_currency_info(fx_result: Dict[str, Any], card_result: Dict[str, Any]) -> CurrencyInfo:
    """Extract and calculate currency information."""
    if not fx_result or "error" in fx_result:
        return CurrencyInfo(
            usd_to_eur=None,
            sample_meal_usd=100.0,
            sample_meal_eur=None,
            points_earned=None
        )

    try:
        # FX API format: {"amount": 100, "base": "USD", "rates": {"EUR": 85.16}}
        # The rates value is already the converted amount for the original amount
        original_amount = fx_result.get("amount", 100.0)
        rates = fx_result.get("rates", {})

        # Get the converted amount and calculate exchange rate
        converted_amount = None
        exchange_rate = None
        for currency, value in rates.items():
            converted_amount = value
            if original_amount > 0:
                exchange_rate = value / original_amount
            break

        # Sample meal cost
        sample_meal_usd = 100.0
        # If original amount equals sample, use converted_amount directly
        if original_amount == sample_meal_usd:
            sample_meal_local = converted_amount
        elif exchange_rate:
            sample_meal_local = sample_meal_usd * exchange_rate
        else:
            sample_meal_local = None

        # Calculate points earned from card
        points_earned = None
        if card_result and "best" in card_result:
            perk = card_result["best"].get("perk", "1x")
            if "x" in perk:
                try:
                    multiplier = float(perk.split("x")[0])
                    points_earned = int(sample_meal_usd * multiplier)
                except ValueError:
                    points_earned = 100

        return CurrencyInfo(
            usd_to_eur=round(exchange_rate, 4) if exchange_rate else None,
            sample_meal_usd=sample_meal_usd,
            sample_meal_eur=round(sample_meal_local, 2) if sample_meal_local else None,
            points_earned=points_earned
        )
    except Exception:
        return CurrencyInfo(
            usd_to_eur=None,
            sample_meal_usd=100.0,
            sample_meal_eur=None,
            points_earned=None
        )


def _generate_citations(tool_results: Dict[str, Any]) -> List[str]:
    """Generate citations from tool results."""
    citations = []

    # Add search result URLs
    if "search" in tool_results and isinstance(tool_results["search"], list):
        for result in tool_results["search"][:3]:
            if "url" in result and result["url"]:
                citations.append(result["url"])

    # Add API sources
    if "weather" in tool_results and tool_results["weather"]:
        citations.append("https://open-meteo.com - Weather data")

    if "fx" in tool_results and tool_results["fx"]:
        citations.append("https://www.frankfurter.app - Currency rates")

    return citations if citations else ["No external sources cited"]


def _generate_next_steps(requirements: Dict[str, str], weather: Optional[Weather]) -> List[str]:
    """Generate next steps for the traveler."""
    steps = []

    destination = requirements.get("destination", "your destination")
    steps.append(f"Book your flights to {destination}")
    steps.append(f"Reserve accommodations in {destination}")

    if weather:
        if "rain" in weather.conditions.lower():
            steps.append("Pack rain gear and umbrella")
        if weather.temperature_c and weather.temperature_c > 25:
            steps.append("Pack light, breathable clothing for warm weather")
        elif weather.temperature_c and weather.temperature_c < 15:
            steps.append("Pack warm clothing and layers")

    steps.append("Research local attractions and create an itinerary")
    steps.append("Notify your credit card company of travel plans")

    return steps


def synthesize_to_tripplan(tool_results: Dict[str, Any], requirements: Dict[str, str]) -> str:
    """
    Synthesize tool results into a comprehensive travel plan.

    Args:
        tool_results: Dictionary containing results from various tools (weather, fx, search, card)
        requirements: Dictionary containing destination, dates, and card info

    Returns:
        JSON string representing the complete TripPlan
    """
    try:
        # Extract and format data from each tool
        weather = _extract_weather_data(tool_results.get("weather", {}))
        results = _extract_search_results(tool_results.get("search", []))
        card_recommendation = _extract_card_recommendation(tool_results.get("card", {}))
        currency_info = _extract_currency_info(tool_results.get("fx", {}), tool_results.get("card", {}))
        citations = _generate_citations(tool_results)
        next_steps = _generate_next_steps(requirements, weather)

        # Create TripPlan model
        trip_plan = TripPlan(
            destination=requirements.get("destination", "Unknown"),
            travel_dates=requirements.get("dates", "Unknown"),
            weather=weather,
            results=results,
            card_recommendation=card_recommendation,
            currency_info=currency_info,
            citations=citations,
            next_steps=next_steps
        )

        # Convert to JSON
        return trip_plan.model_dump_json(indent=2, exclude_none=False)

    except Exception as e:
        # Return error as JSON
        return json.dumps({"error": f"Error synthesizing trip plan: {str(e)}"}, indent=2)