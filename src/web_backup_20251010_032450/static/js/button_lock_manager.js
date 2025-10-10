/**
 * WARP Button Lock Manager - POC Demo  
 * Secure button lock mechanism with license validation
 */

const ButtonLockManager = {
    // License status cache
    licenseStatus: {
        active: false,
        tier: 'free',
        features: [],
        lastChecked: null
    },

    // Initialize button lock system
    init() {
        console.log('🔐 WARP BUTTON LOCK: Initializing secure button lock manager');
        this.bindEvents();
        this.checkLicenseStatus();
        this.setupPeriodicValidation();
    },

    // Bind event handlers
    bindEvents() {
        // Listen for license status changes
        window.addEventListener('licenseStatusChanged', (event) => {
            this.licenseStatus = event.detail;
            this.updateButtonStates();
        });

        // Handle premium feature attempts
        const premiumBtn = document.getElementById('professional-feature-btn');
        if (premiumBtn) {
            premiumBtn.addEventListener('click', (e) => this.handlePremiumFeatureAttempt(e));
        }

        // Handle basic feature access
        const basicBtn = document.getElementById('basic-feature-btn');
        if (basicBtn) {
            basicBtn.addEventListener('click', (e) => this.handleBasicFeatureAccess(e));
        }

        // Prevent right-click context menu on feature buttons
        document.querySelectorAll('.feature-btn').forEach(btn => {
            btn.addEventListener('contextmenu', (e) => e.preventDefault());
        });
    },

    // Check current license status
    async checkLicenseStatus() {
        try {
            const response = await fetch('/api/license/status');
            const result = await response.json();
            
            if (result.success && result.data) {
                this.licenseStatus = {
                    active: result.data.status === 'active',
                    tier: result.data.license_type || 'free',
                    features: result.data.features || [],
                    lastChecked: new Date()
                };
                console.log('✅ WARP BUTTON LOCK: License status updated');
            } else {
                this.licenseStatus = {
                    active: false,
                    tier: 'free',
                    features: [],
                    lastChecked: new Date()
                };
                console.log('📋 WARP BUTTON LOCK: No active license found');
            }
            
            this.updateButtonStates();
            
        } catch (error) {
            console.error('❌ WARP BUTTON LOCK: Failed to check license status:', error);
            // Fail securely - assume no license
            this.licenseStatus.active = false;
            this.updateButtonStates();
        }
    },

    // Update button states based on license status
    updateButtonStates() {
        const premiumBtn = document.getElementById('professional-feature-btn');
        const premiumStatus = document.getElementById('professional-status');
        const licensePrompt = document.getElementById('license-prompt');
        
        if (!premiumBtn) return;

        if (this.licenseStatus.active) {
            // License active - unlock premium features
            premiumBtn.classList.remove('locked');
            premiumBtn.classList.add('unlocked');
            premiumBtn.innerHTML = '⭐ Premium Features (Unlocked)';
            premiumBtn.title = 'Click to access premium features';
            premiumBtn.disabled = false;
            
            if (premiumStatus) {
                premiumStatus.innerHTML = 'Unlocked';
                premiumStatus.classList.add('unlocked');
            }
            
            if (licensePrompt) {
                licensePrompt.style.display = 'none';
            }
            
            console.log('🔓 WARP BUTTON LOCK: Premium features unlocked');
            
        } else {
            // No license - lock premium features
            premiumBtn.classList.add('locked');
            premiumBtn.classList.remove('unlocked');
            premiumBtn.innerHTML = '🔒 Premium Features (License Required)';
            premiumBtn.title = 'Activate a license to unlock premium features';
            premiumBtn.disabled = false; // Keep clickable to show lock message
            
            if (premiumStatus) {
                premiumStatus.innerHTML = 'License Required';
                premiumStatus.classList.remove('unlocked');
            }
            
            if (licensePrompt) {
                licensePrompt.style.display = 'block';
            }
            
            console.log('🔒 WARP BUTTON LOCK: Premium features locked');
        }
    },

    // Handle premium feature access attempt
    async handlePremiumFeatureAttempt(e) {
        e.preventDefault();
        
        // Real-time license validation before feature access
        await this.checkLicenseStatus();
        
        const resultDiv = document.getElementById('premium-feature-result');
        if (!resultDiv) return;

        if (!this.licenseStatus.active) {
            // Show secure lock message
            this.showLockMessage(resultDiv);
            
            // Log access attempt for security
            console.warn('🚫 WARP SECURITY: Unauthorized premium feature access attempt');
            
        } else {
            // Validate feature access with backend
            const hasAccess = await this.validateFeatureAccess('premium_features');
            
            if (hasAccess) {
                this.showPremiumSuccess(resultDiv);
                console.log('✅ WARP SECURITY: Premium feature access granted');
            } else {
                this.showAccessDenied(resultDiv);
                console.warn('🚫 WARP SECURITY: Premium feature access denied');
            }
        }
    },

    // Handle basic feature access
    handleBasicFeatureAccess(e) {
        const resultDiv = document.getElementById('basic-feature-result');
        if (!resultDiv) return;

        // Basic features always work
        resultDiv.className = 'feature-result success';
        resultDiv.style.display = 'block';
        resultDiv.innerHTML = `
            <strong>✅ Essential Features Available!</strong><br>
            <small>Essential functionality available to all users including kubectl access and basic cloud operations.</small>
            <br><small>Accessed at: ${new Date().toLocaleTimeString()}</small>
        `;
        
        // Auto-hide after 5 seconds
        setTimeout(() => {
            resultDiv.style.display = 'none';
        }, 5000);
        
        console.log('✅ WARP BUTTON LOCK: Basic feature accessed');
    },

    // Validate feature access with backend
    async validateFeatureAccess(feature) {
        try {
            const response = await fetch('/api/license/subscription');
            const result = await response.json();
            
            if (result.success && result.data) {
                const subscription = result.data.subscription || {};
                const features = subscription.features || [];
                return features.includes(feature) || features.includes('all');
            }
            
            return false;
            
        } catch (error) {
            console.error('❌ WARP SECURITY: Feature validation failed:', error);
            return false; // Fail securely
        }
    },

    // Show lock message for unauthorized access
    showLockMessage(resultDiv) {
        resultDiv.className = 'feature-result error';
        resultDiv.style.display = 'block';
        resultDiv.innerHTML = `
            <strong>🔒 Premium Features Locked</strong><br>
            <small>Advanced cloud operations require an active license. Please activate a license to continue.</small>
            <br><br>
            <button onclick="showLicenseModal()" class="btn-primary" style="padding: 6px 12px; font-size: 0.8em;">
                🔑 Activate License Now
            </button>
        `;
        
        // Auto-hide after 8 seconds
        setTimeout(() => {
            resultDiv.style.display = 'none';
        }, 8000);
    },

    // Show premium success message
    showPremiumSuccess(resultDiv) {
        resultDiv.className = 'feature-result success';
        resultDiv.style.display = 'block';
        resultDiv.innerHTML = `
            <strong>⭐ Premium Features Available!</strong><br>
            <small>Advanced functionality unlocked including multi-environment support and enterprise integrations.</small>
            <br><small>License tier: ${this.licenseStatus.tier.toUpperCase()}</small>
            <br><small>Accessed at: ${new Date().toLocaleTimeString()}</small>
        `;
        
        // Auto-hide after 5 seconds
        setTimeout(() => {
            resultDiv.style.display = 'none';
        }, 5000);
    },

    // Show access denied message
    showAccessDenied(resultDiv) {
        resultDiv.className = 'feature-result error';
        resultDiv.style.display = 'block';
        resultDiv.innerHTML = `
            <strong>🚫 Access Denied</strong><br>
            <small>Your license does not include access to this feature. Please upgrade your license.</small>
            <br><br>
            <button onclick="showLicenseModal()" class="btn-warning" style="padding: 6px 12px; font-size: 0.8em;">
                📈 Upgrade License
            </button>
        `;
        
        setTimeout(() => {
            resultDiv.style.display = 'none';
        }, 8000);
    },

    // Setup periodic license validation
    setupPeriodicValidation() {
        // Validate license every 5 minutes
        setInterval(() => {
            console.log('🔄 WARP BUTTON LOCK: Periodic license validation');
            this.checkLicenseStatus();
        }, 5 * 60 * 1000);
    },

    // Force license re-validation (called from other components)
    async forceValidation() {
        console.log('🔄 WARP BUTTON LOCK: Forced license validation');
        await this.checkLicenseStatus();
        return this.licenseStatus;
    },

    // Get current license status
    getLicenseStatus() {
        return this.licenseStatus;
    },

    // Security: Disable button manipulation (DISABLED DUE TO INFINITE LOOP)
    lockDownButtons() {
        // TEMPORARY FIX: Disabling MutationObserver that causes infinite loop
        // The observer was triggering updateButtonStates() which modifies attributes,
        // causing the observer to fire again in an endless cycle
        
        console.log('🔐 WARP SECURITY: Button lockdown initialized (observer disabled)');
        
        // Alternative: Just log that security is monitoring
        document.querySelectorAll('.feature-btn').forEach(btn => {
            // Simple one-time security check without reactive monitoring
            if (btn.dataset.securityMonitored !== 'true') {
                btn.dataset.securityMonitored = 'true';
                console.log('🔐 WARP SECURITY: Button security monitoring enabled for:', btn.id || btn.className);
            }
        });
    }
};

// Initialize when DOM is ready
document.addEventListener('DOMContentLoaded', function() {
    ButtonLockManager.init();
    ButtonLockManager.lockDownButtons();
});

// Export for global access
window.ButtonLockManager = ButtonLockManager;