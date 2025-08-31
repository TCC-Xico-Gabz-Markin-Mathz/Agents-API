def get_system_message() -> str:
    """
    Returns the system message for the weight calculation prompt.
    """
    return (
        "You are a database performance expert.\n"
        "Your task is to generate weights for a SQL query scoring model,\n"
        "considering infrastructure data and usage profile.\n"
        "Provide only a JSON with normalized weights."
    )

def get_user_message(ram_gb: int = None, priority: str = None) -> str:
    """
    Returns the user message for the weight calculation prompt.
    """
    return f"""
        {'The database has approximately ' + str(ram_gb) + 'GB of RAM available for operations.' if ram_gb else ''}
        {'The system priority is: ' + priority + '.' if priority else ''}

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
