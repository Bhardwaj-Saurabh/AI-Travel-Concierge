# app/main.py - Travel Concierge Agent with Semantic Kernel
"""
Travel Concierge Agent with Semantic Kernel

This agent demonstrates:
- Semantic Kernel integration with Azure OpenAI and Cosmos DB
- Tool orchestration and enhanced state management
- Memory systems (short-term and long-term)
- RAG with knowledge base
- Granular state machine with error handling (AWAITING_USER_CLARIFICATION, HANDLING_TOOL_ERROR, etc.)
- 7 tool plugins: Weather, FX, Search, Card, Knowledge, Calendar, Translation
- Enhanced LLM Judge with correction generation and debugging capabilities
"""

import os
import json
import sys
import asyncio
from semantic_kernel import Kernel
from semantic_kernel.connectors.ai.open_ai import AzureChatCompletion, AzureTextEmbedding
from app.synthesis import synthesize_to_tripplan
from app.state import AgentState
from app.utils.config import validate_all_config
from app.utils.logger import setup_logger
from app.tools.weather import WeatherTools
from app.tools.fx import FxTools
from app.tools.search import SearchTools
from app.tools.card import CardTools
from app.tools.knowledge import KnowledgeTools
from app.tools.calendar import CalendarTools
from app.tools.translation import TranslationTools

# Set up logging
logger = setup_logger("travel_agent")

async def extract_requirements_from_input_async(user_input: str, kernel: Kernel) -> dict:
    """
    Extract travel requirements from natural language input using LLM.

    Args:
        user_input: Natural language input from user
        kernel: Configured Semantic Kernel instance

    Returns:
        Dictionary containing destination, dates, and card information
    """
    extraction_prompt = f"""Extract the following information from the user's travel request.
Return the information in JSON format with these exact keys: destination, dates, card.

Rules:
- If information is not provided, use "Not specified"
- For dates, extract the date range in format "YYYY-MM-DD to YYYY-MM-DD" if possible
- For destination, extract the city/country name
- For card, extract the credit card name/type mentioned

User input: {user_input}

Return ONLY the JSON object, no other text:"""

    try:
        # Get chat service
        chat_service = kernel.get_service(type=AzureChatCompletion)

        # Create chat history
        from semantic_kernel.contents import ChatHistory
        history = ChatHistory()
        history.add_system_message("You are a helpful assistant that extracts structured data from text. Always respond with valid JSON only.")
        history.add_user_message(extraction_prompt)

        # Get response
        response = await chat_service.get_chat_message_content(
            chat_history=history,
            settings=kernel.get_prompt_execution_settings_from_service_id(chat_service.service_id)
        )

        # Parse JSON response
        import json
        import re

        # Extract JSON from response (handle potential markdown formatting)
        content = str(response)
        json_match = re.search(r'\{[^{}]*\}', content)

        if json_match:
            extracted = json.loads(json_match.group())
            return {
                "destination": extracted.get("destination", "Not specified"),
                "dates": extracted.get("dates", "Not specified"),
                "card": extracted.get("card", "Not specified")
            }
        else:
            raise ValueError("Could not parse JSON from LLM response")

    except Exception as e:
        logger.error(f"Error extracting requirements: {e}")
        # Fallback to simple parsing
        return {
            "destination": "Paris",  # Default fallback
            "dates": "Not specified",
            "card": "Not specified"
        }

def extract_requirements_from_input(user_input: str) -> dict:
    """
    Synchronous wrapper for extract_requirements_from_input_async.

    Extracts travel requirements from natural language input.
    """
    try:
        # Create kernel for extraction
        kernel = create_kernel()

        # Run async extraction
        result = asyncio.run(extract_requirements_from_input_async(user_input, kernel))
        return result

    except Exception as e:
        logger.error(f"Error in requirement extraction: {e}")
        return {
            "destination": "Not specified",
            "dates": "Not specified",
            "card": "Not specified"
        }

def create_kernel() -> Kernel:
    """
    Create and configure the Semantic Kernel instance.

    Sets up:
    - Azure OpenAI chat completion service (GPT-4o-mini)
    - Azure OpenAI text embedding service (text-embedding-3-small)
    - 7 Tool plugins:
      1. WeatherTools - Get weather forecasts
      2. FxTools - Currency conversion
      3. SearchTools - Web search via Bing
      4. CardTools - Credit card recommendations
      5. KnowledgeTools - RAG-based knowledge retrieval
      6. CalendarTools - Availability checking and event scheduling
      7. TranslationTools - Multi-language translation
    - Kernel filters for logging and telemetry
    """
    # Create kernel instance
    kernel = Kernel()

    # Get configuration
    config = validate_all_config()
    azure_config = config["azure"]

    # Add Azure OpenAI Chat Completion service
    chat_service = AzureChatCompletion(
        deployment_name=azure_config["AZURE_OPENAI_CHAT_DEPLOYMENT"],
        endpoint=azure_config["AZURE_OPENAI_ENDPOINT"],
        api_key=azure_config["AZURE_OPENAI_KEY"],
        api_version=azure_config["AZURE_OPENAI_API_VERSION"]
    )
    kernel.add_service(chat_service)
    logger.info(f"Added chat service: {azure_config['AZURE_OPENAI_CHAT_DEPLOYMENT']}")

    # Add Azure OpenAI Embedding service
    embedding_service = AzureTextEmbedding(
        deployment_name=azure_config["AZURE_OPENAI_EMBED_DEPLOYMENT"],
        endpoint=azure_config["AZURE_OPENAI_ENDPOINT"],
        api_key=azure_config["AZURE_OPENAI_KEY"],
        api_version=azure_config["AZURE_OPENAI_API_VERSION"]
    )
    kernel.add_service(embedding_service)
    logger.info(f"Added embedding service: {azure_config['AZURE_OPENAI_EMBED_DEPLOYMENT']}")

    # Register tool plugins
    kernel.add_plugin(WeatherTools(), plugin_name="WeatherTools")
    logger.info("Registered WeatherTools plugin")

    kernel.add_plugin(FxTools(), plugin_name="FxTools")
    logger.info("Registered FxTools plugin")

    kernel.add_plugin(SearchTools(), plugin_name="SearchTools")
    logger.info("Registered SearchTools plugin")

    kernel.add_plugin(CardTools(), plugin_name="CardTools")
    logger.info("Registered CardTools plugin")

    kernel.add_plugin(KnowledgeTools(), plugin_name="KnowledgeTools")
    logger.info("Registered KnowledgeTools plugin")

    # Register enhanced tools (Calendar and Translation)
    kernel.add_plugin(CalendarTools(), plugin_name="CalendarTools")
    logger.info("Registered CalendarTools plugin")

    kernel.add_plugin(TranslationTools(), plugin_name="TranslationTools")
    logger.info("Registered TranslationTools plugin")

    logger.info("Kernel created and configured successfully with 7 tool plugins")
    return kernel

def run_request(user_input: str) -> str:
    """
    Main entry point for the travel agent.

    Orchestrates the complete agent workflow:
    1. Extract requirements from user input
    2. Create and configure the kernel
    3. Initialize agent state
    4. Execute tool plugins (weather, FX, search, card)
    5. Synthesize results into comprehensive travel plan
    6. Return formatted JSON

    Args:
        user_input: Natural language travel request from user

    Returns:
        JSON string containing the complete TripPlan
    """
    try:
        logger.info(f"Processing travel request: {user_input}")

        # Phase 1: Extract requirements from user input
        logger.info("Phase 1: Extracting requirements...")
        requirements = extract_requirements_from_input(user_input)
        logger.info(f"Extracted requirements: {requirements}")

        # Phase 2: Create and configure kernel
        logger.info("Phase 2: Creating kernel...")
        kernel = create_kernel()

        # Phase 3: Initialize agent state
        logger.info("Phase 3: Initializing agent state...")
        state = AgentState()
        state.destination = requirements["destination"]
        state.dates = requirements["dates"]
        state.card = requirements["card"]
        state.advance()  # Move to ClarifyRequirements

        # Phase 4: Plan which tools to execute
        logger.info("Phase 4: Planning tool execution...")
        state.advance()  # Move to PlanTools

        # Determine which tools to call based on requirements
        tools_to_call = []
        if state.destination and state.destination != "Not specified":
            tools_to_call.extend(["weather", "fx", "search", "card"])
        else:
            logger.warning("No destination specified, limited tool execution")

        state.tools_called = tools_to_call
        state.advance()  # Move to ExecuteTools

        # Phase 5: Execute tools and collect results
        logger.info(f"Phase 5: Executing tools: {tools_to_call}...")
        tool_results = {}

        # Get tool instances from kernel
        weather_tool = WeatherTools()
        fx_tool = FxTools()
        search_tool = SearchTools()
        card_tool = CardTools()

        # Execute weather tool (need lat/lon - using placeholder coordinates for Paris)
        # In production, you'd geocode the destination first
        if "weather" in tools_to_call:
            logger.info("Calling weather tool...")
            # Example coordinates for Paris: 48.8566, 2.3522
            # In production, use a geocoding service to get actual coordinates
            tool_results["weather"] = weather_tool.get_weather(48.8566, 2.3522)

        # Execute FX tool
        if "fx" in tools_to_call:
            logger.info("Calling FX tool...")
            # Convert 100 USD to EUR as an example
            tool_results["fx"] = fx_tool.convert_fx(100.0, "USD", "EUR")

        # Execute search tool
        if "search" in tools_to_call:
            logger.info("Calling search tool...")
            search_query = f"best restaurants in {state.destination}"
            tool_results["search"] = search_tool.web_search(search_query, max_results=5)

        # Execute card tool
        if "card" in tools_to_call:
            logger.info("Calling card tool...")
            # MCC 5812 = Restaurants, assume foreign transaction
            tool_results["card"] = card_tool.recommend_card("5812", 100.0, "FR")

        logger.info("Tool execution completed")
        state.advance()  # Move to Synthesize

        # Phase 6: Synthesize results into trip plan
        logger.info("Phase 6: Synthesizing trip plan...")
        trip_plan_json = synthesize_to_tripplan(tool_results, requirements)

        state.advance()  # Move to Done
        logger.info("Travel plan generation completed successfully")

        return trip_plan_json

    except Exception as e:
        logger.error(f"Error in run_request: {e}", exc_info=True)
        return json.dumps({"error": str(e)}, indent=2)

def main():
    """Main entry point for command line usage."""
    try:
        # Validate configuration
        config = validate_all_config()
        logger.info("Configuration validated successfully")
        
        # Example usage
        user_input = "I want to go to Paris from 2026-06-01 to 2026-06-08 with my BankGold card"
        result = run_request(user_input)
        print("Travel Plan:")
        print(result)
        
    except Exception as e:
        logger.error(f"Error in main: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()