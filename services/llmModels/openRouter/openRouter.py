import os
import json
import httpx
from fastapi import HTTPException
from typing import List
from services.llmModels import BaseLLMService
from helpers.helpers import generate_inserts, process_llm_output


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
        messages = [
            {
                "role": "system",
                "content": (
                    f"You are a SQL expert assistant. "
                    f"Based on the following database structure:\n\n{database_structure}\n\n"
                    f"Generate a single SQL query that exactly meets the following user request. "
                    f"Return only the SQL query, without explanations or additional text."
                ),
            },
            {"role": "user", "content": order},
        ]
        return await self._chat(messages)

    async def get_result_interpretation(self, result: str, order: str) -> str:
        messages = [
            {
                "role": "system",
                "content": (
                    f"You are a SQL expert assistant. "
                    f"Based on the following user question: {order} "
                    f"Format the database-generated response in natural language. "
                    f"Return only the answer for the user, without explanations."
                ),
            },
            {"role": "user", "content": result},
        ]
        return await self._chat(messages)

    async def optimize_generate(self, query: str, database_structure: str) -> str:
        try:
            system_message = """
                You are an expert in SQL query optimization.
                Your task is to analyze a provided SQL query and database structure and identify improvement opportunities.

                The result should be a JSON containing a list of strings. Each string should be an SQL command.

                The response should include at least two elements:
                1. A SQL `CREATE INDEX` command for each column that could be used to improve query performance. If no new indexes are needed, return an empty array for this field.
                2. The rewritten SQL query, optimized to be more efficient and scalable.

                Your response should be *exclusively* the JSON, without any additional text, explanations, or markdown formatting.

                Example response format:
                [
                "CREATE INDEX idx_table_name_column ON table_name (analyzed_column);",
                "SELECT A.column1, B.column2 FROM table_A AS A JOIN table_B AS B ON A.id = B.id WHERE A.column1 > 100;"
                ]

                If no indexes are needed, the response should be:
                [
                "SELECT A.column1 FROM table_A AS A WHERE A.column1 > 100;"
                ]
            """
            user_message = f"""
                Database structure:
                {database_structure}

                Original query to be optimized:
                {query}
            """
            messages = [
                {"role": "system", "content": system_message},
                {"role": "user", "content": user_message},
            ]
            raw_response = await self._chat(messages)
            return process_llm_output(raw_response)
        except Exception as e:
            self.attempt += 1
            if self.attempt < 3:
                return await self.optimize_generate(query, database_structure)
            raise HTTPException(
                500, f"Error generating database optimization: {str(e)}"
            )

    async def create_database(self, database_structure: str) -> str:
        try:
            messages = [
                {
                    "role": "system",
                    "content": (
                        "You are a SQL expert assistant. "
                        "Convert the following descriptive structure into valid CREATE TABLE commands, "
                        "with appropriate types, primary and foreign keys. "
                        "Return a JSON containing only a list of SQL strings (without explanation)."
                        f"\n\n{database_structure}"
                    ),
                }
            ]
            raw = await self._chat(messages)
            return process_llm_output(raw)
        except Exception as e:
            self.attempt += 1
            if self.attempt < 3:
                return await self.create_database(database_structure)
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
        messages = [
            {
                "role": "system",
                "content": (
                    "You are a senior database performance expert. "
                    "Compare the execution metrics of two versions of a query, with or without indexes, and tell if it's worth keeping the optimization. "
                    "Be objective and technical. Indicate whether to **keep** or **not keep**."
                ),
            },
            {
                "role": "user",
                "content": (
                    f"Original query:\n{original_query}\n\n"
                    f"Original metrics:\n{original_metrics}\n\n"
                    f"Optimized query:\n{optimized_query}\n\n"
                    f"Optimized metrics:\n{optimized_metrics}\n\n"
                    f"Applied indexes:\n{applied_indexes}"
                ),
            },
        ]
        import asyncio

        return asyncio.run(self._chat(messages))

    async def get_weights(self, ram_gb: int = None, priority: str = None) -> str:
        try:
            prompt = f"""
                {"The database has approximately " + str(ram_gb) + "GB of RAM available for operations." if ram_gb else ""}
                {"The system priority is: " + priority + "." if priority else ""}

                I want to calculate a cost score for SQL queries using the formula:

                score = w1 * execution_time + w2 * cpu_usage + w3 * io_usage + w4 * rows_read + w5 * execution_frequency + w6 * table_size + w7 * tables_without_index + w8 * join_collisions

                Considering the context above, generate weights w1 to w8 to reflect the real cost of queries in this environment.

                Return only the weights in JSON format, without extra comments, ensuring the sum of weights is 1.0, like this:

                {{
                "execution_time": number,
                "cpu_usage": number,
                "io_usage": number,
                "rows_read": number,
                "execution_frequency": number,
                "table_size": number,
                "tables_without_index": number,
                "join_collisions": number
                }}
                """

            messages = [
                {
                    "role": "system",
                    "content": (
                        "You are a database performance expert.\n"
                        "Your task is to generate weights for an SQL query scoring model,\n"
                        "considering infrastructure data and usage profile.\n"
                        "Provide only a JSON with normalized weights."
                    ),
                },
                {"role": "user", "content": prompt},
            ]

            raw = await self._chat(messages)
            return raw
        except Exception as e:
            raise Exception(f"Error generating weights with LLM: {e}")
