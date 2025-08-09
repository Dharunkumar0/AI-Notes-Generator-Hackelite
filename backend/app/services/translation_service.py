from deep_translator import GoogleTranslator
import logging

logger = logging.getLogger(__name__)

class TranslationService:
    def __init__(self):
        self.supported_languages = {
            'en': 'English',
            'ta': 'Tamil'
        }

    async def translate_text(self, text: str, source_lang: str = 'en', target_lang: str = 'ta') -> str:
        """Translate text from source language to target language."""
        try:
            if source_lang == target_lang:
                return text
                
            translated_text = GoogleTranslator(
                source=source_lang, 
                target=target_lang
            ).translate(text)
            
            return translated_text
            
        except Exception as e:
            logger.error(f"Translation error: {str(e)}")
            raise Exception(f"Failed to translate text: {str(e)}")

    def get_supported_languages(self):
        """Get list of supported languages."""
        return self.supported_languages

translation_service = TranslationService()
