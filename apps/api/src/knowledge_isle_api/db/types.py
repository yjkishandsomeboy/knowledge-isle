from typing import Any

from pgvector.sqlalchemy import Vector
from sqlalchemy import JSON, TypeDecorator


class EmbeddingVector(TypeDecorator[list[float]]):
    """Use pgvector in PostgreSQL and JSON in SQLite-based unit tests."""

    cache_ok = True
    impl = JSON

    def __init__(self, dimensions: int, **kwargs: Any) -> None:
        self.dimensions = dimensions
        super().__init__(**kwargs)

    def load_dialect_impl(self, dialect: Any) -> Any:
        if dialect.name == "postgresql":
            return dialect.type_descriptor(Vector(self.dimensions))
        return dialect.type_descriptor(JSON())
