"""Mock InfinityDB implementation for testing and platforms without support."""

from pathlib import Path
from typing import Any

import numpy as np
import polars as pl


class MockDatabase:
    """Mock database implementation."""

    def __init__(self, name: str):
        self.name = name
        self.tables: dict[str, dict[str, Any]] = {}

    def create_table(self, table_name: str, schema: dict[str, Any]) -> None:
        """Create a table."""
        if table_name not in self.tables:
            self.tables[table_name] = {"schema": schema, "data": []}

    def get_table(self, table_name: str) -> "MockTable":
        """Get a table."""
        if table_name not in self.tables:
            raise ValueError(f"Table {table_name} not found")
        return MockTable(self, table_name)


class MockTable:
    """Mock table implementation."""

    def __init__(self, db: MockDatabase, name: str):
        self.db = db
        self.name = name

    def insert(self, records: list[dict[str, Any]]) -> None:
        """Insert records."""
        self.db.tables[self.name]["data"].extend(records)

    def output(self, columns: list[str]) -> "MockQuery":
        """Start a query."""
        return MockQuery(self, columns)


class MockQuery:
    """Mock query implementation."""

    def __init__(self, table: MockTable, columns: list[str]):
        self.table = table
        self.columns = columns
        self.filters: list[str] = []
        self.vector_search: dict[str, Any] | None = None

    def match_dense(
        self,
        column: str,
        query_vector: list[float],
        dtype: str,
        metric: str,
        limit: int,
    ) -> "MockQuery":
        """Add vector search."""
        self.vector_search = {
            "column": column,
            "query_vector": np.array(query_vector),
            "metric": metric,
            "limit": limit,
        }
        return self

    def filter(self, condition: str) -> "MockQuery":
        """Add filter condition."""
        self.filters.append(condition)
        return self

    def to_pl(self) -> pl.DataFrame:
        """Execute query and return polars DataFrame."""
        # Get all data
        data = self.table.db.tables[self.table.name]["data"]

        # Apply filters
        filtered_data = []
        for record in data:
            include = True
            for filter_cond in self.filters:
                # Simple filter parsing (e.g., "field = 'value'")
                if " = " in filter_cond:
                    field, value = filter_cond.split(" = ")
                    value = value.strip("'\"")
                    if record.get(field) != value:
                        include = False
                        break
            if include:
                filtered_data.append(record)

        # Apply vector search if specified
        if self.vector_search and filtered_data:
            # Calculate similarities
            similarities = []
            for record in filtered_data:
                vec = np.array(record[self.vector_search["column"]])
                query = self.vector_search["query_vector"]

                if self.vector_search["metric"] == "cosine":
                    # Cosine similarity
                    sim = np.dot(vec, query) / (
                        np.linalg.norm(vec) * np.linalg.norm(query)
                    )
                elif self.vector_search["metric"] == "ip":
                    # Inner product
                    sim = np.dot(vec, query)
                else:
                    sim = 0.0

                similarities.append((sim, record))

            # Sort by similarity and limit
            similarities.sort(key=lambda x: x[0], reverse=True)
            filtered_data = [r for _, r in similarities[: self.vector_search["limit"]]]

        # Return as polars DataFrame
        if filtered_data:
            return pl.DataFrame(filtered_data)
        else:
            # Return empty DataFrame with schema
            return pl.DataFrame()


class MockInfinity:
    """Mock Infinity connection."""

    def __init__(self, path: str):
        self.path = Path(path)
        self.databases: dict[str, MockDatabase] = {}

    def create_database(self, name: str) -> None:
        """Create a database."""
        if name not in self.databases:
            self.databases[name] = MockDatabase(name)

    def get_database(self, name: str) -> MockDatabase:
        """Get a database."""
        if name not in self.databases:
            self.create_database(name)
        return self.databases[name]


def connect(path: str) -> MockInfinity:
    """Connect to mock InfinityDB."""
    return MockInfinity(path)
