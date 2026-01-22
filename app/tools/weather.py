# app/tools/weather.py
from semantic_kernel.functions import kernel_function
import requests

class WeatherTools:
    @kernel_function(name="get_weather", description="Get 7-day weather forecast from Open-Meteo API for given coordinates")
    def get_weather(self, lat: float, lon: float):
        """
        Get weather forecast for given coordinates using Open-Meteo API.

        Args:
            lat: Latitude coordinate
            lon: Longitude coordinate

        Returns:
            Dictionary containing weather forecast data with daily temperature and weather codes
        """
        try:
            # Construct API URL with parameters
            base_url = "https://api.open-meteo.com/v1/forecast"
            params = {
                "latitude": lat,
                "longitude": lon,
                "daily": "weathercode,temperature_2m_max,temperature_2m_min",
                "forecast_days": 7,
                "timezone": "UTC"
            }

            # Make API request
            response = requests.get(base_url, params=params, timeout=10)
            response.raise_for_status()

            # Return weather data
            return response.json()

        except requests.exceptions.Timeout:
            return {"error": "Weather API request timed out"}
        except requests.exceptions.RequestException as e:
            return {"error": f"Weather API request failed: {str(e)}"}
        except Exception as e:
            return {"error": f"Unexpected error getting weather: {str(e)}"}