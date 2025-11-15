# Quick Start Deployment Guide

This is a simplified guide to get you deployed quickly. For detailed information, see [DEPLOYMENT.md](DEPLOYMENT.md).

## 🚀 5-Minute Deployment

### Prerequisites Check
- ✅ Server: `5.75.171.23`
- ✅ SSH User: `lukas`
- ✅ SSH Key: `C:\Users\lukb9\.ssh\id_ed25519`

---

## Option 1: Automatic CI/CD Deployment (Recommended)

### Step 1: Setup Server (One-Time)

```powershell
# From your local machine
scp -i C:\Users\lukb9\.ssh\id_ed25519 scripts/setup-server.sh lukas@5.75.171.23:~/
ssh -i C:\Users\lukb9\.ssh\id_ed25519 lukas@5.75.171.23 "bash ~/setup-server.sh"
```

**Important**: Log out and back in after running the setup script!

### Step 2: Configure GitHub Secrets

Go to your GitHub repo → Settings → Secrets and variables → Actions

Add these secrets:

```
SERVER_IP = 5.75.171.23
SSH_USER = lukas
SSH_PRIVATE_KEY = <paste contents of C:\Users\lukb9\.ssh\id_ed25519>
SECRET_KEY = <generate using: python -c "import secrets; print(secrets.token_urlsafe(50))">
ALLOWED_HOSTS = api.project100x.run.place,5.75.171.23
CORS_ALLOWED_ORIGINS = https://project100x.run.place
DB_NAME = autoapply
DB_USER = admin
DB_PASSWORD = <your-existing-postgres-password>
```

### Step 3: Deploy

```bash
git add .
git commit -m "Initial deployment"
git push origin main
```

That's it! GitHub Actions will handle everything.

Monitor at: `https://github.com/<your-username>/autoapply-be/actions`

---

## Option 2: Manual Deployment

### Step 1: Setup Server

Same as Option 1, Step 1

### Step 2: Copy Files to Server

```powershell
cd "C:\Users\lukb9\Desktop\Dev Projects\autoapply-be"

# Copy deployment files
scp -i C:\Users\lukb9\.ssh\id_ed25519 docker compose.yml lukas@5.75.171.23:~/autoapply-be/
scp -i C:\Users\lukb9\.ssh\id_ed25519 docker compose.prod.yml lukas@5.75.171.23:~/autoapply-be/
scp -i C:\Users\lukb9\.ssh\id_ed25519 -r nginx lukas@5.75.171.23:~/autoapply-be/
scp -i C:\Users\lukb9\.ssh\id_ed25519 env.production.template lukas@5.75.171.23:~/autoapply-be/.env
scp -i C:\Users\lukb9\.ssh\id_ed25519 -r scripts lukas@5.75.171.23:~/autoapply-be/
```

### Step 3: Configure Environment

```bash
ssh -i C:\Users\lukb9\.ssh\id_ed25519 lukas@5.75.171.23
cd ~/autoapply-be
nano .env
```

Edit these values:
- `SECRET_KEY` - Generate a new one
- `DB_PASSWORD` - Set a strong password
- `ALLOWED_HOSTS` - Your server IP or domain
- `CORS_ALLOWED_ORIGINS` - Your frontend URL

### Step 4: Deploy

```bash
cd ~/autoapply-be
docker compose -f docker compose.yml -f docker compose.prod.yml up -d --build
```

### Step 5: Run Migrations

```bash
docker compose -f docker compose.yml -f docker compose.prod.yml exec web python manage.py migrate
docker compose -f docker compose.yml -f docker compose.prod.yml exec web python manage.py collectstatic --noinput
docker compose -f docker compose.yml -f docker compose.prod.yml exec web python manage.py createsuperuser
```

---

## ✅ Verify Deployment

### Test from local machine:

```powershell
# Health check
curl http://5.75.171.23/health

# API docs
curl http://5.75.171.23/api/docs
```

### Or in browser:
- API Docs: `http://5.75.171.23/api/docs` (will be `https://api.project100x.run.place/api/docs` after DNS setup)
- Admin Panel: `http://5.75.171.23/admin/` (will be `https://api.project100x.run.place/admin/` after DNS setup)

---

## 📊 Useful Commands

### View logs:
```bash
ssh -i C:\Users\lukb9\.ssh\id_ed25519 lukas@5.75.171.23
cd ~/autoapply-be
docker compose -f docker compose.yml -f docker compose.prod.yml logs -f
```

### Restart services:
```bash
docker compose -f docker compose.yml -f docker compose.prod.yml restart
```

### Stop services:
```bash
docker compose -f docker compose.yml -f docker compose.prod.yml down
```

### Update deployment (manual):
```bash
bash ~/autoapply-be/scripts/deploy.sh
```

---

## 🆘 Quick Troubleshooting

### Can't connect to server?
```powershell
ssh -i C:\Users\lukb9\.ssh\id_ed25519 lukas@5.75.171.23
# If this fails, check your SSH key and server IP
```

### Services not starting?
```bash
docker compose -f docker compose.yml -f docker compose.prod.yml logs web
# Check for error messages
```

### Can't access from browser?
```bash
# Check firewall
sudo ufw status
sudo ufw allow 80/tcp
```

### Database connection issues?
```bash
# Check database is running
docker compose -f docker compose.yml -f docker compose.prod.yml ps db
# Check .env file has correct DB_PASSWORD
```

---

## 📚 Next Steps

- [ ] Set up a domain name
- [ ] Configure SSL/HTTPS (see DEPLOYMENT.md)
- [ ] Set up automated backups
- [ ] Configure monitoring
- [ ] Review security checklist in DEPLOYMENT.md

For detailed information, troubleshooting, and advanced configuration, see [DEPLOYMENT.md](DEPLOYMENT.md).

