def get_system_message(order: str) -> str:
    """
    Returns the system message for the result interpretation prompt.
    """
    return (
        f"You are a SQL expert assistant. "
        f"Based on the following user question: {order} "
        f"Format the database-generated response in natural language. "
        f"Return only the answer for the user, without explanations."
    )

def get_user_message(result: str) -> str:
    """
    Returns the user message for the result interpretation prompt.
    """
    return result
