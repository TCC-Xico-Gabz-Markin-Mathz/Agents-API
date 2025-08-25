from services.llmModels.openRouter import OpenRouterBaseLLMService
import os


class HermesLLM(OpenRouterBaseLLMService):
    def __init__(self):
        model_name = os.getenv(
            "HERMES_MODEL_NAME", "nousresearch/deephermes-3-llama-3-8b-preview:free"
        )
        super().__init__(model_name=model_name)
