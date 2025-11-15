# autoapply-be
Generate Perfect Cover Letters with AI Upload your documents, search jobs from 6+ sources, and generate personalized cover letters tailored to each application. Powered by LLM technology for authentic, experience-based content.

## Setup

### 1. Create and Activate Virtual Environment

**Windows (PowerShell):**
```powershell
python -m venv venv
.\venv\Scripts\Activate.ps1
```

**Windows (Command Prompt):**
```cmd
python -m venv venv
venv\Scripts\activate.bat
```

**Linux/Mac:**
```bash
python -m venv venv
source venv/bin/activate
```

**Note:** If you get an execution policy error on Windows PowerShell, run:
```powershell
Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser
```

### 2. Install Dependencies

```bash
pip install --upgrade pip
pip install -r requirements.txt
```

### 3. Database Configuration

#### For Local Development

1. Create a `.env` file from the example:
   ```bash
   cp .env.example .env
   ```

2. Edit `.env` and fill in your database credentials:
   ```env
   DB_NAME=autoapply
   DB_USER=postgres
   DB_PASSWORD=your-password
   ```

3. Set up SSH tunnel to access the remote database:
   
   **Windows (PowerShell):**
   ```powershell
   .\setup-ssh-tunnel.ps1 -SSHUser your-username -SSHKey path\to\your\ssh\key
   ```
   
   **Linux/Mac:**
   ```bash
   chmod +x setup-ssh-tunnel.sh
   SSH_USER=your-username SSH_KEY_PATH=/path/to/your/key ./setup-ssh-tunnel.sh
   ```
   
   Or set environment variables:
   ```bash
   export SSH_USER=your-username
   export SSH_KEY_PATH=/path/to/your/key
   ./setup-ssh-tunnel.sh
   ```

   The SSH tunnel will forward `localhost:5433` to the remote database at `5.75.171.23:5433`.

4. Keep the SSH tunnel running in a separate terminal while developing.

#### For Production (on the server)

1. Create a `.env` file with production settings:
   ```env
   SECRET_KEY=your-production-secret-key
   DEBUG=False
   ALLOWED_HOSTS=your-domain.com,5.75.171.23
   DB_HOST=localhost
   DB_PORT=5433
   DB_NAME=autoapply
   DB_USER=postgres
   DB_PASSWORD=your-password
   ```

   Since the application runs on the same server as the database, use `localhost` as the host.

### 4. Run Migrations

```bash
python manage.py migrate
```

### 5. Create Superuser (optional)

```bash
python manage.py createsuperuser
```

### 6. Run Development Server

```bash
python manage.py runserver
```

The API will be available at:
- API: http://127.0.0.1:8000/api/
- API Docs: http://127.0.0.1:8000/api/docs
- Admin: http://127.0.0.1:8000/admin/

## Environment Variables

See `.env.example` for all available environment variables.

## Virtual Environment

This project uses a Python virtual environment to isolate dependencies. Always activate the virtual environment before working on the project:

**Activate (Windows PowerShell):**
```powershell
.\venv\Scripts\Activate.ps1
```

**Activate (Windows CMD):**
```cmd
venv\Scripts\activate.bat
```

**Activate (Linux/Mac):**
```bash
source venv/bin/activate
```

**Deactivate:**
```bash
deactivate
```

When the virtual environment is active, you'll see `(venv)` at the beginning of your command prompt.

## SSH Tunnel

The SSH tunnel is required for local development to access the remote PostgreSQL database securely. Make sure to:

1. Keep the tunnel running while developing
2. Use the correct SSH key with proper permissions (chmod 600 on Linux/Mac)
3. The tunnel forwards local port 5433 to the remote database port 5433

## Production Deployment

This project includes complete Docker deployment with CI/CD pipeline.

### Quick Start
See [QUICK_START_DEPLOY.md](QUICK_START_DEPLOY.md) for a 5-minute deployment guide.

### Full Documentation
See [DEPLOYMENT.md](DEPLOYMENT.md) for comprehensive deployment instructions including:
- Server setup with Docker
- GitHub Actions CI/CD configuration
- SSL/HTTPS setup
- Monitoring and maintenance
- Troubleshooting guide

### Deployment Options

**Option 1: Automatic CI/CD (Recommended)**
- Push to main/master branch
- GitHub Actions automatically deploys to server
- No manual intervention needed

**Option 2: Manual Deployment**
- Use provided deployment scripts
- Full control over deployment process
- Useful for testing and debugging

### Files Structure
```
├── Dockerfile                  # Production Docker image
├── docker-compose.yml          # Docker services configuration
├── docker-compose.prod.yml     # Production overrides
├── nginx/                      # Nginx reverse proxy config
├── scripts/
│   ├── setup-server.sh        # One-time server setup
│   ├── deploy.sh              # Deployment script
│   ├── rollback.sh            # Rollback script
│   └── local-deploy-test.ps1  # Test deployment from Windows
├── .github/workflows/
│   └── deploy.yml             # CI/CD pipeline
└── env.production.template    # Production environment template
```