# Nginx Integration Guide

Your frontend already has nginx running on port 80. We'll configure it to handle both frontend and backend.

## Current Setup

```
Frontend: https://project100x.run.place/ → nginx (port 80) → React app
Backend: Will be at https://api.project100x.run.place/ → nginx (port 80) → Django (port 8000)
```

## Changes Made

✅ **Removed** nginx from backend docker-compose  
✅ **Django now exposed** directly on port 8000  
✅ **Your existing nginx** will proxy both domains  

---

## Step 1: Clean Up Old Containers

First, clean up the orphan containers and failed deployment:

```bash
ssh -i C:\Users\lukb9\.ssh\id_ed25519 lukas@5.75.171.23

cd ~/autoapply-be

# Stop and remove all containers
docker compose -f docker-compose.yml -f docker-compose.prod.yml down --remove-orphans

# Remove any lingering containers
docker ps -a | grep autoapply
docker rm -f autoapply_db autoapply_nginx autoapply_web 2>/dev/null || true
```

---

## Step 2: Find Your Frontend Nginx Configuration

Your frontend nginx config is likely in one of these locations:

```bash
# Common locations:
/etc/nginx/sites-available/project100x
/etc/nginx/conf.d/project100x.conf
/etc/nginx/nginx.conf

# If using Docker for frontend:
~/project100x-frontend/nginx.conf
```

Find it:

```bash
# List nginx config files
sudo ls -la /etc/nginx/sites-available/
sudo ls -la /etc/nginx/conf.d/

# Or check running nginx container
docker ps | grep nginx
```

---

## Step 3: Add Backend Configuration

### Option A: If nginx is running on host (most common)

```bash
# Create new config file for backend
sudo nano /etc/nginx/sites-available/api.project100x

# Add this content:
```

```nginx
server {
    listen 80;
    server_name api.project100x.run.place;
    return 301 https://$host$request_uri;
}

server {
    listen 443 ssl http2;
    server_name api.project100x.run.place;

    # SSL Configuration (get cert with certbot)
    ssl_certificate /etc/letsencrypt/live/api.project100x.run.place/fullchain.pem;
    ssl_certificate_key /etc/letsencrypt/live/api.project100x.run.place/privkey.pem;
    
    ssl_protocols TLSv1.2 TLSv1.3;
    ssl_ciphers HIGH:!aNULL:!MD5;
    ssl_prefer_server_ciphers on;

    # Proxy to Django on port 8000
    location / {
        proxy_pass http://localhost:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        proxy_redirect off;
    }

    # Static files
    location /static/ {
        alias /home/lukas/autoapply-be/staticfiles/;
        expires 30d;
    }

    # Media files
    location /media/ {
        alias /home/lukas/autoapply-be/mediafiles/;
        expires 7d;
    }
}
```

```bash
# Enable the site
sudo ln -s /etc/nginx/sites-available/api.project100x /etc/nginx/sites-enabled/

# Test nginx config
sudo nginx -t

# Reload nginx
sudo systemctl reload nginx
```

### Option B: If nginx is in Docker container

Add the backend configuration to your frontend's nginx config file and restart the container.

---

## Step 4: Get SSL Certificate for Backend

```bash
# Stop nginx temporarily
sudo systemctl stop nginx
# OR if in Docker:
# docker stop <frontend-nginx-container>

# Get SSL certificate for backend
sudo certbot certonly --standalone \
  -d api.project100x.run.place \
  --agree-tos \
  --email your-email@example.com

# Start nginx again
sudo systemctl start nginx
# OR if in Docker:
# docker start <frontend-nginx-container>
```

---

## Step 5: Update .env on Server

Make sure static/media paths are accessible:

```bash
ssh -i C:\Users\lukb9\.ssh\id_ed25519 lukas@5.75.171.23
cd ~/autoapply-be
nano .env
```

Ensure it has:

```env
DB_HOST=host.docker.internal
DB_PORT=5433
# ... other settings ...
```

---

## Step 6: Mount Static/Media Volumes

Update docker-compose to make static files accessible to nginx:

The volumes are already configured, but make sure nginx can read them:

```bash
# Give nginx access to static files
sudo chown -R www-data:www-data ~/autoapply-be/staticfiles
sudo chown -R www-data:www-data ~/autoapply-be/mediafiles

# Or if nginx runs as different user:
sudo chmod -R 755 ~/autoapply-be/staticfiles
sudo chmod -R 755 ~/autoapply-be/mediafiles
```

---

## Step 7: Redeploy Backend

Now redeploy from GitHub or manually:

```bash
cd ~/autoapply-be

# Pull and start (without nginx)
docker compose -f docker-compose.yml -f docker-compose.prod.yml up -d

# Check Django is running
docker compose ps
curl http://localhost:8000/api/docs
```

---

## Step 8: Test Everything

```bash
# Test from server
curl http://localhost:8000/health
curl https://api.project100x.run.place/health

# From your local machine
curl https://api.project100x.run.place/health
curl https://api.project100x.run.place/api/docs
```

---

## Architecture Now

```
Internet
   │
   ▼
┌─────────────────────────────────┐
│   Your Existing Nginx           │
│   (Port 80/443)                 │
├─────────────────────────────────┤
│  project100x.run.place          │──▶ React Frontend
│  api.project100x.run.place      │──▶ Django (port 8000)
└─────────────────────────────────┘
                                   │
                                   ▼
                    ┌──────────────────────────┐
                    │ Django Container         │
                    │ Port 8000                │
                    └────────┬─────────────────┘
                             │
                             ▼
                    ┌──────────────────────────┐
                    │ PostgreSQL (existing)    │
                    │ Port 5433                │
                    └──────────────────────────┘
```

---

## Troubleshooting

### Can't find nginx config

```bash
# Check if nginx is running
ps aux | grep nginx

# Find nginx config
sudo nginx -t  # Shows config file location

# If nginx in Docker
docker ps | grep nginx
docker exec <container> cat /etc/nginx/nginx.conf
```

### Port 8000 not accessible

```bash
# Check Django is running
docker compose ps

# Check logs
docker compose logs web

# Test from inside server
curl http://localhost:8000/api/docs
```

### Static files not loading

```bash
# Check paths
ls -la ~/autoapply-be/staticfiles/

# Collect static files
docker compose exec web python manage.py collectstatic --noinput

# Fix permissions
sudo chmod -R 755 ~/autoapply-be/staticfiles/
```

---

## Quick Commands

```bash
# Restart backend
cd ~/autoapply-be
docker compose -f docker-compose.yml -f docker-compose.prod.yml restart

# Reload nginx
sudo systemctl reload nginx
# OR
sudo nginx -s reload

# View logs
docker compose logs -f web
sudo tail -f /var/log/nginx/error.log
```

---

**Next**: Clean up old containers (Step 1), configure your nginx (Steps 2-3), then redeploy! 🚀

