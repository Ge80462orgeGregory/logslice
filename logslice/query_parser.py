"""Simple query parser for filtering structured JSON log entries."""

import re
from dataclasses import dataclass
from typing import Any, Optional

OPERATORS = [">=", "<=", "!=", ">", "<", "=", "~"]


@dataclass
class QueryExpression:
    field: str
    operator: str
    value: Any


class QueryParseError(Exception):
    pass


def _coerce_value(value: str) -> Any:
    """Try to coerce a string value to int or float, else return as-is."""
    try:
        return int(value)
    except ValueError:
        pass
    try:
        return float(value)
    except ValueError:
        pass
    return value


def parse_query(query: str) -> QueryExpression:
    """Parse a query string like 'level=error' or 'status>=400'.

    Supported operators: =, !=, >, <, >=, <=, ~ (contains/regex)
    """
    query = query.strip()
    for op in OPERATORS:
        idx = query.find(op)
        if idx > 0:
            field = query[:idx].strip()
            value = query[idx + len(op):].strip()
            if not field:
                raise QueryParseError(f"Missing field name in query: {query!r}")
            if not value:
                raise QueryParseError(f"Missing value in query: {query!r}")
            return QueryExpression(field=field, operator=op, value=_coerce_value(value))
    raise QueryParseError(f"No valid operator found in query: {query!r}")


def evaluate(entry: dict, expr: QueryExpression) -> bool:
    """Evaluate a QueryExpression against a log entry dict."""
    value = entry
    for part in expr.field.split("."):
        if not isinstance(value, dict) or part not in value:
            return False
        value = value[part]

    op = expr.operator
    target = expr.value

    try:
        if op == "=":
            return str(value).lower() == str(target).lower()
        elif op == "!=":
            return str(value).lower() != str(target).lower()
        elif op == ">":
            return float(value) > float(target)
        elif op == "<":
            return float(value) < float(target)
        elif op == ">=":
            return float(value) >= float(target)
        elif op == "<=":
            return float(value) <= float(target)
        elif op == "~":
            return bool(re.search(str(target), str(value), re.IGNORECASE))
    except (TypeError, ValueError):
        return False

    return False
