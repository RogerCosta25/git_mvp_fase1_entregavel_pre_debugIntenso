"""
Motor de regras para avaliação de condições e validações.

Este módulo implementa o motor de regras que avalia condições
e executa validações associadas a campos do documento.
"""

import os
import sys
import re
import json
from typing import Any, Dict, List, Optional, Union, Callable, Tuple, Set, cast

# Adiciona o diretório pai ao path para importar módulos
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.logger import logger
from src.exceptions import (
    RegraError,
    RegraInvalidaError
)

class MotorRegras:
    """
    Motor de avaliação de regras para validação de condições 
    nos campos de formulários.
    """
    
    def __init__(self, usar_modelo_relacional: bool = False):
        """
        Inicializa o motor de regras.
        
        Args:
            usar_modelo_relacional: Se True, usa o modelo relacional para campos e regras.
        """
        self.usar_modelo_relacional = usar_modelo_relacional
        
        # Dicionário de operadores de comparação
        self.operadores: Dict[str, Callable[[Any, Any], bool]] = {
            "==": lambda a, b: a == b,
            "!=": lambda a, b: a != b,
            ">": lambda a, b: a > b,
            "<": lambda a, b: a < b,
            ">=": lambda a, b: a >= b,
            "<=": lambda a, b: a <= b,
            "in": lambda a, b: a in b,
            "not_in": lambda a, b: a not in b,
            "contains": lambda a, b: b in a if isinstance(a, str) else False,
            "not_contains": lambda a, b: b not in a if isinstance(a, str) else False,
            "startswith": lambda a, b: a.startswith(b) if isinstance(a, str) else False,
            "endswith": lambda a, b: a.endswith(b) if isinstance(a, str) else False,
            "matches": lambda a, b: bool(re.match(b, a)) if isinstance(a, str) and isinstance(b, str) else False,
            "is_empty": lambda a, _: a is None or a == "" or (isinstance(a, (list, dict)) and len(a) == 0),
            "is_not_empty": lambda a, _: a is not None and a != "" and (not isinstance(a, (list, dict)) or len(a) > 0)
        }
        
        # Dicionário de operadores lógicos
        self.operadores_logicos: Dict[str, Callable[[List[bool]], bool]] = {
            "and": lambda conds: all(conds),
            "or": lambda conds: any(conds),
            "not": lambda conds: not conds[0] if conds else False
        }
        
        # Cache de resultados de avaliação para otimização
        self.cache_avaliacao: Dict[str, Dict[str, bool]] = {}
        
        # Regras carregadas do arquivo de regras
        self.regras: Dict[str, Any] = {}
        
        # Definições de seções e suas regras de ativação
        self.definicoes_secoes: Dict[str, Dict[str, Any]] = {}
        
    def carregar_regras(self, caminho_regras: Optional[str] = None) -> None:
        """
        Carrega as regras condicionais de um arquivo JSON.
        
        Args:
            caminho_regras: Caminho para o arquivo JSON com as regras. Se None, usa o padrão em config.
        """
        try:
            import config  # Importa aqui para evitar dependência circular
            
            # Se não for especificado, usa o caminho padrão do config
            if caminho_regras is None:
                caminho_regras = getattr(config, 'REGRAS_JSON', None)
                
            if caminho_regras is None or not os.path.exists(caminho_regras):
                logger.warning(f"Arquivo de regras não encontrado: {caminho_regras}")
                self.regras = {}
                return
                
            # Carrega o arquivo JSON
            with open(caminho_regras, 'r', encoding='utf-8') as f:
                self.regras = json.load(f)
                
            # Extrai definições de seções
            self.definicoes_secoes = self.regras.get('secoes', {})
            
            logger.info(f"Regras carregadas de {caminho_regras}: {len(self.regras)} regras principais")
            logger.debug(f"Definições de seções carregadas: {len(self.definicoes_secoes)} seções")
        except Exception as e:
            logger.error(f"Erro ao carregar regras: {str(e)}")
            self.regras = {}
            self.definicoes_secoes = {}
    
    def avaliar_secoes_ativas(self, dados: Dict[str, Any]) -> List[str]:
        """
        Avalia quais seções devem estar ativas com base nos dados fornecidos.
        
        Args:
            dados: Dicionário com os dados para avaliação.
            
        Returns:
            Lista com os IDs das seções que devem estar ativas.
        """
        secoes_ativas: List[str] = []
        
        # Se não tiver definições de seções, retorna lista vazia
        if not self.definicoes_secoes:
            logger.warning("Nenhuma definição de seção encontrada para avaliação")
            return secoes_ativas
            
        # Avalia cada seção
        for secao_id, definicao in self.definicoes_secoes.items():
            # Se a seção não tiver regra de ativação, considera sempre ativa
            if 'regra_ativacao' not in definicao:
                secoes_ativas.append(secao_id)
                continue
                
            # Obtém a regra de ativação
            regra = definicao['regra_ativacao']
            
            # Avalia a condição
            try:
                if self.avaliar_condicao(regra, dados):
                    secoes_ativas.append(secao_id)
                    logger.debug(f"Seção {secao_id} ativada")
            except Exception as e:
                logger.error(f"Erro ao avaliar regra de ativação da seção {secao_id}: {str(e)}")
                # Em caso de erro, não ativa a seção
        
        return secoes_ativas
        
    def avaliar_condicao(self, 
                        condicao: Dict[str, Any], 
                        dados: Dict[str, Any],
                        contexto: Optional[Dict[str, Any]] = None) -> bool:
        """
        Avalia uma condição com base nos dados fornecidos.
        
        Args:
            condicao: Dicionário representando a condição a ser avaliada.
                    Exemplo: {"campo": "idade", "operador": ">", "valor": 18}
            dados: Dicionário com os dados para avaliação.
            contexto: Contexto adicional para avaliação (opcional).
            
        Returns:
            True se a condição for satisfeita, False caso contrário.
            
        Raises:
            RegraInvalidaError: Se a condição for inválida.
        """
        if not condicao:
            # Condição vazia é considerada verdadeira por padrão
            return True
            
        # Verifica se é uma condição composta (com operadores lógicos)
        if "tipo" in condicao and condicao["tipo"] in self.operadores_logicos:
            return self._avaliar_condicao_composta(condicao, dados, contexto)
        
        # Avalia uma condição simples
        return self._avaliar_condicao_simples(condicao, dados, contexto)
    
    def _avaliar_condicao_simples(self, 
                                condicao: Dict[str, Any], 
                                dados: Dict[str, Any],
                                contexto: Optional[Dict[str, Any]] = None) -> bool:
        """
        Avalia uma condição simples (sem operadores lógicos).
        
        Args:
            condicao: Dicionário representando a condição.
            dados: Dicionário com os dados para avaliação.
            contexto: Contexto adicional para avaliação (opcional).
            
        Returns:
            True se a condição for satisfeita, False caso contrário.
            
        Raises:
            RegraInvalidaError: Se a condição for inválida.
        """
        if not contexto:
            contexto = {}
            
        try:
            # Obtém os componentes da condição
            campo = condicao.get("campo")
            operador = condicao.get("operador")
            valor_esperado = condicao.get("valor")
            
            # Valida a condição
            if not campo or not operador:
                raise RegraInvalidaError("Campo ou operador não especificado na condição")
                
            if operador not in self.operadores:
                raise RegraInvalidaError(f"Operador inválido: {operador}")
            
            # Para operadores que não precisam de valor (is_empty, is_not_empty)
            if operador in ["is_empty", "is_not_empty"]:
                valor_esperado = None
            elif valor_esperado is None:
                raise RegraInvalidaError(f"Valor esperado não especificado para operador {operador}")
            
            # Obtém o valor atual do campo nos dados
            valor_atual = self._obter_valor_campo(campo, dados, contexto)
            
            # Executa a comparação
            resultado = self.operadores[operador](valor_atual, valor_esperado)
            
            logger.debug(f"Avaliação: {campo} {operador} {valor_esperado} = {resultado}")
            return resultado
            
        except KeyError as e:
            logger.error(f"Campo não encontrado na condição: {e}")
            return False
        except Exception as e:
            logger.error(f"Erro ao avaliar condição: {e}")
            if isinstance(e, RegraInvalidaError):
                raise
            raise RegraInvalidaError(f"Erro ao avaliar condição: {str(e)}")
    
    def _avaliar_condicao_composta(self, 
                                 condicao: Dict[str, Any], 
                                 dados: Dict[str, Any],
                                 contexto: Optional[Dict[str, Any]] = None) -> bool:
        """
        Avalia uma condição composta (com operadores lógicos).
        
        Args:
            condicao: Dicionário representando a condição composta.
            dados: Dicionário com os dados para avaliação.
            contexto: Contexto adicional para avaliação (opcional).
            
        Returns:
            True se a condição for satisfeita, False caso contrário.
            
        Raises:
            RegraInvalidaError: Se a condição for inválida.
        """
        if not contexto:
            contexto = {}
            
        try:
            tipo_operador = condicao.get("tipo")
            sub_condicoes = condicao.get("condicoes", [])
            
            if not tipo_operador or tipo_operador not in self.operadores_logicos:
                raise RegraInvalidaError(f"Operador lógico inválido: {tipo_operador}")
                
            if not sub_condicoes:
                # Para NOT, uma lista vazia retorna True por padrão
                if tipo_operador == "not":
                    return True
                # Para AND, uma lista vazia retorna True
                if tipo_operador == "and":
                    return True
                # Para OR, uma lista vazia retorna False
                return False
            
            # Avalia cada sub-condição
            resultados = []
            for sub_cond in sub_condicoes:
                resultado = self.avaliar_condicao(sub_cond, dados, contexto)
                resultados.append(resultado)
            
            # Aplica o operador lógico aos resultados
            resultado_final = self.operadores_logicos[tipo_operador](resultados)
            
            logger.debug(f"Avaliação composta ({tipo_operador}): {resultados} = {resultado_final}")
            return resultado_final
            
        except Exception as e:
            logger.error(f"Erro ao avaliar condição composta: {e}")
            if isinstance(e, RegraInvalidaError):
                raise
            raise RegraInvalidaError(f"Erro ao avaliar condição composta: {str(e)}")
    
    def _obter_valor_campo(self, 
                         campo: str, 
                         dados: Dict[str, Any],
                         contexto: Dict[str, Any]) -> Any:
        """
        Obtém o valor de um campo nos dados fornecidos.
        
        Args:
            campo: Nome do campo a ser obtido.
            dados: Dicionário com os dados.
            contexto: Contexto adicional para avaliação.
            
        Returns:
            Valor do campo.
        """
        # Verifica se é uma referência especial do tipo ${campo}
        if campo.startswith("${") and campo.endswith("}"):
            campo_referencia = campo[2:-1]  # Remove ${ e }
            
            # Verifica se existe nos dados
            if campo_referencia in dados:
                return dados[campo_referencia]
                
            # Verifica se existe no contexto
            if campo_referencia in contexto:
                return contexto[campo_referencia]
                
            logger.warning(f"Campo de referência não encontrado: {campo_referencia}")
            return None
        
        # Se não for referência, retorna o valor literal
        if campo.startswith('"') and campo.endswith('"'):
            return campo[1:-1]  # Remove as aspas
            
        if campo.startswith("'") and campo.endswith("'"):
            return campo[1:-1]  # Remove as aspas
            
        # Tenta converter para número se possível
        if campo.isdigit():
            return int(campo)
            
        try:
            return float(campo)
        except ValueError:
            pass
        
        # Valores booleanos
        if campo.lower() == "true":
            return True
        if campo.lower() == "false":
            return False
        if campo.lower() == "null" or campo.lower() == "none":
            return None
            
        # Se não for um valor literal, busca nos dados
        if campo in dados:
            return dados[campo]
            
        # Busca no contexto
        if campo in contexto:
            return contexto[campo]
            
        # Se não encontrou, retorna None
        logger.warning(f"Campo não encontrado: {campo}")
        return None
    
    def verificar_acesso_campo(self, 
                              campo_id: Union[str, int], 
                              regras_visibilidade: Dict[str, Dict[str, Any]], 
                              dados: Dict[str, Any]) -> bool:
        """
        Verifica se um campo deve ser mostrado com base em suas regras de visibilidade.
        
        Args:
            campo_id: Identificador do campo.
            regras_visibilidade: Dicionário com as regras de visibilidade.
            dados: Dados atuais do formulário.
            
        Returns:
            True se o campo deve ser mostrado, False caso contrário.
        """
        campo_id_str = str(campo_id)
        
        # Se não houver regras, o campo é sempre visível
        if not regras_visibilidade or campo_id_str not in regras_visibilidade:
            return True
            
        # Obtém a regra para o campo
        regra = regras_visibilidade.get(campo_id_str, {})
        condicao = regra.get("condicao")
        
        # Se não houver condição, o campo é sempre visível
        if not condicao:
            return True
            
        # Avalia a condição
        try:
            return self.avaliar_condicao(condicao, dados)
        except Exception as e:
            logger.error(f"Erro ao verificar visibilidade do campo {campo_id}: {e}")
            # Em caso de erro, mostra o campo por segurança
            return True
    
    def validar_campo(self, 
                     campo_id: Union[str, int], 
                     valor: Any, 
                     regras_validacao: Dict[str, List[Dict[str, Any]]], 
                     dados: Dict[str, Any]) -> List[str]:
        """
        Valida um campo de acordo com as regras de validação especificadas.
        
        Args:
            campo_id: Identificador do campo.
            valor: Valor do campo a ser validado.
            regras_validacao: Dicionário com as regras de validação.
            dados: Dados atuais do formulário.
            
        Returns:
            Lista de mensagens de erro. Lista vazia significa que o campo é válido.
        """
        campo_id_str = str(campo_id)
        erros: List[str] = []
        
        # Se não houver regras, o campo é sempre válido
        if not regras_validacao or campo_id_str not in regras_validacao:
            return erros
            
        # Obtém as regras para o campo
        regras = regras_validacao.get(campo_id_str, [])
        
        # Aplica cada regra de validação
        for regra in regras:
            tipo = regra.get("tipo", "")  # Usa string vazia como valor padrão para tipo
            parametros = regra.get("parametros", {})
            mensagem = regra.get("mensagem", f"Campo {campo_id} inválido")
            condicao = regra.get("condicao")
            
            # Verifica se a regra deve ser aplicada (se houver condição)
            if condicao:
                try:
                    if not self.avaliar_condicao(condicao, dados):
                        continue  # Pula esta regra se a condição não for satisfeita
                except Exception as e:
                    logger.error(f"Erro ao avaliar condição para validação do campo {campo_id}: {e}")
                    continue
            
            # Executa a validação de acordo com o tipo
            try:
                if tipo and not self._validar_por_tipo(tipo, valor, parametros):
                    erros.append(mensagem)
            except Exception as e:
                logger.error(f"Erro ao validar campo {campo_id}: {e}")
                erros.append(f"Erro interno na validação: {str(e)}")
        
        return erros
    
    def _validar_por_tipo(self, 
                        tipo: str, 
                        valor: Any, 
                        parametros: Dict[str, Any]) -> bool:
        """
        Executa uma validação de acordo com o tipo especificado.
        
        Args:
            tipo: Tipo de validação a ser executada.
            valor: Valor a ser validado.
            parametros: Parâmetros para a validação.
            
        Returns:
            True se o valor for válido, False caso contrário.
            
        Raises:
            RegraInvalidaError: Se o tipo de validação for inválido.
        """
        # Tratamento de valores nulos
        if valor is None:
            # Validação de obrigatoriedade
            if tipo == "required":
                return False
            
            # Outras validações são ignoradas para valores nulos
            return True
            
        # Validações básicas
        if tipo == "required":
            if isinstance(valor, str):
                return valor.strip() != ""
            if isinstance(valor, (list, dict)):
                return len(valor) > 0
            return valor is not None
            
        elif tipo == "min_length":
            min_length = parametros.get("length", 0)
            if not isinstance(min_length, int):
                raise RegraInvalidaError(f"Parâmetro 'length' inválido para validação min_length: {min_length}")
                
            if isinstance(valor, str):
                return len(valor) >= min_length
            if isinstance(valor, (list, dict)):
                return len(valor) >= min_length
            return True  # Não aplicável a outros tipos
            
        elif tipo == "max_length":
            max_length = parametros.get("length", float('inf'))
            if not isinstance(max_length, int):
                raise RegraInvalidaError(f"Parâmetro 'length' inválido para validação max_length: {max_length}")
                
            if isinstance(valor, str):
                return len(valor) <= max_length
            if isinstance(valor, (list, dict)):
                return len(valor) <= max_length
            return True  # Não aplicável a outros tipos
            
        elif tipo == "pattern":
            pattern = parametros.get("regex", "")
            if not pattern:
                raise RegraInvalidaError("Parâmetro 'regex' não especificado para validação pattern")
                
            if isinstance(valor, str):
                try:
                    return bool(re.match(pattern, valor))
                except Exception as e:
                    raise RegraInvalidaError(f"Erro ao aplicar regex '{pattern}': {str(e)}")
            return True  # Não aplicável a outros tipos
            
        elif tipo == "min_value":
            min_value = parametros.get("value")
            if min_value is None:
                raise RegraInvalidaError("Parâmetro 'value' não especificado para validação min_value")
                
            try:
                return float(valor) >= float(min_value)
            except (ValueError, TypeError):
                return False
                
        elif tipo == "max_value":
            max_value = parametros.get("value")
            if max_value is None:
                raise RegraInvalidaError("Parâmetro 'value' não especificado para validação max_value")
                
            try:
                return float(valor) <= float(max_value)
            except (ValueError, TypeError):
                return False
                
        elif tipo == "email":
            if not isinstance(valor, str):
                return False
                
            # Regex simples para validação básica de email
            email_pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
            return bool(re.match(email_pattern, valor))
            
        elif tipo == "url":
            if not isinstance(valor, str):
                return False
                
            # Regex simples para validação básica de URL
            url_pattern = r'^(https?|ftp)://[^\s/$.?#].[^\s]*$'
            return bool(re.match(url_pattern, valor))
            
        elif tipo == "in_list":
            valid_values = parametros.get("values", [])
            if not valid_values:
                raise RegraInvalidaError("Parâmetro 'values' não especificado ou vazio para validação in_list")
                
            return valor in valid_values
            
        elif tipo == "not_in_list":
            invalid_values = parametros.get("values", [])
            if not invalid_values:
                raise RegraInvalidaError("Parâmetro 'values' não especificado ou vazio para validação not_in_list")
                
            return valor not in invalid_values
            
        elif tipo == "custom":
            # Para validações customizadas, deve haver uma condição específica
            # definida no parâmetro 'condicao'
            condicao = parametros.get("condicao")
            if not condicao:
                raise RegraInvalidaError("Parâmetro 'condicao' não especificado para validação custom")
                
            # Cria um contexto com o valor atual
            contexto = {"valor": valor}
            
            # Avalia a condição
            try:
                return self.avaliar_condicao(condicao, {}, contexto)
            except Exception as e:
                logger.error(f"Erro ao avaliar condição customizada: {e}")
                return False
        
        # Tipo de validação não reconhecido
        logger.warning(f"Tipo de validação não reconhecido: {tipo}")
        return True  # Por segurança, considera válido
    
    def limpar_cache(self) -> None:
        """
        Limpa o cache de avaliações.
        """
        self.cache_avaliacao = {} 