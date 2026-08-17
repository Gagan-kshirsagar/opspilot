"""Document and DocumentChunk ORM models for Knowledge Base and RAG."""

from __future__ import annotations

import enum
import uuid
from typing import TYPE_CHECKING, Any

from pgvector.sqlalchemy import Vector
from sqlalchemy import Enum, ForeignKey, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base, TimestampMixin, UUIDPrimaryKeyMixin

if TYPE_CHECKING:
    pass


class DocumentKind(str, enum.Enum):
    """Classification of knowledge base documents."""

    RUNBOOK = "runbook"
    POLICY = "policy"
    SLA = "sla"
    FAQ = "faq"
    GUIDE = "guide"


class Document(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    """Represents a high-level knowledge base source document."""

    __tablename__ = "documents"

    title: Mapped[str] = mapped_column(
        String(255), unique=True, nullable=False, index=True
    )
    source: Mapped[str] = mapped_column(String(255), nullable=False)
    kind: Mapped[DocumentKind] = mapped_column(
        Enum(DocumentKind, native_enum=False, length=50),
        nullable=False,
        default=DocumentKind.GUIDE,
        index=True,
    )

    # Relationships
    chunks: Mapped[list[DocumentChunk]] = relationship(
        "DocumentChunk",
        back_populates="document",
        cascade="all, delete-orphan",
        order_by="DocumentChunk.ordinal",
        lazy="selectin",
    )


class DocumentChunk(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    """A chunked section of a document stored with embedding vector."""

    __tablename__ = "document_chunks"

    document_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("documents.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    ordinal: Mapped[int] = mapped_column(Integer, nullable=False)
    content: Mapped[str] = mapped_column(Text, nullable=False)
    token_count: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    embedding: Mapped[Any] = mapped_column(Vector(768), nullable=False)

    # Relationships
    document: Mapped[Document] = relationship("Document", back_populates="chunks", lazy="selectin")
