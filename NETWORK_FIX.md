# Network Connection Fix

## The Final Issue

After fixing the Dockerfile and removing port conflicts, Django still couldn't connect to PostgreSQL:

```
OperationalError: connection to server at "host.docker.internal" (172.17.0.1), port 5433 failed: Connection refused
```

## Why It Failed

Your PostgreSQL is bound to `127.0.0.1:5433` in your docker-compose:

```yaml
ports:
  - "127.0.0.1:5433:5432"  # Only localhost can access!
```

This means:
- ✅ Host can access via `localhost:5433`
- ❌ Other Docker containers **cannot** access it via `host.docker.internal`

## The Solution: Shared Docker Network

Both containers now use the same Docker network (`postgres_network`):

```yaml
# django docker-compose.yml
networks:
  - postgres_network  # Join existing network

networks:
  postgres_network:
    external: true  # Use your existing postgres_network
```

## How It Works Now

```
┌─────────────────────────────────────────────┐
│      postgres_network (Docker Network)      │
│                                             │
│  ┌────────────────┐    ┌──────────────┐   │
│  │ Django         │───▶│ PostgreSQL   │   │
│  │ (autoapply_web)│    │ (postgres)   │   │
│  │ port 8000      │    │ port 5432    │   │
│  └────────────────┘    └──────────────┘   │
│                                             │
│  Connection: postgres:5432 (internal DNS)  │
└─────────────────────────────────────────────┘
```

### Benefits:
1. ✅ **Direct communication** - No need for host networking
2. ✅ **More secure** - PostgreSQL doesn't need to expose ports
3. ✅ **Better performance** - Native Docker networking
4. ✅ **DNS resolution** - Use container name `postgres` instead of IP
5. ✅ **No configuration changes** needed to your existing PostgreSQL

## Configuration

### .env file:
```env
DB_HOST=postgres       # Container name (Docker DNS)
DB_PORT=5432          # Internal port (not 5433)
DB_NAME=autoapply
DB_USER=admin
DB_PASSWORD=your-password
```

### Your PostgreSQL (no changes needed):
```yaml
# Your existing postgres docker-compose.yml
services:
  postgres:
    image: postgres:18.1-alpine
    container_name: postgres
    ports:
      - "127.0.0.1:5433:5432"  # Keep as is
    networks:
      - postgres_network  # Already configured
```

### Django:
```yaml
# autoapply-be docker-compose.yml
services:
  web:
    networks:
      - autoapply_network   # Its own network
      - postgres_network    # Shared with PostgreSQL
```

## Verification

After deployment, verify the connection:

```bash
# SSH to server
ssh -i C:\Users\lukb9\.ssh\id_ed25519 lukas@5.75.171.23

# Check both containers are on same network
docker network inspect postgres_network

# Should show both:
# - postgres
# - autoapply_web

# Test Django can reach PostgreSQL
docker compose -f docker-compose.yml -f docker-compose.prod.yml exec web \
  python -c "import psycopg2; psycopg2.connect('dbname=autoapply user=admin password=your-pass host=postgres')"

# Check Django logs
docker compose -f docker-compose.yml -f docker-compose.prod.yml logs web
```

## Summary

**Before**: Trying to use `host.docker.internal` → Connection refused  
**After**: Using Docker network → Direct container-to-container communication ✅

This is the standard and recommended way to connect Docker containers!

