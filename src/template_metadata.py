"""
Classe para gerenciar metadados de templates de documentos.
"""
import os
import sys
import csv
import pathlib
from typing import Dict, List, Any, Optional, Set, Tuple, Union, cast

# Adiciona o diretório pai ao path para importar módulos
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import config
from src.exceptions import MetadataError
from src.logger import logger

class TemplateMetadata:
    """
    Classe para gerenciar os metadados de templates, mapeando placeholders para campos.
    """
    
    def __init__(self, metadata_path: Optional[str] = None):
        """
        Inicializa a classe de metadados de templates.
        
        Args:
            metadata_path: Caminho para o arquivo CSV de metadados (opcional).
                         Se None, usa o caminho padrão em config.TEMPLATE_METADATA_CSV.
        """
        # Inicia com estado válido
        if metadata_path:
            self.metadata_path = metadata_path
        elif hasattr(config, 'TEMPLATE_METADATA_CSV'):
            self.metadata_path = config.TEMPLATE_METADATA_CSV
        else:
            # Fallback para um caminho dentro do diretório de dados
            data_dir = getattr(config, 'DATA_DIR', os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'data'))
            os.makedirs(data_dir, exist_ok=True)
            self.metadata_path = os.path.join(data_dir, 'template_metadata.csv')
            logger.warning(f"config.TEMPLATE_METADATA_CSV não encontrado, usando caminho padrão: {self.metadata_path}")
            
        # Mapeamento de placeholders para campos
        self.placeholders_to_fields: Dict[str, str] = {}
        # Mapeamento de campos para placeholders
        self.fields_to_placeholders: Dict[str, List[str]] = {}
        # Informações adicionais por placeholder
        self.placeholders_info: Dict[str, Dict[str, Any]] = {}
        
        # Carrega os metadados
        self._carregar_metadados()
    
    def _carregar_metadados(self) -> None:
        """
        Carrega os metadados do arquivo CSV.
        
        Returns:
            Número de placeholders carregados.
            
        Raises:
            MetadataError: Se ocorrer um erro ao carregar os metadados.
        """
        if not os.path.exists(self.metadata_path):
            logger.warning(f"Arquivo de metadados não encontrado: {self.metadata_path}")
            # Cria um arquivo vazio se não existir
            try:
                os.makedirs(os.path.dirname(self.metadata_path), exist_ok=True)
                with open(self.metadata_path, 'w', encoding='utf-8-sig', newline='') as f:
                    fieldnames = ['placeholder', 'campo', 'categoria', 'descricao', 'tipo', 'obrigatorio']
                    writer = csv.DictWriter(f, fieldnames=fieldnames, delimiter=getattr(config, 'CSV_SEPARATOR', ';'))
                    writer.writeheader()
                logger.info(f"Arquivo de metadados criado: {self.metadata_path}")
            except Exception as e:
                logger.error(f"Erro ao criar arquivo de metadados: {str(e)}")
            return
        
        try:
            # Limpa os mapeamentos existentes
            self.placeholders_to_fields = {}
            self.fields_to_placeholders = {}
            self.placeholders_info = {}
            
            with open(self.metadata_path, 'r', encoding='utf-8-sig') as f:
                reader = csv.DictReader(f, delimiter=getattr(config, 'CSV_SEPARATOR', ';'))
                
                for row in reader:
                    # Pula linhas vazias ou sem placeholder
                    if not row or 'placeholder' not in row or not row['placeholder']:
                        continue
                    
                    # Normaliza o placeholder removendo espaços
                    placeholder = row['placeholder'].strip().replace(' ', '')
                    
                    # Obtém o nome do campo e normaliza
                    field_name = row.get('campo', '').strip()
                    if not field_name:
                        logger.warning(f"Placeholder sem campo associado: {placeholder}")
                        continue
                    
                    # Adiciona ao mapeamento de placeholder -> campo
                    self.placeholders_to_fields[placeholder] = field_name
                    
                    # Adiciona ao mapeamento de campo -> placeholders (um campo pode ter múltiplos placeholders)
                    if field_name not in self.fields_to_placeholders:
                        self.fields_to_placeholders[field_name] = []
                    self.fields_to_placeholders[field_name].append(placeholder)
                    
                    # Armazena informações adicionais do placeholder
                    self.placeholders_info[placeholder] = {
                        'campo': field_name,
                        'categoria': row.get('categoria', ''),
                        'descricao': row.get('descricao', ''),
                        'tipo': row.get('tipo', ''),
                        'obrigatorio': row.get('obrigatorio', 'N').upper() == 'S'
                    }
            
            logger.info(f"Metadados carregados: {len(self.placeholders_to_fields)} placeholders")
            return
        except Exception as e:
            logger.error(f"Erro ao carregar metadados: {str(e)}")
            raise MetadataError(f"Erro ao carregar metadados: {str(e)}")
    
    def get_field_name(self, placeholder: str) -> Optional[str]:
        """
        Obtém o nome do campo associado a um placeholder.
        
        Args:
            placeholder: Nome do placeholder.
            
        Returns:
            Nome do campo ou None se o placeholder não existir.
        """
        # Normaliza o placeholder removendo espaços
        placeholder_norm = placeholder.strip().replace(' ', '')
        return self.placeholders_to_fields.get(placeholder_norm)
    
    def get_placeholders(self, field_name: str) -> List[str]:
        """
        Obtém os placeholders associados a um campo.
        
        Args:
            field_name: Nome do campo.
            
        Returns:
            Lista de placeholders associados ao campo, ou lista vazia se o campo não existir.
        """
        return self.fields_to_placeholders.get(field_name, [])
    
    def get_placeholder_info(self, placeholder: str) -> Optional[Dict[str, Any]]:
        """
        Obtém todas as informações disponíveis sobre um placeholder.
        
        Args:
            placeholder: Nome do placeholder.
            
        Returns:
            Dicionário com informações do placeholder, ou None se não existir.
        """
        # Normaliza o placeholder removendo espaços
        placeholder_norm = placeholder.strip().replace(' ', '')
        return self.placeholders_info.get(placeholder_norm)
    
    def is_placeholder_mandatory(self, placeholder: str) -> bool:
        """
        Verifica se um placeholder é obrigatório.
        
        Args:
            placeholder: Nome do placeholder.
            
        Returns:
            True se o placeholder for obrigatório, False caso contrário.
        """
        info = self.get_placeholder_info(placeholder)
        return bool(info and info.get('obrigatorio', False))
    
    def get_all_placeholders(self) -> Set[str]:
        """
        Obtém todos os placeholders conhecidos.
        
        Returns:
            Conjunto com todos os placeholders.
        """
        return set(self.placeholders_to_fields.keys())
    
    def get_all_fields(self) -> Set[str]:
        """
        Obtém todos os campos conhecidos.
        
        Returns:
            Conjunto com todos os campos.
        """
        return set(self.fields_to_placeholders.keys())
    
    def get_placeholders_by_category(self, categoria: str) -> List[str]:
        """
        Obtém placeholders por categoria.
        
        Args:
            categoria: Nome da categoria.
            
        Returns:
            Lista de placeholders na categoria especificada.
        """
        result = []
        for ph, info in self.placeholders_info.items():
            if info.get('categoria') == categoria:
                result.append(ph)
        return result
    
    def get_required_placeholders(self) -> List[str]:
        """
        Obtém todos os placeholders obrigatórios.
        
        Returns:
            Lista de placeholders obrigatórios.
        """
        result = []
        for ph, info in self.placeholders_info.items():
            if info.get('obrigatorio', False):
                result.append(ph)
        return result
    
    def add_placeholder(self, placeholder: str, field_name: str, info: Optional[Dict[str, Any]] = None) -> None:
        """
        Adiciona um novo placeholder ao metadata.
        
        Args:
            placeholder: Nome do placeholder.
            field_name: Nome do campo associado.
            info: Informações adicionais sobre o placeholder (opcional).
        """
        # Normaliza o placeholder removendo espaços
        placeholder_norm = placeholder.strip().replace(' ', '')
        
        # Adiciona ao mapeamento de placeholder -> campo
        self.placeholders_to_fields[placeholder_norm] = field_name
        
        # Adiciona ao mapeamento de campo -> placeholders
        if field_name not in self.fields_to_placeholders:
            self.fields_to_placeholders[field_name] = []
        if placeholder_norm not in self.fields_to_placeholders[field_name]:
            self.fields_to_placeholders[field_name].append(placeholder_norm)
        
        # Armazena informações adicionais do placeholder
        if info is None:
            info = {}
        self.placeholders_info[placeholder_norm] = {
            'campo': field_name,
            'categoria': info.get('categoria', ''),
            'descricao': info.get('descricao', ''),
            'tipo': info.get('tipo', ''),
            'obrigatorio': info.get('obrigatorio', False)
        }
        
        logger.info(f"Placeholder adicionado: {placeholder_norm} -> {field_name}")
    
    def save_to_csv(self, output_path: Optional[str] = None) -> None:
        """
        Salva os metadados atuais em um arquivo CSV.
        
        Args:
            output_path: Caminho para o arquivo de saída (opcional).
                       Se None, sobrescreve o arquivo original.
        
        Raises:
            MetadataError: Se ocorrer um erro ao salvar os metadados.
        """
        try:
            # Se não foi especificado, usa o caminho original
            save_path = output_path or self.metadata_path
            
            # Verifica se o diretório existe
            os.makedirs(os.path.dirname(save_path), exist_ok=True)
            
            with open(save_path, 'w', encoding='utf-8-sig', newline='') as f:
                # Define os campos
                fieldnames = ['placeholder', 'campo', 'categoria', 'descricao', 'tipo', 'obrigatorio']
                writer = csv.DictWriter(f, fieldnames=fieldnames, delimiter=getattr(config, 'CSV_SEPARATOR', ';'))
                
                # Escreve o cabeçalho
                writer.writeheader()
                
                # Escreve os dados
                for placeholder, info in sorted(self.placeholders_info.items()):
                    row = {
                        'placeholder': placeholder,
                        'campo': info['campo'],
                        'categoria': info.get('categoria', ''),
                        'descricao': info.get('descricao', ''),
                        'tipo': info.get('tipo', ''),
                        'obrigatorio': 'S' if info.get('obrigatorio', False) else 'N'
                    }
                    writer.writerow(row)
            
            logger.info(f"Metadados salvos em: {save_path}")
        except Exception as e:
            logger.error(f"Erro ao salvar metadados: {str(e)}")
            raise MetadataError(f"Erro ao salvar metadados: {str(e)}")
            
if __name__ == "__main__":
    # Exemplo de uso independente
    metadata = TemplateMetadata()
    print(f"Placeholders carregados: {len(metadata.get_all_placeholders())}")
    print(f"Campos únicos: {len(metadata.get_all_fields())}")
    print(f"Placeholders obrigatórios: {len(metadata.get_required_placeholders())}")
    
    # Exemplo de adição de um novo placeholder
    metadata.add_placeholder(
        "novoPlaceholder", 
        "campo_teste",
        {
            'categoria': 'TESTE',
            'descricao': 'Placeholder de teste',
            'tipo': 'texto',
            'obrigatorio': True
        }
    )
    
    # Salva em um novo arquivo para não modificar o original
    metadata.save_to_csv("template_metadata_updated.csv") 