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
  - 

## Schema
### tasks

### tags

### task_tags


# Testing

# Production readiness improvements
