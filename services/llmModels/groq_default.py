import json
from fastapi import HTTPException
from helpers.helpers import process_llm_output
from services.groq import llm_connect
from helpers.helpers import generate_inserts


class GroqLLM:
    def __init__(self):
        self.client = llm_connect()
        self.attempt = 0
        self.model = "gemma2-9b-it"

    async def get_sql_query_with_database_structure(
        self, database_structure: str, order: str
    ) -> str:
        from prompts import sql_generation
        try:
            system_message = sql_generation.get_system_message(database_structure)
            user_message = sql_generation.get_user_message(order)
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {
                        "role": "system",
                        "content": system_message,
                    },
                    {"role": "user", "content": user_message},
                ],
            )
            return response.choices[0].message.content
        except Exception as e:
            raise HTTPException(500, f"Erro ao gerar query SQL com Groq: {str(e)}")

    async def get_result_interpretation(self, result: str, order: str) -> str:
        from prompts import result_interpretation
        try:
            system_message = result_interpretation.get_system_message(order)
            user_message = result_interpretation.get_user_message(result)
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {
                        "role": "system",
                        "content": system_message,
                    },
                    {"role": "user", "content": user_message},
                ],
            )
            return response.choices[0].message.content
        except Exception as e:
            raise HTTPException(
                500, f"Erro ao interpretar resultado com Groq: {str(e)}"
            )

    async def create_database(self, database_structure: dict) -> str:
        from prompts import database_creation
        is_retry = False
        while self.attempt < 3:
            try:
                system_message = database_creation.get_system_message(is_retry=is_retry)
                user_message = database_creation.get_user_message(database_structure)

                response = self.client.chat.completions.create(
                    model=self.model,
                    messages=[
                        {"role": "system", "content": system_message},
                        {"role": "user", "content": user_message},
                    ],
                )
                return process_llm_output(response.choices[0].message.content)
            except Exception as e:
                self.attempt += 1
                is_retry = True
                if self.attempt >= 3:
                    raise HTTPException(500, f"Erro ao gerar estrutura de banco com Groq após 3 tentativas: {str(e)}")
        self.attempt = 0

    async def optimize_generate(self, query: str, database_structure: str) -> str:
        from prompts import query_optimization
        is_retry = False
        while self.attempt < 3:
            try:
                system_message = query_optimization.get_system_message(is_retry=is_retry)
                user_message = query_optimization.get_user_message(query, database_structure)

                response = self.client.chat.completions.create(
                    model=self.model,
                    messages=[
                        {"role": "system", "content": system_message},
                        {"role": "user", "content": user_message},
                    ],
                )
                return process_llm_output(response.choices[0].message.content)
            except Exception as e:
                self.attempt += 1
                is_retry = True
                if self.attempt >= 3:
                    raise HTTPException(500, f"Erro ao otimizar query com Groq após 3 tentativas: {str(e)}")
        self.attempt = 0

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
        try:
            system_prompt = optimization_analysis.get_system_message()
            user_prompt = optimization_analysis.get_user_message(
                original_metrics,
                optimized_metrics,
                original_query,
                optimized_query,
                applied_indexes,
            )
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt},
                ],
            )
            return response.choices[0].message.content
        except Exception as e:
            raise HTTPException(500, f"Erro ao analisar otimização com Groq: {str(e)}")

    async def get_weights(self, ram_gb: int = None, priority: str = None) -> str:
        from prompts import weight_calculation
        try:
            system_message = weight_calculation.get_system_message()
            user_message = weight_calculation.get_user_message(ram_gb, priority)

            chat_completion = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {
                        "role": "system",
                        "content": system_message,
                    },
                    {
                        "role": "user",
                        "content": user_message,
                    },
                ],
            )

            content = chat_completion.choices[0].message.content
            return content

        except Exception as e:
            raise Exception(f"Erro ao gerar pesos com LLM: {e}")
