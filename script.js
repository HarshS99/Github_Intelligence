const API_URL = 'http://localhost:8000';

// Check server status on load
window.addEventListener('load', checkStatus);

async function checkStatus() {
    try {
        const response = await fetch(`${API_URL}/status`);
        const data = await response.json();

        document.getElementById('mcpStatus').textContent = '🟢 Connected';
        document.getElementById('dbStatus').textContent = data.vector_db ? '🟢 Ready' : '🔴 Not Ready';
        document.getElementById('agentStatus').textContent = '🟢 Ready';
    } catch (error) {
        console.error('Status check failed:', error);
    }
}

async function analyzeRepo() {
    const repo = document.getElementById('repoInput').value;
    if (!repo) {
        alert('Please enter a repository name');
        return;
    }

    setLoading('analyzeBtn', true);
    updateAgentStatus('🟡 Analyzing...');

    try {
        const response = await fetch(`${API_URL}/analyze`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ repository: repo })
        });

        const data = await response.json();
        displayResults(data);
        updateAgentStatus('🟢 Ready');
    } catch (error) {
        displayError('Analysis failed: ' + error.message);
        updateAgentStatus('🔴 Error');
    } finally {
        setLoading('analyzeBtn', false);
    }
}

async function askQuestion() {
    const query = document.getElementById('queryInput').value;
    if (!query) {
        alert('Please enter a question');
        return;
    }

    setLoading('askBtn', true);
    updateAgentStatus('🟡 Thinking...');

    try {
        const response = await fetch(`${API_URL}/query`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ query: query })
        });

        const data = await response.json();
        displayResults(data);
        updateAgentStatus('🟢 Ready');
    } catch (error) {
        displayError('Query failed: ' + error.message);
        updateAgentStatus('🔴 Error');
    } finally {
        setLoading('askBtn', false);
    }
}

async function runTool(toolName) {
    updateAgentStatus('🟡 Running tool...');

    try {
        const response = await fetch(`${API_URL}/tool/${toolName}`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({})
        });

        const data = await response.json();
        displayResults(data);
        updateAgentStatus('🟢 Ready');
    } catch (error) {
        displayError('Tool execution failed: ' + error.message);
        updateAgentStatus('🔴 Error');
    }
}

function displayResults(data) {
    const resultsDiv = document.getElementById('results');
    resultsDiv.innerHTML = '';

    if (data.error) {
        displayError(data.error);
        return;
    }

    if (Array.isArray(data.results)) {
        data.results.forEach(item => {
            const resultItem = document.createElement('div');
            resultItem.className = 'result-item';
            resultItem.innerHTML = `
                <h4>${item.title || 'Result'}</h4>
                <p>${item.description || JSON.stringify(item)}</p>
            `;
            resultsDiv.appendChild(resultItem);
        });
    } else {
        const resultItem = document.createElement('div');
        resultItem.className = 'result-item';
        resultItem.innerHTML = `
            <h4>Response</h4>
            <p>${data.response || JSON.stringify(data)}</p>
        `;
        resultsDiv.appendChild(resultItem);
    }
}

function displayError(message) {
    const resultsDiv = document.getElementById('results');
    resultsDiv.innerHTML = `
        <div class="result-item" style="border-left-color: #e74c3c;">
            <h4>Error</h4>
            <p>${message}</p>
        </div>
    `;
}

function setLoading(buttonId, isLoading) {
    const button = document.getElementById(buttonId);
    button.disabled = isLoading;
    if (isLoading) {
        button.innerHTML = '<span class="loading"></span>';
    } else {
        button.textContent = buttonId === 'analyzeBtn' ? 'Analyze Repository' : 'Ask AI Agent';
    }
}

function updateAgentStatus(status) {
    document.getElementById('agentStatus').textContent = status;
}