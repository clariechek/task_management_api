from fastapi import APIRouter, Depends, HTTPException, Query, Path
from sqlalchemy.orm import Session
from app.database import get_db
from app.schemas import (
    TaskCreate, TaskUpdate, TaskResponse, TaskListResponse
)
from app import crud

router = APIRouter(prefix="/tasks", tags=["Tasks"])


def task_to_response(task) -> TaskResponse:
    """Convert SQLAlchemy Task model to TaskResponse schema."""
    return TaskResponse(
        id=task.id,
        title=task.title,
        description=task.description,
        priority=task.priority,
        due_date=task.due_date,
        completed=task.completed,
        is_deleted=task.is_deleted,
        created_at=task.created_at,
        updated_at=task.updated_at,
        tags=[tag.name for tag in task.tags], # Convert SQLAlchemy Tag models to string names for Pydantic model validation.
    )


@router.post(
    "",
    response_model=TaskResponse,
    status_code=201,
    summary="Create a new task",
    responses={
        201: {"description": "Task created successfully"},
        422: {"description": "Validation error"},
    },
)
def create_task(task_data: TaskCreate, db: Session = Depends(get_db)):
    """
    Create a new task with the following fields:
    
    - **title**: Required, non-empty, max 200 characters
    - **description**: Optional task description
    - **priority**: Integer 1-5 (5 is highest priority)
    - **due_date**: Date in YYYY-MM-DD format, must not be in the past
    - **tags**: Optional list of tag names

    Args:
        task_data: TaskCreate schema containing the task data. Pydantic model validation is performed.
        db: Database session dependency.
    Returns:
        TaskResponse schema containing the created task.
    """
    task = crud.create_task(db, task_data) # parse JSON into TaskCreate schema and create task in database.
    return task_to_response(task) # Convert to TaskResponse schema


@router.get(
    "",
    response_model=TaskListResponse,
    summary="List tasks with filtering and pagination",
)
def get_tasks(
    completed: bool | None = Query(None, description="Filter by completion status"),
    priority: int | None = Query(None, ge=1, le=5, description="Filter by priority level (1-5)"),
    tags: str | None = Query(None, description="Comma-separated tag names (e.g., work,urgent)"),
    limit: int = Query(10, ge=1, le=100, description="Number of results per page"),
    offset: int = Query(0, ge=0, description="Number of results to skip"),
    db: Session = Depends(get_db),
):
    """
    Retrieve a paginated list of tasks with optional filtering.
    
    - **completed**: Filter by completion status (true/false)
    - **priority**: Filter by specific priority level
    - **tags**: Filter by tags (comma-separated, matches any)
    - **limit/offset**: Pagination controls

    Args:
        completed: Filter by completion status (true/false).
        priority: Filter by specific priority level.
        tags: Filter by tags (comma-separated, matches any).
        limit: Number of results per page.
        offset: Number of results to skip.
        db: Database session dependency.
    Returns:
        TaskListResponse schema containing the list of tasks.
    """
    # Convert comma-separated tags into list of strings.
    tag_list = [t.strip() for t in tags.split(",")] if tags else None
    tasks, total = crud.get_tasks(
        db,
        completed=completed,
        priority=priority,
        tags=tag_list,
        limit=limit,
        offset=offset,
    )
    return TaskListResponse(
        total=total,
        limit=limit,
        offset=offset,
        tasks=[task_to_response(t) for t in tasks],
    )


@router.get(
    "/{task_id}",
    response_model=TaskResponse,
    summary="Get a task by ID",
    responses={
        200: {"description": "Task found"},
        404: {"description": "Task not found"},
    },
)
def get_task(
    task_id: int = Path(..., description="The ID of the task to retrieve"),
    db: Session = Depends(get_db),
):
    """
    Retrieve a single task by its ID.
    Args:
        task_id: The ID of the task to retrieve.
        db: Database session dependency.
    Returns:
        TaskResponse schema containing the task.
    """
    task = crud.get_task(db, task_id)
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")
    return task_to_response(task)


@router.patch(
    "/{task_id}",
    response_model=TaskResponse,
    summary="Partially update a task",
    responses={
        200: {"description": "Task updated successfully"},
        404: {"description": "Task not found"},
        422: {"description": "Validation error"},
    },
)
def update_task(
    task_data: TaskUpdate,
    task_id: int = Path(..., description="The ID of the task to update"),
    db: Session = Depends(get_db),
):
    """
    Partially update a task. Only fields provided in the request body will be modified.
    
    - **title**: Update task title (max 200 chars)
    - **description**: Update description
    - **priority**: Update priority (1-5)
    - **due_date**: Update due date (must not be in the past)
    - **completed**: Mark task as completed/incomplete
    - **tags**: Replace all tags with new list

    Args:
        task_data: TaskUpdate schema containing the task data. Pydantic model validation is performed.
        task_id: The ID of the task to update.
        db: Database session dependency.
    Returns:
        TaskResponse schema containing the updated task.
    """
    task = crud.update_task(db, task_id, task_data)
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")
    return task_to_response(task)


@router.delete(
    "/{task_id}",
    status_code=204,
    summary="Delete a task (soft delete)",
    responses={
        204: {"description": "Task deleted successfully"},
        404: {"description": "Task not found"},
    },
)
def delete_task(
    task_id: int = Path(..., description="The ID of the task to delete"),
    db: Session = Depends(get_db),
):
    """
    Soft delete a task by setting its is_deleted flag to True.
    
    The task will no longer appear in list queries but remains in the database
    for potential recovery or auditing purposes.

    Args:
        task_id: The ID of the task to delete.
        db: Database session dependency.
    Returns:
        None. If the task is not found, a 404 error is raised.
    """
    success = crud.delete_task(db, task_id)
    if not success:
        raise HTTPException(status_code=404, detail="Task not found")
    return None
