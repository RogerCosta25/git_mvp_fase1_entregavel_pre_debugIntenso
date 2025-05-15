# Sistema de Peticionamento Jurídico - MVP Fase 1

Este repositório contém o Sistema de Peticionamento Jurídico, desenvolvido para gerar documentos jurídicos automatizados a partir de templates DOCX e dados de entrevistas.

## Correções e Melhorias na Versão Atual

A versão atual do sistema incluiu várias correções e melhorias significativas:

1. **Correção na Detecção e Substituição de Placeholders**:
   - Implementação de solução robusta para detecção e substituição de placeholders no documento
   - Suporte para placeholders fragmentados entre diferentes "runs" do Word
   - Preservação da formatação durante a substituição

2. **Processamento de Seções Condicionais**:
   - Implementação de processamento in-place de seções, evitando perda de conteúdo
   - Suporte para formato padronizado de marcadores de seção: `{{#SECAO_ID}}` e `{{/SECAO_ID}}`
   - Utilitário para converter templates existentes para o formato padronizado

3. **Melhorias nos Logs e Relatórios**:
   - Logs estruturados com categorização de campos ausentes
   - Estatísticas detalhadas do processamento
   - Diagnóstico avançado para problemas de formatação

4. **Processamento Multi-registro**:
   - Suporte para processar múltiplos registros de um CSV em uma única execução
   - Geração de documentos individuais para cada registro

## Estrutura do Projeto

```
mvp_fase1_entregavel/
├── data/                   # Dados de configuração do sistema
│   ├── campos_definicao/   # CSVs do modelo relacional (ver detalhes abaixo)
│   └── condicionais.json   # Regras para ativação de seções condicionais
├── dados/                  # Dados de entrada para processamento
│   ├── dados.csv           # Dados de entrevista em formato CSV
│   └── caso_teste_1.json   # Exemplo de dados em JSON
├── logs/                   # Diretório para arquivos de log
├── output/                 # Diretório para documentos gerados
├── src/                    # Código-fonte do sistema
│   ├── utils/              # Utilitários do sistema
│   └── ...                 # Outros módulos do sistema
├── templates/              # Templates de documentos
│   └── modelo_trabalhista.docx  # Template de exemplo
├── converter_template.ps1  # Script para converter templates para formato padronizado
├── executar_sistema.ps1    # Script para execução do sistema
└── README.md               # Este arquivo
```

## Modelo Relacional de Campos

O sistema utiliza um modelo relacional para definição de campos, composto pelos seguintes arquivos CSV:

- `campos_definicao.csv`: Definições dos campos
- `categorias_campos.csv`: Categorias para agrupamento de campos
- `tipos_dados.csv`: Tipos de dados e formatações
- `regras_ativacao.csv`: Regras de ativação de campos
- `opcoes_selecao.csv`: Opções para campos de seleção

Estes arquivos devem estar localizados em `data/campos_definicao/`.

## Como Executar

### Pré-requisitos

- Python 3.8 ou superior
- Bibliotecas Python necessárias (listadas em `requirements.txt`)

### Passos para Execução

1. **Configurar o ambiente**:
   ```
   pip install -r requirements.txt
   ```

2. **Converter o template para formato padronizado** (opcional, mas recomendado):
   ```
   .\converter_template.ps1
   ```
   Isso criará uma versão do template com os marcadores de seção no formato padronizado.

3. **Executar o sistema**:
   ```
   .\executar_sistema.ps1
   ```

   Ou, alternativamente, executar diretamente o script Python:
   ```
   python main.py --template templates/modelo_trabalhista.docx --csv dados/dados.csv --saida output/documento_gerado.docx
   ```

### Parâmetros de Linha de Comando

O script principal (`main.py`) aceita os seguintes parâmetros:

- `--template`: Caminho para o arquivo de template DOCX. (Padrão: definido em `config.py`)
- `--csv`: Caminho para o arquivo CSV com os dados da entrevista.
- `--dados`: Caminho para o arquivo JSON com os dados da entrevista (usado apenas se `--csv` não for fornecido).
- `--saida`: Caminho para salvar o documento DOCX processado. (Padrão: gerado automaticamente)
- `--debug`: Ativa modo de depuração com logs mais detalhados.
- `--primeiro-registro`: Processa apenas o primeiro registro do CSV (útil para testes).

## Formato do Template

O sistema processa templates DOCX contendo placeholders no formato `{{nome_campo}}`. Além disso, suporta seções condicionais delimitadas por `{{#SECAO_ID}}` e `{{/SECAO_ID}}`.

### Exemplo:

```
{{nome_parte_autora}} solicita...

{{#SECAO_HORAS_EXTRAS}}
Horas extras trabalhadas: {{horas_extras_quantidade}}
Valor devido: {{horas_extras_valor}}
{{/SECAO_HORAS_EXTRAS}}
```

O arquivo `condicionais.json` define quais seções serão incluídas com base nos dados fornecidos.

## Troubleshooting

### Problemas Comuns e Soluções

1. **Placeholders não são substituídos**:
   - Verifique se os nomes dos campos no template correspondem exatamente aos nomes no CSV/JSON
   - Confirme que o template está em formato DOCX (não DOC)
   - Verifique se os placeholders não estão fragmentados entre diferentes "runs" do Word
   - Use o modo debug para obter logs detalhados: `python main.py --debug`

2. **Seções condicionais não funcionam**:
   - Converta o template para o formato padronizado usando `converter_template.ps1`
   - Verifique se as regras em `condicionais.json` correspondem aos nomes dos campos nos dados
   - Confira se o formato é exatamente `{{#SECAO_ID}}` e `{{/SECAO_ID}}`

3. **Erro "Template não encontrado"**:
   - Verifique se o caminho para o template está correto
   - Confirme que o arquivo existe e tem permissões de leitura

## Licença

Este projeto é de uso interno e confidencial. Todos os direitos reservados.
