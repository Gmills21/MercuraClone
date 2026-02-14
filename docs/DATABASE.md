# Database Configuration Guide

OpenMercura now supports both **SQLite** (default, for development/small deployments) and **PostgreSQL** (for production).

## Quick Start

### SQLite (Default - No Setup Required)

By default, OpenMercura uses SQLite which requires no configuration:

```bash
# Default - uses SQLite
DATABASE_URL=sqlite:///mercura.db
```

**Pros:**
- Zero configuration
- No external dependencies
- Perfect for development and small teams

**Cons:**
- Single-server only (no horizontal scaling)
- File locks during writes
- Risk of data loss on ephemeral filesystems (Render free tier)

### PostgreSQL (Recommended for Production)

For production deployments with multiple users or high availability requirements:

```bash
# Switch to PostgreSQL
DATABASE_URL=postgresql://user:password@localhost:5432/mercura
```

**Pros:**
- Handles concurrent writes
- Horizontal scaling ready
- Automatic backups on most platforms
- No risk of file corruption

**Cons:**
- Requires PostgreSQL server
- Slightly more complex setup

## Switching to PostgreSQL

### 1. Provision PostgreSQL

**Render.com:**
- Go to Dashboard → New → PostgreSQL
- Choose plan (Free tier available)
- Copy the "External Database URL"

**Railway:**
- Add PostgreSQL service
- Copy connection string

**Local/Docker:**
```bash
docker run -d --name postgres \
  -e POSTGRES_USER=mercura \
  -e POSTGRES_PASSWORD=yourpassword \
  -e POSTGRES_DB=mercura \
  -p 5432:5432 \
  postgres:15
```

### 2. Update Environment Variables

Add to your `.env` file:

```bash
# PostgreSQL connection
DATABASE_URL=postgresql://user:password@host:5432/dbname

# Optional: Force SQLAlchemy mode (auto-detected by default)
USE_SQLALCHEMY=true
```

### 3. Migrate Data (Optional)

If you have existing SQLite data you want to keep:

```bash
# Set source and target
export SOURCE_DB="sqlite:///mercura.db"
export TARGET_DB="postgresql://user:password@host:5432/dbname"

# Run migration
python -m app.migrate_sqlite_to_postgres
```

### 4. Deploy

```bash
# Install dependencies (includes psycopg2)
pip install -r requirements.txt

# Start application
uvicorn app.main:app --host 0.0.0.0 --port 8000
```

## Environment Variables

| Variable | Description | Default |
|----------|-------------|---------|
| `DATABASE_URL` | Database connection string | `sqlite:///mercura.db` |
| `USE_SQLALCHEMY` | Force SQLAlchemy mode | `auto` (auto-detects) |

## Database URLs Format

**SQLite:**
```
sqlite:///mercura.db                    # Relative path
sqlite:////absolute/path/to/mercura.db  # Absolute path (Unix)
sqlite:///C:\path\to\mercura.db         # Absolute path (Windows)
```

**PostgreSQL:**
```
postgresql://user:password@localhost/dbname
postgresql://user:password@host:5432/dbname?sslmode=require
postgresql://user:password@host/dbname?sslmode=require&schema=mercura
```

## Backup Strategy

### SQLite
- Back up the `.db` file directly
- Use the built-in backup API: `/backups/create`
- Schedule regular file copies

### PostgreSQL
- Use platform automated backups (Render/Railway provide this)
- Use `pg_dump` for manual backups:
  ```bash
  pg_dump $DATABASE_URL > backup.sql
  ```
- Built-in backup API also works

## Troubleshooting

### "psycopg2 not found"
```bash
pip install psycopg2-binary
```

### "Database does not exist"
Create the database first:
```bash
createdb mercura
```

### Migration fails with foreign key errors
Ensure tables are migrated in the correct order (the migration script handles this automatically).

### Connection errors on Render/Railway
- Check if you're using the **External** database URL (not Internal)
- Verify SSL mode settings
- Check if IP is allowlisted

## Performance Comparison

| Users | SQLite | PostgreSQL |
|-------|--------|------------|
| 1-5 | ⭐⭐⭐ Perfect | ⭐⭐⭐ Perfect |
| 5-20 | ⭐⭐ Good | ⭐⭐⭐ Perfect |
| 20-100 | ⭐ Slow | ⭐⭐⭐ Perfect |
| 100+ | ❌ Not recommended | ⭐⭐⭐ Perfect |

## Recommendation

- **Development:** SQLite (default)
- **Small team (1-10 users):** SQLite with persistent disk
- **Production with 10+ users:** PostgreSQL
- **High availability required:** PostgreSQL with read replicas
