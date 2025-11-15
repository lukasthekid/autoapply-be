# Deployment Guide for autoapply-be

This guide walks you through deploying your Django Ninja application to your server using Docker and GitHub Actions CI/CD.

## Table of Contents

1. [Prerequisites](#prerequisites)
2. [Server Setup](#server-setup)
3. [GitHub Repository Setup](#github-repository-setup)
4. [Manual Deployment](#manual-deployment)
5. [CI/CD Deployment](#cicd-deployment)
6. [SSL Certificate Setup](#ssl-certificate-setup)
7. [Monitoring and Maintenance](#monitoring-and-maintenance)
8. [Troubleshooting](#troubleshooting)

---

## Prerequisites

- A server with Ubuntu 20.04+ (your server: **5.75.171.23**)
- SSH access with key authentication (user: **lukas**)
- Docker and Docker Compose installed on the server
- A GitHub account with your code repository
- Domain name (optional, but recommended for production)

---

## Server Setup

### Step 1: Initial Server Configuration

SSH into your server:

```bash
ssh -i C:\Users\lukb9\.ssh\id_ed25519 lukas@5.75.171.23
```

### Step 2: Run the Server Setup Script

Copy the setup script to your server and run it:

```bash
# From your local machine (PowerShell)
scp -i C:\Users\lukb9\.ssh\id_ed25519 scripts/setup-server.sh lukas@5.75.171.23:~/

# Then SSH to the server and run it
ssh -i C:\Users\lukb9\.ssh\id_ed25519 lukas@5.75.171.23
bash ~/setup-server.sh
```

This script will:
- Update system packages
- Install Docker and Docker Compose
- Configure the firewall (UFW)
- Create the project directory structure
- Set up SSL certificate directories

After running the script, **log out and log back in** for Docker group membership to take effect.

### Step 3: Verify Installation

```bash
docker --version
docker compose --version
docker ps  # Should work without sudo
```

---

## GitHub Repository Setup

### Step 1: Make Your Repository Package-Accessible

1. Go to your GitHub repository settings
2. Navigate to **Actions** > **General**
3. Under **Workflow permissions**, select **Read and write permissions**
4. Save changes

### Step 2: Add GitHub Secrets

Go to your repository **Settings** > **Secrets and variables** > **Actions**, and add these secrets:

| Secret Name | Value | Description |
|-------------|-------|-------------|
| `SERVER_IP` | `5.75.171.23` | Your server IP address |
| `SSH_USER` | `lukas` | Your SSH username |
| `SSH_PRIVATE_KEY` | Contents of `C:\Users\lukb9\.ssh\id_ed25519` | Your SSH private key |
| `SECRET_KEY` | Generate a strong random key | Django secret key for production |
| `ALLOWED_HOSTS` | `5.75.171.23,your-domain.com` | Allowed hosts for Django |
| `CORS_ALLOWED_ORIGINS` | `https://your-frontend.com` | CORS allowed origins |
| `DB_NAME` | `autoapply` | Database name |
| `DB_USER` | `postgres` | Database user |
| `DB_PASSWORD` | Strong password | Database password |

#### Generate a Strong Secret Key

Run this in Python:

```python
import secrets
print(secrets.token_urlsafe(50))
```

Or use an online generator: https://djecrety.ir/

### Step 3: Configure Package Visibility

After the first successful workflow run:

1. Go to your GitHub profile
2. Click on **Packages**
3. Find your `autoapply-be` package
4. Click **Package settings**
5. Under **Danger Zone**, change visibility to **Public** (or keep private and configure access)

---

## Manual Deployment

If you want to deploy manually without CI/CD:

### Step 1: Copy Files to Server

From your local machine (PowerShell):

```powershell
# Navigate to your project directory
cd "C:\Users\lukb9\Desktop\Dev Projects\autoapply-be"

# Run the test deployment script
.\scripts\local-deploy-test.ps1
```

Or manually:

```powershell
scp -i C:\Users\lukb9\.ssh\id_ed25519 docker compose.yml lukas@5.75.171.23:~/autoapply-be/
scp -i C:\Users\lukb9\.ssh\id_ed25519 docker compose.prod.yml lukas@5.75.171.23:~/autoapply-be/
scp -i C:\Users\lukb9\.ssh\id_ed25519 -r nginx lukas@5.75.171.23:~/autoapply-be/
scp -i C:\Users\lukb9\.ssh\id_ed25519 env.production.template lukas@5.75.171.23:~/autoapply-be/.env
```

### Step 2: Configure Environment Variables

SSH to your server and edit the `.env` file:

```bash
ssh -i C:\Users\lukb9\.ssh\id_ed25519 lukas@5.75.171.23
cd ~/autoapply-be
nano .env
```

Fill in all the required values from `env.production.template`.

### Step 3: Build and Start Services

```bash
cd ~/autoapply-be
docker compose -f docker compose.yml -f docker compose.prod.yml up -d --build
```

### Step 4: Run Migrations

```bash
docker compose -f docker compose.yml -f docker compose.prod.yml exec web python manage.py migrate
docker compose -f docker compose.yml -f docker compose.prod.yml exec web python manage.py collectstatic --noinput
```

### Step 5: Create Superuser (Optional)

```bash
docker compose -f docker compose.yml -f docker compose.prod.yml exec web python manage.py createsuperuser
```

### Step 6: Verify Deployment

```bash
curl http://localhost/health
curl http://5.75.171.23/api/docs
```

---

## CI/CD Deployment

Once GitHub secrets are configured, deployment is automatic:

### Automatic Deployment

1. **Push to main/master branch**:
   ```bash
   git add .
   git commit -m "Deploy to production"
   git push origin main
   ```

2. **GitHub Actions will automatically**:
   - Run tests
   - Build Docker image
   - Push to GitHub Container Registry
   - Deploy to your server
   - Run migrations
   - Collect static files
   - Perform health check

3. **Monitor deployment**:
   - Go to your GitHub repository
   - Click on **Actions** tab
   - Watch the deployment progress

### Manual Trigger

You can also manually trigger deployment:

1. Go to **Actions** tab
2. Select **Deploy to Production** workflow
3. Click **Run workflow**
4. Select branch and click **Run workflow**

---

## SSL Certificate Setup (Optional but Recommended)

### Using Let's Encrypt with Certbot

1. **Install Certbot on server**:

```bash
ssh -i C:\Users\lukb9\.ssh\id_ed25519 lukas@5.75.171.23
sudo apt-get install certbot
```

2. **Obtain SSL certificate**:

```bash
sudo certbot certonly --webroot -w ~/autoapply-be/certbot/www -d your-domain.com -d www.your-domain.com
```

3. **Update nginx configuration**:

Edit `nginx/conf.d/autoapply.conf` and uncomment the HTTPS server block, replacing `your-domain.com` with your actual domain.

4. **Restart nginx**:

```bash
cd ~/autoapply-be
docker compose -f docker compose.yml -f docker compose.prod.yml restart nginx
```

5. **Set up auto-renewal**:

```bash
sudo crontab -e
# Add this line:
0 12 * * * /usr/bin/certbot renew --quiet && cd ~/autoapply-be && docker compose -f docker compose.yml -f docker compose.prod.yml restart nginx
```

---

## Monitoring and Maintenance

### View Logs

```bash
# All services
docker compose -f docker compose.yml -f docker compose.prod.yml logs -f

# Specific service
docker compose -f docker compose.yml -f docker compose.prod.yml logs -f web
docker compose -f docker compose.yml -f docker compose.prod.yml logs -f db
docker compose -f docker compose.yml -f docker compose.prod.yml logs -f nginx
```

### Check Service Status

```bash
docker compose -f docker compose.yml -f docker compose.prod.yml ps
```

### Check Resource Usage

```bash
docker stats
```

### Database Backup

```bash
# Backup
docker compose -f docker compose.yml -f docker compose.prod.yml exec db pg_dump -U postgres autoapply > backup_$(date +%Y%m%d_%H%M%S).sql

# Restore
cat backup_file.sql | docker compose -f docker compose.yml -f docker compose.prod.yml exec -T db psql -U postgres autoapply
```

### Update Application

With CI/CD, just push to main/master branch. For manual update:

```bash
cd ~/autoapply-be
bash scripts/deploy.sh
```

### Rollback

If something goes wrong:

```bash
cd ~/autoapply-be
bash scripts/rollback.sh
```

---

## Troubleshooting

### Service Won't Start

**Check logs**:
```bash
docker compose -f docker compose.yml -f docker compose.prod.yml logs web
```

**Common issues**:
- Database connection: Check DB_HOST, DB_PORT, DB_PASSWORD in `.env`
- Port conflicts: Make sure ports 80, 443, 5433, 8000 are not in use
- Permissions: Make sure `.env` file is readable

### Database Connection Failed

```bash
# Check if database is running
docker compose -f docker compose.yml -f docker compose.prod.yml ps db

# Test database connection
docker compose -f docker compose.yml -f docker compose.prod.yml exec db psql -U postgres -d autoapply -c "SELECT 1;"
```

### Cannot Access from Internet

**Check firewall**:
```bash
sudo ufw status
sudo ufw allow 80/tcp
sudo ufw allow 443/tcp
```

**Check nginx**:
```bash
docker compose -f docker compose.yml -f docker compose.prod.yml logs nginx
```

### CI/CD Deployment Failed

1. Check GitHub Actions logs
2. Verify all secrets are set correctly
3. Make sure SSH key doesn't have a passphrase
4. Verify Docker is running on server: `docker ps`

### High Memory Usage

**Restart services**:
```bash
docker compose -f docker compose.yml -f docker compose.prod.yml restart
```

**Prune old containers and images**:
```bash
docker system prune -a --volumes
```

### Static Files Not Loading

```bash
docker compose -f docker compose.yml -f docker compose.prod.yml exec web python manage.py collectstatic --noinput
docker compose -f docker compose.yml -f docker compose.prod.yml restart nginx
```

---

## Useful Commands Reference

### Docker Compose Commands

```bash
# Start services
docker compose -f docker compose.yml -f docker compose.prod.yml up -d

# Stop services
docker compose -f docker compose.yml -f docker compose.prod.yml down

# Restart services
docker compose -f docker compose.yml -f docker compose.prod.yml restart

# View logs
docker compose -f docker compose.yml -f docker compose.prod.yml logs -f

# Execute command in container
docker compose -f docker compose.yml -f docker compose.prod.yml exec web python manage.py shell

# Rebuild and restart
docker compose -f docker compose.yml -f docker compose.prod.yml up -d --build
```

### Django Management Commands

```bash
# Run migrations
docker compose -f docker compose.yml -f docker compose.prod.yml exec web python manage.py migrate

# Create superuser
docker compose -f docker compose.yml -f docker compose.prod.yml exec web python manage.py createsuperuser

# Collect static files
docker compose -f docker compose.yml -f docker compose.prod.yml exec web python manage.py collectstatic --noinput

# Django shell
docker compose -f docker compose.yml -f docker compose.prod.yml exec web python manage.py shell
```

---

## Architecture Overview

```
┌─────────────────────────────────────────────────────────┐
│                     Internet                             │
└──────────────────────┬──────────────────────────────────┘
                       │
                       ▼
            ┌──────────────────┐
            │   Nginx (Port 80)│  ◄── Reverse Proxy & Static Files
            └─────────┬────────┘
                      │
                      ▼
            ┌─────────────────┐
            │  Django App      │  ◄── Gunicorn WSGI Server
            │  (Port 8000)     │      Django Ninja API
            └─────────┬────────┘
                      │
                      ▼
            ┌─────────────────┐
            │  PostgreSQL      │  ◄── Database
            │  (Port 5432)     │
            └──────────────────┘
```

---

## Security Checklist

- [ ] Strong SECRET_KEY set in production
- [ ] DEBUG=False in production
- [ ] ALLOWED_HOSTS properly configured
- [ ] CORS_ALLOWED_ORIGINS restricted to your frontend
- [ ] Strong database password
- [ ] Firewall (UFW) enabled and configured
- [ ] SSH key-based authentication (no password login)
- [ ] SSL/TLS certificate installed (HTTPS)
- [ ] Regular backups configured
- [ ] Docker containers running as non-root user
- [ ] GitHub secrets properly protected

---

## Support

If you encounter issues:

1. Check the [Troubleshooting](#troubleshooting) section
2. Review logs: `docker compose logs -f`
3. Check GitHub Actions workflow logs
4. Verify all environment variables are set correctly

---

## Next Steps

1. **Set up monitoring**: Consider using tools like Prometheus, Grafana, or Sentry
2. **Configure backups**: Set up automated database backups
3. **Add domain**: Point your domain to the server IP
4. **Enable HTTPS**: Follow the SSL certificate setup guide
5. **Set up email**: Configure email backend for password resets and notifications
6. **Performance tuning**: Adjust Gunicorn workers based on server resources

---

**Last Updated**: November 2025  
**Version**: 1.0

