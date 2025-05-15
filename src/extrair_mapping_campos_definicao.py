#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Script para extrair o mapping de campos de definição do CSV para JSON.

Este script lê o arquivo CamposDefinicao.csv e gera um arquivo mapping_campos_definicao.json
que contém a estrutura de todos os campos, suas propriedades, validações e dependências.
"""

import os
import sys
import json
import csv
import argparse
from typing import Dict, List, Any, Optional

# Adiciona o diretório pai ao path para importar módulos
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import config

def parse_csv(caminho_csv: str) -> List[Dict[str, str]]:
    """
    Lê o arquivo CSV e retorna uma lista de dicionários, um por linha.
    
    Args:
        caminho_csv: Caminho para o arquivo CSV
        
    Returns:
        Lista de dicionários, onde cada dicionário representa uma linha do CSV
        
    Raises:
        FileNotFoundError: Se o arquivo não for encontrado
        Exception: Para outros erros ao processar o CSV
    """
    rows = []
    try:
        with open(caminho_csv, 'r', encoding='utf-8-sig') as f:
            reader = csv.DictReader(f, delimiter=';')
            for row in reader:
                rows.append({k.strip(): v.strip() if v else v for k, v in row.items()})
        return rows
    except FileNotFoundError:
        print(f"Arquivo não encontrado: {caminho_csv}")
        raise
    except Exception as e:
        print(f"Erro ao processar CSV: {str(e)}")
        raise

def extrair_propriedades_campo(campo: Dict[str, str]) -> Dict[str, Any]:
    """
    Extrai as propriedades de um campo do CSV e as converte para o formato JSON.
    
    Args:
        campo: Dicionário representando uma linha do CSV
        
    Returns:
        Dicionário com as propriedades do campo formatadas para JSON
    """
    # Propriedades básicas
    propriedades = {
        "campo_id": int(campo["campo_id"]) if campo.get("campo_id", "").isdigit() else None,
        "nome_campo": campo.get("nome_campo", ""),
        "categoria": campo.get("categoria", ""),
        "tipo_dado_programacao": campo.get("tipo_dado_programacao", "string"),
        "tipo_controle_interface": campo.get("tipo_controle_interface", ""),
        "obrigatorio_quando_ativo": campo.get("obrigatorio_quando_ativo", "não") == "sim",
        "visivel_quando": campo.get("visivel_quando", ""),
        "invisivel_quando": campo.get("invisivel_quando", ""),
        "depende_de": campo.get("depende_de", ""),
        "opcoes_valores": campo.get("opcoes_valores", ""),
        "valor_padrao": campo.get("valor_padrao", ""),
        "valor_minimo": campo.get("valor_minimo", ""),
        "valor_maximo": campo.get("valor_maximo", ""),
        "tamanho_maximo": int(campo.get("tamanho_maximo", 0)) if campo.get("tamanho_maximo", "").isdigit() else None,
        "mascara_formato": campo.get("mascara_formato", ""),
        "regex_validacao": campo.get("regex_validacao", ""),
        "calcular_quando": campo.get("calcular_quando", ""),
        "formula_calculo": campo.get("formula_calculo", ""),
        "campos_calculados_dependentes": campo.get("campos_calculados_dependentes", "").split(",") if campo.get("campos_calculados_dependentes", "") else [],
        "placeholder_texto": campo.get("placeholder_texto", "")
    }
    
    # Remove propriedades vazias para economizar espaço
    return {k: v for k, v in propriedades.items() if v is not None and v != ""}

def construir_mapping_campos(dados_csv: List[Dict[str, str]]) -> Dict[str, Any]:
    """
    Constrói o mapping de campos a partir dos dados do CSV.
    
    Args:
        dados_csv: Lista de dicionários, onde cada dicionário representa uma linha do CSV
        
    Returns:
        Dicionário com o mapping completo de campos
    """
    mapping = {
        "campos": {},
        "campos_por_id": {},
        "campos_por_categoria": {},
        "metadata": {
            "total_campos": len(dados_csv),
            "versao_schema": "1.0"
        }
    }
    
    categorias = {}
    
    for linha in dados_csv:
        # Pula linhas sem campo_id
        if not linha.get("campo_id", "").strip():
            continue
            
        try:
            campo_id = int(linha["campo_id"])
            nome_campo = linha.get("nome_campo", "").strip()
            categoria = linha.get("categoria", "").strip()
            
            # Extrai propriedades
            propriedades = extrair_propriedades_campo(linha)
            
            # Adiciona ao mapping principal
            if nome_campo:
                mapping["campos"][nome_campo] = propriedades
            
            # Adiciona ao mapping por ID
            mapping["campos_por_id"][str(campo_id)] = propriedades
            
            # Agrupa por categoria
            if categoria:
                if categoria not in categorias:
                    categorias[categoria] = []
                categorias[categoria].append(propriedades)
                
        except Exception as e:
            print(f"Erro ao processar campo ID {linha.get('campo_id', 'N/A')}: {str(e)}")
    
    # Adiciona campos agrupados por categoria
    mapping["campos_por_categoria"] = categorias
    
    # Atualiza metadata
    mapping["metadata"]["total_campos_validos"] = len(mapping["campos"])
    mapping["metadata"]["total_categorias"] = len(categorias)
    
    return mapping

def salvar_json(dados: Dict[str, Any], caminho_json: str) -> None:
    """
    Salva os dados em formato JSON no caminho especificado.
    
    Args:
        dados: Dicionário a ser salvo
        caminho_json: Caminho onde o arquivo JSON será salvo
        
    Raises:
        Exception: Se ocorrer erro ao salvar o arquivo
    """
    try:
        # Cria o diretório se não existir
        os.makedirs(os.path.dirname(caminho_json), exist_ok=True)
        
        with open(caminho_json, 'w', encoding='utf-8') as f:
            json.dump(dados, f, ensure_ascii=False, indent=2)
            
        print(f"Arquivo JSON salvo em: {caminho_json}")
    except Exception as e:
        print(f"Erro ao salvar JSON: {str(e)}")
        raise

def extrair_mapping_campos_definicao(caminho_csv: Optional[str] = None, caminho_json: Optional[str] = None) -> Dict[str, Any]:
    """
    Função principal que extrai o mapping dos campos de definição do CSV para JSON.
    
    Args:
        caminho_csv: Caminho para o arquivo CSV (opcional, usa config.CAMPOS_CSV se None)
        caminho_json: Caminho para salvar o arquivo JSON (opcional, usa config.MAPPING_CAMPOS_JSON se None)
        
    Returns:
        Dicionário com o mapping completo de campos
        
    Raises:
        Exception: Se ocorrer erro no processo
    """
    # Usa caminhos padrão se não especificados
    caminho_csv = caminho_csv or config.CAMPOS_CSV
    caminho_json = caminho_json or config.MAPPING_CAMPOS_JSON
    
    print(f"Processando CSV: {caminho_csv}")
    
    # Lê o CSV
    dados_csv = parse_csv(caminho_csv)
    print(f"Total de linhas no CSV: {len(dados_csv)}")
    
    # Constrói o mapping
    mapping = construir_mapping_campos(dados_csv)
    
    # Salva o JSON se caminho_json for fornecido
    if caminho_json:
        salvar_json(mapping, caminho_json)
    
    return mapping

def main():
    """
    Função principal do script.
    """
    parser = argparse.ArgumentParser(description='Extrai mapping de campos de definição CSV para JSON')
    parser.add_argument('--csv', help='Caminho para o arquivo CSV (padrão: config.CAMPOS_CSV)')
    parser.add_argument('--json', help='Caminho para salvar o arquivo JSON (padrão: config.MAPPING_CAMPOS_JSON)')
    args = parser.parse_args()
    
    try:
        extrair_mapping_campos_definicao(args.csv, args.json)
        print("Processo concluído com sucesso.")
    except Exception as e:
        print(f"Erro: {str(e)}")
        sys.exit(1)

if __name__ == "__main__":
    main() 