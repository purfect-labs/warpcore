/**
 * WARPCORE License Activation - Complete License Management
 * JavaScript functionality for license activation flow
 * Adapted from apex codebase for WARPCORE PAP architecture
 */

// License Modal Functions (adapted from apex)
function showLicenseModal() {
    console.log('🔑 WARPCORE: Opening license modal');
    const modal = document.getElementById('license-modal');
    if (modal) {
        modal.style.display = 'flex';
    } else {
        console.error('❌ License modal not found');
    }
}

function closeLicenseModal() {
    console.log('🔑 WARPCORE: Closing license modal');
    const modal = document.getElementById('license-modal');
    if (modal) {
        modal.style.display = 'none';
    }
}

function showLicenseTab(tabName) {
    console.log(`🔑 WARPCORE: Switching to ${tabName} tab`);
    
    // Update tab buttons
    document.querySelectorAll('.license-tab').forEach(tab => {
        tab.classList.remove('active');
    });
    
    const activeTab = document.querySelector(`button[onclick="showLicenseTab('${tabName}')"]`);
    if (activeTab) {
        activeTab.classList.add('active');
    }
    
    // Update tab content
    document.querySelectorAll('.license-tab-content').forEach(content => {
        content.classList.remove('active');
    });
    
    const activeContent = document.getElementById(`license-tab-${tabName}`);
    if (activeContent) {
        activeContent.classList.add('active');
    }
}

async function validateLicenseKey() {
    console.log('🔑 WARPCORE: Validating license key');
    
    const licenseKey = document.getElementById('license-key').value;
    const resultDiv = document.getElementById('license-validation-result');
    
    if (!resultDiv) {
        console.warn('⚠️ License validation result div not found');
        return;
    }
    
    if (!licenseKey) {
        resultDiv.innerHTML = '<div class="error">Please enter a license key</div>';
        return;
    }
    
    // Show loading state
    resultDiv.innerHTML = '<div class="loading">🔄 Validating...</div>';
    
    try {
        const response = await fetch('/api/license/validate-sync', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ license_key: licenseKey })
        });
        
        const result = await response.json();
        
        if (result.valid) {
            resultDiv.innerHTML = '<div class="success">✅ License key is valid!</div>';
        } else {
            resultDiv.innerHTML = `<div class="error">❌ ${result.error || 'Invalid license key'}</div>`;
        }
    } catch (error) {
        console.error('❌ License validation error:', error);
        resultDiv.innerHTML = '<div class="error">❌ Validation failed - network error</div>';
    }
}

async function refreshLicenseStatus() {
    console.log('🔑 WARPCORE: Refreshing license status');
    
    try {
        const response = await fetch('/api/license/status-sync');
        const result = await response.json();
        
        if (result.success) {
            console.log('✅ License status refreshed');
            // Reload page to update UI with new status
            location.reload();
        } else {
            alert('Failed to refresh license status');
        }
    } catch (error) {
        console.error('❌ Refresh error:', error);
        alert('Failed to refresh license status: ' + error.message);
    }
}

async function deactivateLicense() {
    if (!confirm('Are you sure you want to deactivate your license? This will revert to the basic tier.')) {
        return;
    }
    
    console.log('🔑 WARPCORE: Deactivating license');
    
    try {
        const response = await fetch('/api/license/deactivate-sync', {
            method: 'POST'
        });
        
        const result = await response.json();
        
        if (result.success) {
            console.log('✅ License deactivated');
            alert('License deactivated. Page will reload.');
            location.reload();
        } else {
            alert('Failed to deactivate license: ' + (result.error || 'Unknown error'));
        }
    } catch (error) {
        console.error('❌ Deactivation error:', error);
        alert('Failed to deactivate license: ' + error.message);
    }
}

function selectUpgrade(tier) {
    console.log(`🔑 WARPCORE: Upgrade to ${tier} selected`);
    alert(`Upgrade to ${tier} selected. Contact sales for licensing options.`);
}

// Direct license status refresh (used by profile dropdown)
async function refreshLicenseStatusDirect() {
    console.log('🔑 WARPCORE: Direct license status refresh');
    
    try {
        const response = await fetch('/api/license/status-sync');
        const result = await response.json();
        
        if (result.success) {
            console.log('✅ License status refreshed');
            // Update license status badge in header
            const headerBadge = document.getElementById('license-status-badge-header');
            if (headerBadge && result.data) {
                if (result.data.status === 'active') {
                    headerBadge.textContent = '✅ Licensed';
                    headerBadge.className = 'status-badge active';
                } else {
                    headerBadge.textContent = '❌ Unlicensed';
                    headerBadge.className = 'status-badge inactive';
                }
            }
        } else {
            console.warn('Failed to refresh license status');
        }
    } catch (error) {
        console.error('❌ Direct refresh error:', error);
    }
}

// Hardware fingerprinting for license binding (from WARPCORE template)
function getHardwareSignature() {
    console.log('🔑 WARPCORE: Generating hardware signature');
    
    // Generate hardware fingerprint for license binding
    const canvas = document.createElement('canvas');
    const ctx = canvas.getContext('2d');
    ctx.textBaseline = 'top';
    ctx.font = '14px Arial';
    ctx.fillText('WARPCORE hardware fingerprint', 2, 2);
    
    const signature = [
        navigator.userAgent,
        navigator.language,
        screen.width + 'x' + screen.height,
        screen.colorDepth,
        new Date().getTimezoneOffset(),
        canvas.toDataURL()
    ].join('|');
    
    // Simple hash function
    let hash = 0;
    for (let i = 0; i < signature.length; i++) {
        const char = signature.charCodeAt(i);
        hash = ((hash << 5) - hash) + char;
        hash = hash & hash; // Convert to 32-bit integer
    }
    
    return Math.abs(hash).toString(16);
}

// License activation state management
const LicenseActivation = {
    // Current license state
    currentStatus: {
        active: false,
        tier: 'free',
        features: [],
        user_email: null,
        expires_at: null
    },

    // Initialize license activation system
    init() {
        console.log('🔑 WARP LICENSE: Initializing license activation system');
        this.bindEvents();
        this.initWebSocket(); // Initialize WebSocket for real-time updates
        this.checkInitialStatus();
    },

    // Bind event handlers
    bindEvents() {
        // License activation form
        const activationForm = document.getElementById('license-activate-form');
        if (activationForm) {
            activationForm.addEventListener('submit', (e) => this.handleActivation(e));
        }

        // Trial form
        const trialForm = document.getElementById('trial-form');
        if (trialForm) {
            trialForm.addEventListener('submit', (e) => this.handleTrialRequest(e));
        }

        // Real-time key validation
        const licenseKeyInput = document.getElementById('license-key');
        if (licenseKeyInput) {
            licenseKeyInput.addEventListener('input', (e) => this.validateKeyFormat(e.target.value));
        }
    },

    // Check initial license status
    async checkInitialStatus() {
        try {
            const response = await fetch('/api/license/status-sync');
            const result = await response.json();
            
            if (result.success && result.data) {
                this.currentStatus = {
                    active: result.data.status === 'active',
                    tier: result.data.license_type || 'free',
                    features: result.data.features || [],
                    user_email: result.data.user_email,
                    expires_at: result.data.expires_at
                };
                console.log('✅ WARP LICENSE: Status loaded successfully');
            } else {
                console.log('📋 WARP LICENSE: No active license found');
            }
            
            this.updateUI();
            this.notifyStatusChange();
            
        } catch (error) {
            console.error('❌ WARP LICENSE: Failed to load initial status:', error);
            this.showError('Failed to load license status');
        }
    },

    // Validate license key format in real-time
    validateKeyFormat(key) {
        const formatDiv = document.getElementById('license-format-feedback');
        if (!formatDiv) return;

        if (!key) {
            formatDiv.innerHTML = '';
            return;
        }

        // WARPCORE production license format: WARP-XXXX-XXXX-XXXX
        const format = /^WARP-[A-Z0-9]{4}-[A-Z0-9]{4}-[A-Z0-9]{4}$/;
        
        if (format.test(key.toUpperCase())) {
            formatDiv.innerHTML = '<div class="format-valid">✅ Valid format</div>';
        } else {
            formatDiv.innerHTML = '<div class="format-hint">💡 Format: WARP-XXXX-XXXX-XXXX</div>';
        }
    },

    // Handle license activation
    async handleActivation(e) {
        e.preventDefault();
        
        const licenseKey = document.getElementById('license-key').value.trim();
        const userEmail = document.getElementById('user-email').value.trim();
        
        if (!licenseKey || !userEmail) {
            this.showError('Please fill in all fields');
            return;
        }

        if (!this.isValidEmail(userEmail)) {
            this.showError('Please enter a valid email address');
            return;
        }

        this.showLoading('Activating license...');
        
        try {
            const response = await fetch('/api/license/activate-sync', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({
                    license_key: licenseKey.toUpperCase(),
                    user_email: userEmail
                })
            });
            
            const result = await response.json();
            
            if (result.success) {
                this.showSuccess('License activated successfully!');
                // Update status immediately since sync endpoint
                setTimeout(() => this.checkInitialStatus(), 1000);
                this.clearForm();
            } else {
                this.showError(result.error || 'License activation failed');
            }
            
        } catch (error) {
            console.error('❌ WARP LICENSE: Activation failed:', error);
            this.showError('Network error during activation');
        }
    },

    // Handle trial license request
    async handleTrialRequest(e) {
        e.preventDefault();
        
        const email = document.getElementById('trial-email').value.trim();
        
        if (!email || !this.isValidEmail(email)) {
            this.showError('Please enter a valid email address');
            return;
        }

        this.showLoading('Starting trial license...');
        
        try {
            const response = await fetch('/api/license/generate-trial-sync', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({
                    user_email: email,
                    days: 14
                })
            });
            
            const result = await response.json();
            
            if (result.success) {
                this.showSuccess('Trial license activated! Professional features are now available.');
                setTimeout(() => this.checkInitialStatus(), 1000);
            } else {
                this.showError(result.error || 'Trial activation failed');
            }
            
        } catch (error) {
            console.error('❌ WARP LICENSE: Trial failed:', error);
            this.showError('Network error during trial activation');
        }
    },

    // WebSocket connection for real-time updates
    websocket: null,
    websocketConnected: false,
    
    // Initialize WebSocket connection
    initWebSocket() {
        if (this.websocket || this.websocketConnected) {
            return; // Already connected
        }
        
        try {
            const clientId = this.generateClientId();
            const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
            const wsUrl = `${protocol}//${window.location.host}/ws/${clientId}`;
            
            console.log('🔗 WARP LICENSE: Connecting to WebSocket:', wsUrl);
            
            this.websocket = new WebSocket(wsUrl);
            
            this.websocket.onopen = () => {
                console.log('✅ WARP LICENSE: WebSocket connected');
                this.websocketConnected = true;
                
                // Subscribe to license events
                this.websocket.send(JSON.stringify({
                    type: 'subscribe',
                    events: ['license_activated', 'license_deactivated', 'trial_license_generated', 'license_validated']
                }));
            };
            
            this.websocket.onmessage = (event) => {
                try {
                    const message = JSON.parse(event.data);
                    this.handleWebSocketMessage(message);
                } catch (error) {
                    console.error('❌ WARP LICENSE: WebSocket message parsing error:', error);
                }
            };
            
            this.websocket.onclose = () => {
                console.log('🔌 WARP LICENSE: WebSocket disconnected');
                this.websocketConnected = false;
                this.websocket = null;
                
                // Reconnect after delay
                setTimeout(() => this.initWebSocket(), 5000);
            };
            
            this.websocket.onerror = (error) => {
                console.error('❌ WARP LICENSE: WebSocket error:', error);
                this.websocketConnected = false;
            };
            
        } catch (error) {
            console.error('❌ WARP LICENSE: WebSocket initialization failed:', error);
        }
    },
    
    // Generate unique client ID for WebSocket
    generateClientId() {
        return 'license-' + Math.random().toString(36).substr(2, 9) + Date.now().toString(36);
    },
    
    // Handle WebSocket messages
    handleWebSocketMessage(message) {
        console.log('📨 WARP LICENSE: Received WebSocket message:', message.type);
        
        switch (message.type) {
            case 'license_activated':
                this.handleLicenseActivated(message.data);
                break;
                
            case 'license_deactivated':
                this.handleLicenseDeactivated(message.data);
                break;
                
            case 'trial_license_generated':
                this.handleTrialGenerated(message.data);
                break;
                
            case 'license_validated':
                this.handleLicenseValidated(message.data);
                break;
                
            default:
                console.log('📋 WARP LICENSE: Unhandled message type:', message.type);
        }
    },
    
    // Handle license activation events from WebSocket
    handleLicenseActivated(data) {
        console.log('🎉 WARP LICENSE: License activated via WebSocket:', data);
        
        this.showSuccess(`🎉 License activated for ${data.user_email}! Features: ${data.license_type}`);
        
        // Update current status
        this.currentStatus = {
            active: true,
            tier: data.license_type || 'professional',
            features: data.features || ['premium'],
            user_email: data.user_email,
            expires_at: data.expires_at
        };
        
        this.updateUI();
        this.clearForm();
        this.notifyStatusChange();
    },
    
    // Handle license deactivation events
    handleLicenseDeactivated(data) {
        console.log('📋 WARP LICENSE: License deactivated via WebSocket:', data);
        
        this.showSuccess('License deactivated. Reverted to basic tier.');
        
        // Reset to basic tier
        this.currentStatus = {
            active: false,
            tier: 'free',
            features: [],
            user_email: null,
            expires_at: null
        };
        
        this.updateUI();
        this.notifyStatusChange();
    },
    
    // Handle trial license generation
    handleTrialGenerated(data) {
        console.log('🎁 WARP LICENSE: Trial generated via WebSocket:', data);
        
        this.showSuccess(`🎁 Trial license activated for ${data.user_email}! ${data.days} days of premium features.`);
        
        // Update to trial status
        this.currentStatus = {
            active: true,
            tier: 'trial',
            features: ['trial', 'professional'],
            user_email: data.user_email,
            expires_at: data.expires_at
        };
        
        this.updateUI();
        this.notifyStatusChange();
    },
    
    // Handle license validation events
    handleLicenseValidated(data) {
        console.log('✅ WARP LICENSE: License validated via WebSocket:', data);
        
        // Update validation UI if visible
        const resultDiv = document.getElementById('license-validation-result');
        if (resultDiv) {
            if (data.valid) {
                resultDiv.innerHTML = `<div class="success">✅ Valid ${data.license_type} license</div>`;
            } else {
                resultDiv.innerHTML = '<div class="error">❌ License validation failed</div>';
            }
        }
    },
    
    // Poll for activation completion (fallback if WebSocket fails)
    async pollActivationStatus() {
        // If WebSocket is connected, rely on real-time updates
        if (this.websocketConnected) {
            console.log('📡 WARP LICENSE: Using WebSocket for real-time updates');
            return;
        }
        
        // Fallback polling for browsers without WebSocket support
        console.log('📋 WARP LICENSE: Using polling fallback');
        let attempts = 0;
        const maxAttempts = 10;
        
        const poll = async () => {
            attempts++;
            
            try {
                await this.checkInitialStatus();
                
                if (this.currentStatus.active) {
                    this.showSuccess('🎉 License activated successfully!');
                    this.clearForm();
                    return;
                }
                
                if (attempts < maxAttempts) {
                    setTimeout(poll, 3000);
                } else {
                    this.showError('Activation is taking longer than expected. Please refresh and check status.');
                }
                
            } catch (error) {
                if (attempts < maxAttempts) {
                    setTimeout(poll, 3000);
                } else {
                    this.showError('Failed to verify activation status');
                }
            }
        };
        
        poll();
    },

    // Update UI based on license status
    updateUI() {
        // Update modal license info
        const currentBadge = document.getElementById('current-license-badge');
        const currentDetails = document.getElementById('current-license-details');
        
        if (currentBadge && currentDetails) {
            if (this.currentStatus.active) {
                currentBadge.className = 'license-badge active';
                currentBadge.innerHTML = `✅ ${this.currentStatus.tier.toUpperCase()} License Active`;
                
                currentDetails.innerHTML = `
                    <p><strong>User:</strong> ${this.currentStatus.user_email}</p>
                    <p><strong>Type:</strong> ${this.currentStatus.tier}</p>
                    <p><strong>Features:</strong> ${this.currentStatus.features.length} available</p>
                    ${this.currentStatus.expires_at ? `<p><strong>Expires:</strong> ${this.currentStatus.expires_at}</p>` : ''}
                `;
            } else {
                currentBadge.className = 'license-badge inactive';
                currentBadge.innerHTML = '❌ No Active License';
                currentDetails.innerHTML = '<p>You are using the free Basic tier with limited features.</p>';
            }
        }
    },

    // Notify other components of status change
    notifyStatusChange() {
        const event = new CustomEvent('licenseStatusChanged', {
            detail: this.currentStatus
        });
        window.dispatchEvent(event);
    },

    // Utility functions
    isValidEmail(email) {
        return /^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(email);
    },

    showLoading(message) {
        const resultDiv = document.getElementById('license-validation-result');
        if (resultDiv) {
            resultDiv.innerHTML = `<div class="loading">⏳ ${message}</div>`;
        }
    },

    showSuccess(message) {
        const resultDiv = document.getElementById('license-validation-result');
        if (resultDiv) {
            resultDiv.innerHTML = `<div class="success">✅ ${message}</div>`;
        }
    },

    showError(message) {
        const resultDiv = document.getElementById('license-validation-result');
        if (resultDiv) {
            resultDiv.innerHTML = `<div class="error">❌ ${message}</div>`;
        }
    },

    clearForm() {
        const licenseKey = document.getElementById('license-key');
        const userEmail = document.getElementById('user-email');
        
        if (licenseKey) licenseKey.value = '';
        if (userEmail) userEmail.value = '';
        
        const resultDiv = document.getElementById('license-validation-result');
        if (resultDiv) resultDiv.innerHTML = '';
    }
};

// Initialize when DOM is ready
document.addEventListener('DOMContentLoaded', function() {
    LicenseActivation.init();
});

// Export for global access
window.LicenseActivation = LicenseActivation;