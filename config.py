"""
Configurações do sistema.
"""
import os
from pathlib import Path

# Caminho da pasta base do projeto
BASE_DIR = os.path.dirname(os.path.abspath(__file__))

# Arquivo de dados JSON (entrada da entrevista)
DADOS_JSON = os.path.join(BASE_DIR, "dados", "caso_teste_1.json")

# Arquivo de template Word
TEMPLATE_DOCX = os.path.join(BASE_DIR, "templates", "modelo_trabalhista.docx")

# Pasta de saída para documentos gerados
OUTPUT_DIR = os.path.join(BASE_DIR, "output")

# Arquivos do modelo relacional (campos_definicao refatorado)
CAMPOS_DEFINICAO_DIR = os.path.join(BASE_DIR, "data", "campos_definicao")
CAMPOS_CSV = os.path.join(CAMPOS_DEFINICAO_DIR, "campos_definicao.csv")
CATEGORIAS_CAMPOS_CSV = os.path.join(CAMPOS_DEFINICAO_DIR, "categorias_campos.csv")
REGRAS_ATIVACAO_CSV = os.path.join(CAMPOS_DEFINICAO_DIR, "regras_ativacao.csv")
TIPOS_DADOS_CSV = os.path.join(CAMPOS_DEFINICAO_DIR, "tipos_dados.csv")
OPCOES_SELECAO_CSV = os.path.join(CAMPOS_DEFINICAO_DIR, "opcoes_selecao.csv")

# Arquivo JSON de regras condicionais
REGRAS_JSON = os.path.join(BASE_DIR, "data", "condicionais.json")

# Arquivo JSON de mapping de campos de definição (legado, para compatibilidade)
MAPPING_CAMPOS_JSON = os.path.join(CAMPOS_DEFINICAO_DIR, "mapping_campos_definicao.json")

# Categorias para o MVP (usadas pelo motor de regras)
CATEGORIAS_MVP = [
    "ESTRUTURA_SEMPRE_ATIVA",
    "ESTRUTURA_CONDICIONAL_SIMPLES"
]

# Configuração de log
LOG_DIR = os.path.join(BASE_DIR, "logs")
LOG_LEVEL = "INFO"  # DEBUG, INFO, WARNING, ERROR, CRITICAL
LOG_FILE = os.path.join(LOG_DIR, "peticionamento.log")  # Arquivo de log

# Modo estrito para validação de campos (se True, valida todos os campos mesmo que não usados)
MODO_ESTRITO = False  # Default: False

# Separador para arquivos CSV
CSV_SEPARATOR = ";"

# Para uso com o processador CSV (legado)
ENTREVISTAS_CSV = os.path.join(BASE_DIR, "dados", "dados.csv")
DEFINICAO_CAMPOS_CSV = CAMPOS_CSV

# Criar diretórios necessários se não existirem
os.makedirs(OUTPUT_DIR, exist_ok=True)
os.makedirs(LOG_DIR, exist_ok=True)
os.makedirs(os.path.join(BASE_DIR, "data"), exist_ok=True)
os.makedirs(os.path.join(BASE_DIR, "templates"), exist_ok=True)
os.makedirs(os.path.join(BASE_DIR, "dados"), exist_ok=True)
os.makedirs(CAMPOS_DEFINICAO_DIR, exist_ok=True) 