from fastapi import HTTPException
from helpers.helpers import process_llm_output
from services.groq import llm_connect


class GroqLLM:
    def __init__(self):
        self.client = llm_connect()
        self.attempt = 0
        self.model = "gemma2-9b-it"

    async def get_sql_query_with_database_structure(
        self, database_structure: str, order: str
    ) -> str:
        try:
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {
                        "role": "system",
                        "content": (
                            f"Você é um assistente especializado em SQL. "
                            f"Com base na seguinte estrutura de banco de dados:\n\n{database_structure}\n\n"
                            f"Gere uma única query SQL que atenda exatamente à seguinte solicitação do usuário. "
                            f"Retorne apenas a query SQL, sem explicações ou texto adicional."
                        ),
                    },
                    {"role": "user", "content": order},
                ],
            )
            return response.choices[0].message.content
        except Exception as e:
            raise HTTPException(500, f"Erro ao gerar query SQL com Groq: {str(e)}")

    async def get_result_interpretation(self, result: str, order: str) -> str:
        try:
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {
                        "role": "system",
                        "content": (
                            f"Você é um assistente especializado em SQL. "
                            f"Com base na seguinte pergunta do usuário: {order} "
                            f"Formate a resposta gerada pelo banco em linguagem natural. "
                            f"Retorne apenas a resposta para o usuário, sem explicações."
                        ),
                    },
                    {"role": "user", "content": result},
                ],
            )
            return response.choices[0].message.content
        except Exception as e:
            raise HTTPException(
                500, f"Erro ao interpretar resultado com Groq: {str(e)}"
            )

    async def optimize_generate(self, query: str, database_structure: str) -> str:
        try:
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {
                        "role": "system",
                        "content": (
                            "Você é um assistente especializado em SQL e otimização de queries. A seguir está a estrutura do banco de dados e uma query a ser otimizada. "
                            "Sua tarefa é analisar, sugerir comandos CREATE INDEX se necessário e reescrever a query de forma mais eficiente. "
                            "Retorne apenas um JSON como lista de strings com os comandos (sem explicações ou markdown)."
                            f"\n\nEstrutura do banco:\n{database_structure}"
                        ),
                    },
                    {"role": "user", "content": f"Query original:\n{query}"},
                ],
            )
            return process_llm_output(response.choices[0].message.content)
        except Exception as e:
            self.attempt += 1
            if self.attempt < 3:
                return await self.optimize_generate(query, database_structure)
            raise HTTPException(500, f"Erro ao otimizar query com Groq: {str(e)}")

    async def create_database(self, database_structure: str) -> str:
        try:
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {
                        "role": "system",
                        "content": (
                            "Você é um assistente especialista em DDL SQL. Gere comandos CREATE TABLE com base na descrição a seguir. "
                            "Retorne uma lista JSON de strings com os comandos, sem explicações, ordenados corretamente. "
                            f"\n\n{database_structure}"
                        ),
                    },
                    {"role": "user", "content": database_structure},
                ],
            )
            return process_llm_output(response.choices[0].message.content)
        except Exception as e:
            raise HTTPException(
                500, f"Erro ao gerar estrutura de banco com Groq: {str(e)}"
            )

    async def populate_database(
        self, creation_command: str, number_insertions: int
    ) -> str:
        try:
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {
                        "role": "system",
                        "content": (
                            f"Você é um assistente especializado em gerar dados fictícios coerentes com comandos CREATE TABLE. "
                            f"Gere até {number_insertions} comandos INSERT INTO por tabela, em formato de lista de strings JSON, sem explicações."
                        ),
                    },
                    {"role": "user", "content": creation_command},
                ],
            )
            return response.choices[0].message.content
        except Exception as e:
            raise HTTPException(500, f"Erro ao popular banco com Groq: {str(e)}")

    def analyze_optimization_effects(
        self,
        original_metrics: dict,
        optimized_metrics: dict,
        original_query: str,
        optimized_query: str,
        applied_indexes: list,
    ) -> str:
        try:
            system_prompt = (
                "Você é um especialista em performance SQL. Compare a versão original e otimizada de uma query, "
                "com suas métricas e índices aplicados. Decida se vale a pena manter a otimização com justificativa técnica. "
                "Responda com clareza, analisando tempo, memória, uso de índices e impacto percentual."
            )
            user_prompt = (
                f"Query original:\n{original_query}\n\n"
                f"Métricas da query original:\n{original_metrics}\n\n"
                f"Query otimizada:\n{optimized_query}\n\n"
                f"Métricas da query otimizada:\n{optimized_metrics}\n\n"
                f"Índices aplicados:\n" + "\n".join(applied_indexes)
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
