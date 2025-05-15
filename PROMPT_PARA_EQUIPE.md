# Instruções para Análise e Debug do Sistema de Peticionamento

## Contexto do Projeto
O Sistema de Automação de Peticionamento Jurídico é uma ferramenta desenvolvida para automatizar a geração de petições jurídicas. O sistema está em sua primeira fase (MVP) e precisa de uma análise completa para garantir seu funcionamento adequado.

Estamos desenvolvendo este sistema para escritórios de advocacia que precisam gerar petições jurídicas com eficiência e precisão, substituindo o trabalho manual repetitivo. O sistema utiliza templates DOCX com marcadores no formato `{{nome_campo}}` que são substituídos por dados fornecidos em formato CSV ou JSON.

## Objetivo da Análise
Realizar uma análise completa do sistema, identificar e corrigir problemas, e garantir que o sistema seja capaz de gerar petições corretamente usando o arquivo de dados atual (dados CSV) que contém um caso real.

## Pontos Críticos para Análise

### 1. Processamento de Templates
- Verificar se o sistema está lidando corretamente com todos os marcadores no formato `{{nome_campo}}`
- Analisar o tratamento de campos ausentes
- Verificar a aplicação de regras condicionais para ativação de seções do documento (marcadores `{{#SECAO_ID}}` e `{{/SECAO_ID}}`)
- Testar templates com grande número de campos (o atual tem aproximadamente 150 campos)
- Validar a remoção correta de seções inativas do documento final

### 2. Uso do Modelo Relacional
- Verificar se as tabelas refatoradas (campos_definicao, categorias_campos, etc.) estão sendo carregadas corretamente
- Validar a integração entre o adaptador de modelo relacional e o restante do sistema
- Confirmar que as regras de obrigatoriedade dos campos estão sendo aplicadas corretamente
- Testar o fluxo completo utilizando o modelo relacional
- Verificar se a formatação baseada em tipo de dados está funcionando corretamente

### 3. Manipulação de Dados
- Verificar a leitura correta dos arquivos CSV (prioridade) e JSON (alternativa)
- Validar o tratamento de diferentes separadores de CSV (vírgula, ponto-e-vírgula, tab)
- Testar a robustez do sistema com dados incompletos
- Analisar o tratamento de caracteres especiais
- Verificar a detecção e formatação correta de tipos de dados especiais (moeda, datas, etc.)

### 4. Tabelas de CamposDefinicao
- Verificar a consistência entre todas as tabelas relacionais:
  - `campos_definicao.csv`: Definição principal dos campos
  - `categorias_campos.csv`: Categorias e agrupamento de campos
  - `regras_ativacao.csv`: Regras para visibilidade e obrigatoriedade
  - `tipos_dados.csv`: Tipos de dados e validações
  - `opcoes_selecao.csv`: Opções para campos do tipo lista
- Validar se todos os campos do template estão mapeados corretamente
- Testar o processamento de campos com diferentes tipos e formatos
- Verificar o tratamento de campos obrigatórios vs opcionais
- Analisar a eficácia das transformações definidas no mapeamento
- Garantir que as regras de validação estão sendo aplicadas corretamente

### 5. Logs e Mensagens de Erro
- Verificar se os logs estão sendo gerados corretamente
- Analisar a clareza das mensagens de erro
- Verificar se as estatísticas de processamento estão corretas
- Validar a exibição organizada de campos ausentes por categoria
- Verificar o registro adequado de seções encontradas e processadas

### 6. Performance e Escalabilidade
- Testar o sistema com documentos grandes (até 150 placeholders e 30-40 páginas)
- Analisar o consumo de memória durante o processamento
- Identificar possíveis gargalos de performance
- Testar com tabelas complexas e seções aninhadas
- Sugerir melhorias para escalabilidade

### 7. Processamento de Seções Condicionais
- Verificar a identificação e processamento correto das seções condicionais
- Testar seções aninhadas (uma seção dentro de outra)
- Verificar tratamento de seções que incluem tabelas
- Validar o comportamento com marcadores incompletos ou ausentes
- Testar diferentes combinações de seções ativas/inativas

## Fluxo de Trabalho Recomendado

1. **Configuração do Ambiente**
   - Clone o repositório e instale as dependências usando `pip install -r requirements.txt`
   - Verifique se todos os arquivos necessários estão presentes (veja a lista abaixo)
   - Execute o script `executar_sistema.ps1` para um teste inicial, escolhendo CSV como fonte de dados

2. **Análise do Código**
   - Familiarize-se com a estrutura geral do código
   - Analise o fluxo de dados entre os diferentes componentes
   - Verifique a implementação do modelo relacional e do processamento CSV

3. **Teste com Caso Real**
   - Use o arquivo CSV (`dados.csv`) para testar a geração de documentos
   - Verifique a qualidade do documento gerado
   - Identifique campos ausentes ou mal formatados
   - Compare com a versão gerada pelo JSON para identificar possíveis diferenças

4. **Debug e Correções**
   - Corrija problemas identificados mantendo a arquitetura atual
   - Adicione logs adicionais para diagnóstico se necessário
   - Documente todas as mudanças feitas
   - Teste especificamente o processamento de seções condicionais

5. **Validação**
   - Execute novamente os testes com o caso real após as correções
   - Verifique se todos os problemas foram resolvidos
   - Teste com diferentes configurações (templates, dados, etc.)
   - Prepare um relatório detalhado das descobertas e correções

## Estrutura do Projeto
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
│   └── extrair_mapping_campos_definicao.py # Extração de mapeamentos
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
├── output/                 # Documentos gerados
├── logs/                   # Logs do sistema
├── config.py               # Configurações globais
├── main.py                 # Ponto de entrada
├── requirements.txt        # Dependências
└── executar_sistema.ps1    # Script para execução interativa
```

## Critérios de Aceitação

O trabalho será considerado concluído quando:

1. O sistema processar corretamente o template com o arquivo CSV de dados atual
2. Todos os campos mapeados forem substituídos corretamente no documento
3. As regras condicionais forem aplicadas corretamente com seções ativas/inativas
4. O modelo relacional for utilizado para obtenção e validação dos campos
5. A formatação adequada for aplicada com base nos tipos de dados
6. Todos os erros críticos forem corrigidos
7. Um relatório detalhado for fornecido com as descobertas e correções

## Expectativas de Entrega

1. Código corrigido e funcional
2. Relatório detalhado descrevendo:
   - Problemas encontrados
   - Soluções implementadas
   - Testes realizados
   - Recomendações para melhorias futuras
3. Documentação das mudanças feitas no código
4. Exemplos de documentos gerados antes e depois das correções
5. Análise de performance com documentos grandes
6. Recomendações de otimização

## Lista de Arquivos Necessários

**Arquivos Principais:**
- `main.py`
- `config.py`
- `executar_sistema.ps1`
- `requirements.txt`

**Módulos Core:**
- `src/documento_processor.py`
- `src/motor_regras.py`
- `src/adaptador_modelo_relacional.py`
- `src/processador_csv.py`
- `src/template_repository.py`
- `src/avaliador_condicoes.py`
- `src/logger.py`
- `src/exceptions.py`

**Módulos Auxiliares:**
- `src/extrair_mapping_campos_definicao.py`
- `src/gerador_documento.py`
- `src/template_metadata.py`

**Arquivos de Dados:**
- `data/condicionais.json`
- `data/campos_definicao/campos_definicao.csv`
- `data/campos_definicao/categorias_campos.csv`
- `data/campos_definicao/regras_ativacao.csv`
- `data/campos_definicao/tipos_dados.csv`
- `data/campos_definicao/opcoes_selecao.csv`
- `data/campos_definicao/mapping_campos_definicao.json`

**Templates e Dados de Teste:**
- `templates/modelo_trabalhista.docx`
- `dados/dados.csv`
- `dados/caso_teste_1.json`

## Contato e Suporte

Se tiver dúvidas ou precisar de esclarecimentos adicionais durante a análise, entre em contato imediatamente. Queremos garantir que você tenha todas as informações necessárias para realizar um trabalho completo e eficaz.

Boa sorte e agradecemos sua contribuição para este projeto! 