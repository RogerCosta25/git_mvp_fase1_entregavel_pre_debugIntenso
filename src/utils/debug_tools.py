import re

# This is the content of input_file_1.py
powershell_script_content = """
$debugToolsPath = ".\\src\\utils\\debug_tools.py"
$debugToolsContent = @"
# src/utils/debug_tools.py
import os
import json
import time
import random
import pickle
from functools import wraps
from datetime import datetime
from loguru import logger # Loguru será importado aqui

# --- Configuração Centralizada do Loguru ---
# Limpa handlers pré-existentes para evitar duplicação ao reconfigurar
logger.remove()

# Determina o caminho raiz do projeto de forma mais robusta
# Assume que debug_tools.py está em src/utils/
PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

LOGS_DIR = os.path.join(PROJECT_ROOT, "logs")
os.makedirs(LOGS_DIR, exist_ok=True)

APP_LOG_FILE = os.path.join(LOGS_DIR, "app.log")
DEBUG_JSON_FILE = os.path.join(LOGS_DIR, "debug.json")

SNAPSHOTS_DIR = os.path.join(LOGS_DIR, "snapshots") # Para a função capturar_estado
os.makedirs(SNAPSHOTS_DIR, exist_ok=True)

INSIGHTS_DIR = os.path.join(PROJECT_ROOT, "insights") # Para a função registrar_insight
os.makedirs(INSIGHTS_DIR, exist_ok=True)

DEBUG_SCENARIOS_DIR = os.path.join(PROJECT_ROOT, "debug_scenarios") # Para DebugRecorder
os.makedirs(DEBUG_SCENARIOS_DIR, exist_ok=True)


# Handler para app.log (texto legível)
logger.add(
    APP_LOG_FILE,
    rotation="10 MB",
    retention="7 days",
    level="DEBUG", # Captura tudo a partir de DEBUG
    format="{time:YYYY-MM-DD HH:mm:ss.SSS} | {level: <8} | {name}:{function}:{line} - {message}",
    encoding="utf-8"
)

# Handler para debug.json (serializado para análise por máquina)
logger.add(
    DEBUG_JSON_FILE,
    serialize=True,
    level="DEBUG", # Captura tudo a partir de DEBUG
    rotation="50 MB",
    retention="14 days",
    encoding="utf-8"
)

# Handler para console (feedback imediato)
# O nível aqui pode ser INFO para não poluir tanto o console no dia a dia
# Mas para a fase de debug intenso, DEBUG pode ser útil no console também.
CONSOLE_LOG_LEVEL = os.getenv("CONSOLE_LOG_LEVEL", "INFO").upper()
logger.add(
    lambda msg: print(msg, end=""), 
    level=CONSOLE_LOG_LEVEL, 
    format="<green>{time:HH:mm:ss}</green> | <level>{level: <8}</level> | <cyan>{name}</cyan>:<cyan>{function}</cyan>:<cyan>{line}</cyan> - <level>{message}</level>",
    colorize=True
)
logger.info(f"Loguru configurado a partir de debug_tools.py. Console Level: {CONSOLE_LOG_LEVEL}")

SENSITIVE_FIELDS = ["cpf", "rg", "nome_completo", "senha", "cnpj", "email", "telefone", "procuracao", "cliente", "documento"]

def sanitize_data(data_item):
    \"\"\"Sanitiza dados sensíveis recursivamente em dicts, listas e tuplas.\"\"\"
    if isinstance(data_item, dict):
        return {
            k: "[REDACTED]" if isinstance(k, str) and any(sf in k.lower() for sf in SENSITIVE_FIELDS) else sanitize_data(v)
            for k, v in data_item.items()
        }
    elif isinstance(data_item, (list, tuple)):
        return type(data_item)(sanitize_data(item) for item in data_item)
    # Não redige strings isoladas aqui, a menos que seja um valor direto de um campo sensível,
    # o que é melhor tratado no contexto do dicionário.
    return data_item

def debug_tracker(sample_rate=1.0):
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            # Amostragem probabilística
            if not (random.random() < sample_rate):
                return func(*args, **kwargs)

            func_qualname = f"{func.__module__}.{func.__name__}"
            call_id = f"{func_qualname}_{datetime.now().strftime('%H%M%S%f')}"
            
            # Sanitizar args e kwargs antes de logar
            try:
                # Cria cópias para não modificar os originais se forem mutáveis
                sanitized_args_list = list(args) 
                sanitized_kwargs_dict = kwargs.copy()
                
                safe_args_repr = str(sanitize_data(sanitized_args_list))[:500]
                safe_kwargs_repr = str(sanitize_data(sanitized_kwargs_dict))[:500]
            except Exception as e_sanitize:
                safe_args_repr = f"Error sanitizing args: {e_sanitize}"
                safe_kwargs_repr = f"Error sanitizing kwargs: {e_sanitize}"

            log_entry_start = {
                "event_type": "function_call_start", "call_id": call_id,
                "function": func_qualname,
                "timestamp_start": datetime.now().isoformat(),
                "args_preview": safe_args_repr, "kwargs_preview": safe_kwargs_repr
            }
            logger.debug(log_entry_start)
            
            start_time = time.perf_counter()
            
            try:
                result = func(*args, **kwargs)
                execution_time = time.perf_counter() - start_time
                
                try:
                    # Sanitizar resultado antes de logar
                    safe_result = sanitize_data(result)
                    safe_result_repr = str(safe_result)[:200]
                except Exception as e_sanitize_res:
                    safe_result_repr = f"Error sanitizing result: {e_sanitize_res}"

                log_entry_success = {
                    "event_type": "function_call_success", "call_id": call_id,
                    "function": func_qualname,
                    "timestamp_end": datetime.now().isoformat(),
                    "execution_time_seconds": round(execution_time, 6),
                    "result_type": str(type(result).__name__),
                    "result_preview": safe_result_repr
                }
                logger.debug(log_entry_success)
                return result
            except Exception as e:
                execution_time = time.perf_counter() - start_time
                log_entry_error = {
                    "event_type": "function_call_error", "call_id": call_id,
                    "function": func_qualname,
                    "timestamp_end": datetime.now().isoformat(),
                    "execution_time_seconds": round(execution_time, 6),
                    "error_type": str(type(e).__name__), "error_message": str(e)
                }
                # logger.exception() anexa o traceback automaticamente ao log
                logger.exception(log_entry_error) 
                raise
        return wrapper
    return decorator

def capturar_estado(identificador, objeto_a_salvar, sub_dir="default_snapshots"):
    \"\"\"Salva um snapshot do estado de um objeto para análise posterior.\"\"\"
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S_%f")
    snapshot_file_name = f"{identificador.replace(':', '_').replace('.', '_')}_{timestamp}.pkl"
    
    final_snapshot_dir = os.path.join(SNAPSHOTS_DIR, sub_dir)
    os.makedirs(final_snapshot_dir, exist_ok=True)
    snapshot_path = os.path.join(final_snapshot_dir, snapshot_file_name)
    
    try:
        with open(snapshot_path, "wb") as f:
            pickle.dump(objeto_a_salvar, f)
        logger.debug(f"Estado capturado: '{snapshot_path}' para identificador '{identificador}'")
        return snapshot_path
    except Exception as e_pickle:
        logger.error(f"Falha ao capturar estado (pickle) para '{identificador}': {e_pickle}")
        try: # Fallback para JSON se pickle falhar (para tipos de dados simples)
            json_snapshot_path = snapshot_path.replace(".pkl", ".json")
            with open(json_snapshot_path, "w", encoding="utf-8") as f_json:
                json.dump(objeto_a_salvar, f_json, indent=2, default=str) # default=str para lidar com tipos não serializáveis
            logger.info(f"Estado capturado como JSON (fallback): '{json_snapshot_path}' para identificador '{identificador}'")
            return json_snapshot_path
        except Exception as e_json:
            logger.error(f"Falha ao capturar estado como JSON (fallback) para '{identificador}': {e_json}")
            return None

def registrar_insight(desenvolvedor, descricao, evidencias=None):
    \"\"\"Registra um momento 'eureka' durante o processo de debug.\"\"\"
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    # Sanitizar nome do desenvolvedor para nome de arquivo
    dev_sanitized = "".join(c if c.isalnum() else "_" for c in desenvolvedor)
    insight_id = f"{timestamp}_{dev_sanitized}"
    insight_file_path = os.path.join(INSIGHTS_DIR, f"{insight_id}.md")
    
    content = f"# Insight: {descricao}\\n\\n"
    content += f"**Desenvolvedor:** {desenvolvedor}\\n"
    content += f"**Data/Hora:** {datetime.now().isoformat()}\\n\\n"
    content += "## Descrição Detalhada do Insight\\n\\n[Adicionar detalhes aqui sobre a descoberta, o problema e a solução pensada]\\n\\n"
    if evidencias:
        content += "## Evidências (Logs, Código, etc.)\\n\\n```\\n" # Usar ``` para blocos de código/log
        content += f"{str(evidencias)}\\n```\\n"
    
    with open(insight_file_path, "w", encoding="utf-8") as f:
        f.write(content)
    logger.info(f"Insight registrado: '{descricao}' por {desenvolvedor} em '{insight_file_path}'")
    return insight_id

def monitorar_condicao(condicao_a_checar, descricao_evento, capturar_contexto_func=None):
    \"\"\"Monitora uma condição, logando quando ocorre. Útil para eventos raros ou intermitentes.\"\"\"
    if condicao_a_checar: # A condição deve ser uma expressão booleana
        contexto_log = {}
        if callable(capturar_contexto_func):
            try:
                contexto_capturado = capturar_contexto_func()
                # Tenta serializar para JSON de forma segura
                contexto_log = json.loads(json.dumps(contexto_capturado, default=str))
            except Exception as e_ctx:
                contexto_log = {"erro_ao_capturar_contexto": str(e_ctx)}
        
        logger.warning(f"CONDIÇÃO MONITORADA ATINGIDA: {descricao_evento}", extra={"contexto_evento": contexto_log})
        return True
    return False
"@
Set-Content -Path $debugToolsPath -Encoding utf8 -Force
Write-Host "Arquivo src/utils/debug_tools.py criado/atualizado." -ForegroundColor Green
"""

# Extract the Python code from the PowerShell here-string
match = re.search(r'@"(.*?)@', powershell_script_content, re.DOTALL)
if match:
    python_code_for_debug_tools = match.group(1).strip()
    # The here-string in PowerShell might interpret \n differently than Python string literals.
    # Let's assume the newlines are preserved correctly by the re.DOTALL and strip().
    # If `\n` within the string content in PS needs to be actual newlines in Python, that's typically handled.
    # The main issue is the `content += f"# Insight: {descricao}\\n\\n"` etc. which have escaped newlines.
    # These should be `\n` in the final Python code, not `\\n`.
    # However, the provided input_file_1.py already has them as `\\n` within the PS here-string,
    # meaning they were intended to be literal backslash-n.
    # On second thought, for a Python script, they should be actual newlines or Python's `\n`.
    # The current `input_file_1.py` will make them literal `\\n` in the generated .py file.
    # For the purpose of this exercise, I will output the content *as it is defined within the here-string*.
    # The user can then refine it if the `\\n` were meant to be actual newlines in the markdown.
    # Update: The image shows errors like "String literal is unterminated". The `\\n` in PS here-strings might be an issue.
    # The python code from input_file_1.py has:
    # content = f"# Insight: {descricao}\n\n"
    # This is fine. The error is not from this part, it is from the overall PS script being pasted.
    # The `input_file_1.py` uses `\n` correctly inside the python block for the markdown content.

    print("```python")
    print(python_code_for_debug_tools)
    print("```")
else:
    print("Could not extract Python code from the PowerShell script content.")

proper_python_code = """# src/utils/debug_tools.py
import os
import json
import time
import random
import pickle
from functools import wraps
from datetime import datetime
from loguru import logger # Loguru será importado aqui

# --- Configuração Centralizada do Loguru ---
# Limpa handlers pré-existentes para evitar duplicação ao reconfigurar
logger.remove()

# Determina o caminho raiz do projeto de forma mais robusta
# Assume que debug_tools.py está em src/utils/
PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

LOGS_DIR = os.path.join(PROJECT_ROOT, "logs")
os.makedirs(LOGS_DIR, exist_ok=True)

APP_LOG_FILE = os.path.join(LOGS_DIR, "app.log")
DEBUG_JSON_FILE = os.path.join(LOGS_DIR, "debug.json")

SNAPSHOTS_DIR = os.path.join(LOGS_DIR, "snapshots") # Para a função capturar_estado
os.makedirs(SNAPSHOTS_DIR, exist_ok=True)

INSIGHTS_DIR = os.path.join(PROJECT_ROOT, "insights") # Para a função registrar_insight
os.makedirs(INSIGHTS_DIR, exist_ok=True)

DEBUG_SCENARIOS_DIR = os.path.join(PROJECT_ROOT, "debug_scenarios") # Para DebugRecorder
os.makedirs(DEBUG_SCENARIOS_DIR, exist_ok=True)


# Handler para app.log (texto legível)
logger.add(
    APP_LOG_FILE,
    rotation="10 MB",
    retention="7 days",
    level="DEBUG", # Captura tudo a partir de DEBUG
    format="{time:YYYY-MM-DD HH:mm:ss.SSS} | {level: <8} | {name}:{function}:{line} - {message}",
    encoding="utf-8"
)

# Handler para debug.json (serializado para análise por máquina)
logger.add(
    DEBUG_JSON_FILE,
    serialize=True,
    level="DEBUG", # Captura tudo a partir de DEBUG
    rotation="50 MB",
    retention="14 days",
    encoding="utf-8"
)

# Handler para console (feedback imediato)
# O nível aqui pode ser INFO para não poluir tanto o console no dia a dia
# Mas para a fase de debug intenso, DEBUG pode ser útil no console também.
CONSOLE_LOG_LEVEL = os.getenv("CONSOLE_LOG_LEVEL", "INFO").upper()
logger.add(
    lambda msg: print(msg, end=""), 
    level=CONSOLE_LOG_LEVEL, 
    format="<green>{time:HH:mm:ss}</green> | <level>{level: <8}</level> | <cyan>{name}</cyan>:<cyan>{function}</cyan>:<cyan>{line}</cyan> - <level>{message}</level>",
    colorize=True
)
logger.info(f"Loguru configurado a partir de debug_tools.py. Console Level: {CONSOLE_LOG_LEVEL}")

SENSITIVE_FIELDS = ["cpf", "rg", "nome_completo", "senha", "cnpj", "email", "telefone", "procuracao", "cliente", "documento"]

def sanitize_data(data_item):
    \"\"\"Sanitiza dados sensíveis recursivamente em dicts, listas e tuplas.\"\"\"
    if isinstance(data_item, dict):
        return {
            k: "[REDACTED]" if isinstance(k, str) and any(sf in k.lower() for sf in SENSITIVE_FIELDS) else sanitize_data(v)
            for k, v in data_item.items()
        }
    elif isinstance(data_item, (list, tuple)):
        return type(data_item)(sanitize_data(item) for item in data_item)
    # Não redige strings isoladas aqui, a menos que seja um valor direto de um campo sensível,
    # o que é melhor tratado no contexto do dicionário.
    return data_item

def debug_tracker(sample_rate=1.0):
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            # Amostragem probabilística
            if not (random.random() < sample_rate):
                return func(*args, **kwargs)

            func_qualname = f"{func.__module__}.{func.__name__}"
            call_id = f"{func_qualname}_{datetime.now().strftime('%H%M%S%f')}"
            
            # Sanitizar args e kwargs antes de logar
            try:
                # Cria cópias para não modificar os originais se forem mutáveis
                sanitized_args_list = list(args) 
                sanitized_kwargs_dict = kwargs.copy()
                
                safe_args_repr = str(sanitize_data(sanitized_args_list))[:500]
                safe_kwargs_repr = str(sanitize_data(sanitized_kwargs_dict))[:500]
            except Exception as e_sanitize:
                safe_args_repr = f"Error sanitizing args: {e_sanitize}"
                safe_kwargs_repr = f"Error sanitizing kwargs: {e_sanitize}"

            log_entry_start = {
                "event_type": "function_call_start", "call_id": call_id,
                "function": func_qualname,
                "timestamp_start": datetime.now().isoformat(),
                "args_preview": safe_args_repr, "kwargs_preview": safe_kwargs_repr
            }
            logger.debug(log_entry_start)
            
            start_time = time.perf_counter()
            
            try:
                result = func(*args, **kwargs)
                execution_time = time.perf_counter() - start_time
                
                try:
                    # Sanitizar resultado antes de logar
                    safe_result = sanitize_data(result)
                    safe_result_repr = str(safe_result)[:200]
                except Exception as e_sanitize_res:
                    safe_result_repr = f"Error sanitizing result: {e_sanitize_res}"

                log_entry_success = {
                    "event_type": "function_call_success", "call_id": call_id,
                    "function": func_qualname,
                    "timestamp_end": datetime.now().isoformat(),
                    "execution_time_seconds": round(execution_time, 6),
                    "result_type": str(type(result).__name__),
                    "result_preview": safe_result_repr
                }
                logger.debug(log_entry_success)
                return result
            except Exception as e:
                execution_time = time.perf_counter() - start_time
                log_entry_error = {
                    "event_type": "function_call_error", "call_id": call_id,
                    "function": func_qualname,
                    "timestamp_end": datetime.now().isoformat(),
                    "execution_time_seconds": round(execution_time, 6),
                    "error_type": str(type(e).__name__), "error_message": str(e)
                }
                # logger.exception() anexa o traceback automaticamente ao log
                logger.exception(log_entry_error) 
                raise
        return wrapper
    return decorator

def capturar_estado(identificador, objeto_a_salvar, sub_dir="default_snapshots"):
    \"\"\"Salva um snapshot do estado de um objeto para análise posterior.\"\"\"
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S_%f")
    snapshot_file_name = f"{identificador.replace(':', '_').replace('.', '_')}_{timestamp}.pkl"
    
    final_snapshot_dir = os.path.join(SNAPSHOTS_DIR, sub_dir)
    os.makedirs(final_snapshot_dir, exist_ok=True)
    snapshot_path = os.path.join(final_snapshot_dir, snapshot_file_name)
    
    try:
        with open(snapshot_path, "wb") as f:
            pickle.dump(objeto_a_salvar, f)
        logger.debug(f"Estado capturado: '{snapshot_path}' para identificador '{identificador}'")
        return snapshot_path
    except Exception as e_pickle:
        logger.error(f"Falha ao capturar estado (pickle) para '{identificador}': {e_pickle}")
        try: # Fallback para JSON se pickle falhar (para tipos de dados simples)
            json_snapshot_path = snapshot_path.replace(".pkl", ".json")
            with open(json_snapshot_path, "w", encoding="utf-8") as f_json:
                json.dump(objeto_a_salvar, f_json, indent=2, default=str) # default=str para lidar com tipos não serializáveis
            logger.info(f"Estado capturado como JSON (fallback): '{json_snapshot_path}' para identificador '{identificador}'")
            return json_snapshot_path
        except Exception as e_json:
            logger.error(f"Falha ao capturar estado como JSON (fallback) para '{identificador}': {e_json}")
            return None

def registrar_insight(desenvolvedor, descricao, evidencias=None):
    \"\"\"Registra um momento 'eureka' durante o processo de debug.\"\"\"
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    # Sanitizar nome do desenvolvedor para nome de arquivo
    dev_sanitized = "".join(c if c.isalnum() else "_" for c in desenvolvedor)
    insight_id = f"{timestamp}_{dev_sanitized}"
    insight_file_path = os.path.join(INSIGHTS_DIR, f"{insight_id}.md")
    
    content = f"# Insight: {descricao}\\n\\n"
    content += f"**Desenvolvedor:** {desenvolvedor}\\n"
    content += f"**Data/Hora:** {datetime.now().isoformat()}\\n\\n"
    content += "## Descrição Detalhada do Insight\\n\\n[Adicionar detalhes aqui sobre a descoberta, o problema e a solução pensada]\\n\\n"
    if evidencias:
        content += "## Evidências (Logs, Código, etc.)\\n\\n```\\n" # Usar ``` para blocos de código/log
        content += f"{str(evidencias)}\\n```\\n"
    
    with open(insight_file_path, "w", encoding="utf-8") as f:
        f.write(content)
    logger.info(f"Insight registrado: '{descricao}' por {desenvolvedor} em '{insight_file_path}'")
    return insight_id

def monitorar_condicao(condicao_a_checar, descricao_evento, capturar_contexto_func=None):
    \"\"\"Monitora uma condição, logando quando ocorre. Útil para eventos raros ou intermitentes.\"\"\"
    if condicao_a_checar: # A condição deve ser uma expressão booleana
        contexto_log = {}
        if callable(capturar_contexto_func):
            try:
                contexto_capturado = capturar_contexto_func()
                # Tenta serializar para JSON de forma segura
                contexto_log = json.loads(json.dumps(contexto_capturado, default=str))
            except Exception as e_ctx:
                contexto_log = {"erro_ao_capturar_contexto": str(e_ctx)}
        
        logger.warning(f"CONDIÇÃO MONITORADA ATINGIDA: {descricao_evento}", extra={"contexto_evento": contexto_log})
        return True
    return False
"""
# Storing this code to be presented in the final response without the tool_code block
print(proper_python_code)