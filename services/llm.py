from fastapi import HTTPException

from helpers.helpers import process_llm_output
from services.groq import llm_connect


class LLMService:
    def __init__(self):
        self.client = llm_connect()
        self.attempt = 0

    async def get_sql_query_with_database_structure(
        self, database_structure: str, order: str
    ) -> str:
        from prompts import sql_generation
        try:
            system_message = sql_generation.get_system_message(database_structure)
            user_message = sql_generation.get_user_message(order)
            chat_completion = self.client.chat.completions.create(
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
                model="gemma2-9b-it",
            )
            return chat_completion.choices[0].message.content
        except Exception as e:
            raise HTTPException(
                status_code=500,
                detail=f"Erro no processamento da query com LLM: {str(e)}",
            )

    async def get_result_interpretation(self, result: str, order: str) -> str:
        from prompts import result_interpretation
        try:
            system_message = result_interpretation.get_system_message(order)
            user_message = result_interpretation.get_user_message(result)
            chat_completion = self.client.chat.completions.create(
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
                model="gemma2-9b-it",
            )
            return chat_completion.choices[0].message.content
        except Exception as e:
            raise HTTPException(
                status_code=500,
                detail=f"Erro no processamento da query com LLM: {str(e)}",
            )

    async def optimize_generate(self, query: str, database_structure: str) -> str:
        from prompts import query_optimization
        is_retry = False
        while self.attempt < 3:
            try:
                system_message = query_optimization.get_system_message(is_retry=is_retry)
                user_message = query_optimization.get_user_message(query, database_structure)
                chat_completion = self.client.chat.completions.create(
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
                    model="gemma2-9b-it",
                )
                response = process_llm_output(chat_completion.choices[0].message.content)
                self.attempt = 0
                return response
            except Exception as e:
                self.attempt += 1
                is_retry = True
                if self.attempt >= 3:
                    raise HTTPException(
                        status_code=500,
                        detail=f"Erro ao processar a resposta do LLM após 3 tentativas: {str(e)}",
                    )

    async def create_database(self, database_structure: str) -> str:
        from prompts import database_creation_string as database_creation
        is_retry = False
        while self.attempt < 5:
            try:
                system_message = database_creation.get_system_message(is_retry=is_retry)
                user_message = database_creation.get_user_message(database_structure)
                chat_completion = self.client.chat.completions.create(
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
                    model="gemma2-9b-it",
                )
                response = process_llm_output(chat_completion.choices[0].message.content)
                self.attempt = 0
                return response
            except Exception as e:
                self.attempt += 1
                is_retry = True
                if self.attempt >= 5:
                    raise HTTPException(
                        status_code=500,
                        detail=f"Erro ao processar a resposta do LLM após {self.attempt} tentativas: {str(e)}",
                    )

    async def populate_database(self, creation_command: str, number_insertions) -> str:
        from prompts import database_population
        try:
            system_message = database_population.get_system_message(number_insertions)
            user_message = database_population.get_user_message(creation_command)
            chat_completion = self.client.chat.completions.create(
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
                model="gemma2-9b-it",
            )

            return chat_completion.choices[0].message.content
        except Exception as e:
            raise HTTPException(
                status_code=500,
                detail=f"Erro no processamento da estrutura do banco com LLM: {str(e)}",
            )

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

            chat_completion = self.client.chat.completions.create(
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt},
                ],
                model="gemma2-9b-it",
            )
            return chat_completion.choices[0].message.content
        except Exception as e:
            raise HTTPException(
                status_code=500,
                detail=f"Erro ao avaliar efeitos da otimização com LLM: {str(e)}",
            )
