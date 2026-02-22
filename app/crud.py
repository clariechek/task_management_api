from sqlalchemy.orm import Session
from sqlalchemy import func
from app.models import Task, Tag
from app.schemas import TaskCreate, TaskUpdate


def get_or_create_tag(db: Session, tag_name: str) -> Tag:
    """
    Get existing tag or create new one.
    - tag_name: Name of the tag to get or create.
    - Returns: The tag object.
    """

    tag = db.query(Tag).filter(Tag.name == tag_name).first()
    if not tag:
        tag = Tag(name=tag_name)
        db.add(tag)
        db.flush() # Flush to get the tag id. Commit in create_task to allow rollback on error.
    return tag


def create_task(db: Session, task_data: TaskCreate) -> Task:
    """
    Create a new task with associated tags.
    - task_data: Task creation request data.
    - Returns: The created task object.
    """
    # Create the task object
    task = Task(
        title=task_data.title,
        description=task_data.description,
        priority=task_data.priority,
        due_date=task_data.due_date,
    )
    
    # Handle tags
    if task_data.tags:
        for tag_name in task_data.tags:
            tag = get_or_create_tag(db, tag_name)
            task.tags.append(tag)
    
    # Save to database
    db.add(task)
    db.commit()
    db.refresh(task) # Refresh from DB to get: id, created_at
    return task


def get_tasks(
    db: Session,
    completed: bool | None = None,
    priority: int | None = None,
    tags: list[str] | None = None,
    limit: int = 10,
    offset: int = 0,
) -> tuple[list[Task], int]:
    """
    Get tasks with filtering and pagination.
    Returns tuple of (tasks, total_count).
    """
    # Filter out soft-deleted tasks.
    query = db.query(Task).filter(Task.is_deleted == False)
    
    # Apply filters
    if completed is not None:
        query = query.filter(Task.completed == completed)
    
    if priority is not None:
        query = query.filter(Task.priority == priority)
    
    if tags:
        query = query.filter(Task.tags.any(Tag.name.in_(tags)))
    
    # Total number of tasks matching the filter for pagination
    total = query.count()

    # Get tasks with pagination and ordering
    tasks = query.order_by(Task.created_at.desc()).offset(offset).limit(limit).all()
    
    return tasks, total


def get_task(db: Session, task_id: int) -> Task | None:
    """
    Get a single task by ID (excluding soft-deleted).
    - task_id: ID of the task to get.
    - Returns: The task object.
    - Returns None if the task is not found (including soft-deleted).
    """
    return db.query(Task).filter(
        Task.id == task_id,
        Task.is_deleted == False
    ).first()


def update_task(db: Session, task_id: int, task_data: TaskUpdate) -> Task | None:
    """
    Update a task with partial data.
    - task_id: ID of the task to update.
    - task_data: Task update request data.
    - Returns: The updated task object.
    - Returns None if the task is not found (including soft-deleted).
    """
    # Get the task to update
    task = get_task(db, task_id)
    if not task:
        return None
    
    # Update the task with the partial data. Exclude fields that are not set.
    update_data = task_data.model_dump(exclude_unset=True)
    
    # Handle tags. If tags are provided, clear existing tags and add new ones.
    if "tags" in update_data:
        tag_names = update_data.pop("tags")
        if tag_names:
            for tag_name in tag_names:
                tag = get_or_create_tag(db, tag_name)
    
    # Update other fields
    for field, value in update_data.items():
        setattr(task, field, value)
    
    # Save to database
    db.commit()
    db.refresh(task) # Refresh from DB to get: updated_at
    return task


def delete_task(db: Session, task_id: int) -> bool:
    """
    Soft delete a task by setting is_deleted flag.
    - task_id: ID of the task to delete.
    - Returns: True if the task was deleted, False if the task was not found (including soft-deleted).
    """
    # Get the task to delete
    task = get_task(db, task_id)
    if not task:
        return False
    
    task.is_deleted = True
    db.commit()
    return True
