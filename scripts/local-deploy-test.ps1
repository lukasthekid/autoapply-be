# PowerShell script for testing deployment locally on Windows

param(
    [string]$ServerIP = "5.75.171.23",
    [string]$SSHUser = "lukas",
    [string]$SSHKey = "C:\Users\lukb9\.ssh\id_ed25519"
)

Write-Host "🚀 Testing deployment to $ServerIP..." -ForegroundColor Green

# Check if SSH key exists
if (-not (Test-Path $SSHKey)) {
    Write-Host "❌ SSH key not found: $SSHKey" -ForegroundColor Red
    exit 1
}

# Test SSH connection
Write-Host "🔐 Testing SSH connection..." -ForegroundColor Yellow
$sshTest = ssh -i $SSHKey -o BatchMode=yes -o ConnectTimeout=5 "${SSHUser}@${ServerIP}" "echo 'Connection successful'" 2>&1
if ($LASTEXITCODE -ne 0) {
    Write-Host "❌ SSH connection failed. Please check your SSH key and server access." -ForegroundColor Red
    Write-Host $sshTest -ForegroundColor Red
    exit 1
}
Write-Host "✅ SSH connection successful" -ForegroundColor Green

# Create project directory on server
Write-Host "📁 Creating project directory on server..." -ForegroundColor Yellow
ssh -i $SSHKey "${SSHUser}@${ServerIP}" "mkdir -p ~/autoapply-be"

# Copy docker-compose files
Write-Host "📦 Copying deployment files to server..." -ForegroundColor Yellow
scp -i $SSHKey docker-compose.yml "${SSHUser}@${ServerIP}:~/autoapply-be/"
scp -i $SSHKey docker-compose.prod.yml "${SSHUser}@${ServerIP}:~/autoapply-be/"
scp -i $SSHKey -r nginx "${SSHUser}@${ServerIP}:~/autoapply-be/"
scp -i $SSHKey .env.production "${SSHUser}@${ServerIP}:~/autoapply-be/.env.production"

Write-Host "✅ Files copied successfully" -ForegroundColor Green
Write-Host ""
Write-Host "Next steps:" -ForegroundColor Yellow
Write-Host "1. SSH to your server: ssh -i $SSHKey ${SSHUser}@${ServerIP}"
Write-Host "2. Edit the .env file: cd ~/autoapply-be && nano .env.production"
Write-Host "3. Rename .env.production to .env: mv .env.production .env"
Write-Host "4. Run the deployment: bash scripts/deploy.sh"

