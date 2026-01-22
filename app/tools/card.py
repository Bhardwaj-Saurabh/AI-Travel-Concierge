# app/tools/card.py
from semantic_kernel.functions import kernel_function

class CardTools:
    """Credit card recommendation tool based on MCC codes and country."""

    # Card database with benefits and FX fees
    CARDS = {
        "Chase Sapphire Reserve": {
            "perks": {
                "3000-3999": "3x points on travel and dining",  # Airlines
                "4000-4999": "3x points on travel and dining",  # Hotels
                "5812": "3x points on travel and dining",  # Restaurants
                "default": "1x points on all purchases"
            },
            "fx_fee": 0.0,
            "annual_fee": 550
        },
        "Amex Platinum": {
            "perks": {
                "3000-3999": "5x points on flights booked directly with airlines",
                "4000-4999": "5x points on hotels booked through Amex Travel",
                "default": "1x points on all purchases"
            },
            "fx_fee": 0.0,
            "annual_fee": 695
        },
        "Capital One Venture X": {
            "perks": {
                "3000-3999": "2x miles on all purchases",
                "4000-4999": "10x miles on hotels and rental cars booked through Capital One Travel",
                "5812": "2x miles on all purchases",
                "default": "2x miles on all purchases"
            },
            "fx_fee": 0.0,
            "annual_fee": 395
        },
        "BankGold": {
            "perks": {
                "default": "1.5x points on all purchases"
            },
            "fx_fee": 0.03,
            "annual_fee": 0
        }
    }

    def _get_mcc_category(self, mcc: str) -> str:
        """Categorize MCC code for benefit matching."""
        try:
            mcc_code = int(mcc)
            if 3000 <= mcc_code <= 3999:
                return "3000-3999"  # Airlines
            elif 4000 <= mcc_code <= 4999:
                return "4000-4999"  # Hotels
            elif mcc_code == 5812:
                return "5812"  # Restaurants
            else:
                return "default"
        except ValueError:
            return "default"

    def _calculate_value(self, card_name: str, card_data: dict, mcc_category: str, amount: float, is_foreign: bool) -> float:
        """Calculate total value including rewards and fees."""
        # Get perk multiplier
        perk = card_data["perks"].get(mcc_category, card_data["perks"]["default"])

        # Extract multiplier from perk string (e.g., "5x points" -> 5.0)
        multiplier = 1.0
        if "x" in perk:
            try:
                multiplier = float(perk.split("x")[0])
            except ValueError:
                multiplier = 1.0

        # Calculate rewards (assuming $1 in rewards per 100 points/miles)
        rewards_value = (amount * multiplier) / 100

        # Calculate FX fee if applicable
        fx_fee = amount * card_data["fx_fee"] if is_foreign else 0.0

        # Net value (rewards minus fees)
        net_value = rewards_value - fx_fee

        return net_value

    @kernel_function(name="recommend_card", description="Recommend best credit card based on MCC code, amount, and country")
    def recommend_card(self, mcc: str, amount: float, country: str):
        """
        Recommend credit card based on merchant category code and country.

        Args:
            mcc: Merchant Category Code (e.g., "5812" for restaurants)
            amount: Transaction amount in USD
            country: Country code (e.g., "US", "FR")

        Returns:
            Dictionary containing best card recommendation with perks and FX fees
        """
        try:
            # Determine if this is a foreign transaction
            is_foreign = country.upper() != "US"

            # Get MCC category for benefit matching
            mcc_category = self._get_mcc_category(mcc)

            # Evaluate each card
            best_card = None
            best_value = -float('inf')
            best_perk = ""
            best_fx_fee = 0.0

            for card_name, card_data in self.CARDS.items():
                value = self._calculate_value(card_name, card_data, mcc_category, amount, is_foreign)

                if value > best_value:
                    best_value = value
                    best_card = card_name
                    best_perk = card_data["perks"].get(mcc_category, card_data["perks"]["default"])
                    best_fx_fee = card_data["fx_fee"]

            # Generate explanation
            fx_fee_text = f"{best_fx_fee * 100}% FX fee" if is_foreign and best_fx_fee > 0 else "No FX fees"
            explanation = f"{best_card} offers {best_perk} for this transaction. {fx_fee_text}."

            return {
                "best": {
                    "card": best_card,
                    "perk": best_perk,
                    "fx_fee": fx_fee_text,
                    "estimated_value": f"${best_value:.2f}"
                },
                "explanation": explanation,
                "mcc": mcc,
                "category": mcc_category
            }

        except Exception as e:
            return {"error": f"Error recommending card: {str(e)}"}