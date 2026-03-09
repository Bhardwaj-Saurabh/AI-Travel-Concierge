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
        # Print tool invocation for evidence
        print(f"\n{'='*60}")
        print(f"🔧 TOOL INVOCATION: get_weather")
        print(f"{'='*60}")
        print(f"   Latitude: {lat}")
        print(f"   Longitude: {lon}")
        print(f"   API: Open-Meteo (https://api.open-meteo.com)")

        # Construct API URL with parameters
        base_url = "https://api.open-meteo.com/v1/forecast"
        params = {
            "latitude": lat,
            "longitude": lon,
            "daily": "weathercode,temperature_2m_max,temperature_2m_min",
            "forecast_days": 7,
            "timezone": "UTC"
        }

        try:
            # Make API request
            response = requests.get(base_url, params=params, timeout=10)
            response.raise_for_status()

            # Parse and display results for evidence
            data = response.json()
            print(f"   ✅ API Response received")
            if 'daily' in data:
                temps = data['daily'].get('temperature_2m_max', [])
                print(f"   🌡️  Temperature forecast (max): {temps[:3]}...")
            print(f"   📍 Timezone: {data.get('timezone', 'N/A')}")

            return data
        except Exception as e:
            print(f"   ❌ Error: {e}")
            return {"error": f"Unexpected error: {str(e)}"}