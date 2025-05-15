import logging
import os
import functools
from datetime import datetime

# Singleton para o logger
@functools.lru_cache(maxsize=1)
def configurar_logger(nome="peticionamento", nivel=logging.INFO):
    """
    Configura e retorna o logger para uso em todo o sistema.
    Utiliza cache para garantir que a mesma instância seja retornada em todas as chamadas.
    """
    # Obter o logger pelo nome (reutiliza se já existir)
    logger = logging.getLogger(nome)
    logger.setLevel(nivel)
    
    # Se o logger já foi configurado, apenas retorná-lo
    if logger.handlers:
        return logger
    
    # Diretório de logs (criado a partir do diretório raiz do projeto)
    import sys
    base_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    logs_dir = os.path.join(base_dir, "logs")
    os.makedirs(logs_dir, exist_ok=True)
    
    # Handler para arquivo com nome único baseado em timestamp
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    log_file = os.path.join(logs_dir, f"{nome}_{timestamp}.log")
    
    # Criar handler de arquivo
    file_handler = logging.FileHandler(log_file, encoding='utf-8')
    file_handler.setLevel(nivel)
    
    # Handler para console (terminal)
    console_handler = logging.StreamHandler()
    console_handler.setLevel(nivel)
    
    # Formato consistente para todos os logs
    formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(filename)s:%(lineno)d - %(message)s')
    file_handler.setFormatter(formatter)
    console_handler.setFormatter(formatter)
    
    # Adicionar handlers ao logger
    logger.addHandler(file_handler)
    logger.addHandler(console_handler)
    
    # Definir propagação para evitar duplicação de logs
    logger.propagate = False
    
    logger.info(f"Logger '{nome}' configurado com sucesso. Nível: {logging.getLevelName(nivel)}, Arquivo: {log_file}")
    return logger 