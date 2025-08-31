from services.llm_providers.openRouter import OpenRouterBaseLLMService

class GemmaLLM(OpenRouterBaseLLMService):
    def __init__(self):
        super().__init__(model_name="google/gemma-3-27b-it:free")
