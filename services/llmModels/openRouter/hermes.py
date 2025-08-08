from services.llmModels.openRouter import OpenRouterBaseLLMService

class HermesLLM(OpenRouterBaseLLMService):
    def __init__(self):
        super().__init__(model_name="nousresearch/deephermes-3-llama-3-8b-preview:free")
