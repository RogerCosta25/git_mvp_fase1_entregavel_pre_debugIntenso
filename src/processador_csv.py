"""
Processador de arquivos CSV para o sistema de peticionamento.
"""
import os
import sys
import pandas as pd
import csv
import re
from datetime import datetime
from typing import Dict, Any, List, Optional, Hashable # <--- ADICIONADO Hashable

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
    
    def __init__(self, modo_estrito: Optional[bool] = None):
        self.modo_estrito = modo_estrito if modo_estrito is not None else config.MODO_ESTRITO
        self.campos_definicao: Dict[str, Dict[str, Any]] = {}
        self._carregar_definicao_campos()
    
    def _carregar_definicao_campos(self):
        # ... (código como na sua última versão, garantindo que self.campos_definicao é sempre um dict)
        try:
            if os.path.exists(config.DEFINICAO_CAMPOS_CSV):
                separador = config.CSV_SEPARATOR
                try:
                    df_definicao = pd.read_csv(
                        config.DEFINICAO_CAMPOS_CSV, 
                        sep=separador, 
                        encoding='utf-8-sig'
                    )
                    if df_definicao.shape[1] <= 1 and separador != ',':
                        df_definicao = pd.read_csv(
                            config.DEFINICAO_CAMPOS_CSV, 
                            sep=",", 
                            encoding='utf-8-sig'
                        )
                except Exception:
                    df_definicao = pd.read_csv(
                        config.DEFINICAO_CAMPOS_CSV, 
                        sep=None, 
                        engine='python', 
                        encoding='utf-8-sig'
                    )
                
                nome_campo_col = next((col for col in ['nome_campo', 'NOME_CAMPO'] if col in df_definicao.columns), None)
                tipo_col = next((col for col in ['tipo_dado_programacao', 'tipo'] if col in df_definicao.columns), 'tipo_dado_programacao')
                obrigatorio_col = next((col for col in ['obrigatorio_quando_ativo', 'obrigatorio'] if col in df_definicao.columns), 'obrigatorio_quando_ativo')

                if nome_campo_col:
                    temp_campos_definicao = {}
                    for _, row in df_definicao.iterrows():
                        nome_campo_val = row.get(nome_campo_col)
                        if pd.notna(nome_campo_val):
                            temp_campos_definicao[str(nome_campo_val)] = {
                                'tipo': str(row.get(tipo_col, 'texto')).lower(),
                                'obrigatorio': str(row.get(obrigatorio_col, 'N')).strip().lower() in ['s', 'sim', 'true', '1']
                            }
                    self.campos_definicao = temp_campos_definicao
                    logger.info(f"Definição de campos carregada: {len(self.campos_definicao)} campos")
                else:
                    logger.warning(f"Coluna 'nome_campo' (ou 'NOME_CAMPO') não encontrada em {config.DEFINICAO_CAMPOS_CSV}.")
                    self.campos_definicao = {}
            else:
                logger.warning(f"Arquivo de definição de campos não encontrado: {config.DEFINICAO_CAMPOS_CSV}")
                self.campos_definicao = {}
        except Exception as e:
            logger.error(f"Erro ao carregar definição de campos: {str(e)}", exc_info=True)
            self.campos_definicao = {}

    def _detectar_separador(self, caminho_arquivo: str, separador: Optional[str] = None) -> str:
        if separador is not None:
            return separador
        try:
            with open(caminho_arquivo, 'r', encoding='utf-8-sig') as f:
                amostra = f.read(4096)
            sniffer = csv.Sniffer()
            dialect = sniffer.sniff(amostra, delimiters=',;\t|') 
            logger.info(f"Separador detectado pelo Sniffer: '{dialect.delimiter}'")
            return dialect.delimiter
        except csv.Error as e:
            logger.warning(f"Sniffer não pôde determinar o delimitador: {str(e)}. Tentando contagem manual.")
            try:
                with open(caminho_arquivo, 'r', encoding='utf-8-sig') as f:
                    primeira_linha = f.readline().strip()
                
                separadores_comuns_str = ';,|\t|' # String de delimitadores para iteração
                contagem: Dict[str, int] = {sep_cand: primeira_linha.count(sep_cand) for sep_cand in separadores_comuns_str}
                
                if any(v > 0 for v in contagem.values()):
                    # CORREÇÃO para max: Usar items() para obter pares chave-valor e então pegar a chave.
                    # Ou, mais simples, iterar sobre as chaves do dicionário se 'key' espera uma função que opera na chave.
                    # A forma `max(contagem, key=contagem.get)` é idiomática.
                    # O Pylance pode estar confuso com a tipagem de `contagem.get`.
                    # Vamos tentar ser mais explícitos ou usar uma alternativa se o Pylance insistir.
                    # Uma forma alternativa, embora mais verbosa:
                    # max_count = -1
                    # separador_mais_frequente = config.CSV_SEPARATOR # Default
                    # for sep_cand, count_val in contagem.items():
                    #     if count_val > max_count:
                    #         max_count = count_val
                    #         separador_mais_frequente = sep_cand
                    # if max_count == 0: # Nenhum dos separadores comuns foi encontrado mais de uma vez
                    #      logger.warning(f"Nenhum separador comum dominante. Usando padrão: '{config.CSV_SEPARATOR}'")
                    #      return config.CSV_SEPARATOR
                    
                    # Tentando a forma idiomática novamente, Pylance pode precisar de mais contexto ou uma versão diferente.
                    # Se o erro persistir, a alternativa acima pode ser usada.
                    separador_mais_frequente = max(contagem, key=lambda k: contagem[k]) # Lambda explícito para o get
                    logger.info(f"Usando separador mais frequente da primeira linha: '{separador_mais_frequente}'")
                    return separador_mais_frequente
                else:
                    logger.warning("Nenhum separador comum encontrado na primeira linha. Usando padrão de config.")
                    return config.CSV_SEPARATOR
            except Exception as e_inner:
                logger.error(f"Erro ao tentar contagem manual de separadores: {e_inner}. Usando padrão de config.")
                return config.CSV_SEPARATOR
        except Exception as e_outer:
            logger.error(f"Erro inesperado na detecção de separador: {e_outer}. Usando padrão de config.")
            return config.CSV_SEPARATOR
    
    def limpar_e_converter_float(self, valor_str: Any) -> Any:
        # ... (código como na sua última versão) ...
        if not isinstance(valor_str, str):
            try:
                return float(valor_str) if valor_str is not None else 0.0
            except (ValueError, TypeError):
                 logger.warning(f"Valor não string '{valor_str}' não pôde ser convertido para float diretamente.")
                 return valor_str 

        original = valor_str
        valor_limpo = valor_str.strip()
        valor_limpo = re.sub(r"[R$\s]", "", valor_limpo) 
        
        try:
            if not valor_limpo: return 0.0 
            if ',' in valor_limpo and '.' in valor_limpo:
                if valor_limpo.rfind('.') < valor_limpo.rfind(','): 
                    valor_processado = valor_limpo.replace('.', '').replace(',', '.')
                else: 
                    valor_processado = valor_limpo.replace(',', '')
            elif ',' in valor_limpo: 
                valor_processado = valor_limpo.replace(',', '.')
            else: 
                valor_processado = valor_limpo
            return float(valor_processado)
        except ValueError:
            logger.warning(f"Não foi possível converter '{original}' para float após limpeza e processamento.")
            return original
    
    def carregar_arquivo(self, caminho_arquivo: Optional[str] = None, separador: Optional[str] = None) -> List[Dict[str, Any]]:
        caminho_arquivo_final = caminho_arquivo or config.ENTREVISTAS_CSV
        if not os.path.exists(caminho_arquivo_final):
            logger.error(f"Arquivo CSV não encontrado: {caminho_arquivo_final}")
            raise ArquivoNaoEncontradoError(f"Arquivo CSV não encontrado: {caminho_arquivo_final}")
        
        try:
            logger.info(f"Carregando arquivo CSV: {caminho_arquivo_final}")
            separador_final = self._detectar_separador(caminho_arquivo_final, separador)
            logger.info(f"Usando separador '{separador_final}' para ler o arquivo CSV")
            
            df = pd.read_csv(caminho_arquivo_final, sep=separador_final, encoding='utf-8-sig', dtype=str, keep_default_na=False, na_filter=False)
            
            if df.empty:
                logger.warning(f"Arquivo CSV '{caminho_arquivo_final}' está vazio.")
                return []
            
            logger.info(f"Arquivo CSV carregado: {len(df)} registros com {df.shape[1]} colunas")
            
            # CORREÇÃO de tipo para a chamada de _processar_registros
            # df.to_dict(orient='records') retorna List[Dict[str, Any]] porque os valores são mistos inicialmente.
            # Mas como lemos com dtype=str, os valores serão strings.
            # O Pylance pode inferir Any para os valores se não for explícito.
            # Vamos garantir que as chaves são strings.
            registros_lidos: List[Dict[str, str]] = []
            for record in df.to_dict(orient='records'):
                registros_lidos.append({str(k): str(v) for k, v in record.items()})

            registros_processados = self._processar_registros(registros_lidos) # <--- Linha 177
            
            if registros_processados:
                 logger.info(f"Amostra das chaves do primeiro registro processado: {list(registros_processados[0].keys())[:10]}")
            return registros_processados
        except Exception as e:
            logger.error(f"Erro crítico ao carregar ou processar CSV '{caminho_arquivo_final}': {str(e)}", exc_info=True)
            raise FormatoArquivoInvalidoError(f"Erro ao processar CSV: {str(e)}")
    
    # Assinatura de _processar_registros já espera List[Dict[str, str]]
    # e retorna List[Dict[str, Any]], o que está correto.
    def _processar_registros(self, registros: List[Dict[str, str]]) -> List[Dict[str, Any]]:
        # ... (código como na sua última versão) ...
        resultados = []
        for i, registro_linha_str in enumerate(registros):
            registro_convertido_atual: Dict[str, Any] = {}
            try:
                for chave_original, valor_original_str in registro_linha_str.items():
                    chave_campo = str(chave_original).strip() 
                    
                    valor_str_processar = "" 
                    if valor_original_str is not None:
                        temp_val = str(valor_original_str).strip()
                        if temp_val.lower() not in ['nan', 'none', '<na>']: 
                            valor_str_processar = temp_val
                    
                    registro_convertido_atual[chave_campo] = self._validar_e_converter_valor_individual(chave_campo, valor_str_processar, i)
                resultados.append(registro_convertido_atual)
            except DadosInvalidosError as die:
                logger.warning(f"Erro de dados inválidos no registro {i+1}: {str(die)}. Modo estrito: {self.modo_estrito}")
                if self.modo_estrito: raise
                resultados.append(registro_convertido_atual) 
            except Exception as e_reg_proc:
                logger.error(f"Erro inesperado ao processar registro {i+1}: {str(e_reg_proc)}", exc_info=True)
                if self.modo_estrito: raise DadosInvalidosError(f"Erro inesperado no registro {i+1}: {str(e_reg_proc)}")
                resultados.append(registro_linha_str) 
        return resultados

    def _validar_e_converter_valor_individual(self, chave: str, valor_str_limpo: str, num_registro: int) -> Any:
        # ... (código como na sua última versão) ...
        if not isinstance(self.campos_definicao, dict): 
            self.campos_definicao = {} 

        definicao = self.campos_definicao.get(chave)
        
        tipo_esperado = 'texto' 
        obrigatorio = False
        if definicao:
            tipo_esperado = definicao.get('tipo', 'texto').lower()
            obrigatorio = definicao.get('obrigatorio', False)

        if not valor_str_limpo: 
            if obrigatorio:
                msg_erro_obr = f"Registro {num_registro+1}: Campo obrigatório '{chave}' está vazio."
                if self.modo_estrito: raise DadosInvalidosError(msg_erro_obr)
                logger.warning(msg_erro_obr) 
            
            if tipo_esperado in ['int', 'inteiro', 'integer']: return 0
            if tipo_esperado in ['float', 'decimal', 'numero', 'number', 'moeda', 'dinheiro']: return 0.0
            if tipo_esperado in ['data', 'date']: return None
            return "" 

        try:
            if tipo_esperado in ['int', 'inteiro', 'integer']:
                val_float = self.limpar_e_converter_float(valor_str_limpo)
                if isinstance(val_float, (int, float)): return int(val_float)
                raise ValueError("Valor não pôde ser convertido para numérico antes de int.")
            elif tipo_esperado in ['float', 'decimal', 'numero', 'number', 'moeda', 'dinheiro']:
                return self.limpar_e_converter_float(valor_str_limpo)
            elif tipo_esperado in ['data', 'date']:
                for fmt in ('%d/%m/%Y', '%Y-%m-%d', '%d-%m-%Y', '%Y/%m/%d', '%d.%m.%Y', '%m/%d/%Y', '%d%m%Y'):
                    try: return datetime.strptime(valor_str_limpo, fmt).strftime('%d/%m/%Y')
                    except ValueError: continue
                raise ValueError(f"Formato de data '{valor_str_limpo}' não reconhecido para campo '{chave}'.")
            elif tipo_esperado in ['bool', 'booleano', 'logico']:
                return valor_str_limpo.lower() in ['sim', 'true', '1', 's', 'yes', 'verdadeiro', 'v']
            else:  
                return str(valor_str_limpo)
        except ValueError as e: 
            msg_erro_conv = f"Registro {num_registro+1}: Erro ao converter campo '{chave}' (valor: '{valor_str_limpo}') para tipo '{tipo_esperado}'. Detalhe: {e}"
            logger.warning(msg_erro_conv)
            if self.modo_estrito: raise DadosInvalidosError(msg_erro_conv)
            return valor_str_limpo 
        except Exception as e_inesperado: 
            msg_erro_inesperado = f"Registro {num_registro+1}: Exceção inesperada ao converter campo '{chave}' (valor: '{valor_str_limpo}') para tipo '{tipo_esperado}'. Erro: {e_inesperado}"
            logger.error(msg_erro_inesperado, exc_info=True)
            if self.modo_estrito: raise DadosInvalidosError(msg_erro_inesperado)
            return valor_str_limpo