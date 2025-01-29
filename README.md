# API-RAG

## Descrição
Esta é uma API desenvolvida em **FastAPI** que recebe informações sobre a estrutura e queries de bancos de dados, utiliza um vector database (**Qdrant**) para fornecer contexto e passa esses dados para um **LLM da Groq**. Com base nas respostas do modelo, a API gera otimizações para as queries SQL.

## Tecnologias Utilizadas
- **FastAPI** - Framework para desenvolvimento de APIs em Python
- **Qdrant** - Vector database para armazenamento de embeddings
- **Groq LLM** - Modelo de linguagem para aprimoramento das queries
- **Docker** - Para conteinerização da aplicação

  ![Python](https://img.shields.io/badge/Python-3776AB?style=for-the-badge&logo=python&logoColor=white)
  ![FastAPI](https://img.shields.io/badge/FastAPI-3776AB?style=for-the-badge&logo=python&logoColor=white)
  ![scikit-learn](https://img.shields.io/badge/scikit--learn-F7931E?style=for-the-badge&logo=scikit-learn&logoColor=white)
  ![Groq](https://img.shields.io/badge/Groq-100C10?style=for-the-badge&logo=groq&logoColor=white)
  ![Qdrant](https://img.shields.io/badge/Qdrant-100C10?style=for-the-badge&logo=groq&logoColor=white)

## Instalação e Execução

### 1. Clonar o repositório
```sh
 git clone https://github.com/franciscoguimaraes/api-rag.git
 cd api-rag
```

### 2. Construir e executar o container Docker
```sh
docker build -t franciscoguimaraes/api-rag-app:1.0 .
docker run -p 8000:8000 franciscoguimaraes/api-rag-app:1.0
```

### 3. Acessar a API
Acesse a documentação interativa no navegador:
```
http://localhost:8000/docs
```

## Exemplo de Requisição
Envie uma requisição **POST** para otimizar uma query SQL:
```sh
curl -X 'POST' \
  'http://localhost:8000/optimize-query' \
  -H 'Content-Type: application/json' \
  -d '{
    "db_structure": "estrutura do banco",
    "query": "SELECT * FROM users WHERE age > 30"
    "process": "Retorne somente uma query otimizada"
  }'
```

### Resposta Esperada
```json
{
  "optimized_query": "SELECT * FROM users WHERE age > 30 AND active = 1",
}
```

## Licença
Este projeto está sob a licença.
