"""
Exceções customizadas para o sistema de peticionamento.
"""

class BaseError(Exception):
    """Classe base para exceções do sistema."""
    pass

class ArquivoNaoEncontradoError(BaseError):
    """Arquivo não encontrado."""
    pass

class DadosInvalidosError(BaseError):
    """Dados inválidos."""
    pass

class ConversaoError(BaseError):
    """Erro na conversão de dados."""
    pass

class TemplateError(BaseError):
    """Erro base para problemas relacionados a templates."""
    pass

class SubstituicaoError(BaseError):
    """Erro na substituição de placeholders."""
    pass

class TemplateNaoEncontradoError(BaseError):
    """Template não encontrado."""
    pass

class TemplateInvalidoError(BaseError):
    """Template inválido."""
    pass

class VersaoNaoEncontradaError(BaseError):
    """Versão do template não encontrada."""
    pass

class ArmazenamentoError(BaseError):
    """Erro de armazenamento."""
    pass

class SegurancaError(BaseError):
    """Violação de segurança."""
    pass

class MetadataError(BaseError):
    """Erro relacionado aos metadados."""
    pass

class FormatoArquivoInvalidoError(BaseError):
    """Erro levantado quando o formato de um arquivo é inválido."""
    pass

# Exceções relacionadas a regras e validações
class RegraError(BaseError):
    """Erro base para problemas relacionados a regras e validações."""
    pass

class RegraValidacaoError(RegraError):
    """Erro levantado quando uma validação de regra falha."""
    pass

class RegraInvalidaError(RegraError):
    """Erro levantado quando uma regra é inválida."""
    pass

# Exceções relacionadas a campos
class CampoError(BaseError):
    """Erro base para problemas relacionados a campos do documento."""
    pass

class CampoInvalidoError(CampoError):
    """Erro levantado quando um campo é inválido."""
    pass

class CampoNaoEncontradoError(CampoError):
    """Erro levantado quando um campo solicitado não foi encontrado."""
    pass

# Exceções relacionadas a configuração
class ConfiguracaoError(BaseError):
    """Erro base para problemas relacionados a configuração."""
    pass

class DadosError(BaseError):
    """Erros relacionados aos dados de entrada."""
    pass

class CampoObrigatorioError(DadosError):
    """Campo obrigatório está ausente."""
    pass

class RegrasError(BaseError):
    """Erros relacionados às regras de negócio."""
    pass

class DocumentoError(BaseError):
    """Erros relacionados à geração de documento."""
    pass 

class ProcessamentoDocumentoError(DocumentoError):
    """Erro ocorrido durante o processamento de um documento."""
    pass 