from services.llmModels import GroqLLM
from services.llmModels.openRouter import MistralLLM
from services.llmModels.openRouter import GemmaLLM
from services.llmModels.openRouter import HermesLLM
from services.llmModels import BaseLLMService

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
