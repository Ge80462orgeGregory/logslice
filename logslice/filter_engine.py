"""Filter engine that applies parsed queries to streams of JSON log entries."""

import json
from typing import Iterable, Iterator, List, Optional

from logslice.query_parser import QueryExpression, evaluate, parse_query, QueryParseError


class FilterEngine:
    """Applies one or more query expressions to JSON log lines."""

    def __init__(self, queries: Optional[List[str]] = None):
        self.expressions: List[QueryExpression] = []
        if queries:
            for q in queries:
                self.add_query(q)

    def add_query(self, query: str) -> None:
        """Parse and register a query expression."""
        expr = parse_query(query)
        self.expressions.append(expr)

    def matches(self, entry: dict) -> bool:
        """Return True if the entry satisfies ALL registered expressions."""
        return all(evaluate(entry, expr) for expr in self.expressions)

    def filter_lines(self, lines: Iterable[str]) -> Iterator[dict]:
        """Yield parsed JSON entries that match all query expressions.

        Silently skips lines that are not valid JSON.
        """
        for line in lines:
            line = line.strip()
            if not line:
                continue
            try:
                entry = json.loads(line)
            except json.JSONDecodeError:
                continue
            if not isinstance(entry, dict):
                continue
            if self.matches(entry):
                yield entry

    def filter_file(self, path: str) -> Iterator[dict]:
        """Open a file and yield matching log entries."""
        with open(path, "r", encoding="utf-8") as fh:
            yield from self.filter_lines(fh)
