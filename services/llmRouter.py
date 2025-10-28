from services.llm_providers import GroqLLM
from services.llm_providers.openRouter import MistralLLM
from services.llm_providers.openRouter import GemmaLLM
from services.llm_providers.openRouter import HermesLLM
from services.llm_providers import BaseLLMService

def get_llm(model: str = "default") -> BaseLLMService:
    match model.lower():
        case "mistral":
            return MistralLLM()
        case "gemma":
            return GemmaLLM()
        case "hermes":
            return HermesLLM()
        case _:
            return GroqLLM()
