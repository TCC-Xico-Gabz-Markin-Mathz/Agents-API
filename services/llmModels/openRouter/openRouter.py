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

    async def get_sql_query_with_database_structure(self, database_structure: str, order: str) -> str:
        messages = [
            {
                "role": "system",
                "content": (
                    "Você é um assistente especializado em SQL. "
                    f"Com base na seguinte estrutura de banco de dados:\n\n{database_structure}\n\n"
                    "Gere uma única query SQL que atenda exatamente à seguinte solicitação do usuário. "
                    "Retorne apenas a query SQL, sem explicações ou texto adicional."
                )
            },
            {
                "role": "user",
                "content": order
            }
        ]
        return await self._chat(messages)

    async def get_result_interpretation(self, result: str, order: str) -> str:
        messages = [
            {
                "role": "system",
                "content": (
                    f"Você é um assistente especializado em SQL. "
                    f"Com base na seguinte pergunta do usuario: {order}\n"
                    f"Formule a resposta do banco ({result}) em linguagem natural para o usuário final."
                    f"Retorne apenas a resposta, sem explicações adicionais."
                ),
            },
            {
                "role": "user",
                "content": result,
            },
        ]
        return await self._chat(messages)

    async def optimize_generate(self, query: str, database_structure: str) -> str:
        prompt = (
            "## Assistente Especializado em SQL e Otimização de Queries\n\n"
            "Você é um **assistente especializado em SQL** e **otimização de desempenho de queries**. A seguir, você receberá:\n"
            "* A **estrutura do banco de dados**\n"
            "* Uma **query SQL** que precisa ser otimizada\n"
            "---\n"
            "### Tarefa\n"
            "1. **Analisar** a query fornecida com base na estrutura do banco\n"
            "2. **Sugerir comandos de otimização**, como criação de índices (`CREATE INDEX`), se necessário\n"
            "3. **Reescrever a query** de forma mais eficiente, mantendo o mesmo resultado\n"
            "---\n"
            "### Formato da Resposta\n"
            "* Retorne **apenas um JSON** com um **array de strings**, **sem explicações**\n"
            "* O array deve conter, na ordem:\n"
            "  1. **Comandos `CREATE INDEX`** (caso necessário)\n"
            "  2. A **query otimizada**\n"
            "---\n"
            "### Estrutura do Banco de Dados\n"
            f"{database_structure}\n"
            "---\n"
            "Query original:\n"
            f"{query}"
        )
        messages = [{"role": "system", "content": prompt}]
        raw_response = await self._chat(messages)
        return process_llm_output(raw_response)

    async def create_database(self, database_structure: str) -> str:
        messages = [
            {
                "role": "system",
                "content": (
                    "Você é um assistente especializado em SQL. "
                    "Converta a seguinte estrutura descritiva em comandos CREATE TABLE válidos, "
                    "com tipos apropriados, chaves primárias e estrangeiras. "
                    "Retorne um JSON contendo apenas uma lista de strings SQL (sem explicação)."
                    f"\n\n{database_structure}"
                )
            }
        ]
        raw = await self._chat(messages)
        return process_llm_output(raw)


    async def populate_database(self, creation_commands: list, number_insertions: int) -> str:
        inserts = []
        fk_values = {
            "VARCHAR": [],
            "INT": [],
        }
        
        for count in range(number_insertions):
            fk_values["VARCHAR"].append(f"fk_value_{count}")
            fk_values["INT"].append(count + 1)
            
        for creation_command in creation_commands:
            inserts.append(generate_inserts(creation_command, number_insertions, fk_values))
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
                    "Você é um especialista sênior em performance de bancos de dados. "
                    "Compare as métricas de execução de duas versões de uma query, com ou sem índices, e diga se vale a pena manter a otimização. "
                    "Seja objetivo e técnico. Indique se deve **manter** ou **não manter**."
                )
            },
            {
                "role": "user",
                "content": (
                    f"Query original:\n{original_query}\n\n"
                    f"Métricas originais:\n{original_metrics}\n\n"
                    f"Query otimizada:\n{optimized_query}\n\n"
                    f"Métricas otimizadas:\n{optimized_metrics}\n\n"
                    f"Índices aplicados:\n{applied_indexes}"
                )
            }
        ]
        import asyncio
        return asyncio.run(self._chat(messages))

    async def get_weights(self, ram_gb: int = None, priority: str = None) -> str:
        try:
            prompt = f"""
                {"O banco possui cerca de " + ram_gb + " de RAM disponível para operações." if ram_gb else ""}
                {"A prioridade do sistema é: " + priority + "." if priority else ""}

                Quero calcular um score de custo para queries SQL usando a fórmula:

                score = w1 * tempo_execucao + w2 * uso_cpu + w3 * uso_io + w4 * linhas_lidas + w5 * frequencia_execucao + w6 * tamanho_tabela + w7 * tabelas_sem_indice + w8 * colisoes_em_join

                Considerando o contexto acima, gere os pesos w1 a w8 para refletir o custo real das queries nesse ambiente.

                Retorne apenas os pesos no formato JSON, sem comentário extras, garantindo que a soma dos pesos seja 1.0, assim:

                {{
                "tempo_execucao": number,
                "uso_cpu": number,
                "uso_io": number,
                "linhas_lidas": number,
                "frequencia_execucao": number,
                "tamanho_tabela": number,
                "tabelas_sem_indice": number,
                "colisoes_em_join": number
                }}
                """

            chat_completion = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {
                        "role": "system",
                        "content": (
                            "Você é um especialista em performance de banco de dados.\n"
                            "Sua tarefa é gerar pesos para um modelo de score de queries SQL,\n"
                            "considerando dados de infraestrutura e perfil de uso.\n"
                            "Forneça apenas um JSON com os pesos normalizados."
                        ),
                    },
                    {
                        "role": "user",
                        "content": prompt,
                    },
                ],
            )

            content = chat_completion.choices[0].message.content
            return content

        except Exception as e:
            raise Exception(f"Erro ao gerar pesos com LLM: {e}")
        
    async def get_weights(self, ram_gb: int = None, priority: str = None) -> str:
        try:
            prompt = f"""
                {"O banco possui cerca de " + ram_gb + " de RAM disponível para operações." if ram_gb else ""}
                {"A prioridade do sistema é: " + priority + "." if priority else ""}

                Quero calcular um score de custo para queries SQL usando a fórmula:

                score = w1 * tempo_execucao + w2 * uso_cpu + w3 * uso_io + w4 * linhas_lidas + w5 * frequencia_execucao + w6 * tamanho_tabela + w7 * tabelas_sem_indice + w8 * colisoes_em_join

                Considerando o contexto acima, gere os pesos w1 a w8 para refletir o custo real das queries nesse ambiente.

                Retorne apenas os pesos no formato JSON, sem comentário extras, garantindo que a soma dos pesos seja 1.0, assim:

                {{
                "tempo_execucao": number,
                "uso_cpu": number,
                "uso_io": number,
                "linhas_lidas": number,
                "frequencia_execucao": number,
                "tamanho_tabela": number,
                "tabelas_sem_indice": number,
                "colisoes_em_join": number
                }}
            """
            
            messages = [
                {
                    "role": "system",
                    "content": (
                        "Você é um especialista em performance de banco de dados.\n"
                        "Sua tarefa é gerar pesos para um modelo de score de queries SQL,\n"
                        "considerando dados de infraestrutura e perfil de uso.\n"
                        "Forneça apenas um JSON com os pesos normalizados."
                    )
                }
            ]
            
            raw = await self._chat(messages)
            return raw
        except Exception as e:
            raise Exception(f"Erro ao gerar pesos com LLM: {e}")