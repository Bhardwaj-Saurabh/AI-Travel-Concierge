# app/tools/translation.py
"""
Translation Tools - Multi-language support for international travel.

This tool provides translation capabilities for travel planning,
allowing the agent to translate common travel phrases, menus, signs,
and communications into the user's preferred language.
"""

from typing import Dict, Any, List
import os
import requests
from semantic_kernel.functions import kernel_function
from app.utils.logger import setup_logger

logger = setup_logger("translation_tool")


class TranslationTools:
    """
    Translation service integration for multi-language travel support.

    This tool integrates with Azure Translator or similar translation APIs
    to provide real-time translation capabilities for travelers.
    """

    # Common travel phrases by category
    TRAVEL_PHRASES = {
        "greetings": [
            "Hello", "Good morning", "Good evening", "Goodbye",
            "Please", "Thank you", "You're welcome", "Excuse me"
        ],
        "directions": [
            "Where is the hotel?", "How do I get to the airport?",
            "Where is the nearest train station?", "Is this the right way?",
            "How far is it?", "Can you show me on the map?"
        ],
        "restaurant": [
            "I would like to order", "Can I see the menu?",
            "What do you recommend?", "I am vegetarian",
            "Check please", "This is delicious", "No spicy food"
        ],
        "emergency": [
            "I need help", "Where is the hospital?", "Call the police",
            "I lost my passport", "I need a doctor", "Emergency"
        ],
        "shopping": [
            "How much does this cost?", "Can I try this on?",
            "Do you accept credit cards?", "I'm just looking",
            "Can I get a receipt?", "Is this tax free?"
        ],
        "hotel": [
            "I have a reservation", "What time is check-in?",
            "Can I have extra towels?", "The WiFi is not working",
            "I need a wake-up call", "Where is breakfast served?"
        ]
    }

    def __init__(self):
        """Initialize translation tool."""
        self.translator_key = os.environ.get("AZURE_TRANSLATOR_KEY")
        self.translator_endpoint = os.environ.get(
            "AZURE_TRANSLATOR_ENDPOINT",
            "https://api.cognitive.microsofttranslator.com"
        )
        self.translator_region = os.environ.get("AZURE_TRANSLATOR_REGION", "global")
        logger.info("Initialized TranslationTools")

    @kernel_function(
        name="translate_text",
        description="Translate text from one language to another using Azure Translator. Supports 100+ languages."
    )
    def translate_text(
        self,
        text: str,
        target_language: str,
        source_language: str = "en"
    ) -> Dict[str, Any]:
        """
        Translate text between languages.

        Args:
            text: Text to translate
            target_language: Target language code (e.g., 'fr', 'es', 'ja')
            source_language: Source language code (default: 'en' for English)

        Returns:
            Dictionary containing translated text and metadata
        """
        try:
            logger.info(f"Translating text from {source_language} to {target_language}")

            # If no API key, use mock translation for demonstration
            if not self.translator_key:
                logger.warning("No Azure Translator API key found, using mock translation")
                return self._mock_translate(text, target_language, source_language)

            # Call Azure Translator API
            endpoint = f"{self.translator_endpoint}/translate"
            params = {
                "api-version": "3.0",
                "from": source_language,
                "to": target_language
            }
            headers = {
                "Ocp-Apim-Subscription-Key": self.translator_key,
                "Ocp-Apim-Subscription-Region": self.translator_region,
                "Content-Type": "application/json"
            }
            body = [{"text": text}]

            response = requests.post(
                endpoint,
                params=params,
                headers=headers,
                json=body,
                timeout=10
            )
            response.raise_for_status()

            result = response.json()
            translated_text = result[0]["translations"][0]["text"]

            return {
                "original_text": text,
                "translated_text": translated_text,
                "source_language": source_language,
                "target_language": target_language,
                "detected_language": result[0].get("detectedLanguage", {}).get("language"),
                "service": "azure_translator"
            }

        except requests.exceptions.RequestException as e:
            logger.error(f"Translation API error: {e}")
            return self._mock_translate(text, target_language, source_language)
        except Exception as e:
            logger.error(f"Error during translation: {e}", exc_info=True)
            return {"error": str(e)}

    @kernel_function(
        name="get_travel_phrases",
        description="Get common travel phrases translated into the target language. Returns phrasebook for greetings, directions, restaurants, emergencies, etc."
    )
    def get_travel_phrases(
        self,
        target_language: str,
        category: str = "all"
    ) -> Dict[str, Any]:
        """
        Get a phrasebook of common travel phrases in the target language.

        Args:
            target_language: Target language code (e.g., 'fr', 'es', 'ja')
            category: Phrase category ('greetings', 'directions', 'restaurant',
                     'emergency', 'shopping', 'hotel', or 'all')

        Returns:
            Dictionary containing translated phrases organized by category
        """
        try:
            logger.info(f"Generating travel phrasebook for {target_language}")

            # Determine which categories to translate
            if category == "all":
                categories_to_translate = self.TRAVEL_PHRASES.keys()
            elif category in self.TRAVEL_PHRASES:
                categories_to_translate = [category]
            else:
                return {
                    "error": f"Unknown category: {category}",
                    "available_categories": list(self.TRAVEL_PHRASES.keys())
                }

            # Translate phrases in each category
            phrasebook = {}
            for cat in categories_to_translate:
                phrases = self.TRAVEL_PHRASES[cat]
                translated_phrases = []

                for phrase in phrases:
                    translation_result = self.translate_text(phrase, target_language, "en")
                    if "translated_text" in translation_result:
                        translated_phrases.append({
                            "english": phrase,
                            "translated": translation_result["translated_text"],
                            "pronunciation": self._get_pronunciation_hint(
                                translation_result["translated_text"],
                                target_language
                            )
                        })

                phrasebook[cat] = translated_phrases

            result = {
                "target_language": target_language,
                "categories": list(phrasebook.keys()),
                "phrases": phrasebook,
                "total_phrases": sum(len(v) for v in phrasebook.values()),
                "usage_tip": f"Learn these phrases before traveling to {self._get_language_name(target_language)}-speaking regions."
            }

            logger.info(f"Phrasebook generated with {result['total_phrases']} phrases")
            return result

        except Exception as e:
            logger.error(f"Error generating phrasebook: {e}", exc_info=True)
            return {"error": str(e)}

    @kernel_function(
        name="detect_language",
        description="Detect the language of a given text. Useful when user provides text in an unknown language."
    )
    def detect_language(self, text: str) -> Dict[str, Any]:
        """
        Detect the language of the input text.

        Args:
            text: Text to analyze

        Returns:
            Dictionary containing detected language and confidence score
        """
        try:
            logger.info(f"Detecting language for text: {text[:50]}...")

            # If no API key, use simple heuristics
            if not self.translator_key:
                return self._mock_detect_language(text)

            # Call Azure Translator API for language detection
            endpoint = f"{self.translator_endpoint}/detect"
            params = {"api-version": "3.0"}
            headers = {
                "Ocp-Apim-Subscription-Key": self.translator_key,
                "Ocp-Apim-Subscription-Region": self.translator_region,
                "Content-Type": "application/json"
            }
            body = [{"text": text}]

            response = requests.post(
                endpoint,
                params=params,
                headers=headers,
                json=body,
                timeout=10
            )
            response.raise_for_status()

            result = response.json()[0]

            return {
                "text": text,
                "language_code": result["language"],
                "language_name": self._get_language_name(result["language"]),
                "confidence": result["score"],
                "is_translation_supported": result.get("isTranslationSupported", True),
                "alternatives": result.get("alternatives", [])
            }

        except Exception as e:
            logger.error(f"Error detecting language: {e}", exc_info=True)
            return self._mock_detect_language(text)

    def _mock_translate(
        self,
        text: str,
        target_language: str,
        source_language: str
    ) -> Dict[str, Any]:
        """
        Provide mock translations for demonstration purposes.
        Returns informative message about what would be translated.
        """
        logger.info("Using mock translation service")

        # Simple mock translations for common languages
        mock_translations = {
            "fr": f"[FR: {text}]",  # French
            "es": f"[ES: {text}]",  # Spanish
            "de": f"[DE: {text}]",  # German
            "it": f"[IT: {text}]",  # Italian
            "ja": f"[JA: {text}]",  # Japanese
            "zh": f"[ZH: {text}]",  # Chinese
        }

        translated = mock_translations.get(target_language, f"[{target_language.upper()}: {text}]")

        return {
            "original_text": text,
            "translated_text": translated,
            "source_language": source_language,
            "target_language": target_language,
            "service": "mock_translator",
            "note": "Using mock translation. Configure AZURE_TRANSLATOR_KEY for real translations."
        }

    def _mock_detect_language(self, text: str) -> Dict[str, Any]:
        """Mock language detection based on simple heuristics."""
        # Very basic heuristics (in production, use proper API)
        if any(char in text for char in "àâäæçéèêëïîôùûü"):
            language = "fr"
        elif any(char in text for char in "áéíñóúü"):
            language = "es"
        elif any(char in text for char in "äöüß"):
            language = "de"
        elif any(char in text for char in "あいうえおかきくけこ"):
            language = "ja"
        else:
            language = "en"

        return {
            "text": text,
            "language_code": language,
            "language_name": self._get_language_name(language),
            "confidence": 0.7,
            "service": "mock_detector",
            "note": "Using mock detection. Configure AZURE_TRANSLATOR_KEY for accurate detection."
        }

    def _get_language_name(self, language_code: str) -> str:
        """Get human-readable language name from language code."""
        language_names = {
            "en": "English",
            "fr": "French",
            "es": "Spanish",
            "de": "German",
            "it": "Italian",
            "pt": "Portuguese",
            "ja": "Japanese",
            "zh": "Chinese",
            "ko": "Korean",
            "ar": "Arabic",
            "ru": "Russian",
            "hi": "Hindi",
            "th": "Thai",
            "vi": "Vietnamese",
            "nl": "Dutch",
            "pl": "Polish",
            "tr": "Turkish"
        }
        return language_names.get(language_code, language_code.upper())

    def _get_pronunciation_hint(self, text: str, language_code: str) -> str:
        """
        Provide pronunciation hints for common languages.
        In production, use a pronunciation API or phonetic transcription service.
        """
        pronunciation_tips = {
            "fr": "Pronounce softly with nasal vowels",
            "es": "Roll the 'r' sounds",
            "de": "Emphasize consonants",
            "ja": "Each syllable has equal emphasis",
            "zh": "Pay attention to tones",
            "ar": "Guttural sounds from the throat",
            "ru": "Hard and soft consonants differ"
        }
        return pronunciation_tips.get(language_code, "Standard pronunciation")
