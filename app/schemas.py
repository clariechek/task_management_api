from datetime import date, datetime
from typing import Optional
from pydantic import BaseModel, Field, field_validator

class TaskCreate(BaseModel):
    """
    Task creation request schema. Validates the request data before creating a task via POST /tasks endpoint.
    - title: Task title (required, max 200 chars).
    - description: Task description (optional).
    - priority: Priority level (1-5, where 1 is lowest and 5 is highest).
    - due_date: Due date in ISO format (YYYY-MM-DD). Must be in the future.
    - tags: List of tag names (optional).
    """
    title: str = Field(..., min_length=1, max_length=200, description="Task title (required, max 200 chars)")
    description: Optional[str] = Field(None, description="Task description (optional)")
    priority: int = Field(..., ge=1, le=5, description="Priority level (1-5, where 5 is highest)")
    due_date: date = Field(..., description="Due date in ISO format (YYYY-MM-DD). Must not be in the past.")
    tags: Optional[list[str]] = Field(default=[], description="List of tag names (optional)")

    @field_validator("due_date")
    @classmethod
    def due_date_not_in_past(cls, v: date) -> date:
        if v < date.today():
            raise ValueError("Due date cannot be in the past")
        return v
    
    @field_validator("tags")
    @classmethod
    def validate_tags(cls, v: Optional[list[str]]) -> Optional[list[str]]:
        """Validate the tags list. Normalize the tag names to lowercase and strip whitespace.
        - v: The tags list to validate.
        - Returns: The validated tags list.
        - Raises: ValueError if the tag names are empty.
        """
        if v is None:
            return v
        validated = []
        for tag in v:
            normalized_name = tag.lower().strip()
            if not normalized_name:
                raise ValueError("Tag names cannot be empty")
            validated.append(normalized_name)
        return validated

    class Config:
        """
        Config for the TaskCreate model.
        - json_schema_extra: Example of the task create request to be used in the API documentation.
        """
        json_schema_extra = {
            "example": {
                "title": "Complete report",
                "description": "Complete case management report for Patient X",
                "priority": 3,
                "due_date": "2026-03-01",
                "tags": ["work", "urgent"]
            }
        }


class TaskUpdate(BaseModel):
    """
    Task update request schema. Validates the request data before partially updating a task via PATCH /tasks/{task_id} endpoint.
    """
    title: Optional[str] = Field(None, min_length=1, max_length=200)
    description: Optional[str] = None
    priority: Optional[int] = Field(None, ge=1, le=5)
    due_date: Optional[date] = None
    completed: Optional[bool] = None
    tags: Optional[list[str]] = None

    @field_validator("due_date")
    @classmethod
    def due_date_not_in_past(cls, v: Optional[date]) -> Optional[date]:
        if v is not None and v < date.today():
            raise ValueError("Due date cannot be in the past")
        return v
    
    @field_validator("tags")
    @classmethod
    def validate_tags(cls, v: Optional[list[str]]) -> Optional[list[str]]:
        """Validate the tags list. Normalize the tag names to lowercase and strip whitespace.
        - v: The tags list to validate.
        - Returns: The validated tags list.
        - Raises: ValueError if the tag names are empty.
        """
        if v is None:
            return v
        validated = []
        for tag in v:
            normalized_name = tag.lower().strip()
            if not normalized_name:
                raise ValueError("Tag names cannot be empty")
            validated.append(normalized_name)
        return validated


class TaskResponse(BaseModel):
    """
    Task response schema. Returns the task details after creation or retrieval via GET /tasks/{task_id} endpoint.
    - id: Task ID from the database.
    - title: Task title.
    - description: Task description.
    - priority: Task priority level.
    - due_date: Task due date.
    - completed: Task completion status.
    - is_deleted: Task soft delete status.
    - created_at: Task creation timestamp.
    - updated_at: Task last modification timestamp.
    - tags: List of tag names associated with the task.
    """

    id: int
    title: str
    description: Optional[str]
    priority: int
    due_date: date
    completed: bool
    is_deleted: bool
    created_at: datetime
    updated_at: Optional[datetime]
    tags: list[str]

    class Config:
        """
        Config for the TaskResponse model.
        - from_attributes: Allows Pydantic to convert SQLAlchemy models to Pydantic models for model validation.
        """
        from_attributes = True


class TaskListResponse(BaseModel):
    """
    Task list response schema. Returns a paginated list of tasks after filtering via GET /tasks endpoint.
    - total: Total number of tasks matching the filter.
    - limit: Number of results per page.
    - offset: Number of results skipped.
    - tasks: List of task responses.
    """
    total: int = Field(..., description="Total number of tasks matching the filter")
    limit: int = Field(..., description="Number of results per page")
    offset: int = Field(..., description="Number of results skipped")
    tasks: list[TaskResponse]


class ErrorDetail(BaseModel):
    """
    Error response schema. Returns an error message and details after an error occurs.
    - error: Error message.
    - details: Dictionary of error details.
    """
    error: str
    details: dict[str, str]
