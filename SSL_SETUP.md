# SSL/HTTPS Setup for api.project100x.run.place

Complete guide to set up SSL certificate for your backend API.

## Prerequisites

- DNS A record for `api.project100x.run.place` pointing to `5.75.171.23`
- Docker deployment running on your server
- SSH access to your server

## Step 1: Add DNS Record

In your DNS provider (where you manage project100x.run.place):

```
Type: A
Name: api
Value: 5.75.171.23
TTL: 3600 (or Auto)
```

Wait 5-10 minutes for DNS propagation. Test with:

```powershell
nslookup api.project100x.run.place
```

Should return: `5.75.171.23`

## Step 2: Install Certbot on Server

```bash
ssh -i C:\Users\lukb9\.ssh\id_ed25519 lukas@5.75.171.23

# Update system
sudo apt-get update

# Install certbot
sudo apt-get install certbot -y
```

## Step 3: Stop Nginx (Temporarily)

```bash
cd ~/autoapply-be
docker-compose -f docker-compose.yml -f docker-compose.prod.yml stop nginx
```

## Step 4: Get SSL Certificate

```bash
sudo certbot certonly --standalone \
  -d api.project100x.run.place \
  --email your-email@example.com \
  --agree-tos \
  --no-eff-email
```

Follow the prompts. Certificate will be saved to:
- Certificate: `/etc/letsencrypt/live/api.project100x.run.place/fullchain.pem`
- Private Key: `/etc/letsencrypt/live/api.project100x.run.place/privkey.pem`

## Step 5: Copy Certificates to Docker Volume

```bash
# Create directories
mkdir -p ~/autoapply-be/certbot/conf
sudo cp -r /etc/letsencrypt/* ~/autoapply-be/certbot/conf/
sudo chown -R lukas:lukas ~/autoapply-be/certbot/
```

## Step 6: Update Nginx Configuration

Edit the nginx config to enable HTTPS:

```bash
cd ~/autoapply-be
nano nginx/conf.d/autoapply.conf
```

Uncomment the HTTPS server block (around line 50-80). Make sure these lines are uncommented:

```nginx
server {
    listen 443 ssl http2;
    server_name api.project100x.run.place;

    ssl_certificate /etc/letsencrypt/live/api.project100x.run.place/fullchain.pem;
    ssl_certificate_key /etc/letsencrypt/live/api.project100x.run.place/privkey.pem;
    
    # ... rest of the configuration
}
```

Also uncomment the HTTP to HTTPS redirect in the HTTP server block:

```nginx
server {
    listen 80;
    server_name api.project100x.run.place 5.75.171.23;
    
    # Redirect HTTP to HTTPS
    return 301 https://$host$request_uri;
    
    # Keep the .well-known location for renewals
    location /.well-known/acme-challenge/ {
        root /var/www/certbot;
    }
}
```

## Step 7: Restart Nginx

```bash
docker-compose -f docker-compose.yml -f docker-compose.prod.yml start nginx

# Or restart all services
docker-compose -f docker-compose.yml -f docker-compose.prod.yml restart
```

## Step 8: Test HTTPS

```bash
# From your local machine
curl https://api.project100x.run.place/health
```

Or open in browser: `https://api.project100x.run.place/api/docs`

## Step 9: Set Up Auto-Renewal

Certbot certificates expire every 90 days. Set up automatic renewal:

```bash
# Test renewal
sudo certbot renew --dry-run

# Set up cron job
sudo crontab -e

# Add this line (runs daily at 2am):
0 2 * * * certbot renew --quiet --deploy-hook "cd /home/lukas/autoapply-be && docker-compose -f docker-compose.yml -f docker-compose.prod.yml restart nginx"
```

## Step 10: Update Django Settings (if needed)

If you want to enforce HTTPS in Django:

```bash
docker-compose -f docker-compose.yml -f docker-compose.prod.yml exec web nano ~/autoapply-be/.env
```

Add these settings to your `.env`:

```env
SECURE_SSL_REDIRECT=True
SESSION_COOKIE_SECURE=True
CSRF_COOKIE_SECURE=True
SECURE_HSTS_SECONDS=31536000
SECURE_HSTS_INCLUDE_SUBDOMAINS=True
SECURE_HSTS_PRELOAD=True
```

Then restart the web container:

```bash
docker-compose -f docker-compose.yml -f docker-compose.prod.yml restart web
```

## Verification Checklist

- [ ] DNS A record for `api.project100x.run.place` points to `5.75.171.23`
- [ ] SSL certificate obtained from Let's Encrypt
- [ ] Nginx HTTPS server block uncommented and configured
- [ ] HTTP to HTTPS redirect enabled
- [ ] Can access `https://api.project100x.run.place/health`
- [ ] Can access `https://api.project100x.run.place/api/docs`
- [ ] Browser shows secure padlock icon
- [ ] Auto-renewal cron job configured

## Frontend Configuration

Update your frontend to use HTTPS:

```javascript
// .env or config
NEXT_PUBLIC_API_URL=https://api.project100x.run.place
```

Make sure to include credentials in API calls:

```javascript
fetch('https://api.project100x.run.place/api/endpoint', {
  credentials: 'include', // Important for cookies
  headers: {
    'Content-Type': 'application/json',
  },
})
```

## Troubleshooting

### Certificate Not Valid

```bash
# Check certificate
sudo certbot certificates

# Check if DNS is resolving
nslookup api.project100x.run.place

# Check nginx logs
docker-compose -f docker-compose.yml -f docker-compose.prod.yml logs nginx
```

### HTTP Still Works (Not Redirecting)

Make sure the HTTP to HTTPS redirect line is uncommented in nginx config.

### Mixed Content Errors in Frontend

Make sure your frontend is also served over HTTPS and all API calls use HTTPS.

### Certificate Renewal Failed

```bash
# Manual renewal
sudo certbot renew --force-renewal

# Check renewal logs
sudo cat /var/log/letsencrypt/letsencrypt.log
```

## Quick Commands Reference

```bash
# Check certificate expiry
sudo certbot certificates

# Manual renewal
sudo certbot renew

# Test renewal (dry run)
sudo certbot renew --dry-run

# View nginx logs
docker-compose -f docker-compose.yml -f docker-compose.prod.yml logs nginx

# Restart nginx
docker-compose -f docker-compose.yml -f docker-compose.prod.yml restart nginx
```

---

**Your backend will be accessible at**: `https://api.project100x.run.place/`  
**Your frontend at**: `https://project100x.run.place/`

