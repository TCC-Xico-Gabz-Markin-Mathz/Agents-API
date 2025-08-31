def get_system_message(database_structure: str) -> str:
    """
    Returns the system message for the SQL generation prompt.
    """
    return (
        f"You are a SQL expert assistant. "
        f"Based on the following database structure:\n\n{database_structure}\n\n"
        f"Generate a single SQL query that exactly meets the following user request. "
        f"Return only the SQL query, without explanations or additional text."
    )

def get_user_message(order: str) -> str:
    """
    Returns the user message for the SQL generation prompt.
    """
    return order
