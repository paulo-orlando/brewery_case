# Setup script for Windows (PowerShell)
# Run with: .\setup.ps1

Write-Host "🚀 Setting up Brewery Pipeline..." -ForegroundColor Green

# Create virtual environment if it doesn't exist
if (-not (Test-Path ".venv")) {
    Write-Host "Creating virtual environment..." -ForegroundColor Yellow
    python -m venv .venv
}

# Activate virtual environment
Write-Host "Activating virtual environment..." -ForegroundColor Yellow
.\.venv\Scripts\Activate.ps1

# Upgrade pip
Write-Host "Upgrading pip..." -ForegroundColor Yellow
python -m pip install --upgrade pip

# Install dependencies
Write-Host "Installing dependencies..." -ForegroundColor Yellow
pip install -r requirements.txt

# Create data directories
Write-Host "Creating data directories..." -ForegroundColor Yellow
New-Item -ItemType Directory -Force -Path "data\raw" | Out-Null
New-Item -ItemType Directory -Force -Path "data\bronze" | Out-Null
New-Item -ItemType Directory -Force -Path "data\silver" | Out-Null
New-Item -ItemType Directory -Force -Path "data\gold" | Out-Null

# Run tests
Write-Host "Running tests..." -ForegroundColor Yellow
pytest src\tests\ -v

Write-Host ""
Write-Host "✅ Setup complete!" -ForegroundColor Green
Write-Host ""
Write-Host "To activate the virtual environment, run:" -ForegroundColor Cyan
Write-Host "  .\.venv\Scripts\Activate.ps1" -ForegroundColor White
Write-Host ""
Write-Host "To test the pipeline locally, run:" -ForegroundColor Cyan
Write-Host "  python src\api\brewery_api.py .\data\raw" -ForegroundColor White
Write-Host "  python src\bronze\bronze_layer.py .\data\raw .\data\bronze" -ForegroundColor White
Write-Host "  python src\silver\silver_layer.py .\data\bronze .\data\silver" -ForegroundColor White
Write-Host "  python src\gold\gold_layer.py .\data\silver .\data\gold" -ForegroundColor White
