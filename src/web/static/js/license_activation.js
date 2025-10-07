/**
 * WARP License Activation - POC Demo
 * JavaScript functionality for license activation flow
 */

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
            const response = await fetch('/api/license/status');
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

        // WARP demo format: WARP-XXXX-XXXX-XXXX
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
            const response = await fetch('/api/license/activate', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({
                    license_key: licenseKey.toUpperCase(),
                    user_email: userEmail
                })
            });
            
            const result = await response.json();
            
            if (result.success) {
                this.showSuccess('License activation started! Please wait...');
                // Poll for activation completion
                setTimeout(() => this.pollActivationStatus(), 2000);
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
            const response = await fetch('/api/license/generate-trial', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({
                    user_email: email,
                    days: 14
                })
            });
            
            const result = await response.json();
            
            if (result.success) {
                this.showSuccess('Trial license started! Professional features are now available.');
                setTimeout(() => this.checkInitialStatus(), 2000);
            } else {
                this.showError(result.error || 'Trial activation failed');
            }
            
        } catch (error) {
            console.error('❌ WARP LICENSE: Trial failed:', error);
            this.showError('Network error during trial activation');
        }
    },

    // Poll for activation completion
    async pollActivationStatus() {
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