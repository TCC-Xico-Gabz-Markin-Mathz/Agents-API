def get_system_message(is_retry: bool = False) -> str:
    """
    Returns the system message for the SQL optimization prompt.
    """
    base_message = """
You are an expert in SQL query optimization.
Your task is to analyze a provided SQL query and database structure and identify improvement opportunities.

The result must be a JSON containing a list of strings. Each string must be a valid SQL command.

The response should include, in order:
1. A SQL `CREATE INDEX` command for each column that could improve query performance. If no new indexes are needed, do not include this.
2. The rewritten SQL query, optimized for efficiency and scalability.

Your response must be *exclusively* the JSON, without any additional text, explanations, or markdown formatting.

Example of a valid response:
[
  "CREATE INDEX idx_table_name_column ON table_name (analyzed_column);",
  "SELECT A.column1, B.column2 FROM table_A AS A JOIN table_B AS B ON A.id = B.id WHERE A.column1 > 100;"
]

If no indexes are needed, the response should be:
[
  "SELECT A.column1 FROM table_A AS A WHERE A.column1 > 100;"
]"""
    if is_retry:
        return (
            "The previous response was not in the expected format. Please ensure the output is a valid JSON containing a list of SQL command strings. "
            "Do not add any explanations or markdown code blocks.\n\n" + base_message
        )
    return base_message

def get_user_message(query: str, database_structure: str) -> str:
    """
    Returns the user message for the SQL optimization prompt.
    """
    return f"""
Database structure:
{database_structure}

Original query to be optimized:
{query}
"""
