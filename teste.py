from groq import Groq
from dotenv import load_dotenv
import os

load_dotenv()

api_key = os.getenv("GROQ_API_KEY")


def llm_connect():
    try:
        client = Groq(api_key=api_key)
        if client:
            print("Conexão LLM estabelecida com sucesso.")
        return client
    except Exception as e:
        print(f"Erro ao conectar ao banco de dados: {e}")
        raise e


client = llm_connect()

query = "SELECT * FROM posts, users, comments, likes WHERE posts.id = comments.post_id AND users.id = comments.user_id AND posts.id = likes.post_id AND comments.comment LIKE '%P%' AND users.name LIKE '%A%';"
database_structure = "Tabela comments\nColunas:\nid - int - não nulo - chave primária\npost_id - int - nulo - referencia tabela posts, coluna id\nuser_id - int - nulo - referencia tabela users, coluna id\ncomment - text - nulo\ncreated_at - timestamp - nulo\n\nTabela followers\nColunas:\nfollower_id - int - não nulo - chave primária - referencia tabela users, coluna id\nfollowed_id - int - não nulo - chave primária - referencia tabela users, coluna id\n\nTabela likes\nColunas:\nid - int - não nulo - chave primária\npost_id - int - nulo - referencia tabela posts, coluna id\nuser_id - int - nulo - referencia tabela users, coluna id\ncreated_at - timestamp - nulo\n\nTabela post_tags\nColunas:\npost_id - int - não nulo - chave primária - referencia tabela posts, coluna id\ntag_id - int - não nulo - chave primária - referencia tabela tags, coluna id\n\nTabela posts\nColunas:\nid - int - não nulo - chave primária\nuser_id - int - nulo - referencia tabela users, coluna id\ntitle - varchar(200) - nulo\ncontent - text - nulo\ncreated_at - timestamp - nulo\n\nTabela query_logs\nColunas:\nid - int - não nulo - chave primária\nquery_text - text - nulo\nexecution_time - float - nulo\nexecuted_at - timestamp - nulo\n\nTabela tags\nColunas:\nid - int - não nulo - chave primária\nname - varchar(50) - nulo\n\nTabela users\nColunas:\nid - int - não nulo - chave primária\nname - varchar(100) - nulo\nemail - varchar(100) - nulo\ncreated_at - timestamp - nulo"

chat_completion = client.chat.completions.create(
    messages=[
        {
            "role": "system",
            "content": (
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
                "#### Exemplos\n"
                "**Com índices:**\n"
                "[\n"
                '  "CREATE INDEX idx_cliente_id ON pedidos(cliente_id);",\n'
                '  "SELECT * FROM pedidos WHERE cliente_id = 123;"\n'
                "]\n"
                "**Sem necessidade de índices:**\n"
                "[\n"
                "  \"SELECT * FROM pedidos WHERE name = 'name';\"\n"
                "]\n"
                "---\n"
                "### Estrutura do Banco de Dados\n"
                f"{database_structure}\n"
                "---\n"
                "### Observações\n"
                "* **Não inclua nenhuma explicação na resposta**\n"
                "* Apenas o JSON com os comandos SQL e a query otimizada, conforme os exemplos acima\n"
                "* Não retorne nenhum demarcador de bloco de código markdown\n"
            ),
        },
        {
            "role": "user",
            "content": f"Query original:\n{query}",
        },
    ],
    model="gemma2-9b-it",
)

print(chat_completion.choices[0].message.content)

import ast
import re

response_str = chat_completion.choices[0].message.content

response_str = re.sub(r"\\'", "'", response_str)
response_str = response_str.replace("‘", "'").replace("’", "'")  # aspas unicode
response_str = response_str.replace("“", '"').replace("”", '"')  # aspas duplas unicode

try:
    response_list = ast.literal_eval(response_str)
    for item in response_list:
        print(item)
except (SyntaxError, ValueError):
    print("A resposta do LLM não pôde ser convertida para uma lista Python.")
