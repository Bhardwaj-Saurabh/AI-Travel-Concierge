# app/tools/fx.py
from semantic_kernel.functions import kernel_function
import requests

class FxTools:
    @kernel_function(name="convert_fx", description="Convert currency from base to target using Frankfurter API")
    def convert_fx(self, amount: float, base: str, target: str):
        """
        Convert currency using Frankfurter API.

        Args:
            amount: Amount to convert
            base: Base currency code (e.g., 'USD')
            target: Target currency code (e.g., 'EUR')

        Returns:
            Dictionary containing conversion data with rates and converted amount
        """
        try:
            # Construct API URL with parameters
            base_url = f"https://api.frankfurter.app/latest"
            params = {
                "amount": amount,
                "from": base.upper(),
                "to": target.upper()
            }

            # Make API request
            response = requests.get(base_url, params=params, timeout=10)
            response.raise_for_status()

            # Return conversion data
            return response.json()

        except requests.exceptions.Timeout:
            return {"error": "Currency conversion API request timed out"}
        except requests.exceptions.RequestException as e:
            return {"error": f"Currency conversion API request failed: {str(e)}"}
        except Exception as e:
            return {"error": f"Unexpected error converting currency: {str(e)}"}