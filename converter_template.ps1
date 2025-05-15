# Script para converter o template para o formato padronizado de seções

# Define a codificação para UTF-8 para lidar com caracteres especiais
[Console]::OutputEncoding = [System.Text.Encoding]::UTF8

# Diretório base do projeto
$BASE_DIR = $PSScriptRoot

# Configuração de ambiente
$env:PYTHONIOENCODING = "utf-8"

# Argumentos padrão
$TEMPLATE_PATH = Join-Path $BASE_DIR "templates\modelo_trabalhista.docx"
$OUTPUT_PATH = Join-Path $BASE_DIR "templates\modelo_trabalhista_convertido.docx"

# Verificação de ambiente virtual
$venvDir = Join-Path $BASE_DIR "venv"
$venvActivate = Join-Path $venvDir "Scripts\Activate.ps1"

if (Test-Path $venvActivate) {
    Write-Host "Ativando ambiente virtual Python..."
    & $venvActivate
} else {
    Write-Host "AVISO: Ambiente virtual não encontrado. O script pode não funcionar corretamente."
    Write-Host "Execute setup_ambiente.ps1 primeiro para configurar o ambiente."
}

# Verifica se o módulo python-docx está instalado
try {
    python -c "import docx" 2>$null
    $docxInstalled = $?
} catch {
    $docxInstalled = $false
}

if (-not $docxInstalled) {
    Write-Host "Instalando pacote python-docx..."
    pip install python-docx
}

# Cria o diretório de saída se não existir
$outputDir = Split-Path -Parent $OUTPUT_PATH
if (-not (Test-Path $outputDir)) {
    New-Item -ItemType Directory -Path $outputDir -Force | Out-Null
}

# Executa o script Python para converter o template
Write-Host "Iniciando conversão do template..."
python (Join-Path $BASE_DIR "src\utils\converter_template.py") --template $TEMPLATE_PATH --output $OUTPUT_PATH

if ($LASTEXITCODE -eq 0) {
    Write-Host "Template convertido com sucesso!" -ForegroundColor Green
    Write-Host "O template convertido está disponível em: $OUTPUT_PATH"
} else {
    Write-Host "Erro ao converter o template. Verifique os logs para mais detalhes." -ForegroundColor Red
}

Write-Host "Pressione qualquer tecla para sair..."
$null = $Host.UI.RawUI.ReadKey("NoEcho,IncludeKeyDown") 