"""
Adaptador para o modelo relacional de campos.

Este módulo implementa a lógica para carregar e disponibilizar as tabelas
do modelo relacional refatorado (campos_definicao, categorias_campos, etc.)
de forma compatível com o código existente do sistema.
"""

import os
import sys
import pandas as pd
from typing import Dict, List, Any, Optional, Union, Tuple, cast

# Adiciona o diretório pai ao path para importar módulos
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import config
from src.logger import logger

class AdaptadorModeloRelacional:
    """
    Classe que adapta o modelo relacional para uso no sistema.
    
    Esta classe carrega as tabelas do modelo relacional refatorado e 
    fornece métodos para acessá-las de forma compatível com o código existente.
    """
    
    def __init__(self):
        """
        Inicializa o adaptador carregando as tabelas do modelo relacional.
        """
        # Inicializa com DataFrames vazios em vez de None
        self.campos = pd.DataFrame()
        self.categorias = pd.DataFrame()
        self.regras = pd.DataFrame()
        self.tipos = pd.DataFrame()
        self.opcoes = pd.DataFrame()
        
        # Carrega as tabelas do modelo relacional
        self._carregar_tabelas()
        
    def _carregar_tabelas(self) -> None:
        """
        Carrega todas as tabelas do modelo relacional.
        """
        try:
            logger.info("Carregando tabelas do modelo relacional...")
            
            # Carrega as tabelas principais
            self.campos = self._carregar_tabela(config.CAMPOS_CSV)
            self.categorias = self._carregar_tabela(config.CATEGORIAS_CAMPOS_CSV)
            self.regras = self._carregar_tabela(config.REGRAS_ATIVACAO_CSV)
            self.tipos = self._carregar_tabela(config.TIPOS_DADOS_CSV)
            self.opcoes = self._carregar_tabela(config.OPCOES_SELECAO_CSV)
            
            # Verifica se as tabelas foram carregadas corretamente
            self._validar_tabelas()
            
            logger.info(f"Tabelas carregadas com sucesso: {len(self.campos)} campos, "
                       f"{len(self.categorias)} categorias, {len(self.regras)} regras, "
                       f"{len(self.tipos)} tipos, {len(self.opcoes)} opções")
        except Exception as e:
            logger.error(f"Erro ao carregar tabelas do modelo relacional: {str(e)}")
            raise
    
    def _carregar_tabela(self, caminho: str) -> pd.DataFrame:
        """
        Carrega uma tabela do modelo relacional a partir de um arquivo CSV.
        
        Args:
            caminho: Caminho para o arquivo CSV.
            
        Returns:
            DataFrame pandas contendo os dados da tabela.
            
        Raises:
            FileNotFoundError: Se o arquivo não for encontrado.
            Exception: Para outros erros ao processar o CSV.
        """
        try:
            if not os.path.exists(caminho):
                raise FileNotFoundError(f"Arquivo não encontrado: {caminho}")
                
            # Tenta carregar o CSV com separador padrão
            try:
                df = pd.read_csv(caminho, sep=config.CSV_SEPARATOR, encoding='utf-8-sig')
            except Exception:
                # Tenta com detecção automática como fallback
                df = pd.read_csv(caminho, sep=None, engine='python', encoding='utf-8-sig')
                
            return df
        except Exception as e:
            logger.error(f"Erro ao carregar tabela {os.path.basename(caminho)}: {str(e)}")
            raise
    
    def _validar_tabelas(self) -> None:
        """
        Valida se as tabelas do modelo relacional foram carregadas corretamente.
        
        Raises:
            Exception: Se alguma tabela estiver vazia ou com formato inválido.
        """
        # Verifica se as tabelas estão vazias
        if len(self.campos) == 0:
            raise Exception("Tabela de campos vazia ou não carregada")
            
        if len(self.categorias) == 0:
            raise Exception("Tabela de categorias vazia ou não carregada")
            
        if len(self.regras) == 0:
            raise Exception("Tabela de regras vazia ou não carregada")
            
        if len(self.tipos) == 0:
            raise Exception("Tabela de tipos vazia ou não carregada")
        
        # Verifica se as colunas principais existem
        colunas_campos = ['campo_id', 'nome_campo']
        colunas_categorias = ['campo_id', 'categoria_1']
        colunas_regras = ['regra_id', 'campo_id', 'campo_vinculo_id']
        colunas_tipos = ['tipo_dado_id', 'nome_tipo']
        
        for coluna in colunas_campos:
            if coluna not in self.campos.columns:
                raise Exception(f"Coluna '{coluna}' não encontrada na tabela de campos")
                
        for coluna in colunas_categorias:
            if coluna not in self.categorias.columns:
                raise Exception(f"Coluna '{coluna}' não encontrada na tabela de categorias")
                
        for coluna in colunas_regras:
            if coluna not in self.regras.columns:
                raise Exception(f"Coluna '{coluna}' não encontrada na tabela de regras")
                
        for coluna in colunas_tipos:
            if coluna not in self.tipos.columns:
                raise Exception(f"Coluna '{coluna}' não encontrada na tabela de tipos")
    
    def obter_campo_por_id(self, campo_id: int) -> Optional[Dict[str, Any]]:
        """
        Obtém as informações de um campo pelo seu ID.
        
        Args:
            campo_id: ID do campo.
            
        Returns:
            Dicionário com as informações do campo, ou None se não encontrado.
        """
        try:
            # Filtra o campo pelo ID
            campo = self.campos[self.campos['campo_id'] == campo_id]
            
            if len(campo) == 0:
                return None
                
            # Converte para dicionário
            resultado = campo.iloc[0].to_dict()
            
            # Adiciona informações de tipo
            if 'tipo_dado_id' in resultado and pd.notna(resultado['tipo_dado_id']):
                tipo_id = int(resultado['tipo_dado_id'])
                tipo = self.tipos[self.tipos['tipo_dado_id'] == tipo_id]
                
                if len(tipo) > 0:
                    resultado['tipo_dado_programacao'] = tipo.iloc[0]['nome_tipo']
                    resultado['mascara_formato'] = tipo.iloc[0]['mascara_formato'] if 'mascara_formato' in tipo.columns else ''
            
            # Adiciona regras de ativação
            regras_campo = self.regras[self.regras['campo_id'] == campo_id]
            if len(regras_campo) > 0:
                # Pega a primeira regra para obrigatoriedade
                resultado['obrigatorio_quando_ativo'] = regras_campo.iloc[0]['obrigatorio_quando_ativo'] == 'sim'
                
                # Adiciona informações de vinculação da primeira regra
                if pd.notna(regras_campo.iloc[0]['campo_vinculo_id']):
                    resultado['campo_vinculo_id'] = regras_campo.iloc[0]['campo_vinculo_id']
                    resultado['condicao_vinculo_tipo'] = regras_campo.iloc[0]['condicao_vinculo_tipo']
                    resultado['condicao_vinculo_valor'] = regras_campo.iloc[0]['condicao_vinculo_valor']
            
            # Adiciona categoria
            categorias_campo = self.categorias[self.categorias['campo_id'] == campo_id]
            if len(categorias_campo) > 0:
                resultado['categoria'] = categorias_campo.iloc[0]['categoria_1']
                resultado['subcategoria'] = categorias_campo.iloc[0]['subcategoria_1'] if 'subcategoria_1' in categorias_campo.columns else ''
            
            # Adiciona opções de seleção
            if 'campo_id' in self.opcoes.columns:
                opcoes_campo = self.opcoes[self.opcoes['campo_id'] == campo_id]
                if len(opcoes_campo) > 0 and 'valor' in opcoes_campo.columns:
                    opcoes_lista = opcoes_campo['valor'].tolist()
                    resultado['opcoes_lista_selecao'] = ';'.join(opcoes_lista)
            
            return resultado
        except Exception as e:
            logger.error(f"Erro ao obter campo por ID {campo_id}: {str(e)}")
            return None
    
    def obter_campo_por_nome(self, nome_campo: str) -> Optional[Dict[str, Any]]:
        """
        Obtém as informações de um campo pelo seu nome.
        
        Args:
            nome_campo: Nome do campo.
            
        Returns:
            Dicionário com as informações do campo, ou None se não encontrado.
        """
        try:
            # Filtra o campo pelo nome
            campo = self.campos[self.campos['nome_campo'] == nome_campo]
            
            if len(campo) == 0:
                return None
                
            # Obtém o ID do campo
            campo_id = int(campo.iloc[0]['campo_id'])
            
            # Usa o método de obtenção por ID
            return self.obter_campo_por_id(campo_id)
        except Exception as e:
            logger.error(f"Erro ao obter campo por nome '{nome_campo}': {str(e)}")
            return None
    
    def listar_campos_por_categoria(self, categoria: str) -> List[Dict[str, Any]]:
        """
        Lista todos os campos de uma determinada categoria.
        
        Args:
            categoria: Nome da categoria.
            
        Returns:
            Lista de dicionários com informações dos campos.
        """
        try:
            # Filtra as categorias
            filtro_categoria = (self.categorias['categoria_1'] == categoria) | (self.categorias['categoria_2'] == categoria)
            categorias_filtradas = self.categorias[filtro_categoria]
            
            if len(categorias_filtradas) == 0:
                return []
                
            # Obtém os IDs dos campos
            campo_ids = categorias_filtradas['campo_id'].unique().tolist()
            
            # Obtém informações detalhadas de cada campo
            resultado: List[Dict[str, Any]] = []
            for campo_id in campo_ids:
                campo = self.obter_campo_por_id(int(campo_id))
                if campo:
                    resultado.append(campo)
            
            return resultado
        except Exception as e:
            logger.error(f"Erro ao listar campos por categoria '{categoria}': {str(e)}")
            return []
    
    def listar_regras_por_campo(self, campo_id: int) -> List[Dict[str, Any]]:
        """
        Lista todas as regras de ativação para um campo.
        
        Args:
            campo_id: ID do campo.
            
        Returns:
            Lista de dicionários com informações das regras.
        """
        try:
            # Filtra as regras pelo ID do campo
            regras_campo = self.regras[self.regras['campo_id'] == campo_id]
            
            if len(regras_campo) == 0:
                return []
                
            # Converte para lista de dicionários
            # Usamos cast para informar ao Pylance que o retorno é compatível
            resultado = []
            for _, row in regras_campo.iterrows():
                resultado.append(row.to_dict())
            return resultado
        except Exception as e:
            logger.error(f"Erro ao listar regras para campo ID {campo_id}: {str(e)}")
            return []
    
    def converter_para_formato_legado(self) -> Dict[str, Any]:
        """
        Converte os dados do modelo relacional para o formato legado usado pelo sistema.
        
        Returns:
            Dicionário no formato do arquivo mapping_campos_definicao.json.
        """
        try:
            logger.info("Convertendo modelo relacional para formato legado...")
            
            resultado: Dict[str, Any] = {
                "campos": {},
                "campos_por_id": {},
                "campos_por_categoria": {},
                "metadata": {
                    "total_campos": len(self.campos),
                    "versao_schema": "1.0"
                }
            }
            
            # Abordagem mais direta: convertemos o DataFrame inteiro para lista de dicionários
            campos_lista = []
            try:
                # Obtemos os dicionários com a conversão manual
                for _, row in self.campos.iterrows():
                    campo_dict = {}
                    for col_name in self.campos.columns:
                        campo_dict[col_name] = row[col_name]
                    campos_lista.append(campo_dict)
            except Exception as e:
                logger.error(f"Erro ao converter DataFrame para dicionários: {e}")
                # Fallback: Tenta a conversão direta como último recurso
                try:
                    # Converte coluna por coluna
                    campos_lista = []
                    for idx in range(len(self.campos)):
                        row = self.campos.iloc[idx]
                        row_dict = {}
                        for col in self.campos.columns:
                            val = row[col]
                            # Evitamos objetos numpy/pandas que possam causar problemas
                            if pd.api.types.is_scalar(val):
                                row_dict[col] = val if not pd.isna(val) else None
                        campos_lista.append(row_dict)
                except Exception as e2:
                    logger.error(f"Erro também no fallback: {e2}")
                    # Se tudo falhar, retorna um dicionário vazio
                    return resultado
            
            # Processa cada registro da lista de dicionários
            for campo_dict in campos_lista:
                try:
                    # Obtém o campo_id com tratamento para valores inválidos
                    if 'campo_id' in campo_dict and campo_dict['campo_id'] is not None:
                        # Evita problemas com tipos int64/numpy.int64
                        campo_id_valor = campo_dict['campo_id']
                        # Convertemos para um int Python padrão
                        campo_id = int(campo_id_valor)
                    else:
                        logger.warning(f"Campo id não encontrado ou inválido")
                        continue
                    
                    # Obtém os detalhes do campo
                    campo_detalhado = self.obter_campo_por_id(campo_id)
                    
                    if campo_detalhado and 'nome_campo' in campo_detalhado:
                        nome_campo = campo_detalhado['nome_campo']
                        
                        # Adiciona ao mapeamento por nome
                        resultado["campos"][nome_campo] = campo_detalhado
                        
                        # Adiciona ao mapeamento por ID
                        resultado["campos_por_id"][str(campo_id)] = campo_detalhado
                        
                        # Agrupa por categoria
                        if 'categoria' in campo_detalhado and campo_detalhado['categoria']:
                            categoria = campo_detalhado['categoria']
                            
                            if categoria not in resultado["campos_por_categoria"]:
                                resultado["campos_por_categoria"][categoria] = []
                                
                            resultado["campos_por_categoria"][categoria].append(campo_detalhado)
                except (ValueError, TypeError) as e:
                    logger.error(f"Erro ao processar campo: {e}")
                    continue
            
            # Atualiza metadata
            resultado["metadata"]["total_campos_validos"] = len(resultado["campos"])
            resultado["metadata"]["total_categorias"] = len(resultado["campos_por_categoria"])
            
            logger.info(f"Conversão concluída: {len(resultado['campos'])} campos válidos")
            return resultado
        except Exception as e:
            logger.error(f"Erro ao converter para formato legado: {str(e)}")
            raise 