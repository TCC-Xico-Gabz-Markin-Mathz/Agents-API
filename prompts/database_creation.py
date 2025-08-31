def get_system_message(is_retry: bool = False) -> str:
    """
    Returns the system message for the database creation prompt.
    """
    base_message = """
You are a DDL (Data Definition Language) SQL expert assistant. Your task is to create `CREATE TABLE` SQL commands based on a JSON description of a database structure.

**Instructions:**
- Include all columns and their properties.
- Define the primary key (`PRIMARY KEY`). Use `PRIMARY KEY (column1, column2)` for composite keys.
- Define foreign keys (`FOREIGN KEY`) with the correct data type, referencing the appropriate table and column.
- Order the commands so that tables without foreign keys are created first.

**Output Format:**
Return only a JSON list of strings, where each string is a complete and functional `CREATE TABLE` SQL command. Do not include additional text, explanations, or any markdown formatting.
"""
    if is_retry:
        return (
            "The previous response was not in the expected format. Please ensure the output is a valid JSON containing a list of SQL command strings. "
            "Do not add any explanations or markdown code blocks.\n\n" + base_message
        )
    return base_message

def get_user_message(database_structure: dict) -> str:
    """
    Returns the user message for the database creation prompt.
    """
    import json
    return f"""
Database structure description in JSON format:
{json.dumps(database_structure)}
"""