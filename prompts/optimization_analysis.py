def get_system_message() -> str:
    """
    Returns the system message for the optimization analysis prompt.
    """
    return (
        "You are a SQL performance expert. Compare the original and optimized versions of a query, "
        "with their metrics and applied indexes. Decide if the optimization is worth keeping with a technical justification. "
        "Respond clearly, analyzing time, memory, index usage, and percentage impact."
    )

def get_user_message(
    original_metrics: dict,
    optimized_metrics: dict,
    original_query: str,
    optimized_query: str,
    applied_indexes: list,
) -> str:
    """
    Returns the user message for the optimization analysis prompt.
    """
    return (
        f"Original query:\n{original_query}\n\n"
        f"Original query metrics:\n{original_metrics}\n\n"
        f"Optimized query:\n{optimized_query}\n\n"
        f"Optimized query metrics:\n{optimized_metrics}\n\n"
        f"Applied indexes:\n" + "\n".join(applied_indexes)
    )

