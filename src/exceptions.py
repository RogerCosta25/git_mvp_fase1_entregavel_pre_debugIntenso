"""
Exceções personalizadas para o sistema de peticionamento.
Todas as exceções específicas do sistema derivam da classe base PeticionamentoError.
"""

class PeticionamentoError(Exception):
    """Classe base para todas as exceções do sistema de peticionamento."""
    pass

# Exceções relacionadas a templates
class TemplateError(PeticionamentoError):
    """Erro base para problemas relacionados a templates."""
    pass

class TemplateNaoEncontradoError(TemplateError):
    """Erro levantado quando um template solicitado não foi encontrado."""
    pass

class TemplateInvalidoError(TemplateError):
    """Erro levantado quando um template é considerado inválido."""
    pass

class VersaoNaoEncontradaError(TemplateError):
    """Erro levantado quando uma versão específica de um template não foi encontrada."""
    pass

class ArmazenamentoError(PeticionamentoError):
    """Erro levantado quando ocorre um problema ao armazenar dados."""
    pass

class SegurancaError(PeticionamentoError):
    """Erro levantado quando uma operação viola restrições de segurança."""
    pass

# Exceções relacionadas a arquivos
class ArquivoError(PeticionamentoError):
    """Erro base para problemas relacionados a arquivos."""
    pass

class ArquivoNaoEncontradoError(ArquivoError):
    """Erro levantado quando um arquivo solicitado não foi encontrado."""
    pass

class FormatoArquivoInvalidoError(ArquivoError):
    """Erro levantado quando o formato de um arquivo é inválido."""
    pass

# Exceções relacionadas a regras e validações
class RegraError(PeticionamentoError):
    """Erro base para problemas relacionados a regras e validações."""
    pass

class RegraInvalidaError(RegraError):
    """Erro levantado quando uma regra é considerada inválida."""
    pass

class AvaliacaoRegraError(RegraError):
    """Erro levantado quando ocorre um problema ao avaliar uma regra."""
    pass

# Exceções relacionadas a campos
class CampoError(PeticionamentoError):
    """Erro base para problemas relacionados a campos do documento."""
    pass

class CampoInvalidoError(CampoError):
    """Erro levantado quando um campo é considerado inválido."""
    pass

class CampoNaoEncontradoError(CampoError):
    """Erro levantado quando um campo não foi encontrado."""
    pass

# Exceções relacionadas a configuração
class ConfiguracaoError(PeticionamentoError):
    """Erro base para problemas relacionados a configuração."""
    pass

class DadosError(PeticionamentoError):
    """Erros relacionados aos dados de entrada."""
    pass

class DadosInvalidosError(DadosError):
    """Dados inválidos ou mal formatados."""
    pass

class CampoObrigatorioError(DadosError):
    """Campo obrigatório está ausente."""
    pass

class RegrasError(PeticionamentoError):
    """Erros relacionados às regras de negócio."""
    pass

class DocumentoError(PeticionamentoError):
    """Erros relacionados à geração de documento."""
    pass 

class ProcessamentoDocumentoError(DocumentoError):
    """Erro ocorrido durante o processamento de um documento."""
    pass 