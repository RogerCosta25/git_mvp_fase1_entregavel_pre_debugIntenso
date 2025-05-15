# Script para diagnóstico de template DOCX
# Verifica e diagnostica problemas em templates para o sistema de peticionamento

# Parâmetros
param(
    [string]$template,
    [switch]$verbose = $false
)

# Configurações
$SCRIPT_DIR = $PSScriptRoot
$BASE_DIR = $SCRIPT_DIR
$PYTHON_PATH = "python"

# Verifica se foi fornecido um template
if (-not $template) {
    # Se não foi fornecido, lista os templates disponíveis
    $templatesDir = Join-Path $BASE_DIR "templates"
    $templates = Get-ChildItem -Path $templatesDir -Filter "*.docx" | Select-Object -ExpandProperty Name
    
    if ($templates.Count -eq 0) {
        Write-Host "Nenhum template encontrado na pasta templates." -ForegroundColor Red
        exit 1
    }
    
    # Apresenta opções
    Write-Host "Templates disponíveis:" -ForegroundColor Cyan
    for ($i = 0; $i -lt $templates.Count; $i++) {
        Write-Host "  $($i+1). $($templates[$i])" -ForegroundColor White
    }
    
    # Solicita escolha
    $escolha = Read-Host "Escolha o número do template para diagnóstico"
    if (-not $escolha -or -not ($escolha -match '^\d+$') -or [int]$escolha -lt 1 -or [int]$escolha -gt $templates.Count) {
        Write-Host "Escolha inválida." -ForegroundColor Red
        exit 1
    }
    
    $template = Join-Path $templatesDir $templates[[int]$escolha-1]
} else {
    # Verifica se o template existe
    if (-not (Test-Path $template)) {
        # Tenta procurar na pasta templates
        $templatesDir = Join-Path $BASE_DIR "templates"
        $templateTestPath = Join-Path $templatesDir $template
        
        if (Test-Path $templateTestPath) {
            $template = $templateTestPath
        } else {
            Write-Host "Template não encontrado: $template" -ForegroundColor Red
            exit 1
        }
    }
}

# Monta os argumentos para o script Python
$arguments = @(
    Join-Path $BASE_DIR "src\utils\template_diagnostico.py",
    "`"$template`""
)

if ($verbose) {
    $arguments += "--verbose"
}

# Executa o script de diagnóstico
Write-Host "Executando diagnóstico de template..." -ForegroundColor Cyan
Write-Host "Template: $template" -ForegroundColor Cyan
Write-Host

try {
    $commandLine = "$PYTHON_PATH $($arguments -join ' ')"
    Write-Host "Comando: $commandLine" -ForegroundColor Gray
    
    & $PYTHON_PATH $arguments
    
    if ($LASTEXITCODE -ne 0) {
        Write-Host "Erro na execução do diagnóstico. Código de saída: $LASTEXITCODE" -ForegroundColor Red
    } else {
        Write-Host "Diagnóstico concluído." -ForegroundColor Green
    }
} catch {
    Write-Host "ERRO: $($_.Exception.Message)" -ForegroundColor Red
}

# Perguntar se deseja executar o conversor de templates
Write-Host
$converter = Read-Host "Deseja converter este template para o formato padrão? (s/n)"
if ($converter.ToLower() -eq "s") {
    $outputTemplate = [System.IO.Path]::GetFileNameWithoutExtension($template) + "_convertido.docx"
    $outputPath = Join-Path (Split-Path $template -Parent) $outputTemplate
    
    $converterArguments = @(
        Join-Path $BASE_DIR "src\utils\template_converter.py",
        "`"$template`"",
        "`"$outputPath`""
    )
    
    Write-Host "Executando conversor de template..." -ForegroundColor Cyan
    Write-Host "Template original: $template" -ForegroundColor Cyan
    Write-Host "Template convertido: $outputPath" -ForegroundColor Cyan
    
    try {
        & $PYTHON_PATH $converterArguments
        
        if ($LASTEXITCODE -ne 0) {
            Write-Host "Erro na execução do conversor. Código de saída: $LASTEXITCODE" -ForegroundColor Red
        } else {
            Write-Host "Conversão concluída com sucesso." -ForegroundColor Green
            Write-Host "O template convertido está em: $outputPath" -ForegroundColor Green
        }
    } catch {
        Write-Host "ERRO: $($_.Exception.Message)" -ForegroundColor Red
    }
}

Write-Host
Write-Host "Pressione qualquer tecla para sair..."
$null = $Host.UI.RawUI.ReadKey("NoEcho,IncludeKeyDown") 