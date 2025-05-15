#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Script para converter um template existente para o formato padronizado de seções.
"""

import os
import sys
import argparse

# Adiciona o diretório pai ao path para importar módulos
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
import config
from src.utils.template_converter import converter_template_para_formato_padrao
from src.utils.logger_config import configurar_logger

logger = configurar_logger()

def main():
    """
    Função principal do script.
    """
    parser = argparse.ArgumentParser(description='Converte um template para o formato padronizado de seções')
    parser.add_argument('--template', required=False, help='Caminho do template a ser convertido')
    parser.add_argument('--output', required=False, help='Caminho onde o template convertido será salvo')
    parser.add_argument('--debug', action='store_true', help='Ativa modo de depuração')
    
    args = parser.parse_args()
    
    # Caminhos padrão
    template_path = args.template or config.TEMPLATE_DOCX
    output_path = args.output
    
    if not output_path:
        # Gera um nome de arquivo de saída padrão
        nome_base, ext = os.path.splitext(template_path)
        output_path = f"{nome_base}_convertido{ext}"
    
    # Definições de seções conhecidas para o template
    secoes_conhecidas = {
        "HORAS_EXTRAS": {
            "inicio": "HORAS EXTRAS",
            "fim": "VALOR REQUERIDO"
        },
        "VERBAS_RESCISORIAS": {
            "inicio": "VERBAS RESCISÓRIAS",
            "fim": "CONCLUSÃO"
        },
        "DANO_MORAL": {
            "inicio": "DANO MORAL",
            "fim": "VALOR REQUERIDO"
        }
    }
    
    # Converte o template
    print(f"Convertendo template de {template_path} para {output_path}...")
    resultado = converter_template_para_formato_padrao(template_path, output_path, secoes_conhecidas)
    
    if resultado:
        print(f"Template convertido com sucesso! Salvo em: {output_path}")
    else:
        print("Erro ao converter o template. Verifique os logs para mais detalhes.")
        sys.exit(1)
    
    return 0

if __name__ == "__main__":
    sys.exit(main()) 