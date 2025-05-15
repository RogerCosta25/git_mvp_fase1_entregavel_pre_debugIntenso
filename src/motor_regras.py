"""
Motor de regras para o sistema de peticionamento.
"""
import os
import sys
import json
from collections import defaultdict

# Adiciona o diretório pai ao path para importar módulos
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import config
from src.exceptions import (
    ArquivoNaoEncontradoError,
    FormatoArquivoInvalidoError,
    RegraInvalidaError
)
from src.avaliador_condicoes import AvaliadorCondicoes
from src.logger import logger

# Importa o adaptador do modelo relacional
try:
    from src.adaptador_modelo_relacional import AdaptadorModeloRelacional
except ImportError:
    logger.warning("Adaptador do modelo relacional não encontrado. Usando apenas modo legado.")
    AdaptadorModeloRelacional = None

class MotorRegras:
    """
    Motor de regras para processamento das condicionais do sistema.
    """
    
    def __init__(self, caminho_json=None, categorias=None, usar_modelo_relacional=True):
        """
        Inicializa o motor de regras.
        
        Args:
            caminho_json: Caminho para o arquivo JSON com as regras. Se None, usa config.REGRAS_JSON.
            categorias: Lista de categorias a serem processadas. Se None, usa config.CATEGORIAS_MVP.
            usar_modelo_relacional: Se True, tenta usar o modelo relacional refatorado.
        """
        self.caminho_json = caminho_json or config.REGRAS_JSON
        self.categorias = categorias or config.CATEGORIAS_MVP
        self.regras = {}
        self.regras_por_categoria = defaultdict(list)
        self.avaliador = AvaliadorCondicoes()
        self.adaptador_modelo_relacional = None
        self.usar_modelo_relacional = usar_modelo_relacional
        
        # Inicializa o adaptador do modelo relacional, se disponível
        if usar_modelo_relacional and AdaptadorModeloRelacional:
            try:
                logger.info("Iniciando adaptador do modelo relacional...")
                self.adaptador_modelo_relacional = AdaptadorModeloRelacional()
                logger.info("Adaptador do modelo relacional inicializado com sucesso.")
            except Exception as e:
                logger.error(f"Erro ao inicializar adaptador do modelo relacional: {str(e)}")
                logger.warning("Fallback para modo legado.")
                self.adaptador_modelo_relacional = None
    
    def carregar_regras(self):
        """
        Carrega as regras a partir do arquivo JSON.
        
        Raises:
            ArquivoNaoEncontradoError: Se o arquivo JSON não for encontrado.
            FormatoArquivoInvalidoError: Se o formato do JSON for inválido.
        """
        if not os.path.exists(self.caminho_json):
            logger.error(f"Arquivo de regras não encontrado: {self.caminho_json}")
            raise ArquivoNaoEncontradoError(f"Arquivo de regras não encontrado: {self.caminho_json}")
        
        try:
            with open(self.caminho_json, 'r', encoding='utf-8') as f:
                dados = json.load(f)
            
            # Verificação básica do formato
            if not isinstance(dados, dict) or 'regras' not in dados:
                raise FormatoArquivoInvalidoError("Formato inválido do JSON de regras. Esperado chave 'regras'.")
            
            # Processa as regras
            self.regras = dados.get('regras', {})
            self._organizar_regras_por_categoria()
            
            logger.info(f"Regras carregadas: {len(self.regras)} regras em {len(self.regras_por_categoria)} categorias")
            
            for categoria, regras in self.regras_por_categoria.items():
                logger.debug(f"Categoria {categoria}: {len(regras)} regras")
            
            return True
        except json.JSONDecodeError as e:
            logger.error(f"Erro ao decodificar JSON: {str(e)}")
            raise FormatoArquivoInvalidoError(f"Erro ao decodificar JSON: {str(e)}")
        except Exception as e:
            logger.error(f"Erro ao carregar regras: {str(e)}")
            raise FormatoArquivoInvalidoError(f"Erro ao carregar regras: {str(e)}")
    
    def _organizar_regras_por_categoria(self):
        """
        Organiza as regras por categoria para facilitar o processamento.
        """
        self.regras_por_categoria = defaultdict(list)
        
        for id_regra, regra in self.regras.items():
            categoria = regra.get('categoria', '')
            self.regras_por_categoria[categoria].append({
                'id': id_regra,
                **regra
            })
    
    def filtrar_regras_por_categorias(self, categorias=None):
        """
        Filtra regras pelas categorias especificadas.
        
        Args:
            categorias: Lista de categorias a serem incluídas. Se None, usa self.categorias.
            
        Returns:
            Dicionário com as regras filtradas por categoria.
        """
        categorias_filtro = categorias or self.categorias
        resultado = {}
        
        for categoria in categorias_filtro:
            if categoria in self.regras_por_categoria:
                resultado[categoria] = self.regras_por_categoria[categoria]
        
        logger.info(f"Regras filtradas: {sum(len(regras) for regras in resultado.values())} regras em {len(resultado)} categorias")
        return resultado
    
    def avaliar_secoes_ativas(self, dados_entrevista):
        """
        Avalia quais seções devem estar ativas com base nos dados da entrevista.
        
        Args:
            dados_entrevista: Dicionário com os dados da entrevista.
            
        Returns:
            Lista de IDs das seções que devem estar ativas.
        """
        # Carrega regras se ainda não foram carregadas
        if not self.regras:
            self.carregar_regras()
        
        secoes_ativas = []
        
        # Processa regras por categoria
        regras_filtradas = self.filtrar_regras_por_categorias()
        
        # Processa ESTRUTURA_SEMPRE_ATIVA
        if 'ESTRUTURA_SEMPRE_ATIVA' in regras_filtradas:
            for regra in regras_filtradas['ESTRUTURA_SEMPRE_ATIVA']:
                secoes_ativas.append(regra['id'])
                logger.debug(f"Seção sempre ativa: {regra['id']}")
        
        # Processa ESTRUTURA_CONDICIONAL_SIMPLES
        if 'ESTRUTURA_CONDICIONAL_SIMPLES' in regras_filtradas:
            for regra in regras_filtradas['ESTRUTURA_CONDICIONAL_SIMPLES']:
                try:
                    condicao = regra.get('condicao', '')
                    if self.avaliador.avaliar(condicao, dados_entrevista):
                        secoes_ativas.append(regra['id'])
                        logger.debug(f"Seção condicional ativa: {regra['id']} (condição: {condicao})")
                    else:
                        logger.debug(f"Seção condicional inativa: {regra['id']} (condição: {condicao})")
                except Exception as e:
                    logger.warning(f"Erro ao avaliar regra {regra['id']}: {str(e)}")
        
        logger.info(f"Avaliação completa: {len(secoes_ativas)} seções ativas de {len(self.regras)} regras")
        return secoes_ativas
    
    def obter_detalhes_secoes_ativas(self, secoes_ativas):
        """
        Obtém detalhes completos das seções ativas.
        
        Args:
            secoes_ativas: Lista de IDs das seções ativas.
            
        Returns:
            Lista de dicionários com detalhes das seções ativas.
        """
        detalhes = []
        
        for id_secao in secoes_ativas:
            if id_secao in self.regras:
                detalhes.append({
                    'id': id_secao,
                    **self.regras[id_secao]
                })
        
        return detalhes
    
    def validar_regras(self):
        """
        Valida se as regras estão no formato esperado.
        
        Raises:
            RegraInvalidaError: Se alguma regra estiver em formato inválido.
        """
        erros = []
        
        for id_regra, regra in self.regras.items():
            # Verifica se tem os campos obrigatórios
            if 'categoria' not in regra:
                erros.append(f"Regra {id_regra}: Falta campo obrigatório 'categoria'")
            
            # Valida ESTRUTURA_CONDICIONAL_SIMPLES
            if regra.get('categoria') == 'ESTRUTURA_CONDICIONAL_SIMPLES':
                if 'condicao' not in regra:
                    erros.append(f"Regra {id_regra}: Regra condicional sem campo 'condicao'")
        
        if erros:
            mensagem_erro = "Erros encontrados nas regras:\n" + "\n".join(erros)
            logger.error(mensagem_erro)
            raise RegraInvalidaError(mensagem_erro)
        
        return True
    
    def carregar_modelo_relacional(self):
        """
        Carrega o modelo relacional de dados.
        
        Returns:
            Dicionário no formato do mapping_campos_definicao.json.
            
        Raises:
            Exception: Se ocorrer erro ao carregar o modelo relacional.
        """
        if not self.adaptador_modelo_relacional:
            raise Exception("Adaptador do modelo relacional não inicializado")
            
        try:
            logger.info("Carregando modelo relacional...")
            return self.adaptador_modelo_relacional.converter_para_formato_legado()
        except Exception as e:
            logger.error(f"Erro ao carregar modelo relacional: {str(e)}")
            raise
    
    def obter_campo_por_nome(self, nome_campo):
        """
        Obtém informações de um campo pelo nome.
        
        Args:
            nome_campo: Nome do campo.
            
        Returns:
            Dicionário com informações do campo ou None se não encontrado.
        """
        if self.adaptador_modelo_relacional:
            try:
                return self.adaptador_modelo_relacional.obter_campo_por_nome(nome_campo)
            except Exception as e:
                logger.warning(f"Erro ao obter campo por nome do modelo relacional: {str(e)}")
                logger.warning("Fallback para modo legado.")
                return None
        return None
    
    def listar_campos_por_categoria(self, categoria):
        """
        Lista campos de uma categoria.
        
        Args:
            categoria: Nome da categoria.
            
        Returns:
            Lista de dicionários com informações dos campos.
        """
        if self.adaptador_modelo_relacional:
            try:
                return self.adaptador_modelo_relacional.listar_campos_por_categoria(categoria)
            except Exception as e:
                logger.warning(f"Erro ao listar campos por categoria do modelo relacional: {str(e)}")
                logger.warning("Fallback para modo legado.")
                return []
        return [] 