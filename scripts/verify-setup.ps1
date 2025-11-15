# PowerShell verification script to check if all deployment files are present
# Run this before attempting deployment

Write-Host "🔍 Verifying deployment setup..." -ForegroundColor Cyan
Write-Host ""

$Errors = 0
$Warnings = 0

function Check-File {
    param([string]$Path)
    if (Test-Path $Path) {
        Write-Host "✓ $Path" -ForegroundColor Green
    } else {
        Write-Host "✗ $Path (MISSING)" -ForegroundColor Red
        $script:Errors++
    }
}

function Check-Dir {
    param([string]$Path)
    if (Test-Path $Path -PathType Container) {
        Write-Host "✓ $Path/" -ForegroundColor Green
    } else {
        Write-Host "✗ $Path/ (MISSING)" -ForegroundColor Red
        $script:Errors++
    }
}

Write-Host "📦 Checking Docker configuration..." -ForegroundColor Yellow
Check-File "Dockerfile"
Check-File "docker-compose.yml"
Check-File "docker-compose.prod.yml"
Check-File ".dockerignore"
Write-Host ""

Write-Host "🌐 Checking Nginx configuration..." -ForegroundColor Yellow
Check-Dir "nginx"
Check-File "nginx\nginx.conf"
Check-File "nginx\conf.d\autoapply.conf"
Write-Host ""

Write-Host "🤖 Checking CI/CD configuration..." -ForegroundColor Yellow
Check-Dir ".github\workflows"
Check-File ".github\workflows\deploy.yml"
Write-Host ""

Write-Host "📜 Checking deployment scripts..." -ForegroundColor Yellow
Check-Dir "scripts"
Check-File "scripts\setup-server.sh"
Check-File "scripts\deploy.sh"
Check-File "scripts\rollback.sh"
Check-File "scripts\local-deploy-test.ps1"
Write-Host ""

Write-Host "📄 Checking configuration files..." -ForegroundColor Yellow
Check-File "env.production.template"
Check-File "requirements.txt"
Write-Host ""

Write-Host "📚 Checking documentation..." -ForegroundColor Yellow
Check-File "DEPLOYMENT.md"
Check-File "QUICK_START_DEPLOY.md"
Check-File "DOCKER_CHEATSHEET.md"
Check-File "DEPLOYMENT_SUMMARY.md"
Write-Host ""

# Check if requirements.txt has gunicorn
if (Select-String -Path "requirements.txt" -Pattern "gunicorn" -Quiet) {
    Write-Host "✓ gunicorn in requirements.txt" -ForegroundColor Green
} else {
    Write-Host "✗ gunicorn not in requirements.txt" -ForegroundColor Red
    $Errors++
}
Write-Host ""

# Optional checks
Write-Host "⚠️  Optional checks..." -ForegroundColor Yellow

if (Test-Path ".env") {
    Write-Host "⚠  .env file exists (should not be committed to git)" -ForegroundColor Yellow
    $Warnings++
} else {
    Write-Host "✓ No .env file in repo (good)" -ForegroundColor Green
}

if (Test-Path "env.example") {
    Write-Host "✓ env.example exists" -ForegroundColor Green
} else {
    Write-Host "⚠  env.example not found (not critical)" -ForegroundColor Yellow
    $Warnings++
}

Write-Host ""
Write-Host "========================================" -ForegroundColor Gray

if ($Errors -eq 0) {
    Write-Host "✅ All required files are present!" -ForegroundColor Green
    Write-Host ""
    Write-Host "Next steps:" -ForegroundColor Cyan
    Write-Host "1. Review DEPLOYMENT_SUMMARY.md"
    Write-Host "2. Follow QUICK_START_DEPLOY.md for deployment"
    Write-Host "3. Configure GitHub secrets for CI/CD"
} else {
    Write-Host "❌ Found $Errors missing files!" -ForegroundColor Red
    Write-Host "Please ensure all required files are present before deploying."
    exit 1
}

if ($Warnings -gt 0) {
    Write-Host "⚠️  $Warnings warnings (review recommended)" -ForegroundColor Yellow
}

Write-Host "========================================" -ForegroundColor Gray

