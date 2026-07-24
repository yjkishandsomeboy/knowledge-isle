"""Add document chunks and chunk-level citation metadata."""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "20260724_0005"
down_revision: str | None = "20260723_0004"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "document_chunks",
        sa.Column("id", sa.String(length=36), nullable=False),
        sa.Column("document_id", sa.String(length=36), nullable=False),
        sa.Column("chunk_index", sa.Integer(), nullable=False),
        sa.Column("content", sa.Text(), nullable=False),
        sa.Column("start_offset", sa.Integer(), nullable=False),
        sa.Column("end_offset", sa.Integer(), nullable=False),
        sa.Column("char_count", sa.Integer(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["document_id"], ["documents.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("document_id", "chunk_index"),
    )
    op.create_index(op.f("ix_document_chunks_document_id"), "document_chunks", ["document_id"])
    op.add_column("citations", sa.Column("chunk_id", sa.String(length=36), nullable=True))
    op.add_column("citations", sa.Column("start_offset", sa.Integer(), nullable=True))
    op.add_column("citations", sa.Column("end_offset", sa.Integer(), nullable=True))
    op.create_index(op.f("ix_citations_chunk_id"), "citations", ["chunk_id"])
    op.create_foreign_key(
        "fk_citations_chunk_id_document_chunks", "citations", "document_chunks", ["chunk_id"], ["id"], ondelete="SET NULL"
    )


def downgrade() -> None:
    op.drop_constraint("fk_citations_chunk_id_document_chunks", "citations", type_="foreignkey")
    op.drop_index(op.f("ix_citations_chunk_id"), table_name="citations")
    op.drop_column("citations", "end_offset")
    op.drop_column("citations", "start_offset")
    op.drop_column("citations", "chunk_id")
    op.drop_index(op.f("ix_document_chunks_document_id"), table_name="document_chunks")
    op.drop_table("document_chunks")
