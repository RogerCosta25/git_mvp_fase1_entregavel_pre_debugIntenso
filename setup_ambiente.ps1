# Script para configurar o ambiente de desenvolvimento
# Este script:
# 1. Verifica e instala as dependências necessárias
# 2. Cria um ambiente virtual Python
# 3. Instala os pacotes Python necessários

# Define a codificação para UTF-8 para lidar com caracteres especiais
[Console]::OutputEncoding = [System.Text.Encoding]::UTF8

# Configuração
$ErrorActionPreference = "Stop"
$BASE_DIR = $PSScriptRoot
$VENV_DIR = Join-Path $BASE_DIR "venv"
$REQUIREMENTS_FILE = Join-Path $BASE_DIR "requirements.txt"

# Cores para output
function Write-ColorOutput($ForegroundColor) {
    $fc = $host.UI.RawUI.ForegroundColor
    $host.UI.RawUI.ForegroundColor = $ForegroundColor
    if ($args) {
        Write-Output $args
    } else {
        $input | Write-Output
    }
    $host.UI.RawUI.ForegroundColor = $fc
}

# Cabeçalho
Clear-Host
Write-ColorOutput Green "======================================================"
Write-ColorOutput Green "  CONFIGURAÇÃO DO AMBIENTE - SISTEMA DE PETICIONAMENTO"
Write-ColorOutput Green "======================================================"
Write-Host 

# Verifica se Python está instalado
Write-Host "Verificando Python..." -NoNewline
try {
    $pythonVersion = python --version 2>&1
    Write-Host " Encontrado!" -ForegroundColor Green
    Write-Host "  Versão: $pythonVersion"
} catch {
    Write-Host " Não encontrado!" -ForegroundColor Red
    Write-Host "Por favor, instale Python 3.8 ou superior: https://www.python.org/downloads/"
    Write-Host "Certifique-se de marcar a opção 'Add Python to PATH' durante a instalação."
    exit 1
}

# Verifica se pip está instalado
Write-Host "Verificando pip..." -NoNewline
try {
    $pipVersion = python -m pip --version 2>&1
    Write-Host " Encontrado!" -ForegroundColor Green
    Write-Host "  Versão: $pipVersion"
} catch {
    Write-Host " Não encontrado!" -ForegroundColor Red
    Write-Host "Tentando instalar pip..."
    try {
        Invoke-WebRequest -Uri https://bootstrap.pypa.io/get-pip.py -OutFile get-pip.py
        python get-pip.py
        Remove-Item get-pip.py
        Write-Host "Pip instalado com sucesso!" -ForegroundColor Green
    } catch {
        Write-Host "Erro ao instalar pip. Por favor, instale manualmente." -ForegroundColor Red
        exit 1
    }
}

# Verifica se virtualenv está instalado
Write-Host "Verificando virtualenv..." -NoNewline
$virtualenvInstalled = $false
try {
    python -m pip show virtualenv >$null 2>&1
    $virtualenvInstalled = $?
} catch {
    $virtualenvInstalled = $false
}

if ($virtualenvInstalled) {
    Write-Host " Encontrado!" -ForegroundColor Green
} else {
    Write-Host " Não encontrado!" -ForegroundColor Yellow
    Write-Host "Instalando virtualenv..."
    try {
        python -m pip install virtualenv
        Write-Host "Virtualenv instalado com sucesso!" -ForegroundColor Green
    } catch {
        Write-Host "Erro ao instalar virtualenv. O script continuará, mas pode falhar." -ForegroundColor Red
    }
}

# Criação do ambiente virtual
Write-Host 
Write-Host "Criando ambiente virtual em $VENV_DIR..." -NoNewline
if (Test-Path $VENV_DIR) {
    $recriateVenv = Read-Host "  O ambiente virtual já existe. Deseja recriá-lo? (s/N)"
    if ($recriateVenv.ToLower() -eq "s") {
        Remove-Item -Recurse -Force $VENV_DIR
        python -m virtualenv $VENV_DIR
        Write-Host " Ambiente virtual recriado!" -ForegroundColor Green
    } else {
        Write-Host " Usando ambiente virtual existente." -ForegroundColor Yellow
    }
} else {
    python -m virtualenv $VENV_DIR
    Write-Host " Ambiente virtual criado!" -ForegroundColor Green
}

# Ativação do ambiente virtual
Write-Host "Ativando ambiente virtual..." -NoNewline
$activateScript = Join-Path $VENV_DIR "Scripts\Activate.ps1"
if (Test-Path $activateScript) {
    & $activateScript
    Write-Host " Ativado!" -ForegroundColor Green
} else {
    Write-Host " Falha ao ativar! O script de ativação não foi encontrado." -ForegroundColor Red
    exit 1
}

# Instalação das dependências
Write-Host 
Write-Host "Instalando dependências do projeto..." -ForegroundColor Green
if (Test-Path $REQUIREMENTS_FILE) {
    try {
        python -m pip install -r $REQUIREMENTS_FILE
        Write-Host "Todas as dependências foram instaladas com sucesso!" -ForegroundColor Green
    } catch {
        Write-Host "Erro ao instalar algumas dependências." -ForegroundColor Red
        Write-Host $_.Exception.Message
    }
} else {
    Write-Host "Arquivo requirements.txt não encontrado em $REQUIREMENTS_FILE" -ForegroundColor Red
    exit 1
}

# Configuração dos diretórios do projeto
Write-Host 
Write-Host "Verificando estrutura de diretórios do projeto..." -ForegroundColor Green
$diretorios = @(
    (Join-Path $BASE_DIR "data"),
    (Join-Path $BASE_DIR "dados"),
    (Join-Path $BASE_DIR "logs"),
    (Join-Path $BASE_DIR "output"),
    (Join-Path $BASE_DIR "templates")
)

foreach ($dir in $diretorios) {
    if (-not (Test-Path $dir)) {
        Write-Host "Criando diretório: $dir" -NoNewline
        New-Item -ItemType Directory -Path $dir -Force | Out-Null
        Write-Host " ✓" -ForegroundColor Green
    } else {
        Write-Host "Diretório existente: $dir ✓" -ForegroundColor Green
    }
}

# Conclusão
Write-Host 
Write-ColorOutput Green "======================================================"
Write-ColorOutput Green "  CONFIGURAÇÃO CONCLUÍDA!"
Write-ColorOutput Green "======================================================"
Write-Host 
Write-Host "O ambiente de desenvolvimento foi configurado com sucesso."
Write-Host "Para utilizar o sistema de peticionamento:"
Write-Host "1. Certifique-se de que há templates em '/templates'"
Write-Host "2. Coloque seus dados em '/dados'"
Write-Host "3. Execute o script 'executar_sistema.ps1'"
Write-Host 
Write-Host "Para converter templates existentes para o formato padronizado:"
Write-Host "   Execute o script 'converter_template.ps1'"
Write-Host 
Write-Host "Pressione qualquer tecla para sair..."
$null = $Host.UI.RawUI.ReadKey("NoEcho,IncludeKeyDown")