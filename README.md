# task_management_api
A FastAPI Task Management API with filtering, tagging and deadlines.

# Prerequisites
- Python 3.10+
- Docker

# Setup and run

# API overview

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

# Testing

# Production readiness improvements
