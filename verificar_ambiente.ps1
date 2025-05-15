# Script para verificação do ambiente
# Verifica dependências, configurações e prepara o ambiente

# Configurações
$SCRIPT_DIR = $PSScriptRoot
$BASE_DIR = $SCRIPT_DIR
$PYTHON_PATH = "python"

# Cores para saída
$COR_INFO = "Cyan"
$COR_ERRO = "Red"
$COR_AVISO = "Yellow"
$COR_SUCESSO = "Green"

# Função para verificar dependências
function Verificar-Dependencias {
    Write-Host "Verificando dependências do projeto..." -ForegroundColor $COR_INFO
    
    # Verifica versão do Python
    try {
        $versaoPython = & $PYTHON_PATH --version
        Write-Host "  ✓ $versaoPython detectado" -ForegroundColor $COR_SUCESSO
    } catch {
        Write-Host "  ✗ Python não encontrado. Instale Python 3.8 ou superior." -ForegroundColor $COR_ERRO
        return $false
    }
    
    # Verifica instalação do pip
    try {
        & $PYTHON_PATH -m pip --version | Out-Null
        Write-Host "  ✓ pip instalado" -ForegroundColor $COR_SUCESSO
    } catch {
        Write-Host "  ✗ pip não encontrado. Verifique a instalação do Python." -ForegroundColor $COR_ERRO
        return $false
    }
    
    # Verifica ambiente virtual
    $venv_ativado = $false
    if ($env:VIRTUAL_ENV) {
        $venv_ativado = $true
        Write-Host "  ✓ Ambiente virtual ativado: $env:VIRTUAL_ENV" -ForegroundColor $COR_SUCESSO
    } else {
        Write-Host "  ✗ Ambiente virtual não ativado" -ForegroundColor $COR_AVISO
        
        # Verifica se existe pasta do ambiente virtual
        $venvDir = Join-Path $BASE_DIR "venv"
        if (Test-Path $venvDir) {
            Write-Host "    Ambiente virtual encontrado em: $venvDir" -ForegroundColor $COR_INFO
            
            # Tenta ativar
            $activateScript = Join-Path $venvDir "Scripts\Activate.ps1"
            if (Test-Path $activateScript) {
                $ativar = Read-Host "    Deseja ativar o ambiente virtual? (s/n)"
                if ($ativar.ToLower() -eq "s") {
                    try {
                        . $activateScript
                        Write-Host "    ✓ Ambiente virtual ativado" -ForegroundColor $COR_SUCESSO
                        $venv_ativado = $true
                    } catch {
                        Write-Host "    ✗ Erro ao ativar ambiente virtual: $($_.Exception.Message)" -ForegroundColor $COR_ERRO
                    }
                }
            }
        } else {
            Write-Host "    Ambiente virtual não encontrado em: $venvDir" -ForegroundColor $COR_INFO
            $criar = Read-Host "    Deseja criar um novo ambiente virtual? (s/n)"
            if ($criar.ToLower() -eq "s") {
                try {
                    & $PYTHON_PATH -m venv $venvDir
                    Write-Host "    ✓ Ambiente virtual criado em: $venvDir" -ForegroundColor $COR_SUCESSO
                    
                    # Tenta ativar o ambiente recém-criado
                    $activateScript = Join-Path $venvDir "Scripts\Activate.ps1"
                    if (Test-Path $activateScript) {
                        . $activateScript
                        Write-Host "    ✓ Ambiente virtual ativado" -ForegroundColor $COR_SUCESSO
                        $venv_ativado = $true
                    }
                } catch {
                    Write-Host "    ✗ Erro ao criar ambiente virtual: $($_.Exception.Message)" -ForegroundColor $COR_ERRO
                }
            }
        }
    }
    
    # Verifica dependências do requirements.txt
    $requirementsFile = Join-Path $BASE_DIR "requirements.txt"
    if (Test-Path $requirementsFile) {
        Write-Host "Verificando pacotes Python instalados..." -ForegroundColor $COR_INFO
        
        # Obtém lista de pacotes instalados
        $pacotesInstalados = & $PYTHON_PATH -m pip freeze
        
        # Lê requirements.txt
        $requirements = Get-Content $requirementsFile
        $pacotesFaltando = @()
        
        foreach ($req in $requirements) {
            if ($req -match "^\s*$" -or $req -match "^\s*#") {
                continue  # Ignora linhas vazias e comentários
            }
            
            # Extrai o nome do pacote (sem versão)
            if ($req -match "^([^=<>~!]+)") {
                $nomePacote = $Matches[1].Trim()
                
                # Verifica se o pacote está instalado
                $instalado = $false
                foreach ($pacote in $pacotesInstalados) {
                    if ($pacote -match "^$nomePacote==") {
                        $instalado = $true
                        break
                    }
                }
                
                if (-not $instalado) {
                    $pacotesFaltando += $req
                    Write-Host "  ✗ Pacote '$req' não instalado" -ForegroundColor $COR_AVISO
                } else {
                    Write-Host "  ✓ Pacote '$nomePacote' instalado" -ForegroundColor $COR_SUCESSO
                }
            }
        }
        
        # Se faltar pacotes, oferece para instalar
        if ($pacotesFaltando.Count -gt 0) {
            Write-Host "Faltam $($pacotesFaltando.Count) pacotes para instalar" -ForegroundColor $COR_INFO
            
            $instalar = Read-Host "Deseja instalar os pacotes faltantes? (s/n)"
            if ($instalar.ToLower() -eq "s") {
                try {
                    & $PYTHON_PATH -m pip install -r $requirementsFile
                    Write-Host "✓ Todos os pacotes foram instalados" -ForegroundColor $COR_SUCESSO
                } catch {
                    Write-Host "✗ Erro ao instalar pacotes: $($_.Exception.Message)" -ForegroundColor $COR_ERRO
                }
            }
        } else {
            Write-Host "✓ Todas as dependências estão instaladas" -ForegroundColor $COR_SUCESSO
        }
    } else {
        Write-Host "✗ Arquivo requirements.txt não encontrado em: $requirementsFile" -ForegroundColor $COR_ERRO
    }
    
    # Verifica estrutura de diretórios
    Write-Host "Verificando estrutura de diretórios..." -ForegroundColor $COR_INFO
    $diretoriosObrigatorios = @(
        (Join-Path $BASE_DIR "src"),
        (Join-Path $BASE_DIR "templates"),
        (Join-Path $BASE_DIR "dados"),
        (Join-Path $BASE_DIR "output"),
        (Join-Path $BASE_DIR "logs")
    )
    
    foreach ($dir in $diretoriosObrigatorios) {
        if (Test-Path $dir) {
            Write-Host "  ✓ Diretório $dir existe" -ForegroundColor $COR_SUCESSO
        } else {
            Write-Host "  ✗ Diretório $dir não existe" -ForegroundColor $COR_ERRO
            
            # Tenta criar o diretório
            try {
                New-Item -ItemType Directory -Path $dir -Force | Out-Null
                Write-Host "    ✓ Diretório $dir criado" -ForegroundColor $COR_SUCESSO
            } catch {
                Write-Host "    ✗ Erro ao criar diretório $dir: $($_.Exception.Message)" -ForegroundColor $COR_ERRO
            }
        }
    }
    
    return $true
}

# Função para verificar arquivos essenciais
function Verificar-Arquivos-Essenciais {
    Write-Host "Verificando arquivos essenciais..." -ForegroundColor $COR_INFO
    
    $arquivos_obrigatorios = @(
        (Join-Path $BASE_DIR "src\motor_regras.py"),
        (Join-Path $BASE_DIR "src\documento_processor.py"),
        (Join-Path $BASE_DIR "src\avaliador_condicoes.py"),
        (Join-Path $BASE_DIR "main.py"),
        (Join-Path $BASE_DIR "data\condicionais.json")
    )
    
    $todos_encontrados = $true
    
    foreach ($arquivo in $arquivos_obrigatorios) {
        if (Test-Path $arquivo) {
            Write-Host "  ✓ Arquivo $arquivo existe" -ForegroundColor $COR_SUCESSO
        } else {
            Write-Host "  ✗ Arquivo $arquivo não encontrado" -ForegroundColor $COR_ERRO
            $todos_encontrados = $false
        }
    }
    
    # Verifica se há pelo menos um template
    $templatesDir = Join-Path $BASE_DIR "templates"
    $templates = Get-ChildItem -Path $templatesDir -Filter "*.docx" -ErrorAction SilentlyContinue
    
    if ($templates.Count -gt 0) {
        Write-Host "  ✓ $($templates.Count) templates DOCX encontrados" -ForegroundColor $COR_SUCESSO
        
        # Lista os templates
        foreach ($template in $templates) {
            Write-Host "    - $($template.Name)" -ForegroundColor $COR_INFO
        }
    } else {
        Write-Host "  ✗ Nenhum template DOCX encontrado na pasta templates" -ForegroundColor $COR_ERRO
        $todos_encontrados = $false
    }
    
    # Verifica se há dados de exemplo
    $dadosDir = Join-Path $BASE_DIR "dados"
    $dadosCSV = Get-ChildItem -Path $dadosDir -Filter "*.csv" -ErrorAction SilentlyContinue
    $dadosJSON = Get-ChildItem -Path $dadosDir -Filter "*.json" -ErrorAction SilentlyContinue
    
    if ($dadosCSV.Count -gt 0 -or $dadosJSON.Count -gt 0) {
        Write-Host "  ✓ $($dadosCSV.Count + $dadosJSON.Count) arquivos de dados encontrados" -ForegroundColor $COR_SUCESSO
        
        # Lista os arquivos de dados
        foreach ($csv in $dadosCSV) {
            Write-Host "    - $($csv.Name) (CSV)" -ForegroundColor $COR_INFO
        }
        foreach ($json in $dadosJSON) {
            Write-Host "    - $($json.Name) (JSON)" -ForegroundColor $COR_INFO
        }
    } else {
        Write-Host "  ✗ Nenhum arquivo de dados (CSV/JSON) encontrado na pasta dados" -ForegroundColor $COR_ERRO
        $todos_encontrados = $false
    }
    
    return $todos_encontrados
}

# Função para executar verificações de qualidade de código (opcional)
function Verificar-Qualidade-Codigo {
    Write-Host "Verificando qualidade do código (opcional)..." -ForegroundColor $COR_INFO
    
    # Verifica se pylint está instalado
    try {
        & $PYTHON_PATH -m pylint --version | Out-Null
        $pylint_instalado = $true
        Write-Host "  ✓ pylint instalado" -ForegroundColor $COR_SUCESSO
    } catch {
        $pylint_instalado = $false
        Write-Host "  ✗ pylint não instalado" -ForegroundColor $COR_AVISO
    }
    
    # Verifica se flake8 está instalado
    try {
        & $PYTHON_PATH -m flake8 --version | Out-Null
        $flake8_instalado = $true
        Write-Host "  ✓ flake8 instalado" -ForegroundColor $COR_SUCESSO
    } catch {
        $flake8_instalado = $false
        Write-Host "  ✗ flake8 não instalado" -ForegroundColor $COR_AVISO
    }
    
    # Verifica se black está instalado
    try {
        & $PYTHON_PATH -m black --version | Out-Null
        $black_instalado = $true
        Write-Host "  ✓ black instalado" -ForegroundColor $COR_SUCESSO
    } catch {
        $black_instalado = $false
        Write-Host "  ✗ black não instalado" -ForegroundColor $COR_AVISO
    }
    
    $src_dir = Join-Path $BASE_DIR "src"
    
    # Deseja instalar ferramentas de linting/formatting?
    $instalar_ferramentas = Read-Host "Deseja instalar ferramentas de qualidade de código? (pylint, flake8, black) (s/n)"
    if ($instalar_ferramentas.ToLower() -eq "s") {
        try {
            & $PYTHON_PATH -m pip install pylint flake8 black
            Write-Host "  ✓ Ferramentas instaladas com sucesso" -ForegroundColor $COR_SUCESSO
            $pylint_instalado = $true
            $flake8_instalado = $true
            $black_instalado = $true
        } catch {
            Write-Host "  ✗ Erro ao instalar ferramentas: $($_.Exception.Message)" -ForegroundColor $COR_ERRO
        }
    }
    
    # Executar verificações se as ferramentas estiverem instaladas
    if ($pylint_instalado -or $flake8_instalado -or $black_instalado) {
        $executar_verificacoes = Read-Host "Deseja executar verificações de qualidade de código agora? (s/n)"
        if ($executar_verificacoes.ToLower() -eq "s") {
            if ($pylint_instalado) {
                Write-Host "Executando pylint..." -ForegroundColor $COR_INFO
                & $PYTHON_PATH -m pylint $src_dir
            }
            
            if ($flake8_instalado) {
                Write-Host "Executando flake8..." -ForegroundColor $COR_INFO
                & $PYTHON_PATH -m flake8 $src_dir
            }
            
            if ($black_instalado) {
                $formatar_codigo = Read-Host "Deseja formatar o código com black? (s/n)"
                if ($formatar_codigo.ToLower() -eq "s") {
                    Write-Host "Formatando código com black..." -ForegroundColor $COR_INFO
                    & $PYTHON_PATH -m black $src_dir
                }
            }
        }
    }
}

# Função principal
function Executar-Verificacao {
    Write-Host "=========================================" -ForegroundColor $COR_INFO
    Write-Host " Verificação de Ambiente - MVP Fase 1 " -ForegroundColor $COR_INFO
    Write-Host "=========================================" -ForegroundColor $COR_INFO
    Write-Host
    
    # Executa verificações
    $dependencias_ok = Verificar-Dependencias
    Write-Host
    
    $arquivos_ok = Verificar-Arquivos-Essenciais
    Write-Host
    
    # Ferramentas opcionais de qualidade de código
    $verificar_qualidade = Read-Host "Deseja verificar qualidade do código e instalar ferramentas opcionais? (s/n)"
    if ($verificar_qualidade.ToLower() -eq "s") {
        Verificar-Qualidade-Codigo
        Write-Host
    }
    
    # Resumo
    Write-Host "=== Resumo da Verificação ===" -ForegroundColor $COR_INFO
    if ($dependencias_ok) {
        Write-Host "✓ Dependências: OK" -ForegroundColor $COR_SUCESSO
    } else {
        Write-Host "✗ Dependências: Problemas encontrados" -ForegroundColor $COR_ERRO
    }
    
    if ($arquivos_ok) {
        Write-Host "✓ Arquivos essenciais: OK" -ForegroundColor $COR_SUCESSO
    } else {
        Write-Host "✗ Arquivos essenciais: Faltando arquivos" -ForegroundColor $COR_ERRO
    }
    
    # Sugestão para próximos passos
    if ($dependencias_ok -and $arquivos_ok) {
        Write-Host
        Write-Host "✓ Ambiente verificado com sucesso!" -ForegroundColor $COR_SUCESSO
        Write-Host "Você pode executar o sistema com:" -ForegroundColor $COR_INFO
        Write-Host "  ./executar_sistema.ps1" -ForegroundColor $COR_INFO
        Write-Host
        Write-Host "Ou diagnosticar um template com:" -ForegroundColor $COR_INFO
        Write-Host "  ./diagnosticar_template.ps1" -ForegroundColor $COR_INFO
    } else {
        Write-Host
        Write-Host "✗ O ambiente possui problemas que precisam ser corrigidos." -ForegroundColor $COR_ERRO
        Write-Host "Por favor, resolva os problemas indicados acima antes de executar o sistema." -ForegroundColor $COR_ERRO
    }
}

# Executa a função principal
Executar-Verificacao

# Aguarda pressionar uma tecla para sair
Write-Host
Write-Host "Pressione qualquer tecla para sair..."
$null = $Host.UI.RawUI.ReadKey("NoEcho,IncludeKeyDown") 