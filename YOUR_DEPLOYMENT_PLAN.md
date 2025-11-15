# 🚀 Your Complete Deployment Plan

## Your Setup

- **Frontend**: `https://project100x.run.place/` ✅ (Already running)
- **Backend API**: `https://api.project100x.run.place/` 📦 (To be deployed)
- **Server IP**: `5.75.171.23`
- **SSH User**: `lukas`
- **SSH Key**: `C:\Users\lukb9\.ssh\id_ed25519`

---

## 📋 Complete Deployment Checklist

### Phase 1: DNS Configuration ⏱️ 5 minutes

- [ ] Add DNS A record:
  - Type: `A`
  - Name: `api`
  - Value: `5.75.171.23`
  - TTL: `3600`

- [ ] Wait 5-10 minutes for DNS propagation
- [ ] Verify DNS: `nslookup api.project100x.run.place` (should return 5.75.171.23)

---

### Phase 2: Server Setup (One-Time) ⏱️ 10 minutes

```bash

sudo apt-get update

sudo apt-get upgrade -y

sudo apt-get install -y \
    apt-transport-https \
    ca-certificates \
    curl \
    gnupg \
    lsb-release \
    git \
    ufw

sudo ufw allow 5433/tcp  # PostgreSQL (if you want external access)

mkdir -p ~/autoapply-be/certbot/conf
mkdir -p ~/autoapply-be/certbot/www

# Verify Docker works without sudo
docker ps
```

---

### Phase 2: GitHub Secrets Configuration ⏱️ 5 minutes

Go to: `https://github.com/<your-username>/autoapply-be/settings/secrets/actions`

Add these secrets:

| Secret Name | Value |
|-------------|-------|
| `SERVER_IP` | `5.75.171.23` |
| `SSH_USER` | `lukas` |
| `SSH_PRIVATE_KEY` | Paste entire contents of `C:\Users\lukb9\.ssh\id_ed25519` |
| `SECRET_KEY` | Generate: `python -c "import secrets; print(secrets.token_urlsafe(50))"` |
| `ALLOWED_HOSTS` | `api.project100x.run.place,5.75.171.23` |
| `CORS_ALLOWED_ORIGINS` | `https://project100x.run.place` |
| `DB_NAME` | `autoapply` |
| `DB_USER` | `postgres` |
| `DB_PASSWORD` | Create a strong password |

**To get your SSH private key contents:**

```powershell
Get-Content C:\Users\lukb9\.ssh\id_ed25519 | Set-Clipboard
# Now paste in GitHub (Ctrl+V)
```

---

### Phase 4: Deploy! ⏱️ 5 minutes

```bash
# In your project directory
cd "C:\Users\lukb9\Desktop\Dev Projects\autoapply-be"

# Commit all deployment files
git add .
git commit -m "Add Docker deployment with CI/CD for project100x.run.place"

# Push to trigger deployment
git push origin main
```

**Monitor deployment**: `https://github.com/<your-username>/autoapply-be/actions`

GitHub Actions will automatically:
1. ✅ Run tests
2. ✅ Build Docker image
3. ✅ Push to GitHub Container Registry
4. ✅ Deploy to your server
5. ✅ Run migrations
6. ✅ Collect static files
7. ✅ Health check

---

### Phase 5: Verify Deployment ⏱️ 2 minutes

```powershell
# Test health endpoint
curl http://5.75.171.23/health

# Open API docs in browser
Start-Process "http://5.75.171.23/api/docs"
```

Should see:
- ✅ Health check returns "healthy"
- ✅ API docs page loads
- ✅ Can access admin at `http://5.75.171.23/admin/`

---

### Phase 6: SSL/HTTPS Setup ⏱️ 10 minutes

**⚠️ Do this AFTER DNS is configured and deployment is working**

```bash
# SSH to server
ssh -i C:\Users\lukb9\.ssh\id_ed25519 lukas@5.75.171.23

# Install certbot
sudo apt-get update
sudo apt-get install certbot -y

# Stop nginx temporarily
cd ~/autoapply-be
docker-compose -f docker-compose.yml -f docker-compose.prod.yml stop nginx

# Get SSL certificate
sudo certbot certonly --standalone \
  -d api.project100x.run.place \
  --email your-email@example.com \
  --agree-tos \
  --no-eff-email

# Copy certificates
mkdir -p ~/autoapply-be/certbot/conf
sudo cp -r /etc/letsencrypt/* ~/autoapply-be/certbot/conf/
sudo chown -R lukas:lukas ~/autoapply-be/certbot/

# Edit nginx config to enable HTTPS
nano ~/autoapply-be/nginx/conf.d/autoapply.conf
```

**In the nginx config file**:
1. Find the HTTPS server block (around line 50)
2. Uncomment the entire HTTPS server block
3. Find line with `return 301 https://$host$request_uri;` (around line 10)
4. Uncomment that line to enable HTTP → HTTPS redirect
5. Save (Ctrl+O, Enter, Ctrl+X)

```bash
# Restart services
docker-compose -f docker-compose.yml -f docker-compose.prod.yml up -d

# Test HTTPS
curl https://api.project100x.run.place/health
```

**Set up auto-renewal**:

```bash
sudo crontab -e
# Add this line:
0 2 * * * certbot renew --quiet --deploy-hook "cd /home/lukas/autoapply-be && docker-compose -f docker-compose.yml -f docker-compose.prod.yml restart nginx"
```

---

### Phase 7: Update Frontend ⏱️ 5 minutes

In your frontend project, update the API URL:

```javascript
// .env.local or .env.production
NEXT_PUBLIC_API_URL=https://api.project100x.run.place

// or for React
REACT_APP_API_URL=https://api.project100x.run.place
```

**Example API call**:

```javascript
// Example with fetch
const response = await fetch(`${process.env.NEXT_PUBLIC_API_URL}/api/your-endpoint`, {
  method: 'GET',
  credentials: 'include', // Important for cookies/JWT
  headers: {
    'Content-Type': 'application/json',
    'Authorization': `Bearer ${token}`, // If using JWT
  },
});

const data = await response.json();
```

**Example with axios**:

```javascript
import axios from 'axios';

const api = axios.create({
  baseURL: process.env.NEXT_PUBLIC_API_URL,
  withCredentials: true, // Important for cookies
});

// Use it
const response = await api.get('/api/your-endpoint');
```

---

## 🎯 Final URLs

After completing all phases:

- **Frontend**: `https://project100x.run.place/`
- **Backend API Docs**: `https://api.project100x.run.place/api/docs`
- **Backend Admin**: `https://api.project100x.run.place/admin/`
- **Health Check**: `https://api.project100x.run.place/health`

---

## 🔄 Daily Workflow (After Initial Setup)

1. **Develop locally** as usual
2. **Commit and push** to GitHub
3. **Automatic deployment** happens via CI/CD
4. **No manual steps needed!** 🎉

---

## 📚 Documentation Reference

| Document | Purpose |
|----------|---------|
| `YOUR_DEPLOYMENT_PLAN.md` | 👉 **This file - Your complete plan** |
| `QUICK_START_DEPLOY.md` | Quick reference guide |
| `DOMAIN_SETUP.md` | Domain configuration details |
| `SSL_SETUP.md` | Detailed SSL/HTTPS setup |
| `DEPLOYMENT.md` | Comprehensive deployment docs |
| `DOCKER_CHEATSHEET.md` | Docker commands reference |

---

## 🆘 Troubleshooting

### DNS not resolving

```powershell
# Check DNS
nslookup api.project100x.run.place

# Wait 10-15 minutes if just added
# Clear local DNS cache
ipconfig /flushdns
```

### GitHub Actions deployment failed

1. Check Actions tab: `https://github.com/<your-username>/autoapply-be/actions`
2. Click on the failed workflow
3. Check which step failed
4. Common issues:
   - SSH key incorrect (make sure no passphrase)
   - Server not accessible
   - Docker not running on server

### Can't access API

```bash
# SSH to server
ssh -i C:\Users\lukb9\.ssh\id_ed25519 lukas@5.75.171.23

# Check services
docker ps

# Check logs
cd ~/autoapply-be
docker-compose -f docker-compose.yml -f docker-compose.prod.yml logs -f
```

### SSL certificate issues

```bash
# Check certificate
sudo certbot certificates

# Renew manually
sudo certbot renew --force-renewal

# Check nginx config
docker-compose -f docker-compose.yml -f docker-compose.prod.yml logs nginx
```

### CORS errors in frontend

Make sure:
- `CORS_ALLOWED_ORIGINS` in `.env` includes `https://project100x.run.place`
- No trailing slash in CORS origin
- Using `credentials: 'include'` in fetch calls

---

## ⏱️ Total Time Estimate

- DNS Configuration: 5 min + 10 min wait
- Server Setup: 10 min
- GitHub Secrets: 5 min
- Deployment: 5 min
- Verification: 2 min
- SSL Setup: 10 min
- Frontend Update: 5 min

**Total: ~50 minutes** (including DNS propagation wait time)

---

## ✅ Success Criteria

You'll know everything is working when:

- [ ] `https://api.project100x.run.place/health` returns "healthy"
- [ ] `https://api.project100x.run.place/api/docs` shows API documentation
- [ ] Browser shows 🔒 (secure padlock) for your API
- [ ] Your frontend at `https://project100x.run.place/` can make API calls successfully
- [ ] No CORS errors in browser console
- [ ] Push to GitHub automatically deploys

---

## 🎉 You're Ready!

Follow the phases in order, and you'll have a production-ready API deployed with automatic CI/CD!

**Start with Phase 1 (DNS Configuration) now!**

Need help? Check the detailed documentation or the troubleshooting section above.

