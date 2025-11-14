# PowerShell script to set up SSH tunnel for PostgreSQL database access
# This script creates an SSH tunnel from localhost:5433 to the remote database

param(
    [string]$SSHUser = $env:SSH_USER,
    [string]$SSHKey = $env:SSH_KEY_PATH,
    [string]$SSHServer = "5.75.171.23",
    [int]$SSHPort = 22,
    [int]$LocalPort = 5433,
    [int]$RemotePort = 5433
)

# Check if SSH key is provided
if (-not $SSHKey) {
    Write-Host "Error: SSH key path not provided." -ForegroundColor Red
    Write-Host "Usage: .\setup-ssh-tunnel.ps1 -SSHUser <username> -SSHKey <path-to-key>" -ForegroundColor Yellow
    Write-Host "Or set environment variables: SSH_USER and SSH_KEY_PATH" -ForegroundColor Yellow
    exit 1
}

# Check if SSH key file exists
if (-not (Test-Path $SSHKey)) {
    Write-Host "Error: SSH key file not found at: $SSHKey" -ForegroundColor Red
    exit 1
}

# Check if port is already in use
$portInUse = Get-NetTCPConnection -LocalPort $LocalPort -ErrorAction SilentlyContinue
if ($portInUse) {
    Write-Host "Warning: Port $LocalPort is already in use. The tunnel might already be running." -ForegroundColor Yellow
    Write-Host "If you want to create a new tunnel, please stop the existing one first." -ForegroundColor Yellow
    $response = Read-Host "Do you want to continue anyway? (y/n)"
    if ($response -ne "y") {
        exit 0
    }
}

# Build SSH command
$sshCommand = "ssh -N -L ${LocalPort}:localhost:${RemotePort} -i `"$SSHKey`" -p $SSHPort ${SSHUser}@${SSHServer}"

Write-Host "Setting up SSH tunnel..." -ForegroundColor Green
Write-Host "Local port: $LocalPort" -ForegroundColor Cyan
Write-Host "Remote server: ${SSHServer}:${RemotePort}" -ForegroundColor Cyan
Write-Host "SSH user: $SSHUser" -ForegroundColor Cyan
Write-Host ""
Write-Host "The tunnel will run in the background. Press Ctrl+C to stop it." -ForegroundColor Yellow
Write-Host ""

# Start SSH tunnel
try {
    Invoke-Expression $sshCommand
} catch {
    Write-Host "Error starting SSH tunnel: $_" -ForegroundColor Red
    exit 1
}

