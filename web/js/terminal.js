/**
 * Discord RAG Bot - Terminal Interface JavaScript
 * Professional CLI-style web interface
 */

// ============================================================================
// Configuration
// ============================================================================

const CONFIG = {
    API_BASE_URL: 'http://localhost:8000/api',
    REFRESH_INTERVAL: 5000,  // 5 seconds
    REQUEST_TIMEOUT: 30000,  // 30 seconds
};

// ============================================================================
// State Management
// ============================================================================

const state = {
    currentFilter: 'moderado',
    queriesCount: 0,
    startTime: Date.now(),
    botStatus: 'checking',
};

// ============================================================================
// DOM Elements
// ============================================================================

const elements = {
    queryInput: null,
    sendBtn: null,
    responseSection: null,
    responseContent: null,
    responseSources: null,
    responseTime: null,
    loadingIndicator: null,
    statusDot: null,
    statusText: null,
    filterChips: null,
    exampleItems: null,
    // Stats
    botStatusValue: null,
    ragStatusValue: null,
    llmModelValue: null,
    cacheStatusValue: null,
    docsCountValue: null,
    queriesCountValue: null,
    uptime: null,
};

// ============================================================================
// Initialization
// ============================================================================

document.addEventListener('DOMContentLoaded', () => {
    initializeElements();
    attachEventListeners();
    startUptimeCounter();
    checkBotStatus();

    // Periodic status check
    setInterval(checkBotStatus, CONFIG.REFRESH_INTERVAL);
});

function initializeElements() {
    elements.queryInput = document.getElementById('query-input');
    elements.sendBtn = document.getElementById('send-query');
    elements.responseSection = document.getElementById('response-section');
    elements.responseContent = document.getElementById('response-content');
    elements.responseSources = document.getElementById('response-sources');
    elements.responseTime = document.getElementById('response-time');
    elements.loadingIndicator = document.getElementById('loading-indicator');
    elements.statusDot = document.getElementById('bot-status');
    elements.statusText = document.getElementById('status-text');
    elements.filterChips = document.querySelectorAll('.filter-chip');
    elements.exampleItems = document.querySelectorAll('.example-item');

    // Stats
    elements.botStatusValue = document.getElementById('bot-status-value');
    elements.ragStatusValue = document.getElementById('rag-status-value');
    elements.llmModelValue = document.getElementById('llm-model-value');
    elements.cacheStatusValue = document.getElementById('cache-status-value');
    elements.docsCountValue = document.getElementById('docs-count-value');
    elements.queriesCountValue = document.getElementById('queries-count-value');
    elements.uptime = document.getElementById('uptime');
}

// ============================================================================
// Event Listeners
// ============================================================================

function attachEventListeners() {
    // Send query
    elements.sendBtn.addEventListener('click', handleSendQuery);
    elements.queryInput.addEventListener('keypress', (e) => {
        if (e.key === 'Enter') {
            handleSendQuery();
        }
    });

    // Filter chips
    elements.filterChips.forEach(chip => {
        chip.addEventListener('click', () => {
            elements.filterChips.forEach(c => c.classList.remove('active'));
            chip.classList.add('active');
            state.currentFilter = chip.dataset.filter;
        });
    });

    // Example items
    elements.exampleItems.forEach(item => {
        item.addEventListener('click', () => {
            const exampleText = item.dataset.example;
            elements.queryInput.value = exampleText;
            elements.queryInput.focus();
        });

        const tryBtn = item.querySelector('.example-try');
        if (tryBtn) {
            tryBtn.addEventListener('click', (e) => {
                e.stopPropagation();
                const exampleText = item.dataset.example;
                elements.queryInput.value = exampleText;
                handleSendQuery();
            });
        }
    });
}

// ============================================================================
// Query Handling
// ============================================================================

async function handleSendQuery() {
    const question = elements.queryInput.value.trim();

    if (!question) {
        showError('Por favor, digite uma pergunta.');
        return;
    }

    showLoading(true);
    hideResponse();

    try {
        const startTime = Date.now();
        const response = await sendQuery(question, state.currentFilter);
        const duration = ((Date.now() - startTime) / 1000).toFixed(2);

        showResponse(response, duration);
        state.queriesCount++;
        updateQueriesCount();

        // Clear input
        elements.queryInput.value = '';

    } catch (error) {
        showError(error.message || 'Erro ao processar consulta.');
    } finally {
        showLoading(false);
    }
}

async function sendQuery(question, filterLevel) {
    // Simulated API call - replace with actual API when backend is ready
    return new Promise((resolve, reject) => {
        setTimeout(() => {
            // Simulated response
            resolve({
                answer: `Esta é uma resposta simulada para a pergunta: "${question}".\n\nO bot está processando com o nível de filtro: ${filterLevel}.\n\nQuando a API REST estiver implementada, você receberá respostas reais baseadas nos documentos indexados no Supabase.`,
                sources: [
                    'documento1.pdf (página 5)',
                    'documento2.pdf (página 12)',
                    'documento3.pdf (página 3)',
                ],
            });
        }, 1500);
    });

    /* Real API call - uncomment when backend is ready
    const response = await fetch(`${CONFIG.API_BASE_URL}/query`, {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
        },
        body: JSON.stringify({
            question,
            filter_level: filterLevel,
        }),
        signal: AbortSignal.timeout(CONFIG.REQUEST_TIMEOUT),
    });

    if (!response.ok) {
        throw new Error(`Erro HTTP: ${response.status}`);
    }

    return await response.json();
    */
}

// ============================================================================
// Response Display
// ============================================================================

function showResponse(response, duration) {
    elements.responseContent.textContent = response.answer;
    elements.responseTime.textContent = `${duration}s`;

    // Show sources
    if (response.sources && response.sources.length > 0) {
        const sourcesHTML = `
            <h4>📚 Fontes:</h4>
            <ul>
                ${response.sources.map(source => `<li><code>${source}</code></li>`).join('')}
            </ul>
        `;
        elements.responseSources.innerHTML = sourcesHTML;
    } else {
        elements.responseSources.innerHTML = '';
    }

    elements.responseSection.style.display = 'block';

    // Scroll to response
    elements.responseSection.scrollIntoView({ behavior: 'smooth', block: 'nearest' });
}

function hideResponse() {
    elements.responseSection.style.display = 'none';
}

function showError(message) {
    elements.responseContent.innerHTML = `<span class="text-error">❌ ${message}</span>`;
    elements.responseSources.innerHTML = '';
    elements.responseTime.textContent = '';
    elements.responseSection.style.display = 'block';
}

function showLoading(show) {
    elements.loadingIndicator.style.display = show ? 'flex' : 'none';
    elements.sendBtn.disabled = show;
    elements.queryInput.disabled = show;
}

// ============================================================================
// Status Checking
// ============================================================================

async function checkBotStatus() {
    try {
        // Simulated status check - replace with actual API
        const status = await getStatus();
        updateStatus(status);
    } catch (error) {
        console.error('Error checking status:', error);
        updateStatus({
            bot_online: false,
            rag_loaded: false,
            llm_model: 'desconhecido',
            cache_enabled: false,
            documents_count: 0,
        });
    }
}

async function getStatus() {
    // Simulated API call - replace with actual API when backend is ready
    return new Promise((resolve) => {
        setTimeout(() => {
            resolve({
                bot_online: true,
                rag_loaded: true,
                llm_model: 'minimax/minimax-m2:free',
                cache_enabled: true,
                cache_stats: {
                    size: 42,
                    max_size: 100,
                    hit_rate: '88.89%',
                },
                documents_count: 127,
            });
        }, 500);
    });

    /* Real API call - uncomment when backend is ready
    const response = await fetch(`${CONFIG.API_BASE_URL}/status`, {
        method: 'GET',
        signal: AbortSignal.timeout(5000),
    });

    if (!response.ok) {
        throw new Error(`Erro HTTP: ${response.status}`);
    }

    return await response.json();
    */
}

function updateStatus(status) {
    // Update status dot
    if (status.bot_online) {
        elements.statusDot.classList.remove('offline');
        elements.statusDot.classList.add('online');
        elements.statusText.textContent = 'Bot online e operacional';
        state.botStatus = 'online';
    } else {
        elements.statusDot.classList.remove('online');
        elements.statusDot.classList.add('offline');
        elements.statusText.textContent = 'Bot offline';
        state.botStatus = 'offline';
    }

    // Update bot status
    elements.botStatusValue.innerHTML = status.bot_online
        ? '<span class="status-indicator online"></span>Online'
        : '<span class="status-indicator offline"></span>Offline';

    // Update RAG status
    elements.ragStatusValue.innerHTML = status.rag_loaded
        ? '<span class="status-indicator online"></span>Carregado'
        : '<span class="status-indicator offline"></span>Não carregado';

    // Update LLM model
    elements.llmModelValue.innerHTML = `<code class="stat-code">${status.llm_model}</code>`;

    // Update cache status
    if (status.cache_enabled && status.cache_stats) {
        elements.cacheStatusValue.innerHTML =
            `<code class="stat-code">${status.cache_stats.size}/${status.cache_stats.max_size} | ${status.cache_stats.hit_rate}</code>`;
    } else {
        elements.cacheStatusValue.innerHTML = '<code class="stat-code">Desabilitado</code>';
    }

    // Update documents count
    elements.docsCountValue.innerHTML = `<code class="stat-code">${status.documents_count}</code>`;
}

function updateQueriesCount() {
    elements.queriesCountValue.innerHTML = `<code class="stat-code">${state.queriesCount}</code>`;
}

// ============================================================================
// Uptime Counter
// ============================================================================

function startUptimeCounter() {
    function updateUptime() {
        const elapsed = Date.now() - state.startTime;
        const hours = Math.floor(elapsed / 3600000);
        const minutes = Math.floor((elapsed % 3600000) / 60000);
        const seconds = Math.floor((elapsed % 60000) / 1000);

        const formatted = [hours, minutes, seconds]
            .map(n => String(n).padStart(2, '0'))
            .join(':');

        elements.uptime.textContent = formatted;
    }

    updateUptime();
    setInterval(updateUptime, 1000);
}

// ============================================================================
// Utility Functions
// ============================================================================

function formatTimestamp(date = new Date()) {
    return date.toLocaleTimeString('pt-BR', {
        hour: '2-digit',
        minute: '2-digit',
        second: '2-digit',
    });
}

function escapeHtml(text) {
    const div = document.createElement('div');
    div.textContent = text;
    return div.innerHTML;
}

// ============================================================================
// Keyboard Shortcuts
// ============================================================================

document.addEventListener('keydown', (e) => {
    // Ctrl/Cmd + K: Focus search
    if ((e.ctrlKey || e.metaKey) && e.key === 'k') {
        e.preventDefault();
        elements.queryInput.focus();
    }

    // Escape: Clear input
    if (e.key === 'Escape') {
        elements.queryInput.value = '';
        elements.queryInput.blur();
    }
});

// ============================================================================
// Console Welcome Message
// ============================================================================

console.log(`
%c╔═══════════════════════════════════════════════════════════════╗
║  ____  _                       _   ____    _    ____          ║
║ |  _ \\(_)___  ___ ___  _ __ __| | |  _ \\  / \\  / ___|         ║
║ | | | | / __|/ __/ _ \\| '__/ _\` | | |_) |/ _ \\| |  _          ║
║ | |_| | \\__ \\ (_| (_) | | | (_| | |  _ </ ___ \\ |_| |         ║
║ |____/|_|___/\\___\\___/|_|  \\__,_| |_| \\_\\_/   \\_\\____|        ║
║                                                                ║
║           Terminal Interface v2.0.0                           ║
╚═══════════════════════════════════════════════════════════════╝
`, 'color: #d97706; font-family: monospace;');

console.log('%c⚙️  Interface carregada com sucesso!', 'color: #10b981; font-weight: bold;');
console.log('%c📚  Documentação: https://github.com/prof-ramos/DiscordRAGBot', 'color: #3b82f6;');
