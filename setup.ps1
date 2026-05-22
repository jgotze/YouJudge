# YouJudge Setup Script for Windows
# Run this script after installing Python

Write-Host "=== YouJudge Setup Script ===" -ForegroundColor Cyan
Write-Host ""

# Check Python installation
Write-Host "1. Checking Python installation..." -ForegroundColor Yellow
try {
    $pythonVersion = python --version 2>&1
    Write-Host "   ✓ $pythonVersion" -ForegroundColor Green
} catch {
    Write-Host "   ✗ Python not found! Please install Python first." -ForegroundColor Red
    Write-Host "   Download from: https://www.python.org/downloads/" -ForegroundColor Yellow
    exit 1
}

# Create virtual environment
Write-Host ""
Write-Host "2. Creating virtual environment..." -ForegroundColor Yellow
if (Test-Path "venv") {
    Write-Host "   Virtual environment already exists." -ForegroundColor Blue
} else {
    python -m venv venv
    Write-Host "   ✓ Virtual environment created" -ForegroundColor Green
}

# Activate virtual environment
Write-Host ""
Write-Host "3. Activating virtual environment..." -ForegroundColor Yellow
& .\venv\Scripts\Activate.ps1
Write-Host "   ✓ Virtual environment activated" -ForegroundColor Green

# Upgrade pip
Write-Host ""
Write-Host "4. Upgrading pip..." -ForegroundColor Yellow
python -m pip install --upgrade pip
Write-Host "   ✓ Pip upgraded" -ForegroundColor Green

# Install dependencies
Write-Host ""
Write-Host "5. Installing dependencies (this may take a few minutes)..." -ForegroundColor Yellow
pip install -r requirements.txt
Write-Host "   ✓ Dependencies installed" -ForegroundColor Green

# Create .env file
Write-Host ""
Write-Host "6. Setting up environment file..." -ForegroundColor Yellow
if (Test-Path ".env") {
    Write-Host "   .env file already exists." -ForegroundColor Blue
} else {
    Copy-Item .env.example .env
    Write-Host "   ✓ .env file created from .env.example" -ForegroundColor Green
    Write-Host "   ⚠ Please edit .env file with your settings!" -ForegroundColor Yellow
}

# Create static and media directories
Write-Host ""
Write-Host "7. Creating directories..." -ForegroundColor Yellow
New-Item -ItemType Directory -Force -Path "static" | Out-Null
New-Item -ItemType Directory -Force -Path "media" | Out-Null
New-Item -ItemType Directory -Force -Path "media\avatars" | Out-Null
New-Item -ItemType Directory -Force -Path "media\competitions" | Out-Null
New-Item -ItemType Directory -Force -Path "media\entries" | Out-Null
Write-Host "   ✓ Directories created" -ForegroundColor Green

Write-Host ""
Write-Host "=== Setup Complete! ===" -ForegroundColor Cyan
Write-Host ""
Write-Host "Next Steps:" -ForegroundColor Yellow
Write-Host "1. Install PostgreSQL (if not installed)" -ForegroundColor White
Write-Host "   Download from: https://www.postgresql.org/download/windows/" -ForegroundColor Gray
Write-Host ""
Write-Host "2. Create database:" -ForegroundColor White
Write-Host "   psql -U postgres" -ForegroundColor Gray
Write-Host "   CREATE DATABASE youjudge_db;" -ForegroundColor Gray
Write-Host "   \q" -ForegroundColor Gray
Write-Host ""
Write-Host "3. Run migrations:" -ForegroundColor White
Write-Host "   python manage.py migrate" -ForegroundColor Gray
Write-Host ""
Write-Host "4. Create superuser:" -ForegroundColor White
Write-Host "   python manage.py createsuperuser" -ForegroundColor Gray
Write-Host ""
Write-Host "5. Run development server:" -ForegroundColor White
Write-Host "   python manage.py runserver" -ForegroundColor Gray
Write-Host ""
