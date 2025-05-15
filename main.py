#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Script principal do sistema de peticionamento.

Este script carrega os dados de um arquivo CSV ou JSON, processa as regras e gera o documento final.
Uso:
    python main.py --template <arquivo_template> --csv <arquivo_csv> --saida <arquivo_output>
    python main.py --template <arquivo_template> --dados <arquivo_json> --saida <arquivo_output>
"""

import os
import sys
import json
import argparse
import logging
from typing import Dict, Any, Optional, List, Union, cast

# Adiciona o diretório atual ao path
# Garante que o diretório do script seja o primeiro no sys.path para priorizar módulos locais.
# Isso é útil se o script for chamado de outros diretórios.
# No entanto, se config.py e src/ estão na mesma pasta que main.py,
# as importações diretas (import config, from src...) geralmente funcionam
# sem modificar sys.path explicitamente, desde que o diretório atual
# esteja no PYTHONPATH ou seja o diretório de trabalho.
# Manter esta linha não deve causar problemas e pode ajudar em alguns cenários de execução.
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))


# Importa os módulos do sistema
import config # Carrega as configurações globais do projeto
from src.motor_regras import MotorRegras # Responsável por carregar e avaliar regras
from src.documento_processor import DocumentoProcessor # Responsável por processar o template DOCX
from src.processador_csv import ProcessadorCSV # Responsável por processar o arquivo CSV
from src.logger import logger, configurar_logger # Módulo de logging customizado
from src.exceptions import ( # Exceções customizadas para tratamento de erros específico
    ArquivoNaoEncontradoError,
    FormatoArquivoInvalidoError,
    TemplateNaoEncontradoError,
    ProcessamentoDocumentoError,
    DadosInvalidosError
)

def carregar_dados_csv(arquivo_csv: str) -> Dict[str, Any]:
    """
    Carrega os dados de um arquivo CSV usando o ProcessadorCSV.
    
    Args:
        arquivo_csv: Caminho para o arquivo CSV.
        
    Returns:
        Dicionário com os dados carregados (primeiro registro do CSV).
        
    Raises:
        ArquivoNaoEncontradoError: Se o arquivo CSV não for encontrado.
        FormatoArquivoInvalidoError: Se o formato do CSV for inválido.
        DadosInvalidosError: Se os dados no CSV forem inválidos.
    """
    if not os.path.exists(arquivo_csv):
        logger.error(f"Arquivo CSV de dados não encontrado: {arquivo_csv}")
        raise ArquivoNaoEncontradoError(f"Arquivo CSV não encontrado: {arquivo_csv}")
    
    try:
        # Inicializa o processador CSV
        processador = ProcessadorCSV()
        
        # Carrega o arquivo CSV
        registros = processador.carregar_arquivo(arquivo_csv)
        
        # Verifica se há pelo menos um registro
        if not registros or len(registros) == 0:
            raise DadosInvalidosError("Arquivo CSV não contém registros.")
        
        # Usa o primeiro registro como dados para o documento
        dados = registros[0]
        
        logger.info(f"Dados carregados com sucesso do arquivo CSV: {arquivo_csv}")
        logger.debug(f"Total de campos carregados dos dados: {len(dados)}")
        return dados
    except Exception as e:
        logger.error(f"Erro ao processar arquivo CSV '{arquivo_csv}': {str(e)}")
        if isinstance(e, (ArquivoNaoEncontradoError, FormatoArquivoInvalidoError, DadosInvalidosError)):
            raise
        raise FormatoArquivoInvalidoError(f"Erro ao processar arquivo CSV '{arquivo_csv}': {str(e)}")

def carregar_dados_json(arquivo_json: str) -> Dict[str, Any]:
    """
    Carrega os dados de um arquivo JSON.
    
    Args:
        arquivo_json: Caminho para o arquivo JSON.
        
    Returns:
        Dicionário com os dados carregados.
        
    Raises:
        ArquivoNaoEncontradoError: Se o arquivo JSON não for encontrado.
        FormatoArquivoInvalidoError: Se o arquivo não for um JSON válido ou ocorrer outro erro de leitura.
    """
    if not os.path.exists(arquivo_json):
        logger.error(f"Arquivo JSON de dados não encontrado: {arquivo_json}")
        raise ArquivoNaoEncontradoError(f"Arquivo JSON não encontrado: {arquivo_json}")
    
    try:
        with open(arquivo_json, 'r', encoding='utf-8') as f:
            dados = json.load(f)
        
        logger.info(f"Dados carregados com sucesso do arquivo JSON: {arquivo_json}")
        logger.debug(f"Total de chaves de primeiro nível carregadas dos dados: {len(dados)}")
        return dados
    except json.JSONDecodeError as e:
        logger.error(f"Erro ao decodificar o arquivo JSON '{arquivo_json}': {str(e)}")
        raise FormatoArquivoInvalidoError(f"Formato inválido do arquivo JSON '{arquivo_json}': {str(e)}")
    except Exception as e:
        logger.error(f"Erro inesperado ao carregar dados do arquivo '{arquivo_json}': {str(e)}")
        raise FormatoArquivoInvalidoError(f"Erro ao carregar dados do arquivo '{arquivo_json}': {str(e)}")

def main() -> int:
    """
    Função principal do script.
    Configura o ambiente, processa os argumentos da linha de comando,
    orquestra o carregamento de dados, a avaliação de regras e a geração do documento.
    
    Returns:
        Código de saída (0 para sucesso, 1 para erro).
    """
    # Configura o parser de argumentos da linha de comando
    parser = argparse.ArgumentParser(description='Processa templates de documentos DOCX para peticionamento jurídico.')
    parser.add_argument('--template', required=False, help='Caminho para o arquivo de template DOCX. Usa o padrão de config.py se não fornecido.')
    parser.add_argument('--csv', required=False, help='Caminho para o arquivo CSV com os dados da entrevista. Prioridade sobre JSON se ambos forem fornecidos.')
    parser.add_argument('--dados', required=False, help='Caminho para o arquivo JSON com os dados da entrevista. Usado apenas se --csv não for fornecido.')
    parser.add_argument('--saida', required=False, help='Caminho para salvar o documento DOCX processado. Gera nome automático em config.OUTPUT_DIR se não fornecido.')
    parser.add_argument('--debug', action='store_true', help='Ativa modo de depuração com logs mais detalhados (nível DEBUG).')
    parser.add_argument('--usar-modelo-relacional', action='store_true', help='Força o uso do modelo relacional refatorado (atualmente, o padrão já tenta usá-lo).')
    parser.add_argument('--primeiro-registro', action='store_true', help='Processa apenas o primeiro registro do CSV.')
    
    args = parser.parse_args()
    
    # Importa o novo configurador de logger
    try:
        from src.utils.logger_config import configurar_logger as novo_configurar_logger
        nivel_log = "DEBUG" if args.debug else config.LOG_LEVEL
        # Usando a função configurar_logger diretamente do módulo logger importado
        configurar_logger(nivel_log)
    except ImportError:
        # Fallback para o logger antigo se o novo não estiver disponível
        nivel_log = "DEBUG" if args.debug else config.LOG_LEVEL
        configurar_logger(nivel_log)
    
    logger.info("Sistema de Peticionamento Iniciado.")
    logger.debug(f"Argumentos recebidos: {args}")

    # Determina os caminhos para os arquivos de template, dados e saída
    template_path = args.template or config.TEMPLATE_DOCX
    
    # Determina a fonte de dados: CSV tem prioridade sobre JSON
    fonte_dados_csv = args.csv or config.ENTREVISTAS_CSV
    fonte_dados_json = args.dados or config.DADOS_JSON
    
    # Verifica se os arquivos existem e decide qual usar
    usar_csv = os.path.exists(fonte_dados_csv)
    usar_json = os.path.exists(fonte_dados_json)
    
    if not usar_csv and not usar_json:
        logger.error("Nenhuma fonte de dados válida encontrada. Verifique os arquivos CSV e JSON.")
        print("\nERRO: Nenhuma fonte de dados válida encontrada. Verifique os arquivos CSV e JSON.")
        return 1
    
    # Se não for especificado um caminho de saída, gera um padrão
    if args.saida:
        output_path_base = args.saida
    else:
        # Gera um nome de arquivo de saída padrão no diretório de output configurado
        nome_base_template = os.path.splitext(os.path.basename(template_path))[0]
        output_path_base = os.path.join(config.OUTPUT_DIR, f"{nome_base_template}_processado")
    
    # Bloco principal de execução com tratamento de exceções
    try:
        logger.info("Iniciando processamento do documento...")
        logger.info(f"Caminho do Template: {os.path.abspath(template_path)}")
        
        # Inicializa o MotorRegras
        motor_regras = MotorRegras(usar_modelo_relacional=True)
        
        # Carrega as regras condicionais
        motor_regras.carregar_regras()
        
        # MODIFICAÇÃO: Processamento para múltiplos registros
        documentos_gerados = []
        
        if usar_csv:
            logger.info(f"Utilizando arquivo CSV: {os.path.abspath(fonte_dados_csv)}")
            
            # Carrega todos os registros do CSV
            processador_csv = ProcessadorCSV()
            registros = processador_csv.carregar_arquivo(fonte_dados_csv)
            
            if not registros:
                logger.error(f"Nenhum registro encontrado no arquivo CSV: {fonte_dados_csv}")
                return 1
            
            logger.info(f"Carregados {len(registros)} registros do CSV")
            
            # Determina quantos registros processar
            registros_a_processar = registros
            if args.primeiro_registro:
                registros_a_processar = [registros[0]]
                logger.info("Processando apenas o primeiro registro do CSV conforme solicitado")
            
            # Processa cada registro
            for i, dados_entrevista in enumerate(registros_a_processar):
                # Gera nome do arquivo de saída único para este registro
                if len(registros_a_processar) > 1:
                    # Se temos múltiplos registros, adiciona índice ao nome do arquivo
                    nome_base, ext = os.path.splitext(output_path_base)
                    output_path = f"{nome_base}_{i+1}{ext}"
                else:
                    # Se é um único registro, usa o nome base diretamente
                    if not output_path_base.endswith('.docx'):
                        output_path = f"{output_path_base}.docx"
                    else:
                        output_path = output_path_base
                
                logger.info(f"Processando registro {i+1}/{len(registros_a_processar)}")
                
                # Avalia seções ativas para este registro
                secoes_ativas = motor_regras.avaliar_secoes_ativas(dados_entrevista)
                logger.info(f"Seções ativas determinadas: {secoes_ativas if secoes_ativas else 'Nenhuma'}")
                
                # Processa o documento para este registro
                processador_documento = DocumentoProcessor(motor_regras=motor_regras)
                caminho_documento_gerado = processador_documento.processar_documento(
                    template_path=template_path,
                    dados=dados_entrevista,
                    secoes_ativas=secoes_ativas,
                    output_path=output_path
                )
                
                # Adiciona à lista de documentos gerados
                documentos_gerados.append({
                    'caminho': caminho_documento_gerado,
                    'estatisticas': processador_documento.obter_estatisticas()
                })
                
                logger.info(f"Documento para registro {i+1} salvo em: {os.path.abspath(caminho_documento_gerado)}")
        else:
            # Processamento para JSON (único registro)
            logger.info(f"Utilizando arquivo JSON: {os.path.abspath(fonte_dados_json)}")
            dados_entrevista = carregar_dados_json(fonte_dados_json)
            
            # Determina o nome do arquivo de saída
            if not output_path_base.endswith('.docx'):
                output_path = f"{output_path_base}.docx"
            else:
                output_path = output_path_base
            
            # Avalia seções ativas
            secoes_ativas = motor_regras.avaliar_secoes_ativas(dados_entrevista)
            logger.info(f"Seções ativas determinadas: {secoes_ativas if secoes_ativas else 'Nenhuma'}")
            
            # Processa o documento
            processador_documento = DocumentoProcessor(motor_regras=motor_regras)
            caminho_documento_gerado = processador_documento.processar_documento(
                template_path=template_path,
                dados=dados_entrevista,
                secoes_ativas=secoes_ativas,
                output_path=output_path
            )
            
            # Adiciona à lista de documentos gerados
            documentos_gerados.append({
                'caminho': caminho_documento_gerado,
                'estatisticas': processador_documento.obter_estatisticas()
            })
            
            logger.info(f"Documento salvo em: {os.path.abspath(caminho_documento_gerado)}")
        
        # Mostra um resumo dos documentos gerados
        logger.info(f"Processamento concluído. {len(documentos_gerados)} documento(s) gerado(s).")
        for i, doc in enumerate(documentos_gerados):
            logger.info(f"Documento {i+1}: {os.path.abspath(doc['caminho'])}")
            estatisticas = doc['estatisticas']
            if estatisticas:
                logger.info(f"  - Status: {estatisticas.get('status', 'N/A')}")
                logger.info(f"  - Completude: {estatisticas.get('porcentagem_completude', 0):.2f}%")
                logger.info(f"  - Campos substituídos: {estatisticas.get('total_campos_substituidos', 0)}/{estatisticas.get('total_campos_encontrados', 0)}")
                
                # Verifica se há campos obrigatórios ausentes
                if estatisticas.get('total_campos_obrigatorios_ausentes', 0) > 0:
                    logger.warning(f"  - ATENÇÃO: {estatisticas.get('total_campos_obrigatorios_ausentes', 0)} campos obrigatórios ausentes!")
        
        # Saída para o usuário no terminal
        print(f"\nProcessamento concluído com sucesso! {len(documentos_gerados)} documento(s) gerado(s):")
        for i, doc in enumerate(documentos_gerados):
            print(f"  {i+1}. {os.path.abspath(doc['caminho'])}")
        
        return 0  # Retorna sucesso
        
    except ArquivoNaoEncontradoError as e:
        logger.error(f"Arquivo não encontrado: {str(e)}")
        print(f"\nERRO: {str(e)}")
        return 1
    except FormatoArquivoInvalidoError as e:
        logger.error(f"Formato de arquivo inválido: {str(e)}")
        print(f"\nERRO: {str(e)}")
        return 1
    except TemplateNaoEncontradoError as e:
        logger.error(f"Template não encontrado: {str(e)}")
        print(f"\nERRO: {str(e)}")
        return 1
    except ProcessamentoDocumentoError as e:
        logger.error(f"Erro no processamento do documento: {str(e)}")
        print(f"\nERRO: {str(e)}")
        return 1
    except DadosInvalidosError as e:
        logger.error(f"Dados inválidos: {str(e)}")
        print(f"\nERRO: {str(e)}")
        return 1
    except Exception as e:
        logger.exception(f"Erro inesperado: {str(e)}")
        print(f"\nERRO INESPERADO: {str(e)}")
        
        # Em modo debug, mostra o traceback completo
        if args.debug:
            import traceback
            traceback.print_exc()
            
        return 1

if __name__ == "__main__":
    sys.exit(main())