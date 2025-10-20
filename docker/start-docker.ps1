# Script PowerShell para iniciar o ambiente Docker/Airflow
# Brewery Data Pipeline

Write-Host "========================================" -ForegroundColor Cyan
Write-Host "🚀 Brewery Pipeline - Docker Setup" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""

# Verificar se Docker está instalado
Write-Host "📋 Verificando Docker..." -ForegroundColor Yellow
try {
    $dockerVersion = docker --version
    Write-Host "✅ Docker encontrado: $dockerVersion" -ForegroundColor Green
} catch {
    Write-Host "❌ Docker não encontrado! Por favor, instale o Docker Desktop." -ForegroundColor Red
    Write-Host "   Download: https://www.docker.com/products/docker-desktop" -ForegroundColor Yellow
    exit 1
}

# Verificar se Docker Compose está disponível
Write-Host "📋 Verificando Docker Compose..." -ForegroundColor Yellow
try {
    $composeVersion = docker compose version
    Write-Host "✅ Docker Compose encontrado: $composeVersion" -ForegroundColor Green
} catch {
    Write-Host "❌ Docker Compose não encontrado!" -ForegroundColor Red
    exit 1
}

# Navegar para o diretório docker
Set-Location -Path $PSScriptRoot
Write-Host "📂 Diretório atual: $(Get-Location)" -ForegroundColor Cyan

# Criar diretórios necessários
Write-Host ""
Write-Host "📁 Criando diretórios necessários..." -ForegroundColor Yellow
$directories = @(
    "../data/raw",
    "../data/bronze",
    "../data/silver", 
    "../data/gold",
    "./logs",
    "./plugins"
)

foreach ($dir in $directories) {
    if (-not (Test-Path $dir)) {
        New-Item -ItemType Directory -Path $dir -Force | Out-Null
        Write-Host "   ✅ Criado: $dir" -ForegroundColor Green
    } else {
        Write-Host "   ⏭️  Já existe: $dir" -ForegroundColor Gray
    }
}

# Parar containers existentes
Write-Host ""
Write-Host "🛑 Parando containers existentes..." -ForegroundColor Yellow
docker compose down 2>&1 | Out-Null

# Construir imagens
Write-Host ""
Write-Host "🔨 Construindo imagens Docker..." -ForegroundColor Yellow
Write-Host "   (Isso pode levar alguns minutos na primeira vez)" -ForegroundColor Gray
docker compose build

if ($LASTEXITCODE -ne 0) {
    Write-Host "❌ Erro ao construir imagens!" -ForegroundColor Red
    exit 1
}

Write-Host "✅ Imagens construídas com sucesso!" -ForegroundColor Green

# Iniciar serviços
Write-Host ""
Write-Host "🚀 Iniciando serviços..." -ForegroundColor Yellow
docker compose up -d

if ($LASTEXITCODE -ne 0) {
    Write-Host "❌ Erro ao iniciar serviços!" -ForegroundColor Red
    exit 1
}

# Aguardar inicialização
Write-Host ""
Write-Host "⏳ Aguardando inicialização dos serviços (30 segundos)..." -ForegroundColor Yellow
Start-Sleep -Seconds 30

# Verificar status
Write-Host ""
Write-Host "📊 Status dos containers:" -ForegroundColor Cyan
docker compose ps

# Informações finais
Write-Host ""
Write-Host "========================================" -ForegroundColor Cyan
Write-Host "✅ Ambiente Docker iniciado!" -ForegroundColor Green
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""
Write-Host "🌐 Acesse o Airflow Web UI:" -ForegroundColor Yellow
Write-Host "   URL: http://localhost:8080" -ForegroundColor White
Write-Host "   Username: airflow" -ForegroundColor White
Write-Host "   Password: airflow" -ForegroundColor White
Write-Host ""
Write-Host "📋 Comandos úteis:" -ForegroundColor Yellow
Write-Host "   Ver logs:        docker compose logs -f" -ForegroundColor White
Write-Host "   Parar serviços:  docker compose down" -ForegroundColor White
Write-Host "   Reiniciar:       docker compose restart" -ForegroundColor White
Write-Host "   Status:          docker compose ps" -ForegroundColor White
Write-Host ""
