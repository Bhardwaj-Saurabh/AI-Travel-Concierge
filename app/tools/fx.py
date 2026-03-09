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
        # Print tool invocation for evidence
        print(f"\n{'='*60}")
        print(f"🔧 TOOL INVOCATION: convert_fx")
        print(f"{'='*60}")
        print(f"   Amount: {amount}")
        print(f"   Base Currency: {base.upper()}")
        print(f"   Target Currency: {target.upper()}")
        print(f"   API: Frankfurter (https://api.frankfurter.app)")

        # Construct API URL with parameters
        base_url = "https://api.frankfurter.app/latest"
        params = {
            "amount": amount,
            "from": base.upper(),
            "to": target.upper()
        }

        try:
            # Make API request
            response = requests.get(base_url, params=params, timeout=10)
            response.raise_for_status()

            # Parse and display results for evidence
            data = response.json()
            print(f"   ✅ API Response received")
            print(f"   💱 Exchange Rate: 1 {base.upper()} = {data.get('rates', {}).get(target.upper(), 'N/A')} {target.upper()}")
            print(f"   📅 Date: {data.get('date', 'N/A')}")

            return data
        except Exception as e:
            print(f"   ❌ Error: {e}")
            return {"error": f"Unexpected error: {str(e)}"}