# Docker Commands Cheatsheet for autoapply-be

Quick reference for common Docker and Docker Compose commands for this project.

## Aliases (Optional but Helpful)

Add to your `~/.bashrc` or `~/.zshrc`:

```bash
alias dc='docker-compose -f docker-compose.yml -f docker-compose.prod.yml'
alias dclogs='docker-compose -f docker-compose.yml -f docker-compose.prod.yml logs -f'
alias dcps='docker-compose -f docker-compose.yml -f docker-compose.prod.yml ps'
alias dcrestart='docker-compose -f docker-compose.yml -f docker-compose.prod.yml restart'
```

Then use: `dc up -d`, `dclogs`, etc.

---

## Basic Operations

### Start Services
```bash
docker-compose -f docker-compose.yml -f docker-compose.prod.yml up -d
```

### Stop Services
```bash
docker-compose -f docker-compose.yml -f docker-compose.prod.yml down
```

### Restart Services
```bash
# All services
docker-compose -f docker-compose.yml -f docker-compose.prod.yml restart

# Specific service
docker-compose -f docker-compose.yml -f docker-compose.prod.yml restart web
docker-compose -f docker-compose.yml -f docker-compose.prod.yml restart db
docker-compose -f docker-compose.yml -f docker-compose.prod.yml restart nginx
```

### View Service Status
```bash
docker-compose -f docker-compose.yml -f docker-compose.prod.yml ps
```

---

## Logs

### View All Logs (Follow Mode)
```bash
docker-compose -f docker-compose.yml -f docker-compose.prod.yml logs -f
```

### View Specific Service Logs
```bash
# Web application
docker-compose -f docker-compose.yml -f docker-compose.prod.yml logs -f web

# Database
docker-compose -f docker-compose.yml -f docker-compose.prod.yml logs -f db

# Nginx
docker-compose -f docker-compose.yml -f docker-compose.prod.yml logs -f nginx
```

### View Last N Lines
```bash
docker-compose -f docker-compose.yml -f docker-compose.prod.yml logs --tail=100 web
```

---

## Django Management Commands

### Run Migrations
```bash
docker-compose -f docker-compose.yml -f docker-compose.prod.yml exec web python manage.py migrate
```

### Create Superuser
```bash
docker-compose -f docker-compose.yml -f docker-compose.prod.yml exec web python manage.py createsuperuser
```

### Collect Static Files
```bash
docker-compose -f docker-compose.yml -f docker-compose.prod.yml exec web python manage.py collectstatic --noinput
```

### Django Shell
```bash
docker-compose -f docker-compose.yml -f docker-compose.prod.yml exec web python manage.py shell
```

### Create App
```bash
docker-compose -f docker-compose.yml -f docker-compose.prod.yml exec web python manage.py startapp myapp
```

### Make Migrations
```bash
docker-compose -f docker-compose.yml -f docker-compose.prod.yml exec web python manage.py makemigrations
```

---

## Database Operations

### Access PostgreSQL Shell
```bash
docker-compose -f docker-compose.yml -f docker-compose.prod.yml exec db psql -U postgres -d autoapply
```

### Common PostgreSQL Commands (once in shell)
```sql
-- List all tables
\dt

-- Describe table structure
\d tablename

-- List all databases
\l

-- Quit
\q
```

### Backup Database
```bash
# Create backup
docker-compose -f docker-compose.yml -f docker-compose.prod.yml exec db pg_dump -U postgres autoapply > backup_$(date +%Y%m%d_%H%M%S).sql

# Or with compression
docker-compose -f docker-compose.yml -f docker-compose.prod.yml exec db pg_dump -U postgres autoapply | gzip > backup_$(date +%Y%m%d_%H%M%S).sql.gz
```

### Restore Database
```bash
# From SQL file
cat backup.sql | docker-compose -f docker-compose.yml -f docker-compose.prod.yml exec -T db psql -U postgres autoapply

# From compressed file
gunzip -c backup.sql.gz | docker-compose -f docker-compose.yml -f docker-compose.prod.yml exec -T db psql -U postgres autoapply
```

### Reset Database (DANGER!)
```bash
docker-compose -f docker-compose.yml -f docker-compose.prod.yml exec db psql -U postgres -c "DROP DATABASE autoapply;"
docker-compose -f docker-compose.yml -f docker-compose.prod.yml exec db psql -U postgres -c "CREATE DATABASE autoapply;"
docker-compose -f docker-compose.yml -f docker-compose.prod.yml exec web python manage.py migrate
```

---

## Docker Image Management

### Pull Latest Images
```bash
docker-compose -f docker-compose.yml -f docker-compose.prod.yml pull
```

### Rebuild Images
```bash
docker-compose -f docker-compose.yml -f docker-compose.prod.yml build --no-cache
```

### Build and Start
```bash
docker-compose -f docker-compose.yml -f docker-compose.prod.yml up -d --build
```

### List Images
```bash
docker images
```

### Remove Unused Images
```bash
# Remove dangling images
docker image prune

# Remove all unused images
docker image prune -a

# Remove images older than 24 hours
docker image prune -a --filter "until=24h"
```

---

## Container Management

### Execute Command in Container
```bash
docker-compose -f docker-compose.yml -f docker-compose.prod.yml exec web bash
```

### Execute Command Without TTY (for scripts)
```bash
docker-compose -f docker-compose.yml -f docker-compose.prod.yml exec -T web python manage.py migrate
```

### Copy Files To/From Container
```bash
# From container to host
docker cp autoapply_web:/app/file.txt ./local-file.txt

# From host to container
docker cp ./local-file.txt autoapply_web:/app/file.txt
```

### View Container Resource Usage
```bash
docker stats
```

---

## Volumes

### List Volumes
```bash
docker volume ls
```

### Inspect Volume
```bash
docker volume inspect autoapply-be_postgres_data
```

### Backup Volume
```bash
docker run --rm -v autoapply-be_postgres_data:/data -v $(pwd):/backup ubuntu tar czf /backup/postgres_backup_$(date +%Y%m%d_%H%M%S).tar.gz /data
```

### Remove Volumes (DANGER!)
```bash
# Remove all stopped containers and unused volumes
docker-compose -f docker-compose.yml -f docker-compose.prod.yml down -v
```

---

## Troubleshooting

### Service Won't Start
```bash
# Check logs
docker-compose -f docker-compose.yml -f docker-compose.prod.yml logs web

# Check service health
docker-compose -f docker-compose.yml -f docker-compose.prod.yml ps

# Restart service
docker-compose -f docker-compose.yml -f docker-compose.prod.yml restart web
```

### Reset Everything (Nuclear Option)
```bash
# Stop all containers
docker-compose -f docker-compose.yml -f docker-compose.prod.yml down

# Remove all containers, networks, volumes, and images
docker-compose -f docker-compose.yml -f docker-compose.prod.yml down -v --rmi all

# Start fresh
docker-compose -f docker-compose.yml -f docker-compose.prod.yml up -d --build
```

### Check Container Health
```bash
docker inspect autoapply_web | grep -A 10 Health
```

### View Container Environment Variables
```bash
docker-compose -f docker-compose.yml -f docker-compose.prod.yml exec web env
```

---

## Network

### List Networks
```bash
docker network ls
```

### Inspect Network
```bash
docker network inspect autoapply-be_autoapply_network
```

### Test Connectivity Between Services
```bash
# From web container to db
docker-compose -f docker-compose.yml -f docker-compose.prod.yml exec web ping db

# Check if port is open
docker-compose -f docker-compose.yml -f docker-compose.prod.yml exec web nc -zv db 5432
```

---

## Clean Up

### Remove Stopped Containers
```bash
docker container prune
```

### Remove Unused Networks
```bash
docker network prune
```

### Remove Everything Unused
```bash
docker system prune -a --volumes
```

### Free Up Space
```bash
# See disk usage
docker system df

# Clean up (interactive)
docker system prune -a
```

---

## Monitoring

### Real-time Stats
```bash
docker stats autoapply_web autoapply_db autoapply_nginx
```

### Check Disk Usage
```bash
docker system df -v
```

### Top Processes in Container
```bash
docker top autoapply_web
```

---

## Quick Deployment Commands

### Full Deployment
```bash
cd ~/autoapply-be
docker-compose -f docker-compose.yml -f docker-compose.prod.yml pull
docker-compose -f docker-compose.yml -f docker-compose.prod.yml up -d
docker-compose -f docker-compose.yml -f docker-compose.prod.yml exec -T web python manage.py migrate
docker-compose -f docker-compose.yml -f docker-compose.prod.yml exec -T web python manage.py collectstatic --noinput
```

### Quick Restart
```bash
cd ~/autoapply-be
docker-compose -f docker-compose.yml -f docker-compose.prod.yml restart
```

### View Status
```bash
cd ~/autoapply-be
docker-compose -f docker-compose.yml -f docker-compose.prod.yml ps
curl http://localhost/health
```

---

## Environment Variables

### Check Current Values
```bash
docker-compose -f docker-compose.yml -f docker-compose.prod.yml config
```

### Update Environment Variables
```bash
# Edit .env file
nano .env

# Restart services to apply changes
docker-compose -f docker-compose.yml -f docker-compose.prod.yml up -d --force-recreate
```

---

**Pro Tip**: Create a `dc.sh` script in your project root:

```bash
#!/bin/bash
docker-compose -f docker-compose.yml -f docker-compose.prod.yml "$@"
```

Make it executable:
```bash
chmod +x dc.sh
```

Then use:
```bash
./dc.sh up -d
./dc.sh logs -f
./dc.sh ps
```

