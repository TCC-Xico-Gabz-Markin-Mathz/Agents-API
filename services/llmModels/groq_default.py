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
            system_message = """
                Você é um especialista em otimização de queries SQL.
                Sua tarefa é analisar uma query SQL fornecida e a estrutura de um banco de dados e identificar oportunidades de melhoria.

                O resultado deve ser um JSON contendo uma lista de strings. Cada string deve ser um comando SQL.

                A resposta deve incluir, no mínimo, dois elementos:
                1. Um comando SQL `CREATE INDEX` para cada coluna que possa ser usada para melhorar a performance da query. Se não houver necessidade de novos índices, retorne um array vazio para este campo.
                2. A query SQL reescrita, otimizada para ser mais eficiente e escalável.

                Sua resposta deve ser *exclusivamente* o JSON, sem qualquer texto adicional, explicações ou formatação de markdown.

                Exemplo de formato de resposta:
                [
                "CREATE INDEX idx_nome_tabela_coluna ON nome_tabela (coluna_analisada);",
                "SELECT A.coluna1, B.coluna2 FROM tabela_A AS A JOIN tabela_B AS B ON A.id = B.id WHERE A.coluna1 > 100;"
                ]

                Se não houver necessidade de índices, a resposta deve ser:
                [
                "SELECT A.coluna1 FROM tabela_A AS A WHERE A.coluna1 > 100;"
                ]
            """
            user_message = f"""
                Estrutura do banco de dados:
                {database_structure}

                Query original a ser otimizada:
                {query}
            """

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
            if self.attempt < 3:
                return await self.optimize_generate(query, database_structure)
            raise HTTPException(500, f"Erro ao otimizar query com Groq: {str(e)}")

    async def create_database(self, database_structure: str) -> str:
        try:
            system_message = """
                Você é um assistente especialista em DDL (Data Definition Language) SQL. Sua tarefa é criar comandos SQL `CREATE TABLE` com base em uma descrição de estrutura de banco de dados fornecida.

                **Importante:** Gere apenas comandos `CREATE TABLE`. Não crie comandos `ALTER TABLE` ou qualquer outro tipo de DDL.

                As regras para a geração das tabelas são:
                - - Cada tabela deve ter uma chave primária, que pode ser uma única coluna ou uma combinação de colunas (chave primária composta). Para chaves primárias compostas, use a sintaxe `PRIMARY KEY (coluna1, coluna2, ...)`..
                - As colunas de chave estrangeira (`FOREIGN KEY`) devem ter um nome que termine com `_id` e seu tipo de dado deve corresponder ao tipo de dado da chave primária da tabela referenciada.
                - Os comandos SQL devem ser ordenados para que as tabelas sem chaves estrangeiras sejam criadas primeiro. Isso garante a correta execução dos comandos.

                O resultado deve ser um JSON contendo uma lista de strings, onde cada string é um comando SQL `CREATE TABLE` completo e funcional. Não inclua texto adicional, explicações ou qualquer tipo de formatação de markdown.

                Exemplo de formato de resposta:
                [
                "CREATE TABLE usuarios ( id INT PRIMARY KEY AUTO_INCREMENT, nome VARCHAR(255) NOT NULL );",
                "CREATE TABLE pedidos ( id INT PRIMARY KEY, usuario_id INT, data DATE, FOREIGN KEY (usuario_id) REFERENCES usuarios(id) );"
                ]
            """
            user_message = f"""
                Descrição da estrutura do banco de dados:
                {database_structure}
            """

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
            if self.attempt < 3:
                return await self.create_database(database_structure)
            raise HTTPException(
                500, f"Erro ao gerar estrutura de banco com Groq: {str(e)}"
            )

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
