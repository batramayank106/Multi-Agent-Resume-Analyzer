# Database Migrations

This directory is reserved for future **Alembic** database migration scripts.

## Current Approach

The app currently manages its schema directly via SQLAlchemy:

- `database/connection.py` — `init_db()` creates all tables on startup using model metadata
- `database/seed.py` — seeds initial data (super admin, demo resumes, etc.)

This works well for development but does not track schema changes over time.

## Future Plan

When the app needs production-grade schema evolution (e.g., adding columns, renaming tables, migrating data), Alembic migration scripts will be placed here:

```bash
alembic init migrations
alembic revision --autogenerate -m "description"
alembic upgrade head
```

Until then, this directory intentionally remains empty.
