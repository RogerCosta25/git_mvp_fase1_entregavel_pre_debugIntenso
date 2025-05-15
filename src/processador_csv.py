"""
Processador de arquivos CSV para o sistema de peticionamento.
"""
import os
import sys
import pandas as pd
import csv
import re
from datetime import datetime

# Adiciona o diretório pai ao path para importar módulos
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import config
from src.exceptions import (
    ArquivoNaoEncontradoError, 
    FormatoArquivoInvalidoError,
    DadosInvalidosError
)
from src.logger import logger

class ProcessadorCSV:
    """
    Classe responsável por carregar e processar arquivos CSV de entrevistas.
    """
    
    def __init__(self, modo_estrito=None):
        """
        Inicializa o processador CSV.
        
        Args:
            modo_estrito: Se True, lança exceção em caso de dados inválidos.
                         Se None, usa o valor de config.MODO_ESTRITO.
        """
        self.modo_estrito = modo_estrito if modo_estrito is not None else config.MODO_ESTRITO
        self.campos_definicao = None
        self._carregar_definicao_campos()
    
    def _carregar_definicao_campos(self):
        """
        Carrega a definição dos campos do CSV para validação.
        """
        try:
            if os.path.exists(config.DEFINICAO_CAMPOS_CSV):
                # Tenta primeiro com o separador padrão
                separador = config.CSV_SEPARATOR
                try:
                    df_definicao = pd.read_csv(
                        config.DEFINICAO_CAMPOS_CSV, 
                        sep=separador, 
                        encoding='utf-8'
                    )
                    # Verifica se a leitura resultou em uma única coluna (separador incorreto)
                    if df_definicao.shape[1] <= 1:
                        # Tenta com vírgula
                        df_definicao = pd.read_csv(
                            config.DEFINICAO_CAMPOS_CSV, 
                            sep=",", 
                            encoding='utf-8'
                        )
                except Exception:
                    # Tenta com detecção automática
                    df_definicao = pd.read_csv(
                        config.DEFINICAO_CAMPOS_CSV, 
                        sep=None, 
                        engine='python', 
                        encoding='utf-8'
                    )
                
                # Cria o dicionário de definições dos campos
                # Campo 'nome_campo' pode estar com minúsculas ou maiúsculas
                nome_campo_col = 'nome_campo'
                if 'nome_campo' not in df_definicao.columns and 'NOME_CAMPO' in df_definicao.columns:
                    nome_campo_col = 'NOME_CAMPO'
                    
                self.campos_definicao = {}
                for _, row in df_definicao.iterrows():
                    if nome_campo_col in row:
                        self.campos_definicao[row[nome_campo_col]] = {
                            'tipo': row.get('tipo', 'texto'),
                            'obrigatorio': row.get('obrigatorio', 'N') == 'S'
                        }
                
                logger.info(f"Definição de campos carregada: {len(self.campos_definicao)} campos")
            else:
                logger.warning(f"Arquivo de definição de campos não encontrado: {config.DEFINICAO_CAMPOS_CSV}")
                self.campos_definicao = {}
        except Exception as e:
            logger.error(f"Erro ao carregar definição de campos: {str(e)}")
            self.campos_definicao = {}

    def _detectar_separador(self, caminho_arquivo, separador=None):
        """
        Detecta o separador do arquivo CSV usando csv.Sniffer.
        
        Args:
            caminho_arquivo: Caminho para o arquivo CSV.
            separador: Separador explicitamente definido (se houver).
            
        Returns:
            Separador detectado ou o separador explicitamente definido.
        """
        # Se um separador foi explicitamente definido, usa-o
        if separador is not None:
            return separador
            
        try:
            with open(caminho_arquivo, 'r', encoding='utf-8') as f:
                # Lê uma amostra do arquivo (primeiras linhas)
                amostra = f.read(4096)
                # Se a amostra é muito curta, lê um pouco mais
                if len(amostra) < 100 and not f.closed:
                    amostra += f.read(4096)
                
                sniffer = csv.Sniffer()
                # Detecta o dialeto (que inclui o separador)
                dialect = sniffer.sniff(amostra)
                separador_detectado = dialect.delimiter
                logger.info(f"Separador detectado pelo Sniffer: '{separador_detectado}'")
                return separador_detectado
        except csv.Error as e:
            logger.warning(f"Não foi possível detectar o separador automaticamente: {str(e)}")
            
            # Tenta identificar o separador mais provável inspecionando a primeira linha
            with open(caminho_arquivo, 'r', encoding='utf-8') as f:
                primeira_linha = f.readline().strip()
                
                # Conta ocorrências de possíveis separadores
                separadores_comuns = [',', ';', '\t', '|']
                contagem = {sep: primeira_linha.count(sep) for sep in separadores_comuns}
                
                # Seleciona o separador com mais ocorrências
                if max(contagem.values()) > 0:
                    separador_mais_frequente = max(contagem.items(), key=lambda x: x[1])[0]
                    logger.info(f"Usando separador mais frequente: '{separador_mais_frequente}'")
                    return separador_mais_frequente
            
            # Se não conseguir determinar, usa o padrão
            logger.info(f"Usando separador padrão: '{config.CSV_SEPARATOR}'")
            return config.CSV_SEPARATOR
        except Exception as e:
            logger.warning(f"Erro ao detectar separador: {str(e)}")
            return config.CSV_SEPARATOR
    
    def limpar_e_converter_float(self, valor_str):
        """
        Limpa e converte strings numéricas para float, suportando diferentes formatos.
        
        Args:
            valor_str: String com valor numérico em vários formatos possíveis.
            
        Returns:
            Float convertido ou o valor original se não for possível converter.
        """
        if not isinstance(valor_str, str):
            # Se já for número, retorna (ou converte para float se necessário)
            return float(valor_str) if valor_str is not None else 0.0

        # Remove espaços extras
        valor_str = valor_str.strip()
        # Remove símbolos de moeda comuns
        valor_str = re.sub(r"[R$€£]", "", valor_str).strip()
        
        # Salva o original para log em caso de erro
        original = valor_str
        
        try:
            # Caso simples: número inteiro ou decimal com ponto
            if re.match(r'^\d+$', valor_str):
                return int(valor_str)
            if re.match(r'^\d+\.\d+$', valor_str):
                return float(valor_str)
            
            # Para números com vírgula como decimal (formato brasileiro)
            if ',' in valor_str:
                # Remove pontos usados como separador de milhar
                if '.' in valor_str:
                    valor_limpo = valor_str.replace('.', '')
                else:
                    valor_limpo = valor_str
                # Troca a vírgula decimal por ponto
                valor_limpo = valor_limpo.replace(',', '.')
            # Se não há vírgula, assume que ponto é decimal (se houver)
            else:
                valor_limpo = valor_str

            # Remove espaços novamente após substituições
            valor_limpo = valor_limpo.strip()

            # Tenta a conversão final
            if valor_limpo:  # Evita float('')
                return float(valor_limpo)
            else:
                return 0.0
        except ValueError:
            logger.warning(f"Não foi possível converter '{original}' para float.")
            return valor_str  # Retorna o valor original em caso de falha
    
    def carregar_arquivo(self, caminho_arquivo=None, separador=None):
        """
        Carrega um arquivo CSV e converte para uma lista de dicionários.
        
        Args:
            caminho_arquivo: Caminho para o arquivo CSV. Se None, usa config.ENTREVISTAS_CSV.
            separador: Separador do CSV. Se None, usa config.CSV_SEPARATOR.
            
        Returns:
            Lista de dicionários, cada um representando uma linha do CSV.
            
        Raises:
            ArquivoNaoEncontradoError: Se o arquivo não for encontrado.
            FormatoArquivoInvalidoError: Se o formato do arquivo for inválido.
        """
        caminho_arquivo = caminho_arquivo or config.ENTREVISTAS_CSV
        
        if not os.path.exists(caminho_arquivo):
            logger.error(f"Arquivo não encontrado: {caminho_arquivo}")
            raise ArquivoNaoEncontradoError(f"Arquivo não encontrado: {caminho_arquivo}")
        
        try:
            logger.info(f"Carregando arquivo CSV: {caminho_arquivo}")
            
            # Detecta o separador automaticamente se não for especificado
            separador_final = self._detectar_separador(caminho_arquivo, separador)
            logger.info(f"Usando separador '{separador_final}' para ler o arquivo CSV")
            
            # Tenta ler o arquivo com o separador detectado
            try:
                df = pd.read_csv(caminho_arquivo, sep=separador_final, encoding='utf-8')
            except Exception as e:
                logger.warning(f"Erro ao ler CSV com separador '{separador_final}': {str(e)}")
                # Tenta com detecção automática como fallback
                df = pd.read_csv(caminho_arquivo, sep=None, engine='python', encoding='utf-8')
            
            # Verificação pós-leitura para validar se o parsing foi correto
            if df.shape[1] == 1:
                # Se só temos uma coluna, o separador está errado
                logger.warning(f"Possível problema de separador: leu apenas uma coluna com '{separador_final}'")
                
                # Tenta com cada separador comum até encontrar um que funcione
                for sep in [',', ';', '\t', '|']:
                    try:
                        temp_df = pd.read_csv(caminho_arquivo, sep=sep, encoding='utf-8')
                        if temp_df.shape[1] > 1:
                            df = temp_df
                            logger.info(f"Leitura bem-sucedida com separador '{sep}': {df.shape[1]} colunas")
                            break
                    except Exception:
                        continue
                
                # Se ainda tiver apenas uma coluna, tenta com engine='python'
                if df.shape[1] == 1:
                    logger.info("Tentando leitura com separador automático do pandas")
                    df = pd.read_csv(caminho_arquivo, sep=None, engine='python', encoding='utf-8')
                    
                    if df.shape[1] > 1:
                        logger.info(f"Leitura bem-sucedida com separador automático: {df.shape[1]} colunas")
                    else:
                        logger.warning("Mesmo com detecção automática, só foi possível ler uma coluna")
            
            logger.info(f"Arquivo CSV carregado: {len(df)} registros com {df.shape[1]} colunas")
            
            # Converte DataFrame para lista de dicionários
            registros = df.to_dict(orient='records')
            
            # Valida e processa os registros
            registros_processados = self._processar_registros(registros)
            logger.info(f"Dados carregados para o contexto: {list(registros_processados[0].keys())}")
            
            return registros_processados
            
        except pd.errors.ParserError as e:
            logger.error(f"Erro ao parsear CSV: {str(e)}")
            raise FormatoArquivoInvalidoError(f"Formato do arquivo CSV inválido: {str(e)}")
        except Exception as e:
            logger.error(f"Erro ao processar CSV: {str(e)}")
            raise FormatoArquivoInvalidoError(f"Erro ao processar CSV: {str(e)}")
    
    def _processar_registros(self, registros):
        """
        Processa e valida os registros do CSV.
        
        Args:
            registros: Lista de dicionários representando registros do CSV.
            
        Returns:
            Lista de dicionários processados e validados.
        """
        resultados = []
        
        for i, registro in enumerate(registros):
            try:
                # Processa valores nulos
                registro_processado = self._processar_valores_nulos(registro)
                
                # Valida tipos de dados
                if self.campos_definicao:
                    registro_processado = self._validar_tipos_dados(registro_processado)
                
                resultados.append(registro_processado)
                logger.debug(f"Registro {i+1} processado com sucesso")
            except Exception as e:
                logger.warning(f"Erro no registro {i+1}: {str(e)}")
                if self.modo_estrito:
                    raise DadosInvalidosError(f"Registro {i+1} inválido: {str(e)}")
                else:
                    # Em modo não-estrito, adiciona registro original mesmo com erros
                    resultados.append(registro)
                    logger.warning(f"Registro {i+1} adicionado com erros (modo não-estrito)")
        
        return resultados
    
    def _processar_valores_nulos(self, registro):
        """
        Processa valores nulos no registro.
        
        Args:
            registro: Dicionário representando um registro do CSV.
            
        Returns:
            Dicionário com valores nulos tratados.
        """
        resultado = {}
        
        for chave, valor in registro.items():
            # Verifica se o valor é NaN ou None
            if pd.isna(valor):
                # Se temos definição do campo e sabemos seu tipo
                if self.campos_definicao and chave in self.campos_definicao:
                    tipo = self.campos_definicao[chave]['tipo'].lower()
                    
                    # Trata de acordo com o tipo
                    if tipo in ['int', 'inteiro', 'integer']:
                        resultado[chave] = 0
                    elif tipo in ['float', 'decimal', 'numero', 'number']:
                        resultado[chave] = 0.0
                    elif tipo in ['data', 'date']:
                        resultado[chave] = None
                    else:  # texto ou outro tipo
                        resultado[chave] = ""
                else:
                    # Se não temos definição, assume string vazia para campos de texto
                    if 'data' in chave.lower():
                        resultado[chave] = None
                    elif any(termo in chave.lower() for termo in ['valor', 'numero', 'bruto', 'qtd']):
                        resultado[chave] = 0.0
                    else:
                        resultado[chave] = ""
            else:
                resultado[chave] = valor
        
        return resultado
    
    def _validar_tipos_dados(self, registro):
        """
        Valida os tipos de dados do registro conforme definição.
        
        Args:
            registro: Dicionário representando um registro do CSV.
            
        Returns:
            Dicionário com valores convertidos para os tipos corretos.
        """
        resultado = {}
        erros = []
        
        for chave, valor in registro.items():
            # Se não temos definição para o campo, mantém o valor original
            if chave not in self.campos_definicao:
                resultado[chave] = valor
                continue
            
            # Verifica se campo obrigatório está preenchido
            if self.campos_definicao[chave]['obrigatorio'] and (valor is None or valor == ""):
                erros.append(f"Campo obrigatório não preenchido: {chave}")
                # Em modo não-estrito, mantém o valor original
                resultado[chave] = valor
                continue
            
            # Se valor é None ou vazio e não é obrigatório, mantém como está
            if valor is None or valor == "":
                resultado[chave] = valor
                continue
            
            # Converte para o tipo correto
            tipo = self.campos_definicao[chave]['tipo'].lower()
            try:
                if tipo in ['int', 'inteiro', 'integer']:
                    if isinstance(valor, str):
                        valor_conv = self.limpar_e_converter_float(valor)
                        resultado[chave] = int(valor_conv) if isinstance(valor_conv, (int, float)) else int(valor)
                    else:
                        resultado[chave] = int(valor)
                elif tipo in ['float', 'decimal', 'numero', 'number']:
                    if isinstance(valor, str):
                        resultado[chave] = self.limpar_e_converter_float(valor)
                    else:
                        resultado[chave] = float(valor)
                elif tipo in ['data', 'date']:
                    # Tenta alguns formatos comuns de data
                    for fmt in ['%d/%m/%Y', '%Y-%m-%d', '%d-%m-%Y', '%d.%m.%Y']:
                        try:
                            resultado[chave] = datetime.strptime(valor, fmt)
                            break
                        except ValueError:
                            continue
                    else:
                        # Se nenhum formato funcionar
                        erros.append(f"Formato de data inválido para o campo {chave}: {valor}")
                        resultado[chave] = valor
                else:  # texto ou outro tipo
                    resultado[chave] = str(valor)
            except Exception as e:
                erros.append(f"Erro na conversão do campo {chave}: {str(e)}")
                resultado[chave] = valor
        
        # Em modo estrito, lança exceção se houver erros
        if erros and self.modo_estrito:
            raise DadosInvalidosError("\n".join(erros))
        
        return resultado 