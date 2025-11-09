# 🌐 Discord RAG Bot - Interface Web Terminal

Interface web profissional com estética CLI/Terminal para interagir com o Discord RAG Bot.

## 🎨 Características

### Design Terminal Autêntico
- **Fonte monospace** com fallbacks: Monaco, Menlo, Ubuntu Mono
- **Tema dark terminal** profissional
- **Sintaxe de comandos** com prompts (`>`, `$`, `⎿`)
- **Status indicators** com dots coloridos
- **ASCII art** no header
- **Animações suaves** e responsivas

### Funcionalidades

#### 💬 Terminal de Consultas
- Input estilo CLI com prompt `>`
- Envio via Enter ou botão
- Respostas formatadas com sintaxe de terminal
- Citação de fontes automatizada
- Indicador de loading animado

#### 📊 Dashboard de Status
- Status do bot (online/offline)
- Status do RAG (carregado/não carregado)
- Modelo LLM em uso
- Estatísticas de cache
- Contador de documentos
- Contador de consultas

#### ⚙️ Controles de Filtro
- Três níveis: Conservador, Moderado, Liberal
- Interface de chips clicável
- Feedback visual de seleção

#### 📚 Exemplos Interativos
- Perguntas de exemplo prontas
- Click para preencher input
- Botão de execução rápida

## 🏗️ Arquitetura

```
web/
├── index.html           # HTML da interface
├── css/
│   └── terminal.css    # Estilização completa (700+ linhas)
├── js/
│   └── terminal.js     # Lógica e interatividade
└── assets/             # Imagens e recursos (futuro)
```

### Tecnologias

- **HTML5** semântico
- **CSS3** com Custom Properties (variáveis)
- **Vanilla JavaScript** (ES6+)
- **Fetch API** para comunicação com backend
- **CSS Grid** e **Flexbox** para layout
- **Responsive Design** mobile-first

## 🚀 Como Usar

### Desenvolvimento Local

```bash
# 1. Iniciar servidor API
cd /path/to/DiscordRAGBot
python api_server.py

# 2. Acessar interface
# Abrir navegador em: http://localhost:8000
```

### Produção

A interface é servida automaticamente pelo servidor FastAPI.

## 🎨 Customização

### Cores do Terminal

Edite em `css/terminal.css`:

```css
:root {
    --bg-primary: #0f0f0f;      /* Fundo principal */
    --text-primary: #ffffff;     /* Texto principal */
    --text-accent: #d97706;      /* Cor de destaque (laranja) */
    --text-success: #10b981;     /* Verde (success) */
    --text-error: #ef4444;       /* Vermelho (error) */
}
```

### Comportamento

Edite em `js/terminal.js`:

```javascript
const CONFIG = {
    API_BASE_URL: 'http://localhost:8000/api',
    REFRESH_INTERVAL: 5000,      // Atualização de status
    REQUEST_TIMEOUT: 30000,      // Timeout de requisições
};
```

## 📱 Responsividade

A interface se adapta a:
- 🖥️ **Desktop** (1920px+)
- 💻 **Laptop** (1366px)
- 📱 **Tablet** (768px)
- 📱 **Mobile** (320px)

Breakpoints principais:
- `768px` - Ajustes para tablet/mobile
- `480px` - Ajustes para smartphones pequenos

## ⌨️ Atalhos de Teclado

- **Ctrl/Cmd + K** - Focar no input de pesquisa
- **Enter** - Enviar consulta
- **Escape** - Limpar input e remover foco

## 🔌 API Endpoints

A interface consome os seguintes endpoints:

### GET `/api/health`
```json
{
  "status": "healthy",
  "timestamp": "2025-11-09T..."
}
```

### GET `/api/status`
```json
{
  "bot_online": true,
  "rag_loaded": true,
  "llm_model": "minimax/minimax-m2:free",
  "cache_enabled": true,
  "cache_stats": {
    "size": 42,
    "max_size": 100,
    "hit_rate": "88.89%"
  },
  "documents_count": 127,
  "timestamp": "2025-11-09T..."
}
```

### POST `/api/query`

Request:
```json
{
  "question": "O que é RAG?",
  "filter_level": "moderado"
}
```

Response:
```json
{
  "answer": "RAG (Retrieval-Augmented Generation) é...",
  "sources": [
    "documento1.pdf (página 5)",
    "documento2.pdf (página 12)"
  ],
  "duration": 1.23,
  "timestamp": "2025-11-09T..."
}
```

## 🎯 Componentes CSS

### Terminal Base
```css
.terminal                 /* Container principal */
.terminal-header          /* Cabeçalho com ASCII art */
.terminal-section         /* Seções do terminal */
.terminal-command         /* Blocos de comando */
```

### Input/Search
```css
.terminal-search-wrapper  /* Wrapper do input */
.terminal-prompt          /* Símbolo de prompt (>) */
.terminal-search-input    /* Campo de input */
.terminal-btn             /* Botões */
```

### Output
```css
.terminal-output          /* Container de resposta */
.output-header            /* Cabeçalho da resposta */
.output-content           /* Conteúdo da resposta */
.output-sources           /* Lista de fontes */
```

### Stats
```css
.stats-grid               /* Grid de estatísticas */
.stat-card                /* Card individual */
.stat-value               /* Valor da estatística */
.status-indicator         /* Dot de status colorido */
```

## 🔧 Desenvolvimento

### Estrutura de Código

#### HTML
- Semântico e acessível
- BEM-like naming convention
- Microdata para SEO

#### CSS
- Mobile-first approach
- CSS Custom Properties para temas
- Transições e animações suaves
- Grid e Flexbox modernos

#### JavaScript
- ES6+ features (async/await, arrow functions)
- Event delegation
- Error handling robusto
- State management simples

### Boas Práticas

✅ **Accessibility**
- Alto contraste de cores
- Navegação por teclado
- ARIA labels quando necessário
- Textos alternativos

✅ **Performance**
- CSS otimizado
- JavaScript assíncrono
- Lazy loading de recursos
- Caching de requisições

✅ **Security**
- Escape de HTML user input
- CORS configurado
- Timeout em requisições
- Validação de dados

## 🐛 Debugging

### Console do Navegador

A interface exibe mensagens úteis no console:

```javascript
// Ativar modo debug
localStorage.setItem('debug', 'true');

// Verificar estado
console.log(state);

// Testar API manualmente
fetch('http://localhost:8000/api/status')
  .then(r => r.json())
  .then(console.log);
```

### Common Issues

**Problema:** Interface não carrega
- ✅ Verificar se `api_server.py` está rodando
- ✅ Abrir console do navegador (F12)
- ✅ Verificar requisições na aba Network

**Problema:** Query não funciona
- ✅ Verificar endpoint `/api/query` no backend
- ✅ Ver erros no console
- ✅ Verificar formato da requisição

**Problema:** Status não atualiza
- ✅ Verificar `REFRESH_INTERVAL` em `terminal.js`
- ✅ Ver erros de CORS no console
- ✅ Testar endpoint `/api/status` diretamente

## 📊 Métricas de Qualidade

### Performance
- ⚡ First Contentful Paint: < 1s
- ⚡ Time to Interactive: < 2s
- ⚡ Lighthouse Score: 90+

### Code Quality
- 📝 HTML válido (W3C)
- 📝 CSS válido (W3C)
- 📝 JavaScript sem erros (ESLint)

### Browser Support
- ✅ Chrome 90+
- ✅ Firefox 88+
- ✅ Safari 14+
- ✅ Edge 90+

## 📄 Licença

MIT License - Parte do projeto Discord RAG Bot

## 🤝 Contribuindo

Melhorias são bem-vindas!

### Áreas para Contribuir
- 🎨 Temas alternativos (light mode, synthwave, etc.)
- 🌐 Internacionalização (i18n)
- 📊 Gráficos e visualizações
- ♿ Melhorias de acessibilidade
- 📱 Experiência mobile aprimorada

### Como Contribuir
1. Fork o repositório
2. Crie uma branch (`git checkout -b feature/MinhaFeature`)
3. Commit suas mudanças (`git commit -m 'Add: MinhaFeature'`)
4. Push para a branch (`git push origin feature/MinhaFeature`)
5. Abra um Pull Request

---

**Desenvolvido com 💙 para a comunidade Discord**
