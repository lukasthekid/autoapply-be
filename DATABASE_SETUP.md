# Database Setup Guide

Your Django application will connect to your **existing PostgreSQL database** running on the host.

## Your Existing PostgreSQL Setup

```yaml
Container: postgres
Image: postgres:18.1-alpine
Port: 127.0.0.1:5433:5432
Network: postgres_network
User: admin
Password: ${DB_PASSWORD}
```

## Step 1: Create Database and User for Autoapply

SSH to your server and create the database:

```bash
ssh -i C:\Users\lukb9\.ssh\id_ed25519 lukas@5.75.171.23

# Connect to your existing PostgreSQL container
docker exec -it postgres psql -U admin -d global

# Create the autoapply database
CREATE DATABASE autoapply;

# Grant all privileges to admin user (or create a new user)
GRANT ALL PRIVILEGES ON DATABASE autoapply TO admin;

# If you want a separate user for this app (recommended):
CREATE USER autoapply_user WITH PASSWORD 'your-secure-password';
GRANT ALL PRIVILEGES ON DATABASE autoapply TO autoapply_user;
ALTER DATABASE autoapply OWNER TO autoapply_user;

# Exit psql
\q
```

## Step 2: Test Database Connection

```bash
# Test connection from host
docker exec -it postgres psql -U admin -d autoapply -c "SELECT version();"

# Should show PostgreSQL version
```

## Step 3: Configure Django to Connect to Existing Database

Your `.env` file should have:

```env
# Database Configuration
# Connect to existing PostgreSQL via Docker network
DB_HOST=postgres
DB_PORT=5432
DB_NAME=autoapply
DB_USER=admin  # or autoapply_user if you created one
DB_PASSWORD=your-database-password
```

### How it Works:

1. **Your PostgreSQL container** is named `postgres` and runs on `postgres_network`
2. **Django container** joins the same `postgres_network`
3. **Django connects** directly to `postgres:5432` using container name (internal Docker DNS)

## Current Setup (Recommended)

✅ **Both containers on same Docker network** (`postgres_network`)

This is the most reliable and secure approach:
- Direct container-to-container communication
- No need to expose PostgreSQL to host
- Uses Docker's internal DNS
- Better performance

## Step 4: Run Migrations

After deployment, Django will automatically run migrations to create tables:

```bash
# These are run automatically during deployment
docker compose -f docker-compose.yml -f docker-compose.prod.yml exec web python manage.py migrate
```

## Verify Database

```bash
# SSH to server
ssh -i C:\Users\lukb9\.ssh\id_ed25519 lukas@5.75.171.23

# Check Django created tables
docker exec -it postgres psql -U admin -d autoapply

# List tables
\dt

# Should see Django tables like:
# - auth_user
# - django_migrations
# - Your custom models

# Exit
\q
```

## Troubleshooting

### Connection Refused

```bash
# Make sure PostgreSQL is running
docker ps | grep postgres

# Check PostgreSQL logs
docker logs postgres

# Test connection from Django container
docker compose exec web python manage.py dbshell
```

### Permission Denied

```bash
# Grant permissions again
docker exec -it postgres psql -U admin -d global
GRANT ALL PRIVILEGES ON DATABASE autoapply TO admin;
GRANT ALL PRIVILEGES ON ALL TABLES IN SCHEMA public TO admin;
GRANT ALL PRIVILEGES ON ALL SEQUENCES IN SCHEMA public TO admin;
\q
```

### Network connection issues

If you get "connection refused":

```bash
# Check both containers are on same network
docker network inspect postgres_network

# Should show both 'postgres' and 'autoapply_web' containers
```

## Database Backup

Your existing setup already handles backups at `./backups`. Continue using your existing backup strategy.

## Summary

✅ Keep your existing PostgreSQL container running  
✅ Create `autoapply` database in your PostgreSQL  
✅ Django connects via `host.docker.internal:5433`  
✅ No port conflicts, no duplicate databases  
✅ Django manages its own tables via migrations  

---

**Next**: Update your `.env` file with these database settings and continue with deployment!

