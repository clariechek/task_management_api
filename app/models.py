from datetime import datetime
from sqlalchemy import (
    Column, Integer, String, Text, Boolean, Date, DateTime,
    ForeignKey, Table, Index
)
from sqlalchemy.orm import relationship
from app.database import Base

# Create join table for many-to-many relationship between tasks and tags with composite key.
task_tags = Table(
    "task_tags",
    Base.metadata,
    Column("task_id", Integer, ForeignKey("tasks.id", ondelete="CASCADE"), primary_key=True),
    Column("tag_id", Integer, ForeignKey("tags.id", ondelete="CASCADE"), primary_key=True),
)


class Task(Base):
    """
    Represents a task in the task management system.
    - id: Unique identifier for the task.
    - title: Title of the task.
    - description: Optional description of the task.
    - priority: Priority level of the task (1-5).
    - due_date: Date the task is due.
    - completed: Completion status of the task.
    - is_deleted: Soft delete flag for the task.
    - created_at: Creation timestamp.
    - updated_at: Last modification timestamp.
    - tags: Many-to-many relationship with tags.
    """
    __tablename__ = "tasks"

    id = Column(Integer, primary_key=True, index=True)
    title = Column(String(200), nullable=False)
    description = Column(Text, nullable=True)
    priority = Column(Integer, nullable=False)
    due_date = Column(Date, nullable=False)
    completed = Column(Boolean, default=False, nullable=False)
    is_deleted = Column(Boolean, default=False, nullable=False) # For soft delete
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, onupdate=datetime.utcnow, nullable=True)

    # Links Task to Tags through the task_tags join table. 'back_populates' ensures bidirectional relationship.
    tags = relationship("Tag", secondary=task_tags, back_populates="tasks")

    __table_args__ = (
        # Indexes for common query patterns
        Index("idx_tasks_priority", "priority"),
        Index("idx_tasks_completed", "completed"),
        Index("idx_tasks_is_deleted", "is_deleted"),
        Index("idx_tasks_due_date", "due_date"),
    )


class Tag(Base):
    """
    Represents a tag in the task management system.
    - id: Unique identifier for the tag.
    - name: Name of the tag.
    - tasks: Many-to-many relationship with tasks.
    """
    __tablename__ = "tags"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(50), unique=True, nullable=False) # Unique constraint to ensure tag names are unique.

    # Links Tag to Tasks through the task_tags join table. 'back_populates' ensures bidirectional relationship.
    tasks = relationship("Task", secondary=task_tags, back_populates="tags")

    __table_args__ = (
        # Index for common query patterns
        Index("idx_tags_name", "name"),
    )
