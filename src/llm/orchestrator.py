from typing import List, Optional, Dict, Any, Tuple
from config.settings import settings
from src.llm.provider import (
    LLMProvider,
    GeminiProvider,
    GroqProvider,
    DeepSeekProvider,
)
from src.utils.logging import logger

class LLMOrchestrator:
    """
    Multi-provider LLM Orchestrator implementing automatic fallback in strict priority:
    1. Gemini
    2. Groq
    3. DeepSeek
    """
    def __init__(self):
        self.providers: List[LLMProvider] = [
            GeminiProvider(settings.GEMINI_API_KEY),
            GroqProvider(settings.GROQ_API_KEY),
            DeepSeekProvider(settings.DEEPSEEK_API_KEY),
        ]
        self.stats: Dict[str, Dict[str, int]] = {
            p.name: {"calls": 0, "success": 0, "failures": 0} for p in self.providers
        }

    def get_available_providers(self) -> List[str]:
        return [p.name for p in self.providers if p.is_available()]

    async def extract_structured(
        self,
        prompt: str,
        system_prompt: str
    ) -> Tuple[Optional[Dict[str, Any]], Optional[str]]:
        """
        Attempts structured JSON extraction by trying providers in order of priority.
        Returns: (result_dict, winning_provider_name) or (None, None)
        """
        for provider in self.providers:
            if not provider.is_available():
                continue

            self.stats[provider.name]["calls"] += 1
            try:
                result = await provider.extract_structured(prompt, system_prompt)
                if result:
                    self.stats[provider.name]["success"] += 1
                    return result, provider.name
                else:
                    self.stats[provider.name]["failures"] += 1
                    logger.warning(f"Provider {provider.name} returned empty or invalid result. Falling back...")
            except Exception as e:
                self.stats[provider.name]["failures"] += 1
                logger.warning(f"Provider {provider.name} failed with error: {e}. Falling back to next provider...")

        logger.info("All configured LLM providers exhausted or unavailable. Using deterministic extraction.")
        return None, None

orchestrator = LLMOrchestrator()
