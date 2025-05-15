"""
Interface e implementação do repositório de templates para o sistema de peticionamento.
"""
import os
import re
import json
import uuid
import shutil
from datetime import datetime
from typing import List, Dict, Any, Optional, Tuple, BinaryIO
import pathlib

from src.exceptions import (
    TemplateNaoEncontradoError, 
    TemplateInvalidoError,
    VersaoNaoEncontradaError,
    ArmazenamentoError,
    SegurancaError
)
from src.logger import logger

class TemplateRepository:
    """
    Interface para repositório de templates de documentos.
    Define os métodos que qualquer implementação de repositório de templates deve fornecer.
    """
    
    def listar_templates(self) -> List[Dict[str, Any]]:
        """
        Lista todos os templates disponíveis no repositório.
        
        Returns:
            Lista de dicionários contendo informações sobre cada template.
        """
        raise NotImplementedError("Método não implementado")
    
    def obter_template(self, identificador: str, versao: Optional[str] = None) -> BinaryIO:
        """
        Obtém um template específico do repositório.
        
        Args:
            identificador: Identificador único do template.
            versao: Versão específica do template (se None, usa a versão mais recente).
            
        Returns:
            Objeto BinaryIO contendo o conteúdo do template.
            
        Raises:
            TemplateNaoEncontradoError: Se o template não for encontrado.
            VersaoNaoEncontradaError: Se a versão especificada não for encontrada.
        """
        raise NotImplementedError("Método não implementado")
    
    def salvar_template(self, 
                       nome: str, 
                       conteudo: BinaryIO, 
                       metadados: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """
        Salva um novo template ou uma nova versão de um template existente.
        
        Args:
            nome: Nome do template.
            conteudo: Conteúdo do template como BinaryIO.
            metadados: Metadados adicionais do template.
            
        Returns:
            Dicionário com as informações do template salvo, incluindo seu identificador.
            
        Raises:
            TemplateInvalidoError: Se o template for inválido.
            ArmazenamentoError: Se ocorrer um erro ao salvar o template.
        """
        raise NotImplementedError("Método não implementado")
    
    def excluir_template(self, identificador: str, excluir_todas_versoes: bool = False) -> bool:
        """
        Exclui um template do repositório.
        
        Args:
            identificador: Identificador único do template.
            excluir_todas_versoes: Se True, exclui todas as versões; se False, exclui apenas a versão mais recente.
            
        Returns:
            True se a exclusão for bem-sucedida, False caso contrário.
            
        Raises:
            TemplateNaoEncontradoError: Se o template não for encontrado.
        """
        raise NotImplementedError("Método não implementado")
    
    def obter_metadados(self, identificador: str, versao: Optional[str] = None) -> Dict[str, Any]:
        """
        Obtém os metadados de um template específico.
        
        Args:
            identificador: Identificador único do template.
            versao: Versão específica do template (se None, usa a versão mais recente).
            
        Returns:
            Dicionário contendo os metadados do template.
            
        Raises:
            TemplateNaoEncontradoError: Se o template não for encontrado.
            VersaoNaoEncontradaError: Se a versão especificada não for encontrada.
        """
        raise NotImplementedError("Método não implementado")


class FileSystemTemplateRepository(TemplateRepository):
    """
    Implementação do repositório de templates que armazena arquivos no sistema de arquivos.
    """
    
    def __init__(self, base_dir: str, max_file_size_mb: int = 10):
        """
        Inicializa o repositório de templates no sistema de arquivos.
        
        Args:
            base_dir: Diretório base onde os templates serão armazenados.
            max_file_size_mb: Tamanho máximo do arquivo em MB.
        """
        self.base_dir = os.path.abspath(base_dir)
        self.templates_dir = os.path.join(self.base_dir, "templates")
        self.metadata_dir = os.path.join(self.base_dir, "metadata")
        self.max_file_size = max_file_size_mb * 1024 * 1024  # Convertendo para bytes
        
        # Padrões para validação de segurança
        self._unsafe_patterns = [
            r'\.\./',  # Path traversal
            r'^\/',    # Caminho absoluto
            r'^[a-zA-Z]:\\' # Caminho absoluto Windows
        ]
        
        # Cria diretórios se não existirem
        os.makedirs(self.templates_dir, exist_ok=True)
        os.makedirs(self.metadata_dir, exist_ok=True)
        logger.info(f"Repositório de templates inicializado em: {self.base_dir}")
    
    def _validar_seguranca_caminho(self, caminho: str) -> None:
        """
        Valida se um caminho é seguro para acesso.
        
        Args:
            caminho: Caminho a ser validado.
            
        Raises:
            SegurancaError: Se o caminho for considerado inseguro.
        """
        # Verificar se o caminho contém padrões inseguros
        for pattern in self._unsafe_patterns:
            if re.search(pattern, caminho):
                logger.error(f"Tentativa de acesso a caminho inseguro: {caminho}")
                raise SegurancaError(f"Caminho inseguro: {caminho}")
        
        # Verificar se o caminho resultante está dentro do diretório base
        caminho_absoluto = os.path.abspath(os.path.join(self.base_dir, caminho))
        if not caminho_absoluto.startswith(self.base_dir):
            logger.error(f"Tentativa de acesso fora do diretório base: {caminho}")
            raise SegurancaError(f"Acesso fora do diretório permitido: {caminho}")
    
    def _gerar_identificador(self) -> str:
        """
        Gera um identificador único para um novo template.
        
        Returns:
            Identificador único.
        """
        return str(uuid.uuid4())
    
    def _gerar_versao(self) -> str:
        """
        Gera um identificador de versão baseado na data e hora atual.
        
        Returns:
            Identificador de versão.
        """
        return datetime.now().strftime("%Y%m%d%H%M%S")
    
    def _obter_caminho_template(self, identificador: str, versao: str) -> str:
        """
        Obtém o caminho do arquivo de template para um identificador e versão específicos.
        
        Args:
            identificador: Identificador único do template.
            versao: Versão específica do template.
            
        Returns:
            Caminho completo para o arquivo de template.
        """
        # Validação para prevenir path traversal
        self._validar_seguranca_caminho(identificador)
        self._validar_seguranca_caminho(versao)
        
        return os.path.join(self.templates_dir, f"{identificador}_{versao}.docx")
    
    def _obter_caminho_metadados(self, identificador: str) -> str:
        """
        Obtém o caminho do arquivo de metadados para um identificador específico.
        
        Args:
            identificador: Identificador único do template.
            
        Returns:
            Caminho completo para o arquivo de metadados.
        """
        # Validação para prevenir path traversal
        self._validar_seguranca_caminho(identificador)
        
        return os.path.join(self.metadata_dir, f"{identificador}.json")
    
    def _validar_template(self, nome: str, conteudo: BinaryIO) -> None:
        """
        Valida se um template é válido para armazenamento.
        
        Args:
            nome: Nome do template.
            conteudo: Conteúdo do template.
            
        Raises:
            TemplateInvalidoError: Se o template for inválido.
        """
        # Valida nome do template
        if not nome or len(nome) < 3:
            raise TemplateInvalidoError("Nome do template deve ter pelo menos 3 caracteres")
        
        if not re.match(r'^[a-zA-Z0-9_\- ]+$', nome):
            raise TemplateInvalidoError("Nome do template contém caracteres inválidos")
        
        # Valida tamanho do arquivo
        conteudo.seek(0, os.SEEK_END)
        tamanho = conteudo.tell()
        conteudo.seek(0)  # Reinicia a posição para o início
        
        if tamanho <= 0:
            raise TemplateInvalidoError("Template vazio")
            
        if tamanho > self.max_file_size:
            raise TemplateInvalidoError(
                f"Tamanho do arquivo excede o limite máximo de {self.max_file_size/1024/1024:.1f} MB"
            )
        
        # Verificação adicional do formato (primeiros bytes de um arquivo DOCX)
        try:
            # Verifica se é um arquivo DOCX (ZIP)
            primeiros_bytes = conteudo.read(4)
            conteudo.seek(0)  # Reinicia a posição para o início
            
            # Assinatura ZIP: PK\x03\x04
            if primeiros_bytes != b'PK\x03\x04':
                raise TemplateInvalidoError("Formato de arquivo inválido. Apenas DOCX é suportado.")
        except Exception as e:
            raise TemplateInvalidoError(f"Erro ao validar formato do template: {str(e)}")
    
    def listar_templates(self) -> List[Dict[str, Any]]:
        """
        Lista todos os templates disponíveis no repositório.
        
        Returns:
            Lista de dicionários contendo informações sobre cada template.
        """
        templates = []
        
        # Lista todos os arquivos de metadados
        for arquivo in os.listdir(self.metadata_dir):
            if arquivo.endswith('.json'):
                try:
                    caminho_metadados = os.path.join(self.metadata_dir, arquivo)
                    with open(caminho_metadados, 'r', encoding='utf-8') as f:
                        metadados = json.load(f)
                    
                    # Adiciona metadados à lista
                    templates.append(metadados)
                except Exception as e:
                    logger.warning(f"Erro ao ler metadados do arquivo {arquivo}: {str(e)}")
        
        return templates
    
    def _obter_versao_mais_recente(self, identificador: str) -> str:
        """
        Obtém a versão mais recente de um template.
        
        Args:
            identificador: Identificador único do template.
            
        Returns:
            Versão mais recente do template.
            
        Raises:
            TemplateNaoEncontradoError: Se o template não for encontrado.
        """
        # Validação para prevenir path traversal
        self._validar_seguranca_caminho(identificador)
        
        # Lista todos os arquivos de template para o identificador
        padrao = re.compile(f"{re.escape(identificador)}_([0-9]+)\\.docx$")
        versoes = []
        
        for arquivo in os.listdir(self.templates_dir):
            match = padrao.match(arquivo)
            if match:
                versoes.append(match.group(1))
        
        if not versoes:
            raise TemplateNaoEncontradoError(f"Template não encontrado: {identificador}")
        
        # Retorna a versão mais recente
        return sorted(versoes)[-1]
    
    def obter_template(self, identificador: str, versao: Optional[str] = None) -> BinaryIO:
        """
        Obtém um template específico do repositório.
        
        Args:
            identificador: Identificador único do template.
            versao: Versão específica do template (se None, usa a versão mais recente).
            
        Returns:
            Objeto BinaryIO contendo o conteúdo do template.
            
        Raises:
            TemplateNaoEncontradoError: Se o template não for encontrado.
            VersaoNaoEncontradaError: Se a versão especificada não for encontrada.
        """
        try:
            # Se a versão não foi especificada, obter a mais recente
            if versao is None:
                versao = self._obter_versao_mais_recente(identificador)
            
            # Validação para prevenir path traversal
            self._validar_seguranca_caminho(identificador)
            self._validar_seguranca_caminho(versao)
            
            # Obtém o caminho do arquivo de template
            caminho_template = self._obter_caminho_template(identificador, versao)
            
            # Verifica se o arquivo existe
            if not os.path.exists(caminho_template):
                if versao is None:
                    raise TemplateNaoEncontradoError(f"Template não encontrado: {identificador}")
                else:
                    raise VersaoNaoEncontradaError(
                        f"Versão {versao} não encontrada para o template {identificador}"
                    )
            
            # Abre o arquivo em modo binário
            return open(caminho_template, 'rb')
            
        except (TemplateNaoEncontradoError, VersaoNaoEncontradaError):
            # Repassa as exceções específicas
            raise
        except Exception as e:
            logger.error(f"Erro ao obter template {identificador}: {str(e)}")
            raise TemplateNaoEncontradoError(f"Erro ao obter template: {str(e)}")
    
    def salvar_template(self, 
                       nome: str, 
                       conteudo: BinaryIO, 
                       metadados: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """
        Salva um novo template ou uma nova versão de um template existente.
        
        Args:
            nome: Nome do template.
            conteudo: Conteúdo do template como BinaryIO.
            metadados: Metadados adicionais do template.
            
        Returns:
            Dicionário com as informações do template salvo, incluindo seu identificador.
            
        Raises:
            TemplateInvalidoError: Se o template for inválido.
            ArmazenamentoError: Se ocorrer um erro ao salvar o template.
        """
        try:
            # Valida o template
            self._validar_template(nome, conteudo)
            
            # Prepara metadados
            metadados_completos = metadados.copy() if metadados else {}
            
            # Verifica se é uma atualização de um template existente ou um novo template
            template_existente = None
            for template in self.listar_templates():
                if template.get('nome') == nome:
                    template_existente = template
                    break
            
            if template_existente:
                # É uma atualização, obtém o identificador existente
                identificador = template_existente.get('identificador')
                versoes_existentes = template_existente.get('versoes', [])
                versao = self._gerar_versao()
                
                metadados_completos.update({
                    'identificador': identificador,
                    'nome': nome,
                    'versoes': versoes_existentes + [versao],
                    'versao_atual': versao,
                    'atualizado_em': datetime.now().isoformat()
                })
            else:
                # É um novo template
                identificador = self._gerar_identificador()
                versao = self._gerar_versao()
                
                metadados_completos.update({
                    'identificador': identificador,
                    'nome': nome,
                    'versoes': [versao],
                    'versao_atual': versao,
                    'criado_em': datetime.now().isoformat(),
                    'atualizado_em': datetime.now().isoformat()
                })
            
            # Salva o arquivo de template
            caminho_template = self._obter_caminho_template(identificador, versao)
            with open(caminho_template, 'wb') as f:
                # Reset position to start
                conteudo.seek(0)
                shutil.copyfileobj(conteudo, f)
            
            # Salva os metadados
            caminho_metadados = self._obter_caminho_metadados(identificador)
            with open(caminho_metadados, 'w', encoding='utf-8') as f:
                json.dump(metadados_completos, f, ensure_ascii=False, indent=2)
            
            logger.info(f"Template '{nome}' salvo com sucesso: {identificador} (versão {versao})")
            return metadados_completos
            
        except TemplateInvalidoError:
            # Repassa as exceções específicas
            raise
        except Exception as e:
            logger.error(f"Erro ao salvar template '{nome}': {str(e)}")
            raise ArmazenamentoError(f"Erro ao salvar template: {str(e)}")
    
    def excluir_template(self, identificador: str, excluir_todas_versoes: bool = False) -> bool:
        """
        Exclui um template do repositório.
        
        Args:
            identificador: Identificador único do template.
            excluir_todas_versoes: Se True, exclui todas as versões; se False, exclui apenas a versão mais recente.
            
        Returns:
            True se a exclusão for bem-sucedida, False caso contrário.
            
        Raises:
            TemplateNaoEncontradoError: Se o template não for encontrado.
        """
        try:
            # Validação para prevenir path traversal
            self._validar_seguranca_caminho(identificador)
            
            # Verifica se o template existe
            caminho_metadados = self._obter_caminho_metadados(identificador)
            if not os.path.exists(caminho_metadados):
                raise TemplateNaoEncontradoError(f"Template não encontrado: {identificador}")
            
            # Carrega os metadados
            with open(caminho_metadados, 'r', encoding='utf-8') as f:
                metadados = json.load(f)
            
            versoes = metadados.get('versoes', [])
            
            if excluir_todas_versoes:
                # Exclui todas as versões
                for versao in versoes:
                    caminho_template = self._obter_caminho_template(identificador, versao)
                    if os.path.exists(caminho_template):
                        os.remove(caminho_template)
                
                # Exclui os metadados
                os.remove(caminho_metadados)
                logger.info(f"Template {identificador} excluído completamente com {len(versoes)} versões")
            else:
                # Exclui apenas a versão mais recente
                if not versoes:
                    # Se não há versões, exclui os metadados apenas
                    os.remove(caminho_metadados)
                    logger.info(f"Template {identificador} excluído (sem versões)")
                    return True
                
                # Obtém a versão mais recente
                versao_atual = sorted(versoes)[-1]
                
                # Exclui o arquivo da versão atual
                caminho_template = self._obter_caminho_template(identificador, versao_atual)
                if os.path.exists(caminho_template):
                    os.remove(caminho_template)
                
                # Atualiza os metadados
                versoes.remove(versao_atual)
                if versoes:
                    # Ainda tem versões, atualiza apenas os metadados
                    metadados['versoes'] = versoes
                    metadados['versao_atual'] = sorted(versoes)[-1]
                    with open(caminho_metadados, 'w', encoding='utf-8') as f:
                        json.dump(metadados, f, ensure_ascii=False, indent=2)
                    logger.info(f"Versão {versao_atual} do template {identificador} excluída")
                else:
                    # Não tem mais versões, exclui os metadados também
                    os.remove(caminho_metadados)
                    logger.info(f"Template {identificador} excluído (última versão)")
            
            return True
            
        except TemplateNaoEncontradoError:
            # Repassa as exceções específicas
            raise
        except Exception as e:
            logger.error(f"Erro ao excluir template {identificador}: {str(e)}")
            return False
    
    def obter_metadados(self, identificador: str, versao: Optional[str] = None) -> Dict[str, Any]:
        """
        Obtém os metadados de um template específico.
        
        Args:
            identificador: Identificador único do template.
            versao: Versão específica do template (se None, usa a versão mais recente).
            
        Returns:
            Dicionário contendo os metadados do template.
            
        Raises:
            TemplateNaoEncontradoError: Se o template não for encontrado.
            VersaoNaoEncontradaError: Se a versão especificada não for encontrada.
        """
        try:
            # Validação para prevenir path traversal
            self._validar_seguranca_caminho(identificador)
            
            # Obtém o caminho do arquivo de metadados
            caminho_metadados = self._obter_caminho_metadados(identificador)
            
            # Verifica se o arquivo existe
            if not os.path.exists(caminho_metadados):
                raise TemplateNaoEncontradoError(f"Template não encontrado: {identificador}")
            
            # Carrega os metadados
            with open(caminho_metadados, 'r', encoding='utf-8') as f:
                metadados = json.load(f)
            
            # Se a versão foi especificada, verifica se existe
            if versao is not None:
                if versao not in metadados.get('versoes', []):
                    raise VersaoNaoEncontradaError(
                        f"Versão {versao} não encontrada para o template {identificador}"
                    )
                
                # Adiciona informações específicas da versão aos metadados
                metadados['versao_atual'] = versao
            
            return metadados
            
        except (TemplateNaoEncontradoError, VersaoNaoEncontradaError):
            # Repassa as exceções específicas
            raise
        except Exception as e:
            logger.error(f"Erro ao obter metadados do template {identificador}: {str(e)}")
            raise TemplateNaoEncontradoError(f"Erro ao obter metadados: {str(e)}")