from services.llm_providers.openRouter import OpenRouterBaseLLMService
import os


class HermesLLM(OpenRouterBaseLLMService):
    def __init__(self):
        model_name = os.getenv(
            "HERMES_MODEL_NAME", "nousresearch/deephermes-3-llama-3-8b-preview:free"
        )
        print(f"Conectando ao modelo: {model_name}")
        super().__init__(model_name=model_name)
