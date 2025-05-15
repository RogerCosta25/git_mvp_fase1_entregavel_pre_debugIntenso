import os
import sys
import pandas as pd
# Adiciona o diretório pai ao path para importar módulos locais
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import config
from src.exceptions import ArquivoNaoEncontradoError
from src.logger import logger

class TemplateMetadata:
    """
    Responsável por ler o d_template.csv e d_campos.csv e fornecer mapeamento
    entre placeholders do template e nomes de campo no CSV de entrevistas.
    """
    def __init__(self):
        self.data_dir = config.DATA_DIR
        self.template_map = self._load_template_map()
        self.field_map = self._load_field_map()

    def _load_template_map(self):
        path = os.path.join(self.data_dir, 'd_template.csv')
        if not os.path.exists(path):
            logger.error(f"d_template.csv não encontrado em {path}")
            raise ArquivoNaoEncontradoError(f"d_template.csv não encontrado: {path}")
        df = pd.read_csv(path, sep=';', encoding='utf-8')
        # Mapeia nome_placeholder -> campo_id
        return {row['nome_placeholder']: row['campo_id'] for _, row in df.iterrows()}

    def _load_field_map(self):
        path = os.path.join(self.data_dir, 'd_campos.csv')
        if not os.path.exists(path):
            logger.error(f"d_campos.csv não encontrado em {path}")
            raise ArquivoNaoEncontradoError(f"d_campos.csv não encontrado: {path}")
        df = pd.read_csv(path, sep=';', encoding='utf-8')
        # Mapeia campo_id -> nome_campo
        return {row['campo_id']: row['nome_campo'] for _, row in df.iterrows()}

    def get_field_name(self, placeholder):
        """Retorna o nome do campo correspondente ao placeholder ou None."""
        campo_id = self.template_map.get(placeholder)
        if campo_id is None:
            return None
        return self.field_map.get(campo_id)

    def get_all_placeholders(self):
        """Retorna a lista de todos os placeholders definidos no template."""
        return list(self.template_map.keys()) 