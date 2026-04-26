from sqlalchemy import Column, Integer, String, Text, ForeignKey, CheckConstraint, DateTime
from sqlalchemy.orm import DeclarativeBase, relationship
from datetime import datetime, timezone, timedelta


class Base(DeclarativeBase):
    pass


_BEIJING = timezone(timedelta(hours=8))


def _now():
    return datetime.now(_BEIJING).strftime("%Y-%m-%d %H:%M:%S")


class PaperLibrary(Base):
    __tablename__ = "paper_libraries"

    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(Text, nullable=False)
    domain_description = Column(Text, nullable=False)
    created_at = Column(Text, nullable=False, default=_now)

    papers = relationship("PaperLibraryAssoc", back_populates="library")


class Paper(Base):
    __tablename__ = "papers"
    __table_args__ = (
        CheckConstraint("source IN ('llm_search', 'manual')", name="ck_paper_source"),
    )

    id = Column(Integer, primary_key=True, autoincrement=True)
    title = Column(Text, nullable=False)
    authors = Column(Text)
    institution = Column(Text)
    abstract = Column(Text)
    structured_summary = Column(Text)
    source = Column(Text, nullable=False)
    published_date = Column(Text)
    source_url = Column(Text)
    pdf_path = Column(Text)
    keywords = Column(Text)
    deep_reading_summary = Column(Text)
    created_at = Column(Text, nullable=False, default=_now)

    library_assocs = relationship("PaperLibraryAssoc", back_populates="paper")
    idea_refs = relationship("IdeaReference", back_populates="paper")
    task_refs = relationship("TaskReference", back_populates="paper")


class PaperLibraryAssoc(Base):
    __tablename__ = "paper_library"

    paper_id = Column(Integer, ForeignKey("papers.id"), primary_key=True)
    library_id = Column(Integer, ForeignKey("paper_libraries.id"), primary_key=True)
    is_read = Column(Integer, nullable=False, default=0)
    is_interested = Column(Integer, nullable=False, default=0)

    paper = relationship("Paper", back_populates="library_assocs")
    library = relationship("PaperLibrary", back_populates="papers")


class Idea(Base):
    __tablename__ = "ideas"

    id = Column(Integer, primary_key=True, autoincrement=True)
    title = Column(Text, nullable=False)
    content = Column(Text)
    status = Column(Text, nullable=False, default="锤炼中")
    created_at = Column(Text, nullable=False, default=_now)
    updated_at = Column(Text, nullable=False, default=_now)

    references = relationship("IdeaReference", back_populates="idea")
    task = relationship("Task", back_populates="source_idea", uselist=False)


class IdeaReference(Base):
    __tablename__ = "idea_references"

    idea_id = Column(Integer, ForeignKey("ideas.id"), primary_key=True)
    paper_id = Column(Integer, ForeignKey("papers.id"), primary_key=True)

    idea = relationship("Idea", back_populates="references")
    paper = relationship("Paper", back_populates="idea_refs")


class Task(Base):
    __tablename__ = "tasks"

    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(Text, nullable=False)
    research_goal = Column(Text)
    source_idea_id = Column(Integer, ForeignKey("ideas.id"), nullable=True)
    created_at = Column(Text, nullable=False, default=_now)

    source_idea = relationship("Idea", back_populates="task")
    references = relationship("TaskReference", back_populates="task")
    experiments = relationship("Experiment", back_populates="task")
    conversations = relationship("Conversation", back_populates="task")


class TaskReference(Base):
    __tablename__ = "task_references"

    task_id = Column(Integer, ForeignKey("tasks.id"), primary_key=True)
    paper_id = Column(Integer, ForeignKey("papers.id"), primary_key=True)
    bibtex = Column(Text)
    tags = Column(Text)
    added_at = Column(Text, nullable=False, default=_now)

    task = relationship("Task", back_populates="references")
    paper = relationship("Paper", back_populates="task_refs")


class Experiment(Base):
    __tablename__ = "experiments"

    id = Column(Integer, primary_key=True, autoincrement=True)
    task_id = Column(Integer, ForeignKey("tasks.id"), nullable=False)
    log_path = Column(Text, nullable=False)
    analysis_report = Column(Text)
    created_at = Column(Text, nullable=False, default=_now)

    task = relationship("Task", back_populates="experiments")


class EvolutionLog(Base):
    __tablename__ = "evolution_logs"

    id = Column(Integer, primary_key=True, autoincrement=True)
    content = Column(Text, nullable=False)
    source = Column(Text)
    dimension = Column(Text, nullable=False)
    level = Column(Integer, nullable=False)
    skill_name = Column(Text, nullable=False)
    created_at = Column(Text, nullable=False, default=_now)


class OperationLog(Base):
    __tablename__ = "operation_logs"

    id = Column(Integer, primary_key=True, autoincrement=True)
    operation_type = Column(Text, nullable=False)
    operation_object = Column(Text)
    result = Column(Text)
    timestamp = Column(Text, nullable=False, default=_now)


class LLMProviderConfig(Base):
    __tablename__ = "llm_provider_configs"

    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(Text, nullable=False)
    base_url = Column(Text, nullable=False)
    api_key = Column(Text, nullable=False)
    model = Column(Text, nullable=False)
    max_context_tokens = Column(Integer, nullable=False, default=131072)
    extra_body = Column(Text)
    is_active = Column(Integer, nullable=False, default=0)
    created_at = Column(Text, nullable=False, default=_now)


class LLMUsage(Base):
    __tablename__ = "llm_usage"

    id = Column(Integer, primary_key=True, autoincrement=True)
    scenario = Column(Text, nullable=False)
    model = Column(Text, nullable=False)
    input_tokens = Column(Integer, nullable=False)
    output_tokens = Column(Integer, nullable=False)
    timestamp = Column(Text, nullable=False, default=_now)


class Conversation(Base):
    __tablename__ = "conversations"

    id = Column(Integer, primary_key=True, autoincrement=True)
    task_id = Column(Integer, ForeignKey("tasks.id"), nullable=True)
    scenario = Column(Text, nullable=False)
    created_at = Column(Text, nullable=False, default=_now)
    updated_at = Column(Text, nullable=False, default=_now)

    task = relationship("Task", back_populates="conversations")
    messages = relationship("ConversationMessage", back_populates="conversation")


class ConversationMessage(Base):
    __tablename__ = "conversation_messages"

    id = Column(Integer, primary_key=True, autoincrement=True)
    conversation_id = Column(Integer, ForeignKey("conversations.id"), nullable=False)
    role = Column(Text, nullable=False)
    content = Column(Text, nullable=False)
    timestamp = Column(Text, nullable=False, default=_now)

    conversation = relationship("Conversation", back_populates="messages")


class PaperNote(Base):
    __tablename__ = "paper_notes"

    id = Column(Integer, primary_key=True, autoincrement=True)
    paper_id = Column(Integer, ForeignKey("papers.id"), nullable=False)
    content = Column(Text, nullable=False)
    created_at = Column(Text, nullable=False, default=_now)

    paper = relationship("Paper")


class WeeklyReport(Base):
    __tablename__ = "weekly_reports"

    id = Column(Integer, primary_key=True, autoincrement=True)
    library_id = Column(Integer, ForeignKey("paper_libraries.id"), nullable=False)
    week_start = Column(Text, nullable=False)
    week_end = Column(Text, nullable=False)
    content = Column(Text, nullable=False)
    created_at = Column(Text, nullable=False, default=_now)

    library = relationship("PaperLibrary")
