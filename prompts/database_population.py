def get_system_message(number_insertions: int) -> str:
    """
    Returns the system message for the database population prompt.
    """
    return (
        "You are an assistant specializing in relational databases.\n"
        "Your task is to generate sample SQL commands to populate an already structured database.\n\n"
        "Based on the provided CREATE TABLE commands, generate INSERT INTO commands to populate the tables with fictitious and coherent data.\n"
        f"- Generate up to {number_insertions} insertions per table.\n"
        "- The data must be consistent with the defined types (e.g., dates in YYYY-MM-DD format, fictitious names, realistic emails, coherent IDs).\n"
        "- Consider the relationships between tables (e.g., foreign keys must point to valid records).\n\n"
        "Return only the INSERT INTO commands, but **in a Python list of strings format**, for example:\n"
        "["
        "    \"INSERT INTO clients (id, name, email) VALUES (1, 'Francisco Silva', 'francisco@email.com');\"",
        "    \"INSERT INTO clients (id, name, email) VALUES (2, 'Laura Lima', 'laura@email.com');\"",
        "    ..."
        "]"
        "### Observations\n"
        "* Only the list of strings with the SQL commands, as in the examples above\n"
        "* Do not return any markdown code block delimiters like ```json or ```sql\n",
    )


def get_user_message(creation_command: str) -> str:
    """
    Returns the user message for the database population prompt.
    """
    return creation_command
