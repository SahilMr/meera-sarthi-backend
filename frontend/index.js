(function() {
    const wsStatusDot = document.getElementById('ws-status').querySelector('.status-dot');
    const wsStatusText = document.getElementById('ws-status').querySelector('.status-text');
    const cardsContainer = document.getElementById('cards-container');
    const emptyState = document.getElementById('empty-state');
    const terminalBody = document.getElementById('terminal-body');

    let socket = null;
    const maxTerminalLines = 300;

    function connectWebSocket() {
        const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
        const host = window.location.host;
        const wsUrl = `${protocol}//${host}/api/v1/ws`;

        wsStatusDot.className = 'status-dot disconnected';
        wsStatusText.textContent = 'Connecting...';

        socket = new WebSocket(wsUrl);

        socket.onopen = function() {
            wsStatusDot.className = 'status-dot connected';
            wsStatusText.textContent = 'Connected';
            console.log('WebSocket connected to', wsUrl);
            addTerminalLine('System connected to live event feed.', 'system-msg');
        };

        socket.onmessage = function(event) {
            try {
                const data = JSON.parse(event.data);
                if (data.type === 'request') {
                    renderRequestCard(data);
                } else if (data.type === 'log') {
                    renderTerminalLog(data);
                }
            } catch (err) {
                console.error('Error handling WebSocket message:', err);
            }
        };

        socket.onclose = function() {
            wsStatusDot.className = 'status-dot disconnected';
            wsStatusText.textContent = 'Disconnected';
            console.warn('WebSocket disconnected. Reconnecting in 3 seconds...');
            addTerminalLine('Connection lost. Reconnecting...', 'ERROR');
            setTimeout(connectWebSocket, 3000);
        };

        socket.onerror = function(err) {
            console.error('WebSocket error:', err);
        };
    }

    function addTerminalLine(text, className = '') {
        const line = document.createElement('div');
        line.className = `terminal-line ${className}`;
        line.textContent = text;
        terminalBody.appendChild(line);

        // Keep terminal light
        while (terminalBody.childElementCount > maxTerminalLines) {
            terminalBody.removeChild(terminalBody.firstChild);
        }

        // Auto Scroll to bottom
        terminalBody.scrollTop = terminalBody.scrollHeight;
    }

    function renderTerminalLog(logData) {
        let className = '';
        if (logData.levelname === 'INFO') {
            className = 'INFO';
        } else if (logData.levelname === 'WARNING') {
            className = 'WARNING';
        } else if (logData.levelname === 'ERROR' || logData.levelname === 'CRITICAL') {
            className = 'ERROR';
        }
        addTerminalLine(logData.message, className);
    }

    function renderRequestCard(cardData) {
        // Remove empty state
        if (emptyState && emptyState.style.display !== 'none') {
            emptyState.style.display = 'none';
        }

        // Create card element
        const card = document.createElement('div');
        card.className = 'activity-card';

        // Format message and highlight parameter values in bold neon yellow
        let formattedMessage = cardData.message;
        const params = cardData.params || {};

        // Find and replace occurrences of parameter values with <strong> tags
        // Sort values by length descending to prevent substring issues
        const valuesToHighlight = Object.values(params)
            .filter(v => typeof v === 'string' || typeof v === 'number')
            .map(v => String(v))
            .filter(v => v.trim() !== '')
            .sort((a, b) => b.length - a.length);

        const uniqueValues = [...new Set(valuesToHighlight)];

        uniqueValues.forEach(val => {
            // Escape regex characters
            const escapedVal = val.replace(/[-\/\\^$*+?.()|[\]{}]/g, '\\$&');
            // Use word bounds if value is alphanumeric, otherwise direct match
            const regex = /^[a-zA-Z0-9_]+$/.test(val)
                ? new RegExp(`\\b${escapedVal}\\b`, 'g')
                : new RegExp(escapedVal, 'g');
            formattedMessage = formattedMessage.replace(regex, `<strong>${val}</strong>`);
        });

        const isSuccess = cardData.status_code >= 200 && cardData.status_code < 400;
        const statusClass = isSuccess ? 'success' : 'error';
        const methodClass = cardData.method || 'POST';

        card.innerHTML = `
            <div class="card-header">
                <span class="method-tag ${methodClass}">${cardData.method}</span>
                <div class="card-metadata">
                    <span class="path-text">${cardData.path}</span>
                    <span class="timestamp">${cardData.timestamp || ''}</span>
                </div>
            </div>
            <div class="card-content">
                ${formattedMessage}
            </div>
            <div class="card-footer">
                <span class="status-pill ${statusClass}">
                    ● ${cardData.status_code} ${isSuccess ? 'OK' : 'Error'}
                </span>
                <span class="duration-tag">${cardData.duration_ms} ms</span>
            </div>
        `;

        // Prepend to feed
        cardsContainer.insertBefore(card, cardsContainer.firstChild);

        // Keep card list capped at 50 to maintain performance
        while (cardsContainer.childElementCount > 50) {
            cardsContainer.removeChild(cardsContainer.lastChild);
        }
    }

    // Initialize connection
    connectWebSocket();
})();
