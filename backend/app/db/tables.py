"""SQLAlchemy database models for acodeaday."""

import enum
import uuid
from datetime import date, datetime

from sqlalchemy import Boolean, Date, Enum, Float, ForeignKey, Index, Integer, String, Text, func
from sqlalchemy.dialects.postgresql import ARRAY, JSONB, UUID
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship


class Base(DeclarativeBase):
    """Base class for all models."""

    pass


class Difficulty(enum.StrEnum):
    """Problem difficulty levels."""

    EASY = "easy"
    MEDIUM = "medium"
    HARD = "hard"


class Language(enum.StrEnum):
    """Supported programming languages."""

    PYTHON = "python"
    JAVASCRIPT = "javascript"
    # Future languages can be added here:
    # JAVA = "java"
    # CPP = "cpp"
    # GO = "go"


class ChatMode(enum.StrEnum):
    """Chat assistant modes."""

    SOCRATIC = "socratic"
    DIRECT = "direct"


class MessageRole(enum.StrEnum):
    """Chat message roles."""

    USER = "user"
    ASSISTANT = "assistant"
    SYSTEM = "system"


class NotificationType(enum.StrEnum):
    """Telegram notification event types."""

    MORNING_DUE = "morning_due"
    DAY_SOLVED = "day_solved"
    EVENING_PENDING = "evening_pending"
    MORNING_FLASHCARDS = "morning_flashcards"


class RoadmapNodeDifficulty(enum.StrEnum):
    """Difficulty marker shown on roadmap nodes."""

    EASY = "easy"
    MEDIUM = "med"
    HARD = "hard"


class RoadmapItemType(enum.StrEnum):
    """Roadmap content item types."""

    TUTORIAL = "tutorial"
    TEMPLATE = "template"


class Problem(Base):
    """Core problem data from Blind 75."""

    __tablename__ = "problems"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    title: Mapped[str] = mapped_column(Text, nullable=False)
    slug: Mapped[str] = mapped_column(String(255), unique=True, nullable=False)
    description: Mapped[str] = mapped_column(Text, nullable=False)
    difficulty: Mapped[Difficulty] = mapped_column(Enum(Difficulty), nullable=False)
    # Patterns as ARRAY of strings (e.g., ["hash-map", "arrays", "complement-search"])
    pattern: Mapped[list[str]] = mapped_column(ARRAY(Text), nullable=False)

    # SEQUENCE_NUMBER: Determines order in Blind 75 (1-75)
    # Used to find "next unsolved problem": SELECT * WHERE sequence_number = (min unsolved)
    sequence_number: Mapped[int] = mapped_column(Integer, unique=True, nullable=False)

    # Constraints as ARRAY of strings (not JSONB)
    constraints: Mapped[list[str]] = mapped_column(ARRAY(Text), nullable=False)

    # Examples stored as JSONB (complex structure with input/output/explanation)
    examples: Mapped[dict] = mapped_column(JSONB, nullable=False)

    created_at: Mapped[datetime] = mapped_column(server_default=func.now())

    # Relationships
    languages: Mapped[list["ProblemLanguage"]] = relationship(
        back_populates="problem", cascade="all, delete", passive_deletes=True
    )
    test_cases: Mapped[list["TestCase"]] = relationship(
        back_populates="problem", cascade="all, delete", passive_deletes=True
    )
    user_progress: Mapped[list["UserProgress"]] = relationship(
        back_populates="problem", cascade="all, delete", passive_deletes=True
    )
    submissions: Mapped[list["Submission"]] = relationship(
        back_populates="problem", cascade="all, delete", passive_deletes=True
    )
    user_codes: Mapped[list["UserCode"]] = relationship(
        back_populates="problem", cascade="all, delete", passive_deletes=True
    )
    chat_sessions: Mapped[list["ChatSession"]] = relationship(
        back_populates="problem", cascade="all, delete", passive_deletes=True
    )
    user_notes: Mapped[list["UserProblemNote"]] = relationship(
        back_populates="problem", cascade="all, delete", passive_deletes=True
    )


class ProblemLanguage(Base):
    """Language-specific code and solutions for problems."""

    __tablename__ = "problem_languages"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    problem_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("problems.id", ondelete="CASCADE"), nullable=False
    )
    language: Mapped[Language] = mapped_column(
        Enum(Language), nullable=False
    )  # Python, JavaScript, etc.
    starter_code: Mapped[str] = mapped_column(Text, nullable=False)
    reference_solution: Mapped[str] = mapped_column(Text, nullable=False)

    # Function signature as JSONB: {"name": "twoSum", "params": [...], "return_type": "List[int]"}
    function_signature: Mapped[dict] = mapped_column(JSONB, nullable=False)

    created_at: Mapped[datetime] = mapped_column(server_default=func.now())

    # Relationship
    problem: Mapped["Problem"] = relationship(back_populates="languages")

    __table_args__ = (
        Index("ix_problem_languages_problem_id", "problem_id"),
        Index("ix_problem_languages_language", "language"),
    )


class TestCase(Base):
    """Test inputs and expected outputs for problems."""

    __tablename__ = "test_cases"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    problem_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("problems.id", ondelete="CASCADE"), nullable=False
    )

    # Input as JSONB array: [[2,7,11,15], 9] means twoSum([2,7,11,15], 9)
    input: Mapped[dict] = mapped_column(JSONB, nullable=False)  # Stored as JSON array

    # Expected output as JSONB: [0,1] or "hello" or {"key": "value"}
    expected: Mapped[dict] = mapped_column(JSONB, nullable=False)

    # Sequence determines order of test case execution
    sequence: Mapped[int] = mapped_column(Integer, nullable=False)

    created_at: Mapped[datetime] = mapped_column(server_default=func.now())

    # Relationship
    problem: Mapped["Problem"] = relationship(back_populates="test_cases")

    __table_args__ = (Index("ix_test_cases_problem_id", "problem_id"),)


class UserProgress(Base):
    """Tracks user's progress and spaced repetition for problems."""

    __tablename__ = "user_progress"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )

    # No auth.users table - user_id is just a string identifier (username)
    user_id: Mapped[str] = mapped_column(String(255), nullable=False)

    problem_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("problems.id", ondelete="CASCADE"), nullable=False
    )

    # Spaced repetition fields (legacy - kept for backwards compatibility)
    times_solved: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    last_solved_at: Mapped[datetime | None] = mapped_column(nullable=True)
    next_review_date: Mapped[date | None] = mapped_column(Date, nullable=True)
    is_mastered: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    show_again: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)

    # Anki SM-2 algorithm fields
    ease_factor: Mapped[float] = mapped_column(Float, default=2.5, nullable=False)
    interval_days: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    review_count: Mapped[int] = mapped_column(Integer, default=0, nullable=False)

    created_at: Mapped[datetime] = mapped_column(server_default=func.now())

    # Relationship
    problem: Mapped["Problem"] = relationship(back_populates="user_progress")

    __table_args__ = (
        Index("ix_user_progress_user_id", "user_id"),
        Index("ix_user_progress_problem_id", "problem_id"),
        Index("ix_user_progress_next_review_date", "next_review_date"),
        Index("ix_user_progress_user_problem", "user_id", "problem_id", unique=True),
    )


class Submission(Base):
    """History of all code submissions."""

    __tablename__ = "submissions"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    user_id: Mapped[str] = mapped_column(String(255), nullable=False)
    problem_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("problems.id", ondelete="CASCADE"), nullable=False
    )

    code: Mapped[str] = mapped_column(Text, nullable=False)
    language: Mapped[Language] = mapped_column(Enum(Language), nullable=False)
    passed: Mapped[bool] = mapped_column(Boolean, nullable=False)
    runtime_ms: Mapped[int | None] = mapped_column(Integer, nullable=True)
    memory_kb: Mapped[int | None] = mapped_column(Integer, nullable=True)

    # Test result summary (for displaying "X / Y testcases passed")
    total_test_cases: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    passed_count: Mapped[int] = mapped_column(Integer, default=0, nullable=False)

    # First failed test details (NULL if all passed)
    failed_test_number: Mapped[int | None] = mapped_column(Integer, nullable=True)
    failed_input: Mapped[dict | None] = mapped_column(JSONB, nullable=True)
    failed_output: Mapped[dict | None] = mapped_column(JSONB, nullable=True)
    failed_expected: Mapped[dict | None] = mapped_column(JSONB, nullable=True)

    submitted_at: Mapped[datetime] = mapped_column(server_default=func.now())

    # Relationship
    problem: Mapped["Problem"] = relationship(back_populates="submissions")

    __table_args__ = (Index("ix_submissions_user_problem", "user_id", "problem_id"),)


class UserCode(Base):
    """Stores user's current code for each problem (server-side code persistence)."""

    __tablename__ = "user_code"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    user_id: Mapped[str] = mapped_column(String(255), nullable=False)
    problem_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("problems.id", ondelete="CASCADE"), nullable=False
    )
    language: Mapped[str] = mapped_column(Text, default="python", nullable=False)
    code: Mapped[str] = mapped_column(Text, nullable=False)
    updated_at: Mapped[datetime] = mapped_column(
        server_default=func.now(), onupdate=func.now()
    )

    # Relationship
    problem: Mapped["Problem"] = relationship(back_populates="user_codes")

    __table_args__ = (
        Index("idx_user_code_user_problem", "user_id", "problem_id"),
        Index(
            "ix_user_code_unique", "user_id", "problem_id", "language", unique=True
        ),
    )


class ChatSession(Base):
    """AI chat sessions for problem-solving assistance."""

    __tablename__ = "chat_sessions"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    user_id: Mapped[str] = mapped_column(String(255), nullable=False)
    problem_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("problems.id", ondelete="CASCADE"), nullable=False
    )
    title: Mapped[str | None] = mapped_column(String(50), nullable=True)
    mode: Mapped[ChatMode] = mapped_column(
        Enum(ChatMode, values_callable=lambda obj: [e.value for e in obj]),
        nullable=False
    )
    model: Mapped[str | None] = mapped_column(String(100), nullable=True)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    created_at: Mapped[datetime] = mapped_column(server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(
        server_default=func.now(), onupdate=func.now()
    )

    # Relationships
    problem: Mapped["Problem"] = relationship(back_populates="chat_sessions")
    messages: Mapped[list["ChatMessage"]] = relationship(
        back_populates="session", cascade="all, delete", passive_deletes=True
    )

    __table_args__ = (
        Index("ix_chat_sessions_user_problem", "user_id", "problem_id"),
        Index("ix_chat_sessions_user_id", "user_id"),
    )


class ChatMessage(Base):
    """Messages within chat sessions."""

    __tablename__ = "chat_messages"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    session_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("chat_sessions.id", ondelete="CASCADE"), nullable=False
    )
    role: Mapped[MessageRole] = mapped_column(
        Enum(MessageRole, values_callable=lambda obj: [e.value for e in obj]),
        nullable=False
    )
    content: Mapped[str] = mapped_column(Text, nullable=False)
    code_snapshot: Mapped[str | None] = mapped_column(Text, nullable=True)
    test_results_snapshot: Mapped[dict | None] = mapped_column(JSONB, nullable=True)
    created_at: Mapped[datetime] = mapped_column(server_default=func.now())

    # Relationship
    session: Mapped["ChatSession"] = relationship(back_populates="messages")

    __table_args__ = (Index("ix_chat_messages_session_id", "session_id"),)


class UserProblemNote(Base):
    """User-owned problem metadata for external problem tracking and revision."""

    __tablename__ = "user_problem_notes"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    user_id: Mapped[str] = mapped_column(String(255), nullable=False)
    problem_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("problems.id", ondelete="CASCADE"), nullable=False
    )
    source_url: Mapped[str | None] = mapped_column(Text, nullable=True)
    personal_solution: Mapped[str | None] = mapped_column(Text, nullable=True)
    revision_notes: Mapped[str | None] = mapped_column(Text, nullable=True)
    is_reference_only: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    send_flashcard_to_telegram: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    flashcard_front: Mapped[str | None] = mapped_column(Text, nullable=True)
    flashcard_back: Mapped[str | None] = mapped_column(Text, nullable=True)
    tags: Mapped[list[str]] = mapped_column(ARRAY(Text), default=list, nullable=False)
    updated_at: Mapped[datetime] = mapped_column(
        server_default=func.now(), onupdate=func.now()
    )

    problem: Mapped["Problem"] = relationship(back_populates="user_notes")

    __table_args__ = (
        Index("ix_user_problem_notes_user_id", "user_id"),
        Index("ix_user_problem_notes_problem_id", "problem_id"),
        Index("ix_user_problem_notes_unique", "user_id", "problem_id", unique=True),
    )


class TelegramNotificationLog(Base):
    """Ensures daily Telegram notifications are sent once per user/type/day."""

    __tablename__ = "telegram_notification_logs"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    user_id: Mapped[str] = mapped_column(String(255), nullable=False)
    notification_date: Mapped[date] = mapped_column(Date, nullable=False)
    notification_type: Mapped[NotificationType] = mapped_column(
        Enum(NotificationType, values_callable=lambda obj: [e.value for e in obj]),
        nullable=False,
    )
    created_at: Mapped[datetime] = mapped_column(server_default=func.now())

    __table_args__ = (
        Index("ix_telegram_logs_user_id", "user_id"),
        Index(
            "ix_telegram_logs_unique",
            "user_id",
            "notification_date",
            "notification_type",
            unique=True,
        ),
    )


class UserFlashcard(Base):
    """Standalone user-created flashcards for revision."""

    __tablename__ = "user_flashcards"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    user_id: Mapped[str] = mapped_column(String(255), nullable=False)
    problem_id: Mapped[uuid.UUID | None] = mapped_column(
        ForeignKey("problems.id", ondelete="SET NULL"), nullable=True
    )
    front: Mapped[str] = mapped_column(Text, nullable=False)
    back: Mapped[str] = mapped_column(Text, nullable=False)
    tags: Mapped[list[str]] = mapped_column(ARRAY(Text), default=list, nullable=False)
    source_url: Mapped[str | None] = mapped_column(Text, nullable=True)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    last_reviewed_at: Mapped[datetime | None] = mapped_column(nullable=True)
    next_review_date: Mapped[date | None] = mapped_column(Date, nullable=True)
    created_at: Mapped[datetime] = mapped_column(server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(
        server_default=func.now(), onupdate=func.now()
    )

    problem: Mapped["Problem | None"] = relationship()

    __table_args__ = (
        Index("ix_user_flashcards_user_id", "user_id"),
        Index("ix_user_flashcards_problem_id", "problem_id"),
        Index("ix_user_flashcards_next_review_date", "next_review_date"),
        Index("ix_user_flashcards_user_active", "user_id", "is_active"),
    )


class Roadmap(Base):
    """Top-level roadmap definition."""

    __tablename__ = "roadmaps"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    slug: Mapped[str] = mapped_column(String(255), unique=True, nullable=False)
    title: Mapped[str] = mapped_column(Text, nullable=False)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    total_problem_goal: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    created_at: Mapped[datetime] = mapped_column(server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(
        server_default=func.now(), onupdate=func.now()
    )

    nodes: Mapped[list["RoadmapNode"]] = relationship(
        back_populates="roadmap", cascade="all, delete", passive_deletes=True
    )


class RoadmapNode(Base):
    """Positioned roadmap topic node."""

    __tablename__ = "roadmap_nodes"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    roadmap_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("roadmaps.id", ondelete="CASCADE"), nullable=False
    )
    slug: Mapped[str] = mapped_column(String(255), nullable=False)
    title: Mapped[str] = mapped_column(Text, nullable=False)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    difficulty: Mapped[RoadmapNodeDifficulty] = mapped_column(
        Enum(RoadmapNodeDifficulty, values_callable=lambda obj: [e.value for e in obj]),
        nullable=False,
        default=RoadmapNodeDifficulty.MEDIUM,
    )
    x: Mapped[int] = mapped_column(Integer, nullable=False)
    y: Mapped[int] = mapped_column(Integer, nullable=False)
    width: Mapped[int] = mapped_column(Integer, default=220, nullable=False)
    height: Mapped[int] = mapped_column(Integer, default=96, nullable=False)
    created_at: Mapped[datetime] = mapped_column(server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(
        server_default=func.now(), onupdate=func.now()
    )

    roadmap: Mapped["Roadmap"] = relationship(back_populates="nodes")
    items: Mapped[list["RoadmapItem"]] = relationship(
        back_populates="node", cascade="all, delete", passive_deletes=True
    )
    practice_links: Mapped[list["RoadmapNodeProblem"]] = relationship(
        back_populates="node", cascade="all, delete", passive_deletes=True
    )
    flashcard_links: Mapped[list["RoadmapNodeFlashcard"]] = relationship(
        back_populates="node", cascade="all, delete", passive_deletes=True
    )

    __table_args__ = (
        Index("ix_roadmap_nodes_roadmap_id", "roadmap_id"),
        Index("ix_roadmap_nodes_slug", "slug"),
        Index("ix_roadmap_nodes_roadmap_slug", "roadmap_id", "slug", unique=True),
    )


class RoadmapEdge(Base):
    """Explicit edge between two roadmap nodes."""

    __tablename__ = "roadmap_edges"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    roadmap_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("roadmaps.id", ondelete="CASCADE"), nullable=False
    )
    source_node_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("roadmap_nodes.id", ondelete="CASCADE"), nullable=False
    )
    target_node_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("roadmap_nodes.id", ondelete="CASCADE"), nullable=False
    )
    created_at: Mapped[datetime] = mapped_column(server_default=func.now())

    __table_args__ = (
        Index("ix_roadmap_edges_roadmap_id", "roadmap_id"),
        Index("ix_roadmap_edges_source_node_id", "source_node_id"),
        Index("ix_roadmap_edges_target_node_id", "target_node_id"),
    )


class RoadmapItem(Base):
    """Tutorial and template content attached to a node."""

    __tablename__ = "roadmap_items"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    roadmap_node_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("roadmap_nodes.id", ondelete="CASCADE"), nullable=False
    )
    item_type: Mapped[RoadmapItemType] = mapped_column(
        Enum(RoadmapItemType, values_callable=lambda obj: [e.value for e in obj]),
        nullable=False,
    )
    title: Mapped[str] = mapped_column(Text, nullable=False)
    body: Mapped[str | None] = mapped_column(Text, nullable=True)
    resource_url: Mapped[str | None] = mapped_column(Text, nullable=True)
    code_language: Mapped[str | None] = mapped_column(String(64), nullable=True)
    group_key: Mapped[str | None] = mapped_column(String(255), nullable=True)
    sort_order: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    created_at: Mapped[datetime] = mapped_column(server_default=func.now())

    node: Mapped["RoadmapNode"] = relationship(back_populates="items")

    __table_args__ = (
        Index("ix_roadmap_items_node_id", "roadmap_node_id"),
        Index("ix_roadmap_items_type", "item_type"),
    )


class UserRoadmapItemProgress(Base):
    """Manual completion state for roadmap items."""

    __tablename__ = "user_roadmap_item_progress"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    user_id: Mapped[str] = mapped_column(String(255), nullable=False)
    roadmap_item_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("roadmap_items.id", ondelete="CASCADE"), nullable=False
    )
    completed: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    completed_at: Mapped[datetime | None] = mapped_column(nullable=True)
    created_at: Mapped[datetime] = mapped_column(server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(
        server_default=func.now(), onupdate=func.now()
    )

    __table_args__ = (
        Index("ix_user_roadmap_item_progress_user_id", "user_id"),
        Index("ix_user_roadmap_item_progress_item_id", "roadmap_item_id"),
        Index(
            "ix_user_roadmap_item_progress_unique",
            "user_id",
            "roadmap_item_id",
            unique=True,
        ),
    )


class RoadmapNodeProblem(Base):
    """Link existing problems to roadmap nodes."""

    __tablename__ = "roadmap_node_problems"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    roadmap_node_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("roadmap_nodes.id", ondelete="CASCADE"), nullable=False
    )
    problem_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("problems.id", ondelete="CASCADE"), nullable=False
    )
    sort_order: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    created_at: Mapped[datetime] = mapped_column(server_default=func.now())

    node: Mapped["RoadmapNode"] = relationship(back_populates="practice_links")
    problem: Mapped["Problem"] = relationship()

    __table_args__ = (
        Index("ix_roadmap_node_problems_node_id", "roadmap_node_id"),
        Index("ix_roadmap_node_problems_problem_id", "problem_id"),
        Index(
            "ix_roadmap_node_problems_unique",
            "roadmap_node_id",
            "problem_id",
            unique=True,
        ),
    )


class RoadmapNodeFlashcard(Base):
    """Explicit link from a user flashcard to a roadmap node."""

    __tablename__ = "roadmap_node_flashcards"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    roadmap_node_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("roadmap_nodes.id", ondelete="CASCADE"), nullable=False
    )
    flashcard_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("user_flashcards.id", ondelete="CASCADE"), nullable=False
    )
    created_at: Mapped[datetime] = mapped_column(server_default=func.now())

    node: Mapped["RoadmapNode"] = relationship(back_populates="flashcard_links")
    flashcard: Mapped["UserFlashcard"] = relationship()

    __table_args__ = (
        Index("ix_roadmap_node_flashcards_node_id", "roadmap_node_id"),
        Index("ix_roadmap_node_flashcards_flashcard_id", "flashcard_id"),
        Index(
            "ix_roadmap_node_flashcards_unique",
            "roadmap_node_id",
            "flashcard_id",
            unique=True,
        ),
    )
