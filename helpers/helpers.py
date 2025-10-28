import ast
import re
import random
import string
from datetime import datetime, timedelta
from collections import defaultdict, deque

import json
import logging

logger = logging.getLogger(__name__)


def process_llm_output(output: str):
    """
    Processa a saída do LLM de forma simples e robusta.
    Tenta diferentes métodos até conseguir fazer o parsing.
    """
    response_str = output.strip()

    response_str = re.sub(r"```(?:json|python|sql)?\s*", "", response_str)
    response_str = re.sub(r"```\s*", "", response_str)

    response_str = response_str.replace('"', '"').replace('"', '"')
    response_str = response_str.replace(""", "'").replace(""", "'")
    response_str = re.sub(r"\\'", "'", response_str)

    try:
        return json.loads(response_str)
    except Exception as _:
        pass

    try:
        return ast.literal_eval(response_str)
    except Exception as _:
        pass

    try:
        match = re.search(r"\[(.*)\]", response_str, re.DOTALL)
        if match:
            list_content = match.group(1)
            items = []

            for item in list_content.split(","):
                item = item.strip()
                if (item.startswith('"') and item.endswith('"')) or (
                    item.startswith("'") and item.endswith("'")
                ):
                    item = item[1:-1]
                if item:
                    items.append(item)
            return items

        pattern = r'["\']([^"\']*)["\']'
        matches = re.findall(pattern, response_str)
        if matches:
            return matches

    except Exception as e:
        logger.debug(f"Extração manual falhou: {e}")

    logger.error(f"Não foi possível processar: {repr(response_str[:100])}")
    raise ValueError(f"Falha ao processar a saída do LLM: {output[:50]}...")


def parse_create_table(creation_command: str):
    table_name = re.search(r"CREATE TABLE\s+`?(\w+)`?", creation_command, re.IGNORECASE)
    if not table_name:
        raise ValueError("Não foi possível identificar o nome da tabela")
    table_name = table_name.group(1)

    cols_block = re.search(r"\((.*)\)", creation_command, re.DOTALL)
    if not cols_block:
        raise ValueError("Não foi possível encontrar a definição das colunas")
    cols_block = cols_block.group(1)

    columns = []
    lines = [line.strip() for line in cols_block.split(",")]

    column_pattern = re.compile(
        r"`?(\w+)`?\s+([A-Z]+)(?:\((\d+)\))?([^,]*)", re.IGNORECASE
    )

    fk_columns = set()

    fk_pattern = re.compile(
        r"FOREIGN KEY\s*\(`?(\w+)`?\)\s+REFERENCES\s+`?(\w+)`?\s*\(`?(\w+)`?\)",
        re.IGNORECASE,
    )
    for line in lines:
        fk_match = fk_pattern.search(line)
        if fk_match:
            fk_col, ref_table, ref_col = fk_match.groups()
            fk_columns.add(fk_col)

    for line in lines:
        if re.match(
            r"^(PRIMARY|CONSTRAINT|UNIQUE|CHECK|KEY|FOREIGN)\b", line, re.IGNORECASE
        ):
            continue

        m = column_pattern.match(line)
        if m:
            col_name, col_type, col_size, col_rest = m.groups()
            columns.append(
                {
                    "name": col_name,
                    "type": col_type.upper(),
                    "size": int(col_size) if col_size else None,
                    "not_null": "NOT NULL" in col_rest.upper(),
                    "auto_inc": "AUTO_INCREMENT" in col_rest.upper(),
                    "primary_key": "PRIMARY KEY" in col_rest.upper(),
                    "foreign_key": col_name in fk_columns,
                }
            )

    return table_name, columns


def random_value(col, fk_values: dict, index: int):
    if col["auto_inc"]:
        return None

    if col["primary_key"]:
        if col["type"] in ("INT", "BIGINT", "SMALLINT"):
            return fk_values["INT"][index]

        elif col["type"] in ("CHAR", "VARCHAR", "TEXT"):
            return fk_values["VARCHAR"][index]

    if col["foreign_key"]:
        if col["type"] in ("INT", "BIGINT", "SMALLINT"):
            return fk_values["INT"][random.randint(0, len(fk_values["INT"]) - 1)]

        elif col["type"] in ("CHAR", "VARCHAR", "TEXT"):
            return fk_values["VARCHAR"][random.randint(0, len(fk_values["INT"]) - 1)]

    if col["type"] in ("INT", "BIGINT", "SMALLINT"):
        return random.randint(1, 1000)

    if col["type"] in ("DECIMAL", "NUMERIC", "FLOAT", "DOUBLE"):
        return round(random.uniform(1, 9999), 2)

    if col["type"] in ("CHAR", "VARCHAR", "TEXT"):
        size = col["size"] if col["size"] else 10
        size = min(size, 15)
        return "".join(random.choices(string.ascii_letters, k=random.randint(3, size)))

    if col["type"] in ("DATE",):
        start = datetime(2000, 1, 1)
        end = datetime(2025, 1, 1)
        return (start + timedelta(days=random.randint(0, (end - start).days))).strftime(
            "%Y-%m-%d"
        )

    if col["type"] in ("DATETIME", "TIMESTAMP"):
        start = datetime(2000, 1, 1)
        end = datetime(2025, 1, 1)
        dt = start + timedelta(
            seconds=random.randint(0, int((end - start).total_seconds()))
        )
        return dt.strftime("%Y-%m-%d %H:%M:%S")

    return None


def generate_inserts(
    creation_command: str, number_insertions: int, fk_values: dict
) -> list:
    table_name, columns = parse_create_table(creation_command)
    inserts = []

    for i in range(number_insertions):
        values = []

        for col in columns:
            val = random_value(col, fk_values, i)
            if val is None:
                values.append("NULL" if not col["not_null"] else "'X'")
            elif isinstance(val, str):
                values.append(f"'{val}'")
            else:
                values.append(str(val))

        col_names = [f"`{c['name']}`" for c in columns if not c["auto_inc"]]
        val_list = [values[i] for i, c in enumerate(columns) if not c["auto_inc"]]
        inserts.append(
            f"INSERT INTO `{table_name}` ({', '.join(col_names)}) VALUES ({', '.join(val_list)});"
        )

    return inserts


def parse_create_table_dependencies(create_table_sql):
    table_match = re.search(
        r"CREATE\s+TABLE\s+`?(\w+)`?", create_table_sql, re.IGNORECASE
    )
    if not table_match:
        raise ValueError(
            f"Não foi possível encontrar o nome da tabela em:\n{create_table_sql}"
        )
    table_name = table_match.group(1)

    fks = re.findall(r"REFERENCES\s+`?(\w+)`?", create_table_sql, re.IGNORECASE)
    return table_name, set(fks)


def order_create_tables(create_tables_sql_list):
    dependencies = defaultdict(set)
    dependents = defaultdict(set)
    tables = set()

    for sql in create_tables_sql_list:
        table, deps = parse_create_table_dependencies(sql)
        tables.add(table)
        dependencies[table] = deps
        for dep in deps:
            dependents[dep].add(table)

    indegree = {t: len(dependencies[t]) for t in tables}

    queue = deque([t for t in tables if indegree[t] == 0])
    ordered_tables = []

    while queue:
        t = queue.popleft()
        ordered_tables.append(t)
        for dep in dependents[t]:
            indegree[dep] -= 1
            if indegree[dep] == 0:
                queue.append(dep)

    if len(ordered_tables) != len(tables):
        raise ValueError("Ciclo detectado nas dependências das tabelas.")

    table_map = {
        parse_create_table_dependencies(sql)[0]: sql for sql in create_tables_sql_list
    }
    return [table_map[t] for t in ordered_tables]
