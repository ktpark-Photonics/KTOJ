from datetime import datetime, timezone

from sqlalchemy import ForeignKey, String, Text
from sqlalchemy.orm import (DeclarativeBase, Mapped, mapped_column,
                            relationship)


class Base(DeclarativeBase):
    pass


class Problem(Base):
    __tablename__ = "problems"
    id: Mapped[int] = mapped_column(primary_key=True)
    slug: Mapped[str] = mapped_column(String(100), unique=True, index=True)
    title: Mapped[str] = mapped_column(String(200))
    statement: Mapped[str] = mapped_column(Text)
    difficulty: Mapped[str] = mapped_column(String(20))
    time_limit_ms: Mapped[int] = mapped_column(default=1000)
    memory_limit_mb: Mapped[int] = mapped_column(default=128)
    starter_code: Mapped[str | None] = mapped_column(Text, default=None)
    testcases: Mapped[list["TestCase"]] = relationship(
        back_populates="problem", cascade="all, delete-orphan",
        order_by="TestCase.ordinal")


class TestCase(Base):
    __test__ = False
    __tablename__ = "testcases"
    id: Mapped[int] = mapped_column(primary_key=True)
    problem_id: Mapped[int] = mapped_column(ForeignKey("problems.id"))
    ordinal: Mapped[int] = mapped_column(default=1)
    input: Mapped[str] = mapped_column(Text)
    expected_output: Mapped[str] = mapped_column(Text)
    is_sample: Mapped[bool] = mapped_column(default=False)
    problem: Mapped["Problem"] = relationship(back_populates="testcases")


class Submission(Base):
    __tablename__ = "submissions"
    id: Mapped[int] = mapped_column(primary_key=True)
    problem_id: Mapped[int] = mapped_column(ForeignKey("problems.id"))
    language: Mapped[str] = mapped_column(String(20))
    source_code: Mapped[str] = mapped_column(Text)
    status: Mapped[str] = mapped_column(String(10), default="PENDING",
                                        index=True)
    time_ms: Mapped[int | None] = mapped_column(default=None)
    memory_kb: Mapped[int | None] = mapped_column(default=None)
    failed_case_no: Mapped[int | None] = mapped_column(default=None)
    message: Mapped[str | None] = mapped_column(Text, default=None)
    created_at: Mapped[datetime] = mapped_column(
        default=lambda: datetime.now(timezone.utc))
