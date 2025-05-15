"""
Avaliador seguro de condições para o sistema de peticionamento.
"""

import os
import sys
import re
import logging
import operator
from typing import Dict, Any, Union, Optional, Callable

# Adiciona o diretório pai ao path para importar módulos
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from src.exceptions import AvaliacaoRegraError
from src.logger import logger

# Operadores seguros permitidos
OPERADORES_SEGUROS = {
    '<': operator.lt,
    '<=': operator.le,
    '>': operator.gt,
    '>=': operator.ge,
    '==': operator.eq,
    '!=': operator.ne,
    '+': operator.add,
    '-': operator.sub,
    '*': operator.mul,
    '/': operator.truediv,
    '%': operator.mod
}

# Funções seguras permitidas
FUNCOES_SEGURAS = {
    'len': len,
    'str': str,
    'int': int,
    'float': float,
    'bool': bool
}

class AvaliadorCondicoes:
    """
    Classe responsável por avaliar expressões condicionais no contexto de dados fornecidos.
    Permite avaliar expressões como "a > b" ou "campo == 'valor'" usando os dados 
    fornecidos como contexto.
    """

    def __init__(self):
        # Regex para identificar variáveis simples, sem pontos ou colchetes
        self._pattern_var_simples = re.compile(r'\b([a-zA-Z][a-zA-Z0-9_]*)\b')
        # Lista de funções e palavras-chave permitidas nas expressões
        self._allowed_functions = ['len', 'str', 'int', 'float', 'bool']
        # Lista de funções e operadores proibidos, para verificação de segurança
        self._danger_patterns = [
            r'\bimport\b', r'\bexec\b', r'\beval\b', r'\bcompile\b', r'\bglobals\b', 
            r'\blocals\b', r'\bgetattr\b', r'\bsetattr\b', r'\bdelattr\b', r'\b__\w+__\b',
            r'\bopen\b', r'\bfile\b', r'\bsystem\b', r'\bos\b', r'\bsys\b'
        ]
        
        # Expressões regulares para reconhecer operadores e comparações
        self._pattern_operador_logico = re.compile(r'(AND|OR)\((.*?)\)', re.IGNORECASE)
        self._pattern_comparacao = re.compile(r'(\w+)\s*([=!<>]=?)\s*([\'"]?)(\w+)\3')

    def verificar_seguranca(self, expressao: str) -> bool:
        """
        Verifica se a expressão contém padrões potencialmente perigosos.
        
        Args:
            expressao: A expressão a ser verificada
            
        Returns:
            True se a expressão for considerada segura, False caso contrário
        """
        expressao = expressao.lower()  # Simplifica verificação case-insensitive
        
        # Verifica padrões perigosos
        for pattern in self._danger_patterns:
            if re.search(pattern, expressao):
                logger.warning(f"Padrão potencialmente perigoso encontrado na expressão: {pattern}")
                return False
                
        return True

    def preparar_contexto(self, dados: Dict[str, Any]) -> Dict[str, Any]:
        """
        Prepara o contexto de avaliação a partir dos dados fornecidos.
        Inclui funções seguras permitidas.
        
        Args:
            dados: Dicionário de dados para o contexto
            
        Returns:
            Dicionário com o contexto preparado para avaliação
        """
        # Cria uma cópia para não modificar o original
        contexto = dados.copy() if dados else {}
        
        # Adiciona funções permitidas
        for func_name, func in FUNCOES_SEGURAS.items():
            contexto[func_name] = func
            
        return contexto

    def avaliar(self, expressao: str, dados: Dict[str, Any] = None) -> Union[bool, Any]:
        """
        Avalia uma expressão no contexto dos dados fornecidos.
        
        Args:
            expressao: A expressão a ser avaliada
            dados: Dicionário de dados para o contexto
            
        Returns:
            O resultado da avaliação da expressão
            
        Raises:
            ValueError: Se a expressão for considerada insegura
            Exception: Se ocorrer erro na avaliação da expressão
        """
        if not expressao:
            return True
        
        # Para manter compatibilidade com o código existente
        if dados is None:
            dados = {}
            
        # DIAGNÓSTICO: Log dos dados para avaliar problemas
        logger.debug(f"Avaliando expressão: '{expressao}'")
        logger.debug(f"Dados disponíveis: {', '.join(sorted(dados.keys()))}")
        
        # Verifica segurança antes de avaliar
        if not self.verificar_seguranca(expressao):
            raise ValueError(f"Expressão insegura não pode ser avaliada: {expressao}")
        
        try:
            # Se a expressão for simples True/False
            if expressao.strip() == "True":
                return True
            if expressao.strip() == "False":
                return False
                
            # Verifica se é uma condição lógica (AND/OR)
            match_logico = self._pattern_operador_logico.match(expressao)
            if match_logico:
                operador = match_logico.group(1).upper()
                condicoes = match_logico.group(2).split(',')
                resultados = []
                for condicao in condicoes:
                    resultados.append(self.avaliar(condicao.strip(), dados))
                    
                if operador == 'AND':
                    return all(resultados)
                elif operador == 'OR':
                    return any(resultados)
            
            # Verifica se é uma comparação simples
            match_comparacao = self._pattern_comparacao.match(expressao)
            if match_comparacao:
                campo = match_comparacao.group(1)
                operador = match_comparacao.group(2)
                valor = match_comparacao.group(4)
                
                if campo not in dados:
                    logger.warning(f"Campo '{campo}' não encontrado nos dados")
                    return False
                
                if operador not in OPERADORES_SEGUROS:
                    logger.warning(f"Operador '{operador}' não permitido")
                    return False
                
                # Valores para comparação
                valor_campo = dados[campo]
                valor_comparacao = valor
                
                # Log de diagnóstico
                logger.debug(f"Comparando campo '{campo}': '{valor_campo}' {operador} '{valor_comparacao}'")
                
                # Executa a comparação
                resultado = OPERADORES_SEGUROS[operador](
                    self._converter_valor(campo, valor_campo), 
                    self._converter_valor(campo, valor_comparacao)
                )
                
                logger.debug(f"Resultado da comparação: {resultado}")
                return resultado
            
            # Compatibilidade com código existente - tenta executar avaliação com eval
            # mas somente para expressões mais simples já validadas por segurança
            contexto = self.preparar_contexto(dados)
            return eval(expressao, {"__builtins__": {}}, contexto)
            
        except Exception as e:
            logger.error(f"Erro ao avaliar expressão '{expressao}': {str(e)}")
            # Relança a exceção para ser tratada pelo chamador
            raise

    def avaliar_condicao(self, expressao: str, campos_ids: str, valores: Dict[str, Any], valor_padrao: bool = False) -> bool:
        """
        Avalia uma expressão condicional, retornando um valor booleano.
        
        Args:
            expressao: A expressão a ser avaliada
            campos_ids: Lista de IDs de campos separados por vírgula
            valores: Dicionário de valores dos campos
            valor_padrao: Valor a retornar em caso de erro (default: False)
            
        Returns:
            Resultado booleano da avaliação ou valor_padrao em caso de erro
        """
        if not expressao or expressao.strip() == "True":
            return True
            
        if expressao.strip() == "False":
            return False
        
        # Processa a expressão
        try:
            # Verifica se é uma condição lógica (AND/OR)
            match_logico = self._pattern_operador_logico.match(expressao)
            if match_logico:
                operador = match_logico.group(1).upper()
                condicoes = match_logico.group(2).split(',')
                
                # Avalia cada condição no operador lógico
                resultados = []
                for condicao in condicoes:
                    resultado = self.avaliar_condicao(condicao.strip(), campos_ids, valores, valor_padrao)
                    resultados.append(resultado)
                
                # Aplica operador lógico (AND/OR)
                if operador == 'AND':
                    return all(resultados)
                elif operador == 'OR':
                    return any(resultados)
            
            # Verifica se é uma comparação simples
            match_comparacao = self._pattern_comparacao.match(expressao)
            if match_comparacao:
                campo = match_comparacao.group(1)
                operador = match_comparacao.group(2)
                valor = match_comparacao.group(4)
                
                if campo not in valores:
                    logger.warning(f"Campo '{campo}' não encontrado nos valores")
                    return False
                
                if operador not in OPERADORES_SEGUROS:
                    logger.warning(f"Operador '{operador}' não permitido")
                    return False
                
                # Executa a comparação
                return OPERADORES_SEGUROS[operador](
                    self._converter_valor(campo, valores[campo]), 
                    self._converter_valor(campo, valor)
                )
            
            # Se não reconheceu o padrão, loga erro
            logger.warning(f"Formato de expressão não reconhecido: {expressao}")
            return valor_padrao
            
        except Exception as e:
            logger.warning(f"Erro ao avaliar condição '{expressao}': {str(e)}. Retornando {valor_padrao}")
            return valor_padrao

    def substituir_variaveis(self, expressao: str, dados: Dict[str, Any]) -> str:
        """
        Substitui variáveis na expressão pelos seus valores no contexto.
        Útil para depuração.
        
        Args:
            expressao: Expressão com variáveis
            dados: Dicionário de dados com valores
            
        Returns:
            Expressão com variáveis substituídas por seus valores
        """
        def substituir(match):
            nome_var = match.group(0)
            if nome_var in dados:
                valor = dados[nome_var]
                if isinstance(valor, str):
                    return f"'{valor}'"
                return str(valor)
            return nome_var
            
        # Substitui apenas variáveis simples (sem pontos ou colchetes)
        return self._pattern_var_simples.sub(substituir, expressao)

    def get_valor_condicao(self, expressao: str, dados: Dict[str, Any], 
                         atributo: str = "condicao") -> Optional[Any]:
        """
        Avalia uma expressão condicional especial que pode retornar um valor.
        Útil para condições que retornam valores em vez de apenas True/False.
        
        Args:
            expressao: A expressão a ser avaliada
            dados: Dicionário de dados para o contexto
            atributo: Nome do atributo para identificar o tipo de condição
            
        Returns:
            O valor retornado pela condição ou None em caso de erro
        """
        if not expressao:
            return None
            
        if atributo == "condicao_valor_retornado":
            try:
                return self.avaliar(expressao, dados)
            except Exception as e:
                logger.error(f"Erro ao avaliar condição com valor retornado '{expressao}': {str(e)}")
                return None
        else:
            return None
    
    def _converter_valor(self, nome_var, valor):
        """
        Converte um valor para o tipo apropriado para comparação.
        
        Args:
            nome_var: Nome da variável (para fins de depuração)
            valor: Valor a ser convertido
            
        Returns:
            Valor convertido para o tipo apropriado
        """
        # MELHORIA: Adiciona logs para diagnosticar problemas de comparação
        logger.debug(f"Convertendo valor para campo '{nome_var}': '{valor}' (tipo: {type(valor).__name__})")
        
        if valor is None:
            return None
            
        # Se o valor for string, tenta normalizar para facilitar comparações
        if isinstance(valor, str):
            # Remove espaços extras e normaliza para comparação
            valor_normalizado = valor.strip()
            logger.debug(f"Valor após normalização básica: '{valor_normalizado}'")
            
            # Normalização especial para valores booleanos
            if valor_normalizado.lower() in ('sim', 'yes', 'true', '1', 's', 'y', 't'):
                logger.debug(f"Convertendo '{valor_normalizado}' para valor booleano True")
                return True
            if valor_normalizado.lower() in ('não', 'nao', 'no', 'false', '0', 'n', 'f'):
                logger.debug(f"Convertendo '{valor_normalizado}' para valor booleano False")
                return False
            
            # Para valores numéricos representados como string
            try:
                if '.' in valor_normalizado:
                    # Tenta converter para float se tiver ponto decimal
                    return float(valor_normalizado)
                else:
                    # Tenta converter para inteiro
                    return int(valor_normalizado)
            except (ValueError, TypeError):
                # Se não conseguir converter, retorna a string original normalizada
                pass
                
            # Retorna a string normalizada
            return valor_normalizado
            
        # Para outros tipos, retorna o valor como está
        return valor

    def avaliar_condicao_composta(self, condicoes, operador='AND'):
        """
        Avalia uma condição composta com múltiplas condições e um operador lógico.
        
        Args:
            condicoes: Lista de condições a serem avaliadas
            operador: Operador lógico (AND/OR)
            
        Returns:
            Resultado da avaliação da condição composta
        """
        if not condicoes:
            return True
            
        resultados = []
        for condicao in condicoes:
            resultado = self.avaliar_condicao(condicao.strip(), '', {})
            resultados.append(resultado)
        
        if operador.upper() == 'AND':
            return all(resultados)
        elif operador.upper() == 'OR':
            return any(resultados)
        else:
            logger.warning(f"Operador lógico desconhecido: {operador}")
            return False
