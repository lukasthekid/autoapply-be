# Django Ninja Deployment Guide

Complete guide for deploying this Django Ninja backend to production with Docker and CI/CD.

## Architecture Overview

```
Internet → Nginx (Port 80/443) → Django (Port 8000) → PostgreSQL
           ├── project100x.run.place (React Frontend)
           ├── api.project100x.run.place (Django API)
           └── n8n.project100x.run.place (n8n)
```

## Prerequisites

- Server with Ubuntu 20.04+ (IP: `5.75.171.23`)
- Docker and Docker Compose installed
- Existing PostgreSQL container running (container name: `postgres`)
- Domain configured (subdomain: `api.project100x.run.place`)
- SSH access with key authentication
- GitHub repository

---

## Quick Start Deployment

### 1. Configure GitHub Secrets

Go to: GitHub Repository → Settings → Secrets and variables → Actions

Add these secrets:

| Secret Name | Value |
|-------------|-------|
| `SERVER_IP` | `5.75.171.23` |
| `SSH_USER` | `lukas` |
| `SSH_PRIVATE_KEY` | Full contents of your SSH private key |
| `SECRET_KEY` | Generate: `python -c "import secrets; print(secrets.token_urlsafe(50))"` |
| `ALLOWED_HOSTS` | `api.project100x.run.place,project100x.run.place,5.75.171.23` |
| `CORS_ALLOWED_ORIGINS` | `https://project100x.run.place` |
| `DB_NAME` | `autoapply` |
| `DB_USER` | `admin` (your PostgreSQL user) |
| `DB_PASSWORD` | Your PostgreSQL password |

### 2. Create Database

SSH to server and create the database:

```bash
docker exec postgres psql -U admin -d global -c "CREATE DATABASE autoapply;"
docker exec postgres psql -U admin -d global -c "GRANT ALL PRIVILEGES ON DATABASE autoapply TO admin;"
```

### 3. Configure Nginx on Server

Create nginx configuration for the API:

```bash
sudo nano /etc/nginx/sites-available/api.project100x
```

Add this configuration:

```nginx
# HTTP - Redirect to HTTPS
server {
    listen 80;
    server_name api.project100x.run.place;
    
    location /.well-known/acme-challenge/ {
        root /var/www/certbot;
    }
    
    location / {
        return 301 https://$host$request_uri;
    }
}

# HTTPS - Main API Server
server {
    listen 443 ssl http2;
    server_name api.project100x.run.place;

    ssl_certificate /etc/letsencrypt/live/api.project100x.run.place/fullchain.pem;
    ssl_certificate_key /etc/letsencrypt/live/api.project100x.run.place/privkey.pem;
    
    ssl_protocols TLSv1.2 TLSv1.3;
    ssl_ciphers HIGH:!aNULL:!MD5;
    ssl_prefer_server_ciphers on;

    location / {
        proxy_pass http://localhost:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        proxy_redirect off;
    }

    location /static/ {
        alias /home/lukas/autoapply-be/staticfiles/;
        expires 30d;
    }

    location /media/ {
        alias /home/lukas/autoapply-be/mediafiles/;
        expires 7d;
    }
}
```

Enable and test:

```bash
sudo ln -s /etc/nginx/sites-available/api.project100x /etc/nginx/sites-enabled/
sudo nginx -t
```

### 4. Get SSL Certificate

```bash
sudo systemctl stop nginx
sudo certbot certonly --standalone -d api.project100x.run.place
sudo systemctl start nginx
sudo systemctl reload nginx
```

### 5. Deploy

```bash
git add .
git commit -m "Initial deployment"
git push origin main
```

GitHub Actions will automatically deploy!

---

## How It Works

### Docker Setup

- **Django** runs in a container (ghcr.io/lukasthekid/autoapply-be)
- **PostgreSQL** uses your existing container (shared Docker network: `postgres_postgres_network`)
- **Nginx** runs on host (proxies to Django on port 8000)

### CI/CD Pipeline

On every push to `main`:

1. ✅ Runs tests
2. ✅ Builds Docker image
3. ✅ Pushes to GitHub Container Registry
4. ✅ Creates database (if not exists)
5. ✅ Deploys container to server
6. ✅ Runs migrations
7. ✅ Collects static files

### Database Connection

Django connects to PostgreSQL via Docker network:
- **Host**: `postgres` (container name)
- **Port**: `5432` (internal)
- **Network**: `postgres_postgres_network`

---

## Local Development

### Setup

```bash
# Create virtual environment
python -m venv venv
.\venv\Scripts\Activate.ps1  # Windows
source venv/bin/activate      # Linux/Mac

# Install dependencies
pip install -r requirements.txt

# Copy environment file
cp env.example .env
# Edit .env with local settings

# Run migrations
python manage.py migrate

# Start dev server
python manage.py runserver
```

### Environment Variables

See `env.example` for local development settings.

---

## Deployment Management

### View Logs

```bash
ssh -i ~/.ssh/id_ed25519 lukas@5.75.171.23
cd ~/autoapply-be
docker compose -f docker-compose.yml -f docker-compose.prod.yml logs -f web
```

### Restart Service

```bash
docker compose -f docker-compose.yml -f docker-compose.prod.yml restart
```

### Run Migrations Manually

```bash
docker compose -f docker-compose.yml -f docker-compose.prod.yml exec web python manage.py migrate
```

### Create Superuser

```bash
docker compose -f docker-compose.yml -f docker-compose.prod.yml exec web python manage.py createsuperuser
```

### Update Deployment

Just push to GitHub:

```bash
git push origin main
```

### Database Backup

```bash
docker exec postgres pg_dump -U admin autoapply > backup_$(date +%Y%m%d).sql
```

---

## Troubleshooting

### Container Won't Start

```bash
docker compose -f docker-compose.yml -f docker-compose.prod.yml logs web
```

### Database Connection Issues

```bash
# Test connection
docker exec postgres psql -U admin -d autoapply -c "SELECT 1;"

# Check network
docker network inspect postgres_postgres_network
```

### Nginx Issues

```bash
sudo nginx -t
sudo systemctl status nginx
sudo tail -f /var/log/nginx/error.log
```

### Static Files Not Loading

```bash
docker compose exec web python manage.py collectstatic --noinput
sudo chown -R www-data:www-data ~/autoapply-be/staticfiles
```

---

## Key Files

- `Dockerfile` - Production Docker image
- `docker-compose.yml` - Service definitions
- `docker-compose.prod.yml` - Production overrides
- `.github/workflows/deploy.yml` - CI/CD pipeline
- `env.production.template` - Production environment template

---

## URLs

- **API Documentation**: `https://api.project100x.run.place/api/docs`
- **Admin Panel**: `https://api.project100x.run.place/admin/`
- **Health Check**: Container health check on `/api/docs`

---

## Security Checklist

- [x] Strong `SECRET_KEY` generated
- [x] `DEBUG=False` in production
- [x] `ALLOWED_HOSTS` configured
- [x] CORS properly configured
- [x] HTTPS enabled with Let's Encrypt
- [x] Database password secured
- [x] SSH key-based authentication
- [x] Firewall configured (UFW)

---

## Support

For issues or questions:
1. Check logs: `docker compose logs -f`
2. Review GitHub Actions workflow runs
3. Check nginx error logs: `sudo tail -f /var/log/nginx/error.log`

