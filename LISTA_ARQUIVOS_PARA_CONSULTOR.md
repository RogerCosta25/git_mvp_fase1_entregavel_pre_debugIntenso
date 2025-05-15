# Lista de Arquivos para Entrega ao Consultor

Esta pasta contém todos os arquivos necessários para a análise e debug do sistema de peticionamento. A estrutura completa foi verificada e os arquivos atualizados conforme as correções implementadas.

## 1. Estrutura Geral

Todos os arquivos estão organizados na pasta `mvp_fase1_entregavel` e possuem a seguinte estrutura:

```
mvp_fase1_entregavel/
├── src/                    # Código fonte
│   ├── documento_processor.py      # Processamento de documentos
│   ├── motor_regras.py             # Motor de regras condicionais
│   ├── adaptador_modelo_relacional.py # Adaptador para tabelas refatoradas
│   ├── processador_csv.py          # Processamento de arquivos CSV
│   ├── template_repository.py      # Gerenciamento de templates
│   ├── logger.py                   # Sistema de logs
│   ├── exceptions.py               # Exceções personalizadas
│   ├── extrair_mapping_campos_definicao.py # Extração de mapeamentos
│   ├── avaliador_condicoes.py      # Avaliação de condições
│   ├── gerador_documento.py        # Geração de documentos
│   └── template_metadata.py        # Metadata dos templates
├── data/                   # Dados de configuração
│   ├── condicionais.json   # Regras condicionais
│   └── campos_definicao/   # Definições de campos (modelo relacional)
│       ├── campos_definicao.csv     # Tabela principal de campos
│       ├── categorias_campos.csv    # Categorias dos campos
│       ├── regras_ativacao.csv      # Regras de ativação/obrigatoriedade
│       ├── tipos_dados.csv          # Tipos de dados
│       ├── opcoes_selecao.csv       # Opções de seleção para campos do tipo lista
│       └── mapping_campos_definicao.json # Mapeamento de campos (legado)
├── templates/              # Templates DOCX
│   └── modelo_trabalhista.docx
├── dados/                  # Arquivos de dados
│   ├── dados.csv           # Dados CSV para teste (formato principal)
│   └── caso_teste_1.json   # Dados JSON para teste (formato alternativo)
├── output/                 # Documentos gerados (criada automaticamente)
├── logs/                   # Logs do sistema (criada automaticamente)
├── config.py               # Configurações globais
├── main.py                 # Ponto de entrada
├── requirements.txt        # Dependências
├── README.md               # Documentação principal
├── PROMPT_PARA_EQUIPE.md   # Instruções de análise e debug
├── DOCUMENTACAO_PARA_CONSULTOR.md  # Documentação técnica com correções
└── executar_sistema.ps1    # Script para execução interativa
```

## 2. Arquivos Principais para Análise

Os arquivos mais importantes para a análise são:

1. `main.py` - Ponto de entrada do sistema, integra todos os componentes
2. `src/documento_processor.py` - Processamento de documentos com suporte a seções condicionais
3. `src/processador_csv.py` - Processamento de arquivos CSV como entrada de dados
4. `src/motor_regras.py` - Avaliação de regras condicionais e controle de seções ativas
5. `executar_sistema.ps1` - Script interativo para execução do sistema

## 3. Arquivos de Dados e Configuração

1. `config.py` - Configurações globais do sistema
2. `data/condicionais.json` - Regras condicionais para seções do documento
3. `data/campos_definicao/*.csv` - Tabelas do modelo relacional
4. `dados/dados.csv` - Arquivo CSV com dados para testes (preferencial)
5. `dados/caso_teste_1.json` - Arquivo JSON alternativo para testes

## 4. Documentação

1. `README.md` - Visão geral do sistema e instruções de uso
2. `PROMPT_PARA_EQUIPE.md` - Instruções detalhadas para análise e debug
3. `DOCUMENTACAO_PARA_CONSULTOR.md` - Documentação técnica sobre as correções implementadas

## 5. Instruções para Execução

Após descompactar a pasta, o sistema pode ser executado através do script interativo:

```powershell
.\executar_sistema.ps1
```

Ou diretamente via linha de comando:

```bash
# Para usar CSV (recomendado):
python main.py --template templates/modelo_trabalhista.docx --csv dados/dados.csv --debug

# Para usar JSON (alternativo):
python main.py --template templates/modelo_trabalhista.docx --dados dados/caso_teste_1.json --debug
```

## 6. Verificação de Completude

- Todos os arquivos essenciais estão presentes
- Dependências estão listadas em `requirements.txt`
- Documentação atualizada com todas as mudanças
- Estrutura de pastas organizada logicamente
- Exemplos e dados de teste incluídos

---

Esperamos que esta estrutura facilite sua análise. Se precisar de arquivos adicionais ou esclarecimentos, por favor, entre em contato. 