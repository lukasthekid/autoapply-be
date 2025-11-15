# Domain Setup Guide for project100x.run.place

Your frontend: `https://project100x.run.place/`  
Recommended backend: `https://api.project100x.run.place/`

## Option 1: Backend on Subdomain (Recommended)

### Step 1: DNS Configuration

Add an A record in your DNS settings:

```
Type: A
Name: api
Value: 5.75.171.23
TTL: Auto or 3600
```

This will make your backend accessible at: `https://api.project100x.run.place/`

### Step 2: Update Environment Variables

Your production `.env` file should have:

```env
SECRET_KEY=your-secret-key-here
DEBUG=False
ALLOWED_HOSTS=api.project100x.run.place,5.75.171.23
CORS_ALLOWED_ORIGINS=https://project100x.run.place
DB_HOST=db
DB_PORT=5432
DB_NAME=autoapply
DB_USER=postgres
DB_PASSWORD=your-database-password
```

### Step 3: Update Nginx Configuration

The nginx configuration has been updated to use your domain.

### Step 4: SSL Certificate (Let's Encrypt)

After DNS is configured and pointing to your server:

```bash
ssh -i C:\Users\lukb9\.ssh\id_ed25519 lukas@5.75.171.23

# Install certbot
sudo apt-get update
sudo apt-get install certbot python3-certbot-nginx -y

# Stop nginx temporarily
cd ~/autoapply-be
docker compose -f docker compose.yml -f docker compose.prod.yml stop nginx

# Get certificate
sudo certbot certonly --standalone -d api.project100x.run.place

# Start nginx again
docker compose -f docker compose.yml -f docker compose.prod.yml start nginx
```

### Step 5: Enable HTTPS in Nginx

After getting the SSL certificate, update the nginx config to enable HTTPS (already prepared in the config).

---

## Option 2: Backend on Same Domain with Path

If you prefer `https://project100x.run.place/api/` instead:

### DNS Configuration
No additional DNS needed, just use the existing domain.

### Nginx Configuration
Would need to be set up on the main domain's server or use a reverse proxy.

---

## GitHub Secrets Configuration

Update these secrets in your GitHub repository:

```
SECRET_KEY = <generate new one>
ALLOWED_HOSTS = api.project100x.run.place,5.75.171.23
CORS_ALLOWED_ORIGINS = https://project100x.run.place
DB_NAME = autoapply
DB_USER = postgres
DB_PASSWORD = <your-password>
SERVER_IP = 5.75.171.23
SSH_USER = lukas
SSH_PRIVATE_KEY = <your-ssh-key>
```

---

## Testing

After deployment:

1. **Frontend can call backend at**: `https://api.project100x.run.place/api/docs`
2. **Health check**: `https://api.project100x.run.place/health`
3. **Admin panel**: `https://api.project100x.run.place/admin/`

---

## Frontend Configuration

In your frontend (React/Next.js/etc.), set the API base URL:

```javascript
// .env or config file
NEXT_PUBLIC_API_URL=https://api.project100x.run.place
# or
REACT_APP_API_URL=https://api.project100x.run.place
```

Then make API calls:

```javascript
const response = await fetch(`${process.env.NEXT_PUBLIC_API_URL}/api/endpoint`, {
  method: 'GET',
  credentials: 'include', // Important for cookies/auth
  headers: {
    'Content-Type': 'application/json',
  },
});
```

---

## Quick Setup Commands

```powershell
# From your local machine
cd "C:\Users\lukb9\Desktop\Dev Projects\autoapply-be"

# Update .env.production locally with the new domain
# Then follow the deployment guide
```

Your API will be accessible at: `https://api.project100x.run.place/`

