// WARPCORE Main JavaScript Initialization

// Status checking functions (throttled)
let lastSSOCheck = 0;
let lastGCPCheck = 0;

async function checkAWSSSO() {
    const now = Date.now();
    
    // Throttle SSO checks to prevent spam (minimum 5 seconds between checks)
    if (now - lastSSOCheck < 5000) {
        console.log('Throttling AWS SSO status check');
        return;
    }
    lastSSOCheck = now;
    
    const ssoStatus = document.getElementById('aws-sso-value');
    if (!ssoStatus) {
        console.warn('⚠️ AWS SSO status element not found');
        return;
    }
    ssoStatus.textContent = 'checking...';
    ssoStatus.className = 'status-value status-warning';
    
    try {
        const response = await fetch('/api/status');
        const status = await response.json();
        
        // More flexible AWS authentication detection
        const awsAuthenticated = status.aws && (
            status.aws.authentication?.all_authenticated || 
            status.aws.authentication?.authenticated_profiles?.length > 0 ||
            (status.aws.authentication?.profiles && Object.values(status.aws.authentication.profiles).some(p => p.authenticated))
        );
        
        console.log('AWS Status Debug:', {
            hasAws: !!status.aws,
            hasAuth: !!status.aws?.authentication,
            allAuth: status.aws?.authentication?.all_authenticated,
            profiles: status.aws?.authentication?.profiles,
            awsAuthenticated
        });
        
        if (awsAuthenticated) {
            ssoStatus.textContent = 'logged in';
            ssoStatus.className = 'status-value status-healthy';
        } else {
            ssoStatus.textContent = 'login required';
            ssoStatus.className = 'status-value status-error';
        }
    } catch (error) {
        ssoStatus.textContent = 'error';
        ssoStatus.className = 'status-value status-error';
        console.error('AWS SSO status check failed:', error);
    }
}

async function checkGCPAuth() {
    const now = Date.now();
    
    // Throttle GCP checks to prevent spam (minimum 5 seconds between checks)
    if (now - lastGCPCheck < 5000) {
        console.log('Throttling GCP auth status check');
        return;
    }
    lastGCPCheck = now;
    
    const gcpStatus = document.getElementById('gcp-auth-value');
    if (!gcpStatus) {
        console.warn('⚠️ GCP auth status element not found');
        return;
    }
    gcpStatus.textContent = 'checking...';
    gcpStatus.className = 'status-value status-warning';
    
    try {
        const response = await fetch('/api/status');
        const status = await response.json();
        
        // Check GCP authentication status
        const gcpAuthenticated = status.gcp && (
            status.gcp.authentication?.authenticated ||
            status.gcp.authentication?.active_account
        );
        
        console.log('GCP Status Debug:', {
            hasGcp: !!status.gcp,
            hasAuth: !!status.gcp?.authentication,
            authenticated: status.gcp?.authentication?.authenticated,
            activeAccount: status.gcp?.authentication?.active_account,
            gcpAuthenticated
        });
        
        if (gcpAuthenticated) {
            const account = status.gcp.authentication.active_account;
            gcpStatus.textContent = 'logged in';
            gcpStatus.className = 'status-value status-healthy';
            gcpStatus.title = `GCP: ${account}`;
        } else {
            gcpStatus.textContent = 'login required';
            gcpStatus.className = 'status-value status-error';
            gcpStatus.title = 'GCP authentication required';
        }
    } catch (error) {
        gcpStatus.textContent = 'error';
        gcpStatus.className = 'status-value status-error';
        console.error('GCP auth status check failed:', error);
    }
}

// Log functions
function clearLogs() {
    const output = document.getElementById('logs-output');
    if (output) {
        output.innerHTML = `
            <div class="terminal-line">
                <span class="terminal-prompt">📊</span>
                <span class="terminal-success">Logs cleared</span>
            </div>
        `;
    }
}

function toggleLogs() {
    const btn = document.getElementById('logs-toggle');
    if (btn) {
        if (btn.textContent === 'Pause') {
            btn.textContent = 'Resume';
            if (window.WARPCORE && window.WARPCORE.addTerminalLine) {
                window.WARPCORE.addTerminalLine('System', '⏸️ Log monitoring paused', 'warning');
            }
        } else {
            btn.textContent = 'Pause';
            if (window.WARPCORE && window.WARPCORE.addTerminalLine) {
                window.WARPCORE.addTerminalLine('System', '▶️ Log monitoring resumed', 'success');
            }
        }
    }
}

// Command initialization functions
function initializeCommandButtons() {
    console.log('⚙️ Initializing command buttons...');
    // Initialize any command-specific button functionality here
    const commandButtons = document.querySelectorAll('[data-command]');
    commandButtons.forEach(btn => {
        if (!btn.hasAttribute('data-initialized')) {
            btn.setAttribute('data-initialized', 'true');
            console.log(`✅ Initialized command button: ${btn.textContent.trim()}`);
        }
    });
}

function initializeTerminalInput() {
    console.log('⚙️ Initializing terminal input...');
    const terminalInput = document.getElementById('terminal-input');
    if (terminalInput) {
        // Add any terminal input event handlers here
        console.log('✅ Terminal input initialized');
    } else {
        console.log('ℹ️ Terminal input not found - skipping initialization');
    }
}

// Make functions available globally
window.checkAWSSSO = checkAWSSSO;
window.checkGCPAuth = checkGCPAuth;
window.clearLogs = clearLogs;
window.toggleLogs = toggleLogs;
window.initializeCommandButtons = initializeCommandButtons;
window.initializeTerminalInput = initializeTerminalInput;
window.updateStopButton = window.WARPCORE?.updateStopButton || function() {};

// Initialize everything when DOM is ready
document.addEventListener('DOMContentLoaded', function() {
    console.log('🌊 WARPCORE Command Center initializing...');
    
    try {
        // Initialize all components with null checks
        if (window.WARPCORE && window.WARPCORE.initializeTabs) {
            window.WARPCORE.initializeTabs();
        } else {
            console.warn('⚠️ WARPCORE.initializeTabs not available');
        }
        
        initializeCommandButtons();
        initializeTerminalInput();
        
        if (window.WARPCORE && window.WARPCORE.initWebSocket) {
            window.WARPCORE.initWebSocket();
        } else {
            console.warn('⚠️ WARPCORE.initWebSocket not available');
        }
        
        // Show welcome message and check auth status once
        setTimeout(() => {
            if (window.WARPCORE && window.WARPCORE.addTerminalLine) {
                window.WARPCORE.addTerminalLine('System', '🌊 WARPCORE Command Center ready!', 'success');
                window.WARPCORE.addTerminalLine('System', '📡 WebSocket connection established', 'success');
            }
            
            // Check both AWS and GCP status on startup
            checkAWSSSO();
            checkGCPAuth();
        }, 1000);
        
        console.log('✅ WARPCORE Command Center initialized!');
    } catch (error) {
        console.error('Initialization error:', error);
        if (window.WARPCORE && window.WARPCORE.addTerminalLine) {
            window.WARPCORE.addTerminalLine('Error', `Initialization failed: ${error}`, 'error');
        }
    }
});
