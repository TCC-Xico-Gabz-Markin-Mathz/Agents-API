from services.llm_providers.openRouter import OpenRouterBaseLLMService

class MistralLLM(OpenRouterBaseLLMService):
    def __init__(self):
        super().__init__(model_name="mistralai/mistral-7b-instruct")
