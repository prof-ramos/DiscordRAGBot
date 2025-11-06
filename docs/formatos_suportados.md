# Suporte a Múltiplos Formatos de Documentos

O Discord RAG Bot agora suporta o carregamento de documentos em diversos formatos, permitindo maior flexibilidade na gestão da base de conhecimento.

## Formatos Suportados

### 📄 Documentos de Texto

#### PDF (`.pdf`)
- **Descrição**: Portable Document Format
- **Loader**: `PyPDFLoader` (LangChain)
- **Características**:
  - Extração de texto de arquivos PDF
  - Suporta PDFs de múltiplas páginas
  - Preserva metadados de página
- **Uso**: Ideal para documentos formais, manuais, relatórios

#### Microsoft Word (`.docx`, `.doc`)
- **Descrição**: Documentos do Microsoft Word
- **Loader**: `UnstructuredWordDocumentLoader` (LangChain)
- **Características**:
  - Suporta formatos DOCX (Office 2007+) e DOC (Office 97-2003)
  - Extrai texto mantendo a estrutura básica
  - Compatível com formatações complexas
- **Uso**: Documentos corporativos, relatórios, especificações

#### Texto Simples (`.txt`)
- **Descrição**: Arquivos de texto simples
- **Loader**: `TextLoader` (LangChain)
- **Características**:
  - Codificação UTF-8
  - Carregamento direto sem processamento
  - Leve e eficiente
- **Uso**: Notas, logs de texto, documentação simples

#### Markdown (`.md`, `.rst`)
- **Descrição**: Arquivos de marcação leve
- **Loader**: `UnstructuredMarkdownLoader` (Markdown), `TextLoader` (ReStructuredText)
- **Características**:
  - Suporta sintaxe Markdown e ReStructuredText
  - Preserva estrutura hierárquica
  - Ideal para documentação técnica
- **Uso**: READMEs, documentação de projetos, wikis

### 📊 Dados Estruturados

#### CSV (`.csv`)
- **Descrição**: Valores Separados por Vírgula
- **Loader**: `CSVLoader` (customizado)
- **Características**:
  - Converte cada linha em um documento
  - Inclui cabeçalhos de coluna no contexto
  - Suporta diferentes encodings
  - Preserva metadados (número da linha, colunas)
- **Formato de saída**: `"Coluna1: valor1, Coluna2: valor2, ..."`
- **Uso**: Dados tabulares, listas, catálogos

#### Excel (`.xlsx`, `.xls`)
- **Descrição**: Planilhas do Microsoft Excel
- **Loader**: `ExcelLoader` (customizado)
- **Características**:
  - Suporta formatos modernos (XLSX) e legados (XLS)
  - Processa múltiplas planilhas
  - Converte cada linha em documento de texto
  - Preserva metadados (planilha, linha, colunas)
- **Engines**:
  - `openpyxl` para arquivos .xlsx
  - `xlrd` para arquivos .xls
- **Formato de saída**: Similar ao CSV com informação de planilha
- **Uso**: Relatórios financeiros, inventários, bases de dados

## Como Usar

### 1. Preparação de Documentos

Coloque seus documentos no diretório `data/` do projeto:

```bash
DiscordRAGBot/
├── data/
│   ├── manual.pdf
│   ├── especificacoes.docx
│   ├── notas.txt
│   ├── README.md
│   ├── produtos.csv
│   └── relatorio.xlsx
```

### 2. Indexação de Documentos

Execute o script de carregamento:

```bash
python load.py
```

O script irá:
1. Detectar automaticamente todos os arquivos suportados
2. Carregar cada arquivo com o loader apropriado
3. Dividir os documentos em chunks
4. Gerar embeddings
5. Indexar no Supabase

### 3. Saída Esperada

```
🚀 INDEXAÇÃO DE DOCUMENTOS - RAG
============================================================

Arquivos suportados encontrados:
  - .pdf: 1 arquivo(s)
  - .docx: 1 arquivo(s)
  - .txt: 1 arquivo(s)
  - .csv: 1 arquivo(s)
  - .xlsx: 1 arquivo(s)

Carregando arquivo: manual.pdf
Arquivo carregado com sucesso: manual.pdf (15 páginas)

Carregando arquivo: especificacoes.docx
Arquivo carregado com sucesso: especificacoes.docx (3 seções)

...

✅ INDEXAÇÃO COMPLETA!
============================================================
📊 Total de vetores: 234
📁 Localização: Supabase (tabela 'documents')

💡 Próximo passo: Execute 'python bot.py' para iniciar o bot
============================================================
```

## Configurações Avançadas

### Loaders Customizados

#### CSVLoader

```python
from src.utils.document_loaders import CSVLoader

# Configuração básica
loader = CSVLoader(
    file_path="data/produtos.csv",
    encoding="utf-8",
    include_headers=True,
    source_column="id"  # Opcional: coluna para identificar fonte
)

documents = loader.load()
```

**Parâmetros**:
- `file_path`: Caminho para o arquivo CSV
- `encoding`: Codificação do arquivo (padrão: `utf-8`)
- `include_headers`: Incluir nomes de colunas (padrão: `True`)
- `source_column`: Coluna para usar como identificador (opcional)

#### ExcelLoader

```python
from src.utils.document_loaders import ExcelLoader

# Carregar planilha específica
loader = ExcelLoader(
    file_path="data/relatorio.xlsx",
    sheet_name="Vendas",  # ou índice: 0, 1, 2...
    include_headers=True
)

documents = loader.load()
```

**Parâmetros**:
- `file_path`: Caminho para o arquivo Excel
- `sheet_name`: Nome ou índice da planilha (padrão: `0`)
- `include_headers`: Incluir nomes de colunas (padrão: `True`)
- `source_column`: Coluna para usar como identificador (opcional)

#### MultiSheetExcelLoader

Para processar todas as planilhas de um arquivo Excel:

```python
from src.utils.document_loaders import MultiSheetExcelLoader

loader = MultiSheetExcelLoader(
    file_path="data/relatorio_completo.xlsx",
    include_headers=True
)

documents = loader.load()  # Carrega todas as planilhas
```

### Processamento Lazy

Para arquivos grandes, use carregamento lazy para economizar memória:

```python
# CSV
loader = CSVLoader("data/grande_dataset.csv")
for document in loader.lazy_load():
    process_document(document)

# Excel
loader = ExcelLoader("data/planilha_grande.xlsx")
for document in loader.lazy_load():
    process_document(document)
```

## Metadados Preservados

Cada documento carregado preserva metadados importantes:

### Documentos de Texto (PDF, DOCX, TXT, MD)
```python
{
    "source": "data/manual.pdf",
    "page": 5  # Para PDF
}
```

### CSV
```python
{
    "source": "data/produtos.csv - Linha 42",
    "row": 42,
    "format": "csv",
    "columns": ["id", "nome", "preco", "quantidade"]
}
```

### Excel
```python
{
    "source": "data/vendas.xlsx - Janeiro - Linha 15",
    "row": 15,
    "sheet": "Janeiro",
    "format": "excel",
    "file_type": ".xlsx",
    "columns": ["data", "produto", "valor", "vendedor"]
}
```

## Tratamento de Erros

O sistema é robusto e continua processando mesmo se alguns arquivos falharem:

```python
# Se um arquivo falhar
⚠️  Falha ao carregar dados_corrompidos.csv: File encoding error
✅ Arquivo carregado com sucesso: outros_dados.xlsx

# Resumo ao final
⚠️  Alguns arquivos falharam ao carregar
    - Arquivos com falha: 1
    - Arquivos processados com sucesso: 8
```

## Melhores Práticas

### 1. Organização de Arquivos
```
data/
├── manuais/
│   ├── manual_usuario.pdf
│   └── manual_tecnico.docx
├── documentacao/
│   ├── README.md
│   └── api_docs.md
├── dados/
│   ├── produtos.csv
│   └── relatorio_mensal.xlsx
└── notas/
    └── observacoes.txt
```

### 2. Nomeação de Arquivos
- Use nomes descritivos
- Evite caracteres especiais
- Prefira underscores ao invés de espaços
- ✅ `relatorio_vendas_2024.xlsx`
- ❌ `relatório vendas (2024).xlsx`

### 3. Codificação de Arquivos
- Use UTF-8 sempre que possível
- Para CSVs com caracteres especiais, verifique a codificação
- Especifique explicitamente se necessário

### 4. Tamanho de Arquivos
- **CSV/Excel grandes**: Use lazy loading
- **PDFs com muitas páginas**: Considere dividir
- **Recomendado**: Arquivos individuais < 50MB

### 5. Estrutura de Dados Tabulares

Para CSV e Excel, estruture os dados de forma que cada linha represente uma unidade de informação completa:

**Bom**:
```csv
produto,descricao,categoria,preco
Mouse,Mouse óptico USB,Periféricos,25.90
Teclado,Teclado mecânico RGB,Periféricos,199.90
```

**Evite**:
```csv
Produtos
Nome,Preço
Mouse,25.90
(metadados misturados com dados)
```

## Requisitos de Sistema

As seguintes bibliotecas são necessárias:

```bash
# Instaladas automaticamente via requirements.txt
python-docx      # Para arquivos DOCX/DOC
openpyxl         # Para arquivos XLSX
xlrd             # Para arquivos XLS
pandas           # Processamento de dados tabulares
unstructured     # Carregamento avançado de documentos
python-magic-bin # Detecção de tipos de arquivo
```

## Limitações Conhecidas

1. **Arquivos DOC antigos**: Podem ter suporte limitado dependendo da complexidade
2. **Fórmulas Excel**: Apenas valores são extraídos, não fórmulas
3. **Imagens**: Texto em imagens não é extraído automaticamente
4. **Formatação**: Formatação visual não é preservada (apenas texto)
5. **Tabelas complexas**: Tabelas mescladas podem não ser processadas perfeitamente

## Solução de Problemas

### Erro ao carregar arquivo DOCX
```
Erro: Package not found
```
**Solução**: Instale `python-docx`:
```bash
pip install python-docx
```

### Erro ao carregar arquivo XLSX
```
Erro: Missing optional dependency 'openpyxl'
```
**Solução**: Instale `openpyxl`:
```bash
pip install openpyxl
```

### Erro ao carregar arquivo XLS
```
Erro: Missing optional dependency 'xlrd'
```
**Solução**: Instale `xlrd`:
```bash
pip install xlrd
```

### Erro de encoding em CSV
```
Erro: 'utf-8' codec can't decode byte
```
**Solução**: Especifique a codificação correta:
```python
loader = CSVLoader("arquivo.csv", encoding="latin-1")
```

### Arquivo não reconhecido
```
Erro: Tipo de arquivo não suportado: .xyz
```
**Solução**: Verifique se o arquivo está na lista de formatos suportados e se a extensão está correta.

## Exemplos Práticos

### Exemplo 1: Base de Conhecimento de Produtos

```
data/
├── catalogo.xlsx        # Planilha com lista de produtos
├── manual_uso.pdf       # Manual de uso dos produtos
└── perguntas_frequentes.md  # FAQ
```

### Exemplo 2: Documentação Técnica

```
data/
├── api_documentation.md
├── architecture.docx
├── endpoints.csv
└── changelog.txt
```

### Exemplo 3: Base de Dados Corporativa

```
data/
├── funcionarios.xlsx
├── politicas.pdf
├── procedimentos.docx
└── contacts.csv
```

## Próximos Passos

Após indexar seus documentos:

1. **Inicie o bot**: `python bot.py`
2. **Teste consultas**: Pergunte ao bot sobre o conteúdo
3. **Monitore logs**: Verifique logs para garantir carregamento correto
4. **Atualize conteúdo**: Re-execute `load.py` quando adicionar novos documentos

## Suporte

Para mais informações, consulte:
- [Instalação](installation.md)
- [Uso do Bot](usage.md)
- [Solução de Problemas](troubleshooting.md)
- [Arquitetura](architecture.md)
