# Database Migrations

This directory contains Alembic database migration scripts.

## Usage

### Create a new migration
```bash
alembic revision --autogenerate -m "Description of changes"
```

### Apply migrations
```bash
alembic upgrade head
```

### Rollback migration
```bash
alembic downgrade -1
```

### View migration history
```bash
alembic history
```

### View current revision
```bash
alembic current
```

## Migration Scripts

- `migrate_json_to_db.py` - One-time migration script to move data from JSON to PostgreSQL

## Important Notes

- Always review auto-generated migrations before applying
- Test migrations on a development database first
- Create backups before running migrations in production
- Never edit existing migration files that have been applied
