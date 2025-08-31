import os
import json
import httpx
from fastapi import HTTPException
from typing import List
from services.llm_providers import BaseLLMService
from helpers.utils import generate_inserts, process_llm_output


class OpenRouterBaseLLMService(BaseLLMService):
    def __init__(self, model_name: str):
        self.api_key = os.getenv("OPENROUTER_API_KEY")
        self.base_url = "https://openrouter.ai/api/v1/chat/completions"
        self.model_name = model_name
        self.attempt = 0

    async def _chat(self, messages: List[dict]) -> str:
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
        }
        body = {"model": self.model_name, "messages": messages}

        async with httpx.AsyncClient(timeout=60) as client:
            response = await client.post(self.base_url, headers=headers, json=body)
            if response.status_code != 200:
                raise HTTPException(500, f"OpenRouter error: {response.text}")
            return response.json()["choices"][0]["message"]["content"]

    async def get_sql_query_with_database_structure(
        self, database_structure: str, order: str
    ) -> str:
        from prompts import sql_generation
        system_message = sql_generation.get_system_message(database_structure)
        user_message = sql_generation.get_user_message(order)
        messages = [
            {
                "role": "system",
                "content": system_message,
            },
            {"role": "user", "content": user_message},
        ]
        return await self._chat(messages)

    async def get_result_interpretation(self, result: str, order: str) -> str:
        from prompts import result_interpretation
        system_message = result_interpretation.get_system_message(order)
        user_message = result_interpretation.get_user_message(result)
        messages = [
            {
                "role": "system",
                "content": system_message,
            },
            {"role": "user", "content": user_message},
        ]
        return await self._chat(messages)

    async def optimize_generate(self, query: str, database_structure: str) -> str:
        from prompts import query_optimization
        is_retry = False
        while self.attempt < 3:
            try:
                system_message = query_optimization.get_system_message(is_retry=is_retry)
                user_message = query_optimization.get_user_message(query, database_structure)
                messages = [
                    {"role": "system", "content": system_message},
                    {"role": "user", "content": user_message},
                ]
                raw_response = await self._chat(messages)
                self.attempt = 0
                return process_llm_output(raw_response)
            except Exception as e:
                self.attempt += 1
                is_retry = True
                if self.attempt >= 3:
                    raise HTTPException(
                        500, f"Error generating database optimization: {str(e)}"
                    )

    async def create_database(self, database_structure: str) -> str:
        from prompts import database_creation_string as database_creation
        is_retry = False
        while self.attempt < 3:
            try:
                system_message = database_creation.get_system_message(is_retry=is_retry)
                user_message = database_creation.get_user_message(database_structure)
                messages = [
                    {
                        "role": "system",
                        "content": system_message,
                    },
                    {
                        "role": "user",
                        "content": user_message,
                    },
                ]
                raw = await self._chat(messages)
                self.attempt = 0
                return process_llm_output(raw)
            except Exception as e:
                self.attempt += 1
                is_retry = True
                if self.attempt >= 3:
                    raise HTTPException(500, f"Error generating database structure: {str(e)}")

    async def populate_database(
        self, creation_commands: list, number_insertions: int
    ) -> str:
        inserts = []
        fk_values = {
            "VARCHAR": [],
            "INT": [],
        }

        for count in range(number_insertions):
            fk_values["VARCHAR"].append(f"fk_value_{count}")
            fk_values["INT"].append(count + 1)

        for creation_command in creation_commands:
            inserts.append(
                generate_inserts(creation_command, number_insertions, fk_values)
            )
        return json.dumps(inserts, ensure_ascii=False)

    def analyze_optimization_effects(
        self,
        original_metrics: dict,
        optimized_metrics: dict,
        original_query: str,
        optimized_query: str,
        applied_indexes: list,
    ) -> str:
        from prompts import optimization_analysis
        system_message = optimization_analysis.get_system_message()
        user_message = optimization_analysis.get_user_message(
            original_metrics,
            optimized_metrics,
            original_query,
            optimized_query,
            applied_indexes,
        )
        messages = [
            {
                "role": "system",
                "content": system_message,
            },
            {
                "role": "user",
                "content": user_message,
            },
        ]
        import asyncio

        return asyncio.run(self._chat(messages))

    async def get_weights(self, ram_gb: int = None, priority: str = None) -> str:
        from prompts import weight_calculation
        try:
            system_message = weight_calculation.get_system_message()
            user_message = weight_calculation.get_user_message(ram_gb, priority)

            messages = [
                {
                    "role": "system",
                    "content": system_message,
                },
                {"role": "user", "content": user_message},
            ]

            raw = await self._chat(messages)
            return raw
        except Exception as e:
            raise Exception(f"Error generating weights with LLM: {e}")
