# Script de execução do sistema de peticionamento

# Define a codificação para UTF-8 para lidar com caracteres especiais
[Console]::OutputEncoding = [System.Text.Encoding]::UTF8

# Diretório base do projeto
$BASE_DIR = $PSScriptRoot

# Configuração de ambiente
$env:PYTHONIOENCODING = "utf-8"

# Diretórios padrão
$TEMPLATES_DIR = Join-Path $BASE_DIR "templates"
$DADOS_DIR = Join-Path $BASE_DIR "dados"
$OUTPUT_DIR = Join-Path $BASE_DIR "output"

# DIAGNÓSTICO: Listar os arquivos diretamente para verificar nomes
Write-Host "====== DIAGNÓSTICO DE ARQUIVOS ======" -ForegroundColor Magenta

# Listar arquivos de templates
Write-Host "Templates:" -ForegroundColor Magenta
Get-ChildItem -Path $TEMPLATES_DIR

# Listar arquivos de dados
Write-Host "Arquivos de dados:" -ForegroundColor Magenta
Get-ChildItem -Path $DADOS_DIR

Write-Host "===================================" -ForegroundColor Magenta

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

# Cria diretórios necessários
if (-not (Test-Path $OUTPUT_DIR)) {
    New-Item -ItemType Directory -Path $OUTPUT_DIR -Force | Out-Null
}

# Início da interação com o usuário
Clear-Host
Write-Host "===============================================" -ForegroundColor Cyan
Write-Host "  SISTEMA DE PETICIONAMENTO - MVP FASE 1" -ForegroundColor Cyan
Write-Host "===============================================" -ForegroundColor Cyan
Write-Host

# Verifica templates disponíveis
Write-Host "Verificando templates disponíveis..." -ForegroundColor Gray
$templatesObjetosDisponiveis = Get-ChildItem -Path $TEMPLATES_DIR -Filter "*.docx"
Write-Host "Encontrados $($templatesObjetosDisponiveis.Count) templates" -ForegroundColor Gray

if ($templatesObjetosDisponiveis.Count -eq 0) {
    Write-Host "ERRO: Nenhum template DOCX encontrado em $TEMPLATES_DIR" -ForegroundColor Red
    Write-Host "Por favor, adicione um template DOCX válido à pasta antes de executar."
    exit 1
}

# Verifica arquivos de dados disponíveis
Write-Host "Verificando arquivos de dados disponíveis..." -ForegroundColor Gray
$csvObjetosDisponiveis = Get-ChildItem -Path $DADOS_DIR -Filter "*.csv"
$jsonObjetosDisponiveis = Get-ChildItem -Path $DADOS_DIR -Filter "*.json"
Write-Host "Encontrados $($csvObjetosDisponiveis.Count) arquivos CSV e $($jsonObjetosDisponiveis.Count) arquivos JSON" -ForegroundColor Gray

if ($csvObjetosDisponiveis.Count -eq 0 -and $jsonObjetosDisponiveis.Count -eq 0) {
    Write-Host "ERRO: Nenhum arquivo de dados (CSV ou JSON) encontrado em $DADOS_DIR" -ForegroundColor Red
    Write-Host "Por favor, adicione um arquivo CSV ou JSON válido à pasta antes de executar."
    exit 1
}

# Seleção de Template
Write-Host "Templates disponíveis:" -ForegroundColor Green
for ($i = 0; $i -lt $templatesObjetosDisponiveis.Count; $i++) {
    # Exibe o nome completo do arquivo
    Write-Host "  $($i+1). $($templatesObjetosDisponiveis[$i].Name)" -ForegroundColor Green
}
Write-Host

$templateIndex = 0
if ($templatesObjetosDisponiveis.Count -gt 1) {
    do {
        $templateIndexInput = Read-Host "Selecione o template (1-$($templatesObjetosDisponiveis.Count)) [1]"
        if ([string]::IsNullOrWhiteSpace($templateIndexInput)) { $templateIndex = 0 }
        else { $templateIndex = [int]$templateIndexInput - 1 }
    } while ($templateIndex -lt 0 -or $templateIndex -ge $templatesObjetosDisponiveis.Count)
}

$templateSelecionado = $templatesObjetosDisponiveis[$templateIndex]
# Confirma que o nome do template não está truncado
Write-Host "VERIFICAÇÃO: Nome completo do template selecionado: '$($templateSelecionado.Name)'" -ForegroundColor Yellow
$templatePath = Join-Path $TEMPLATES_DIR $templateSelecionado.Name
Write-Host "Template selecionado: $($templateSelecionado.Name)" -ForegroundColor Yellow
Write-Host "Caminho completo: $templatePath" -ForegroundColor Yellow
Write-Host

# Conta caracteres para ajudar a diagnosticar truncamento
Write-Host "Detalhes do template:" -ForegroundColor Gray
Write-Host "- Nome: $templateSelecionado ($($templateSelecionado.Name.Length) caracteres)" -ForegroundColor Gray
Write-Host "- Caminho: $templatePath ($($templatePath.Length) caracteres)" -ForegroundColor Gray
Write-Host

# Seleção da fonte de dados
$usarCSV = $true
if ($csvObjetosDisponiveis.Count -gt 0 -and $jsonObjetosDisponiveis.Count -gt 0) {
    Write-Host "Fontes de dados disponíveis:" -ForegroundColor Green
    Write-Host "  1. CSV (recomendado)"
    Write-Host "  2. JSON"
    Write-Host
    
    do {
        $fonteDadosInput = Read-Host "Selecione a fonte de dados (1-2) [1]"
        if ([string]::IsNullOrWhiteSpace($fonteDadosInput) -or $fonteDadosInput -eq "1") { $usarCSV = $true }
        else { $usarCSV = $false }
    } while ($fonteDadosInput -ne "" -and $fonteDadosInput -ne "1" -and $fonteDadosInput -ne "2")
}
else {
    # Só tem uma opção disponível
    $usarCSV = ($csvObjetosDisponiveis.Count -gt 0)
}

# Seleção do arquivo de dados específico
if ($usarCSV) {
    Write-Host "Arquivos CSV disponíveis:" -ForegroundColor Green
    for ($i = 0; $i -lt $csvObjetosDisponiveis.Count; $i++) {
        Write-Host "  $($i+1). $($csvObjetosDisponiveis[$i].Name)"
    }
    Write-Host
    
    $csvIndex = 0
    if ($csvObjetosDisponiveis.Count -gt 1) {
        do {
            $csvIndexInput = Read-Host "Selecione o arquivo CSV (1-$($csvObjetosDisponiveis.Count)) [1]"
            if ([string]::IsNullOrWhiteSpace($csvIndexInput)) { $csvIndex = 0 }
            else { $csvIndex = [int]$csvIndexInput - 1 }
        } while ($csvIndex -lt 0 -or $csvIndex -ge $csvObjetosDisponiveis.Count)
    }
    
    $csvSelecionado = $csvObjetosDisponiveis[$csvIndex]
    # Confirma que o nome do CSV não está truncado
    Write-Host "VERIFICAÇÃO: Nome completo do CSV selecionado: '$($csvSelecionado.Name)'" -ForegroundColor Yellow
    $dadosPath = Join-Path $DADOS_DIR $csvSelecionado.Name
    Write-Host "Arquivo CSV selecionado: $($csvSelecionado.Name)" -ForegroundColor Yellow
    Write-Host "Caminho completo: $dadosPath" -ForegroundColor Yellow
    
    # Conta caracteres para ajudar a diagnosticar truncamento
    Write-Host "Detalhes do CSV:" -ForegroundColor Gray
    Write-Host "- Nome: $csvSelecionado ($($csvSelecionado.Name.Length) caracteres)" -ForegroundColor Gray
    Write-Host "- Caminho: $dadosPath ($($dadosPath.Length) caracteres)" -ForegroundColor Gray
}
else {
    Write-Host "Arquivos JSON disponíveis:" -ForegroundColor Green
    for ($i = 0; $i -lt $jsonObjetosDisponiveis.Count; $i++) {
        Write-Host "  $($i+1). $($jsonObjetosDisponiveis[$i].Name)"
    }
    Write-Host
    
    $jsonIndex = 0
    if ($jsonObjetosDisponiveis.Count -gt 1) {
        do {
            $jsonIndexInput = Read-Host "Selecione o arquivo JSON (1-$($jsonObjetosDisponiveis.Count)) [1]"
            if ([string]::IsNullOrWhiteSpace($jsonIndexInput)) { $jsonIndex = 0 }
            else { $jsonIndex = [int]$jsonIndexInput - 1 }
        } while ($jsonIndex -lt 0 -or $jsonIndex -ge $jsonObjetosDisponiveis.Count)
    }
    
    $jsonSelecionado = $jsonObjetosDisponiveis[$jsonIndex]
    # Confirma que o nome do JSON não está truncado
    Write-Host "VERIFICAÇÃO: Nome completo do JSON selecionado: '$($jsonSelecionado.Name)'" -ForegroundColor Yellow
    $dadosPath = Join-Path $DADOS_DIR $jsonSelecionado.Name
    Write-Host "Arquivo JSON selecionado: $($jsonSelecionado.Name)" -ForegroundColor Yellow
    Write-Host "Caminho completo: $dadosPath" -ForegroundColor Yellow
    
    # Conta caracteres para ajudar a diagnosticar truncamento
    Write-Host "Detalhes do JSON:" -ForegroundColor Gray
    Write-Host "- Nome: $jsonSelecionado ($($jsonSelecionado.Name.Length) caracteres)" -ForegroundColor Gray
    Write-Host "- Caminho: $dadosPath ($($dadosPath.Length) caracteres)" -ForegroundColor Gray
}

# Opções avançadas
Write-Host
Write-Host "Opções avançadas:" -ForegroundColor Green
$debug = (Read-Host "Ativar modo debug? (s/N)").ToLower() -eq "s"
$primeiroRegistroOnly = $false
if ($usarCSV) {
    $processarTodos = (Read-Host "Processar todos os registros do CSV? (S/n)").ToLower()
    $primeiroRegistroOnly = ($processarTodos -eq "n")
}
Write-Host

# Gera o nome do arquivo de saída
$nomeBase = [System.IO.Path]::GetFileNameWithoutExtension($templateSelecionado.Name)
$timestamp = Get-Date -Format "yyyyMMdd_HHmmss"
$nomeArquivoSaida = "${nomeBase}_${timestamp}.docx"
$outputPath = Join-Path $OUTPUT_DIR $nomeArquivoSaida

# Constrói o comando de execução
$pythonExecutable = "python"
$mainScriptPath = "main.py"  # Caminho relativo ao diretório base

# Verificar arquivos fisicamente para garantir que existam
Write-Host "Verificando físicamente a existência dos arquivos..." -ForegroundColor Gray
$template_file_path = Join-Path $TEMPLATES_DIR $templateSelecionado.Name
$data_file_path = Join-Path $DADOS_DIR $(if ($usarCSV) { $csvSelecionado.Name } else { $jsonSelecionado.Name })

if (-not (Test-Path $template_file_path)) {
    Write-Host "ERRO CRÍTICO: Arquivo de template não encontrado em: $template_file_path" -ForegroundColor Red
    exit 1
}

if (-not (Test-Path $data_file_path)) {
    Write-Host "ERRO CRÍTICO: Arquivo de dados não encontrado em: $data_file_path" -ForegroundColor Red
    exit 1
}

Write-Host "✓ Arquivo de template encontrado: $template_file_path" -ForegroundColor Green
Write-Host "✓ Arquivo de dados encontrado: $data_file_path" -ForegroundColor Green

# Montar a lista de argumentos usando array PowerShell com caminhos relativos completos
$argumentos = @($mainScriptPath)

# Usar caminhos relativos com nomes completos de arquivos
$template_relative = Join-Path "templates" $templateSelecionado.Name
$argumentos += "--template", $template_relative

if ($usarCSV) {
    $data_relative = Join-Path "dados" $csvSelecionado.Name
    $argumentos += "--csv", $data_relative
} else {
    $data_relative = Join-Path "dados" $jsonSelecionado.Name
    $argumentos += "--dados", $data_relative
}

# Usar caminho relativo para saída
$outputRelativePath = Join-Path "output" $nomeArquivoSaida
$argumentos += "--saida", $outputRelativePath

if ($debug) {
    $argumentos += "--debug"
}

if ($primeiroRegistroOnly) {
    $argumentos += "--primeiro-registro"
}

# Executa o comando
Write-Host "Executando sistema de peticionamento..." -ForegroundColor Cyan
Write-Host "Executável: $pythonExecutable" -ForegroundColor Gray

# Exibir todos os argumentos individualmente para verificar truncamento
Write-Host "Lista de argumentos:" -ForegroundColor Gray
for ($i = 0; $i -lt $argumentos.Count; $i++) {
    $arg = $argumentos[$i]
    $comprimento = $arg.Length
    Write-Host "  [$i] '$arg' ($comprimento caracteres)" -ForegroundColor Gray
}
Write-Host "Comando completo: $pythonExecutable $($argumentos -join ' ')" -ForegroundColor Gray
Write-Host

# Garantir que o diretório de trabalho atual seja o diretório base
Set-Location $BASE_DIR

try {
    & $pythonExecutable $argumentos
    
    if ($LASTEXITCODE -ne 0) {
        Write-Host
        Write-Host "Erro na execução do script Python. Código de saída: $LASTEXITCODE" -ForegroundColor Red
        Write-Host "Verifique os logs em logs\peticionamento.log para mais detalhes." -ForegroundColor Yellow
    } else {
        Write-Host
        Write-Host "Processamento concluído com sucesso!" -ForegroundColor Green
    }
} catch {
    Write-Host
    Write-Host "ERRO CRÍTICO AO TENTAR EXECUTAR O COMANDO PYTHON:" -ForegroundColor Red
    Write-Host $_.Exception.Message -ForegroundColor Red
}

Write-Host
Write-Host "Pressione qualquer tecla para sair..."
$null = $Host.UI.RawUI.ReadKey("NoEcho,IncludeKeyDown")

# Diagnóstico adicional para verificar o problema de truncamento
Write-Host "Testando funções de seleção de nome:" -ForegroundColor Magenta
Write-Host "Comando: Get-ChildItem -Path $TEMPLATES_DIR -Filter *.docx | Select-Object -ExpandProperty Name" -ForegroundColor Gray

$nomes_templates = Get-ChildItem -Path $TEMPLATES_DIR -Filter "*.docx" | Select-Object -ExpandProperty Name
Write-Host "Resultado: $nomes_templates" -ForegroundColor Magenta
Write-Host "Tipo: $($nomes_templates.GetType().FullName)" -ForegroundColor Magenta
Write-Host "Comprimento: $($nomes_templates.Length)" -ForegroundColor Magenta

# Vamos testar uma alternativa
Write-Host "Testando método alternativo:" -ForegroundColor Magenta
$arquivos_template = Get-ChildItem -Path $TEMPLATES_DIR -Filter "*.docx" 
foreach ($arquivo in $arquivos_template) {
    Write-Host "Nome do arquivo: '$($arquivo.Name)'" -ForegroundColor Yellow
}
Write-Host "===================================" -ForegroundColor Magenta
