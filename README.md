# task_management_api
A FastAPI Task Management API with filtering, tagging and deadlines.

# Prerequisites
- Python 3.10+
- Docker and Docker Compose

# Setup and run

## Quick Start (Docker)
Run the application and PostgreSQL database with a single command:
```bash
docker-compose up --build
```

The API will be available at:
- **API**: http://localhost:8000
- **Swagger Docs**: http://localhost:8000/docs

To stop the services:
```bash
docker-compose down
```

To stop and remove all data:
```bash
docker-compose down -v
```

## Local development (without Docker)

1. Create a virtual environment with Python 3.11
```bash
python3.11 -m venv venv
source venv/bin/activate
```

2. Install dependencies
```bash
pip install -r requirements.txt
```

3. Set up PostgreSQL and configure the connection:
```bash
export DATABASE_URL="postgresql://postgres:postgres@localhost:5432/taskdb"
```

4. Run the application:
```bash
uvicorn app.main:app --reload
```

# API overview
| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/` | Health check |
| POST | `/tasks` | Create a new task |
| GET | `/tasks` | List tasks with filtering and pagination |
| GET | `/tasks/{id}` | Get a single task |
| PATCH | `/tasks/{id}` | Partially update a task |
| DELETE | `/tasks/{id}` | Soft delete a task |


# Design decisions
## Tagging (many-to-many)
- Option A: Join Table (chosen method)
  - Tables: `task`, `tags`, `task_tags`
  - Advantages:
      - Normalised
      - Easy to rename tags
      - Efficient filtering with indexes
  - Disadvantages:
      - Extra joins
      - Extra tables
- Option B: PostgreSQL JSONB
    - Single column on `tasks` eg. `tags` JSONB
    - Advantages:
        - No join
        - Simple schema
        - Schema flexibility
    - Disadvantages:
        - Challenging to enforce tag name uniqueness
        - Duplicate data
        - Inefficient and costly update
        - Challenging to perform analytics
        - Inflexible to future enhancements eg. tag category, colour, ownership, audit logs
- Option C: Array
  - Single column on `tasks` eg. `tags` ARRAY
  - Advantages:
    - Simple list of strings
    - No join
  - Disadvantages:
    - Less flexible than JSONB
    - Same disadvantages as JSONB ie. duplicate data, inefficient/costly update, unsuitable for analytics or future enhancements

## Delete strategy:
- Option A: Soft delete (chosen method)
  - Add `is_deleted` Boolean value on `tasks`. Defaults to False.
  - DELETE sets the flag to True.
  - GET /tasks excludes soft-deleted by default.
  - Advantages:
    - Enables easy data recovery
    - Maintains referential integrity
    - Preserves historical records for auditing/analytics
  - Disadvantages:
    - Increases database size over time
    - Queries need to filter out 'deleted' rows
- Option B: Hard delete
  - Physically remove the row
  - Advantages:
    - Frees up storage space
    - Keeps tables slim and faster
    - Ensures strict data compliance (GDPR right to be forgotten)
  - Disadvantages:
    - Unrecoverable data (requires backup to receover)
    - Break historical links
- Consideration:
  - Use a hybrid approach where soft-delete is performed for a period of time, followed by scheduled hard delete to clear space. Legislation and compliance requirements may guide decision here.
      

# Database and performance
## Indexing
| | Index | Table | Column(s) | Rationale |
| --- |-------|-------|-----------|-----------|
| 1 | idx_tasks_priority | tasks | priority | Frequent filtering |
| 2 | idx_tasks_completed | tasks | completed | Frequent filtering |
| 3 | idx_tasks_is_deleted | tasks | is_deleted | Soft delete queries |
| 4 | idx_tags_name | tags | name | Tag lookups |

## Schema
### tasks
| | Column | Type | Constraints | Description |
| --- |--------|------|-------------|-------------|
| 1 | id | SERIAL | PRIMARY KEY | Unique identifier |
| 2 | title | VARCHAR(200) | NOT NULL | Task title |
| 3 | description | TEXT | | Optional description |
| 4 | priority | INTEGER | NOT NULL, CHECK (1-5) | Priority level with highest being 5 |
| 5 | due_date | DATE | NOT NULL | Task deadline in ISO format (YYYY-MM-DD) |
| 6 | completed | BOOLEAN | DEFAULT FALSE | Completion status |
| 7 | is_deleted | BOOLEAN | DEFAULT FALSE | Soft delete flag |
| 8 | created_at | TIMESTAMP | DEFAULT NOW() | Creation timestamp |
| 9 | updated_at | TIMESTAMP | | Last modification |

### tags
| | Column | Type | Constraints | Description |
| --- |--------|------|-------------|-------------|
| 1 | id | SERIAL | PRIMARY KEY | Unique identifier |
| 2 | name | VARCHAR(50) | UNIQUE, NOT NULL | Tag name |

### task_tags
| | Column | Type | Constraints | Description |
| --- |--------|------|-------------|-------------|
| 1 | task_id | INTEGER | FK → tasks(id) | Reference to task |
| 2 | tag_id | INTEGER | FK → tags(id) | Reference to tag |
| 3 | | | PRIMARY KEY (task_id, tag_id) | Composite key |

Note: Composite key is simpler to use however can be harder to reference externally. A surrogate primary key might be better for production enhancement.

# Testing
Run the test suite using pytest:

```bash
# Setup virtual environment
python3.11 -m venv venv 
source venv/bin/activate

# Install test dependencies
pip install -r requirements.txt

# Run all tests
pytest

# Run with verbose output
pytest -v

# Run with coverage report
pytest --cov=app --cov-report=html
```

The test suite covers:
- Task creation (success and validation failures)
- Filtering by priority, completion status, and tags
- Pagination
- Partial updates (PATCH)
- Edge cases and error handling

**Note**: 
- Tests use SQLite in-memory database for speed and isolation.
- Test cases for getting task by id and soft delete behavior to be implemented.


# Production readiness improvements
The following enhancements would be recommended for production deployment:

## Security
- **Secret Management**: Move credentials to a secrets manager. Never commit secrets to version control.
- **Authentication & Authorization**: Add JWT or OAuth2 authentication
- **Rate Limiting**: Implement rate limiting to prevent abuse
- **Input Sanitization**: Additional input validation and sanitization
- **CORS Configuration**: Configure allowed origins for web clients
- **HTTPS**: Enforce HTTPS in production

## Data Integrity
- **Optimistic Locking**: Add version field to prevent lost updates (ie. when 2 users update the same task - race condition)
- **Transaction Isolation**: Configure appropriate isolation levels for critical operations
- **Retry Logic**: Handle deadlocks and transient failures with exponential backoff
- **Idempotency**: Ensure repeated requests don't cause duplicate effects

## Performance
- **Caching**: Add Redis caching for frequently accessed data
- **Connection Pooling**: Configure database connection pooling (e.g., PgBouncer)
- **Query Optimization**: Add composite indexes for common filter combinations
- **Async Database Operations**: Use async SQLAlchemy for non-blocking I/O

## Observability
- **Logging**: Structured logging with correlation IDs
- **Metrics**: Prometheus metrics (eg. request counts, response times, error rates, database query durations) for monitoring
- **Distributed Tracing**: OpenTelemetry integration to trace where time is spent across all services in request chain

## Infrastructure
- **Database Migrations**: Use Alembic for schema versioning to prevent data loss when schema changes
- **Environment Configuration**: Use pydantic-settings for environment management
- **Container Orchestration**: Kubernetes manifests for scaling
- **CI/CD Pipeline**: Automated testing and deployment
- **Database Backups**: Automated backup and recovery procedures

## Data Management
- **Scheduled Hard Delete**: Periodic cleanup of soft-deleted records
- **Data Archival**: Archive old completed tasks
- **Audit Logging**: Track all changes for compliance (eg. log all create/update/delete operations with user ID, timestamps, before/after values etc.)