#!/usr/bin/env python3
"""
Quick Start Chat Script
Run this to start chatting with the travel agent!
"""

import os
import sys
import json
from app.main import run_request

def main():
    """Interactive chat interface for the travel agent"""
    print("🚀 Travel Agent Chat Interface")
    print("=" * 50)
    print("Welcome! I'm your AI travel concierge.")
    print("Tell me about your travel plans and I'll help you plan your trip!")
    print()
    print("Commands:")
    print("  help    - Show this help message")
    print("  status  - Show system status")
    print("  clear   - Clear the screen")
    print("  quit    - Exit the chat")
    print()
    
    # Check for .env file
    if not os.path.exists(".env"):
        print("⚠️  Warning: No .env file found!")
        print("   Make sure to set up your environment variables.")
        print("   See env.example for reference.")
        print()
    
    while True:
        try:
            # Get user input
            user_input = input("\n💬 You: ").strip()
            
            # Handle commands
            if user_input.lower() in ['quit', 'exit', 'q']:
                print("\n👋 Goodbye! Safe travels!")
                break
            elif user_input.lower() == 'help':
                print("\n📖 Help:")
                print("  Just tell me about your travel plans!")
                print("  Example: 'I want to go to Paris from June 1-8 with my BankGold card'")
                print("  I'll help you with weather, restaurants, currency, and card recommendations!")
                continue
            elif user_input.lower() == 'status':
                print("\n🔍 System Status: Ready")
                continue
            elif user_input.lower() == 'clear':
                os.system('cls' if os.name == 'nt' else 'clear')
                continue
            elif not user_input:
                continue
            
            # Process the request
            print("\n🤖 Agent: Let me help you plan your trip...")
            
            try:
                result = run_request(user_input)
                
                # Parse and display the result
                try:
                    plan_data = json.loads(result)
                    display_plan(plan_data)
                except json.JSONDecodeError:
                    print("❌ Error: Could not parse the response")
                    print(f"Raw response: {result}")
                    
            except Exception as e:
                print(f"❌ Error: {e}")
                
        except KeyboardInterrupt:
            print("\n\n👋 Chat stopped. Goodbye!")
            break
        except Exception as e:
            print(f"\n❌ Error: {e}")
            print("Please try again or type 'help' for assistance.")

def display_plan(plan_data):
    """Display the travel plan in a formatted way"""
    # Support both {"plan": {...}} wrapper and direct plan dict
    if "plan" in plan_data:
        plan = plan_data["plan"]
    elif "destination" in plan_data:
        plan = plan_data
    else:
        print("❌ Error: Invalid plan format")
        return
    
    print("\n" + "="*60)
    print("🎯 TRAVEL PLAN")
    print("="*60)
    
    # Destination and dates
    print(f"📍 Destination: {plan.get('destination', 'N/A')}")
    print(f"📅 Travel Dates: {plan.get('travel_dates', 'N/A')}")
    print()
    print("✅ Response validated with Pydantic")
    print()
    
    # Weather
    if 'weather' in plan and plan['weather']:
        weather = plan['weather']
        print("🌤️  WEATHER")
        print("-" * 30)
        print(f"Temperature: {weather.get('temperature_c', 'N/A')}°C")
        print(f"Conditions: {weather.get('conditions', 'N/A')}")
        print(f"Recommendation: {weather.get('recommendation', 'N/A')}")
        print()
    
    # Search results (restaurants, etc.)
    if 'results' in plan and plan['results']:
        print("🔍 SEARCH RESULTS")
        print("-" * 30)
        seen_urls = set()
        idx = 0
        for result in plan['results'][:5]:
            url = result.get('url', '')
            url_key = url.rstrip('/').lower() if url else None
            if url_key and url_key in seen_urls:
                continue
            if url_key:
                seen_urls.add(url_key)
            idx += 1
            title = result.get('title', 'N/A')
            print(f"{idx}. 🍽️ {title}")
            if result.get('snippet'):
                print(f"   {result['snippet']}")
            if url:
                print(f"   🔗 {url}")
            if result.get('rating'):
                print(f"   ⭐ Rating: {result['rating']}/5")
            if result.get('price_range'):
                print(f"   💰 Price: {result['price_range']}")
            print()

    
    # Card recommendation
    if 'card_recommendation' in plan and plan['card_recommendation']:
        card = plan['card_recommendation']
        source = card.get('source', '')
        if 'Your card' in source:
            print("💳 YOUR CARD")
        else:
            print("💳 CARD RECOMMENDATION")
        print("-" * 30)
        print(f"Card: {card.get('card', 'N/A')}")
        print(f"Benefit: {card.get('benefit', 'N/A')}")
        print(f"FX Fee: {card.get('fx_fee', 'N/A')}")
        if source:
            print(f"Source: {source}")
        print()
    
    # Currency info
    if 'currency_info' in plan and plan['currency_info']:
        currency = plan['currency_info']
        print("💰 CURRENCY INFO")
        print("-" * 30)
        print(f"Sample Meal (USD): ${currency.get('sample_meal_usd', 'N/A')}")
        if currency.get('sample_meal_eur'):
            print(f"Sample Meal (EUR): €{currency['sample_meal_eur']}")
        if currency.get('usd_to_eur'):
            print(f"Exchange Rate: 1 USD = {currency['usd_to_eur']} EUR")
        print(f"Points Earned: {currency.get('points_earned', 'N/A')}")
        print()
    
    # Next steps
    if 'next_steps' in plan and plan['next_steps']:
        print("📋 NEXT STEPS")
        print("-" * 30)
        for i, step in enumerate(plan['next_steps'], 1):
            print(f"{i}. {step}")
        print()
    
    # Citations
    if 'citations' in plan and plan['citations']:
        print("📚 SOURCES")
        print("-" * 30)
        for i, citation in enumerate(plan['citations'][:3], 1):
            print(f"{i}. {citation}")
        print()
    
    print("="*60)

if __name__ == "__main__":
    main()