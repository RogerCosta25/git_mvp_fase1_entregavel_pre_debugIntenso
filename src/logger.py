# logger.py
"""
Sistema de logging para o projeto de peticionamento.
"""
import logging
import os
import sys

# --- Configuração de Caminho e Módulo config ---
# Tenta adicionar o diretório raiz do projeto ao sys.path para encontrar 'config.py'
# Esta abordagem tem suas ressalvas e pode ser melhorada com estruturas de projeto mais robustas
# (ex: projeto instalável, PYTHONPATH configurado externamente).
original_sys_path = list(sys.path) # Salva o sys.path original
project_root_candidate = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

if project_root_candidate not in sys.path:
    sys.path.insert(0, project_root_candidate)

try:
    import config
    # Se config foi importado com sucesso, podemos remover o project_root_candidate do path
    # se ele foi o único motivo da adição e não queremos que ele permaneça lá globalmente.
    # No entanto, deixar pode ser útil se config importar outros módulos relativos à raiz.
    # Para simplificar, não removeremos por enquanto.
except ImportError:
    # Restaura sys.path se a importação de config falhou para evitar poluição
    # e tenta garantir que não estamos em um estado sys.path inesperado.
    # Esta parte pode ser complexa dependendo do que causou o ImportError.
    # Se project_root_candidate foi adicionado e está em original_sys_path, não há problema.
    # Se foi adicionado e não estava, e a importação falhou, o sys.path modificado pode persistir.
    # Uma abordagem mais segura seria manipular sys.path apenas dentro de um try/finally.
    # Por ora, vamos assumir que a estrutura do projeto é tal que config deve ser encontrado.
    
    # Fallback para um MockConfig se 'config.py' não for encontrado ou falhar ao importar.
    class MockConfig:
        LOG_LEVEL = "INFO"
        LOG_DIR = "logs"  # Diretório padrão para logs
        LOG_FILE = None   # Se None, o nome do arquivo será 'peticionamento.log' dentro de LOG_DIR
        DEBUG = False     # Atributo DEBUG para consistência com a lógica de log

    config = MockConfig()
    # Opcional: imprimir um aviso, mas pode ser ruidoso.
    # print("AVISO: Módulo 'config.py' não encontrado ou erro na importação. "
    #       "Usando configurações de log padrão.", file=sys.stderr)


class Logger:
    """
    Implementa um logger configurável para o projeto, usando um padrão Singleton.
    A configuração é gerenciada pela função global `configurar_logger`.
    """
    _instance = None
    
    def __new__(cls, *args, **kwargs):
        if cls._instance is None:
            cls._instance = super(Logger, cls).__new__(cls)
            cls._instance.logger = None # Logger interno será inicializado em setup_logger
        return cls._instance
    
    def _initialize_internal_logger(self):
        """Garante que self.logger (o objeto logging.Logger) exista."""
        if self.logger is None:
            self.logger = logging.getLogger("peticionamento")

    def _determine_log_level(self, debug_mode_override=None):
        """Determina o nível de log a ser usado."""
        if debug_mode_override is True:
            return logging.DEBUG
        
        # Se debug_mode_override é False (explícito) ou None, consulta 'config'
        # Prioriza config.DEBUG se True e debug_mode_override não é False
        if getattr(config, 'DEBUG', False) is True and debug_mode_override is not False:
            return logging.DEBUG
        
        # Caso contrário, usa config.LOG_LEVEL
        level_str = getattr(config, 'LOG_LEVEL', "INFO").upper()
        levels = {
            "DEBUG": logging.DEBUG, "INFO": logging.INFO, "WARNING": logging.WARNING,
            "ERROR": logging.ERROR, "CRITICAL": logging.CRITICAL
        }
        return levels.get(level_str, logging.INFO)

    def setup_logger(self, debug_mode_override=None, log_file_path_override=None):
        """Configura o logger interno com handlers para console e arquivo. Pode ser chamada para reconfigurar."""
        self._initialize_internal_logger()

        current_log_level = self._determine_log_level(debug_mode_override)
        self.logger.setLevel(current_log_level)
        
        # Limpa handlers existentes antes de adicionar novos para evitar duplicação
        for handler in self.logger.handlers[:]:
            self.logger.removeHandler(handler)
            handler.close() # Importante para fechar arquivos de log, se abertos
        
        # Formatos de log
        file_formatter = logging.Formatter(
            '%(asctime)s | %(levelname)-8s | %(name)s | %(module)-15s.%(funcName)-20s | L%(lineno)-4d | %(message)s'
        )
        
        if current_log_level <= logging.DEBUG: # Se DEBUG ou mais baixo (custom)
            console_formatter = logging.Formatter(
                 '%(asctime)s | %(levelname)-8s | %(name)s | %(module)-15s:%(lineno)-4d | %(message)s'
            )
        else:
            console_formatter = logging.Formatter('%(levelname)s: %(message)s')
        
        # Handler para console
        console_handler = logging.StreamHandler(sys.stdout) # Usar sys.stdout para output padrão
        console_handler.setFormatter(console_formatter)
        self.logger.addHandler(console_handler)
        
        # Handler para arquivo
        log_file_to_use = log_file_path_override
        if not log_file_to_use:
            log_file_to_use = getattr(config, 'LOG_FILE', None)
            if not log_file_to_use:
                log_dir_config = getattr(config, 'LOG_DIR', 'logs') # Padrão 'logs'
                
                # Determina o caminho absoluto para o diretório de logs
                # Se log_dir_config for relativo, considera-o relativo à raiz do projeto
                if not os.path.isabs(log_dir_config):
                    log_dir_abs = os.path.join(project_root_candidate, log_dir_config)
                else:
                    log_dir_abs = log_dir_config
                
                os.makedirs(log_dir_abs, exist_ok=True) # Cria o diretório se não existir
                log_file_to_use = os.path.join(log_dir_abs, "peticionamento.log")
        
        # Garante que o diretório do arquivo de log final exista
        final_log_dir = os.path.dirname(log_file_to_use)
        if final_log_dir: # Se não for apenas um nome de arquivo no diretório atual
            os.makedirs(final_log_dir, exist_ok=True)

        file_handler = logging.FileHandler(log_file_to_use, mode='a', encoding='utf-8')
        file_handler.setFormatter(file_formatter)
        self.logger.addHandler(file_handler)

        # self.logger.debug(f"Logger (re)configurado. Nível: {logging.getLevelName(self.logger.level)}. Arquivo: {log_file_to_use}")

    # Métodos de conveniência para logging (delegam para o logger interno)
    def debug(self, message, *args, **kwargs): self.logger.debug(message, *args, **kwargs)
    def info(self, message, *args, **kwargs): self.logger.info(message, *args, **kwargs)
    def warning(self, message, *args, **kwargs): self.logger.warning(message, *args, **kwargs)
    def error(self, message, *args, **kwargs): self.logger.error(message, *args, **kwargs)
    def critical(self, message, *args, **kwargs): self.logger.critical(message, *args, **kwargs)
    def exception(self, message, *args, exc_info=True, **kwargs): self.logger.exception(message, *args, exc_info=exc_info, **kwargs)

# --- Instância Singleton e Função de Configuração Global ---

# Cria a instância singleton da classe Logger.
# Esta é a instância que será exportada como 'logger'.
_the_logger_instance = Logger()

def configurar_logger(debug_mode_override=None, log_file_path_override=None):
    """
    Função global para configurar (ou reconfigurar) o logger singleton.
    Esta é a função que deve ser importada e chamada pelo main.py ou outros módulos.
    """
    global _the_logger_instance # Garante que estamos referenciando a instância global
    if _the_logger_instance is None: # Segurança, mas deve ter sido criada acima
        _the_logger_instance = Logger()
    
    _the_logger_instance.setup_logger(
        debug_mode_override=debug_mode_override,
        log_file_path_override=log_file_path_override
    )
    return _the_logger_instance # Retorna a instância para consistência

# Exporta a instância da classe Logger como 'logger' para uso direto.
# Ex: from src.logger import logger; logger.info("Mensagem")
logger = _the_logger_instance

# Configuração inicial padrão ao importar o módulo.
# Isso garante que o logger esteja minimamente funcional (com defaults de 'config' ou MockConfig)
# mesmo que `configurar_logger` não seja chamada explicitamente pelo código cliente logo de início.
# O código cliente pode, então, chamar `configurar_logger` novamente para ajustar as configurações.
if _the_logger_instance.logger is None or not _the_logger_instance.logger.hasHandlers():
     configurar_logger()

# Restaura sys.path se ele foi modificado E se a importação de config foi bem-sucedida.
# Esta parte é complexa e pode não ser ideal. Melhor se o projeto não precisar disso.
# Se config falhou, sys.path já pode estar "sujo" com project_root_candidate.
# if project_root_candidate in sys.path and project_root_candidate not in original_sys_path:
#    sys.path.remove(project_root_candidate)
# Comentar esta restauração por enquanto, pois pode ser mais problemático do que útil
# dependendo de como o projeto é executado.