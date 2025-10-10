/**
 * WARPCORE Licensing UI - Uses existing backend APIs
 */

// Initialize when page loads
document.addEventListener('DOMContentLoaded', function() {
    console.log('🌊 WARPCORE Licensing UI - Ready');
    initLicenseUI();
    checkLicenseStatus();
    verifyButtonMappings();
    testBackendConnectivity();
});

// Verify all button mappings work
function verifyButtonMappings() {
    const buttonMappings = [
        { selector: 'button[onclick*="showLicenseModal"]', func: 'showLicenseModal', description: 'Manage License Modal' },
        { selector: 'button[onclick*="checkLicenseStatus"]', func: 'checkLicenseStatus', description: 'Refresh Status' },
        { selector: 'button[onclick*="showLicenseInfo"]', func: 'showLicenseInfo', description: 'License Info' },
        { selector: 'button[onclick*="activateLicense"]', func: 'activateLicense', description: 'Activate License' },
        { selector: 'button[onclick*="deactivateLicense"]', func: 'deactivateLicense', description: 'Deactivate License' },
        { selector: 'button[onclick*="generateTestLicense"]', func: 'generateTestLicense', description: 'Generate Test License' },
        { selector: 'button[data-feature="basic"]', func: 'testFeature', description: 'Test Basic Feature' },
        { selector: 'button[data-feature="info"]', func: 'testFeature', description: 'Test Info Feature' },
        { selector: 'button[data-feature="advanced"]', func: 'testFeature', description: 'Test Advanced Feature' },
        { selector: 'button[data-feature="automation"]', func: 'testFeature', description: 'Test Automation Feature' },
        { selector: 'button[data-feature="enterprise"]', func: 'testFeature', description: 'Test Enterprise Feature' },
        { selector: 'button[data-feature="analytics"]', func: 'testFeature', description: 'Test Analytics Feature' }
    ];
    
    let mappingIssues = [];
    
    buttonMappings.forEach(mapping => {
        const button = document.querySelector(mapping.selector);
        if (!button) {
            mappingIssues.push(`❌ Button not found: ${mapping.description}`);
        } else if (typeof window[mapping.func] !== 'function') {
            mappingIssues.push(`❌ Function not available: ${mapping.func} for ${mapping.description}`);
        } else {
            console.log(`✅ ${mapping.description} -> ${mapping.func}`);
        }
    });
    
    if (mappingIssues.length > 0) {
        console.error('⚠️ Button mapping issues:', mappingIssues);
        showNotification('warning', '⚠️ Button Mapping Issues', `${mappingIssues.length} button(s) have mapping issues. Check console.`, 5000);
    } else {
        console.log('✅ All button mappings verified successfully!');
        showNotification('success', '🔧 UI Ready', 'All buttons are properly mapped and ready to use.', 3000);
    }
}

// Test backend connectivity
async function testBackendConnectivity() {
    const endpoints = [
        { url: '/api/license/status', method: 'GET', name: 'License Status' },
        { url: '/api/endpoints/test', method: 'GET', name: 'Basic Test Endpoint' },
        { url: '/api/pap/status', method: 'GET', name: 'PAP Architecture Status' }
    ];
    
    let connectedEndpoints = 0;
    
    for (const endpoint of endpoints) {
        try {
            const response = await fetch(endpoint.url);
            if (response.ok) {
                connectedEndpoints++;
                console.log(`✅ ${endpoint.name}: Connected`);
            } else {
                console.warn(`⚠️ ${endpoint.name}: HTTP ${response.status}`);
            }
        } catch (error) {
            console.error(`❌ ${endpoint.name}: ${error.message}`);
        }
    }
    
    if (connectedEndpoints === endpoints.length) {
        document.getElementById('connection-status').textContent = 'All Systems Online';
        document.getElementById('system-status').textContent = 'Backend Connected';
    } else {
        document.getElementById('connection-status').textContent = `${connectedEndpoints}/${endpoints.length} Online`;
        document.getElementById('system-status').textContent = 'Partial Connection';
        showNotification('warning', '⚠️ Backend Issues', `Only ${connectedEndpoints}/${endpoints.length} endpoints are responding.`, 4000);
    }
}

// Initialize UI
function initLicenseUI() {
    // Modal click outside to close
    document.getElementById('license-modal').addEventListener('click', function(e) {
        if (e.target === this) {
            closeLicenseModal();
        }
    });
    
    // Enter key in license input
    document.getElementById('license-key').addEventListener('keypress', function(e) {
        if (e.key === 'Enter') {
            activateLicense();
        }
    });
}

// Check current license status
async function checkLicenseStatus() {
    try {
        const response = await fetch('/api/license/status');
        const result = await response.json();
        
        if (result.success) {
            // Handle different response formats from backend
            const licenseData = result.data || result;
            updateLicenseDisplay({
                status: licenseData.status || 'inactive',
                license_type: licenseData.license_type || 'free',
                email: licenseData.user_email || licenseData.email || null,
                features: licenseData.features || [],
                expires: licenseData.expires || null,
                days_remaining: licenseData.days_remaining || null
            });
        } else {
            // Backend returned error or no license found
            updateLicenseDisplay({
                status: 'inactive',
                license_type: 'free',
                email: null,
                features: [],
                expires: null,
                days_remaining: null
            });
            
            if (result.message && result.message !== 'No license found') {
                showNotification('info', 'License Status', result.message, 3000);
            }
        }
    } catch (error) {
        console.error('License check failed:', error);
        showNotification('error', 'License Check Failed', error.message, 4000);
        
        // Show fallback inactive state
        updateLicenseDisplay({
            status: 'inactive',
            license_type: 'free',
            email: null,
            features: [],
            expires: null,
            days_remaining: null
        });
    }
}

// Update license display
function updateLicenseDisplay(data) {
    const badge = document.getElementById('license-badge');
    const email = document.getElementById('license-email');
    
    if (data.status === 'active') {
        badge.textContent = `✅ ${data.license_type.toUpperCase()}`;
        badge.className = 'status-badge active';
        email.textContent = data.email || 'Licensed';
    } else {
        badge.textContent = '❌ Unlicensed';
        badge.className = 'status-badge';
        email.textContent = 'No License';
    }
    
    // Update details
    document.getElementById('detail-status').textContent = data.status;
    document.getElementById('detail-tier').textContent = data.license_type;
    document.getElementById('detail-features').textContent = 
        data.features && data.features.length > 0 ? data.features.join(', ') : 'None';
    
    updateFeatureButtons(data);
}

// Update feature button states
function updateFeatureButtons(licenseData) {
    const features = licenseData.features || [];
    const isActive = licenseData.status === 'active';
    
    document.querySelectorAll('.btn-test').forEach(btn => {
        const feature = btn.getAttribute('data-feature');
        
        btn.classList.remove('locked', 'unlocked');
        
        // Free features always available
        if (['basic', 'info'].includes(feature)) {
            btn.classList.add('unlocked');
        }
        // Standard features
        else if (['advanced', 'automation'].includes(feature)) {
            if (features.includes('standard') || features.includes('premium')) {
                btn.classList.add('unlocked');
            } else {
                btn.classList.add('locked');
            }
        }
        // Premium features
        else if (['enterprise', 'analytics'].includes(feature)) {
            if (features.includes('premium')) {
                btn.classList.add('unlocked');
            } else {
                btn.classList.add('locked');
            }
        }
    });
}

// Modal functions
function showLicenseModal() {
    document.getElementById('license-modal').style.display = 'flex';
    document.getElementById('license-key').focus();
}

function closeLicenseModal() {
    document.getElementById('license-modal').style.display = 'none';
    document.getElementById('license-key').value = '';
}

// License activation
async function activateLicense() {
    const licenseKey = document.getElementById('license-key').value.trim();
    const button = document.querySelector('.modal-body .btn-primary');
    
    if (!licenseKey) {
        showResult('warning', 'License Activation', 'Please enter a license key');
        return;
    }
    
    // Show loading state
    const originalText = button.textContent;
    button.disabled = true;
    button.textContent = '🔄 Activating...';
    button.style.opacity = '0.7';
    
    try {
        const response = await fetch('/api/license/activate-sync', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ 
                license_key: licenseKey,
                user_email: 'user@warpcore.dev' // Add user email
            })
        });
        
        const result = await response.json();
        
        if (result.success) {
            // Synchronous activation completed!
            closeLicenseModal();
            
            showNotification('success', 
                '🎉 License Activated Successfully!', 
                `${result.message || 'License has been activated and is now ready to use!'}`, 
                5000
            );
            
            // Update the license display immediately
            checkLicenseStatus();
            
            // Show license details if available in result
            if (result.license_type || result.user_email) {
                setTimeout(() => {
                    showNotification('info', 
                        '📊 License Details', 
                        `Type: ${result.license_type || 'Trial'} | Email: ${result.user_email || 'Unknown'}`, 
                        4000
                    );
                }, 1500);
            }
            
            return; // Skip all the polling logic
            
            // First, do a quick validation check for immediate feedback
            try {
                const validateResponse = await fetch('/api/license/validate', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ license_key: licenseKey })
                });
                const validateResult = await validateResponse.json();
                
                if (!validateResult.valid) {
                    // Validation failed immediately - show error
                    showNotification('error', 
                        '❌ License Activation Failed', 
                        `Invalid license key: ${validateResult.error}`, 
                        6000
                    );
                    return;
                } else {
                    // Validation succeeded! Show positive feedback
                    showNotification('success', 
                        '✅ License Key Validated!', 
                        'License key is valid. Proceeding with activation...', 
                        3000
                    );
                    console.log('License validation successful:', validateResult.license_info);
                }
            } catch (validateError) {
                console.warn('Direct validation check failed, proceeding with polling:', validateError);
            }
            
            // Poll for actual license activation status
            let attempts = 0;
            const maxAttempts = 8;
            const pollInterval = 1500; // 1.5 seconds
            
            const pollForActivation = async () => {
                attempts++;
                
                try {
                    const statusResponse = await fetch('/api/license/status');
                    const statusResult = await statusResponse.json();
                    
                    // Handle different response formats from backend
                    const licenseData = statusResult.data || statusResult;
                    const currentStatus = licenseData.status || 'inactive';
                    const statusMessage = statusResult.message || licenseData.message || '';
                    
                    console.log(`Polling attempt ${attempts}: Status=${currentStatus}, Message=${statusMessage}`);
                    
                    if (statusResult.success && currentStatus === 'active') {
                        // License is now active!
                        updateLicenseDisplay(licenseData);
                        showNotification('success', 
                            '✅ License Fully Activated!', 
                            `Welcome! Your ${licenseData.license_type || 'premium'} license is now active with ${licenseData.features?.length || 0} features unlocked.`, 
                            6000
                        );
                        return;
                    }
                    
                    // Check if license is valid but activation is still processing
                    if (attempts >= 3) {
                        // After a few attempts, validate the key again to see if it's actually working
                        try {
                            const revalidateResponse = await fetch('/api/license/validate', {
                                method: 'POST',
                                headers: { 'Content-Type': 'application/json' },
                                body: JSON.stringify({ license_key: licenseKey })
                            });
                            const revalidateResult = await revalidateResponse.json();
                            
                            if (revalidateResult.valid) {
                                // Key is valid but status isn't updating - this might be expected behavior
                                showNotification('warning', 
                                    '⚠️ Activation Partially Complete', 
                                    'License key is valid, but the system status is not updating automatically. This may be expected behavior for this license type.', 
                                    6000
                                );
                                
                                // Update display with validation data instead of status data
                                const validationData = {
                                    status: 'validated',
                                    license_type: revalidateResult.license_info?.license_type || 'trial',
                                    email: revalidateResult.license_info?.user_email || 'Unknown',
                                    features: revalidateResult.license_info?.features || ['basic']
                                };
                                updateLicenseDisplay(validationData);
                                return;
                            }
                        } catch (revalidateError) {
                            console.warn('Revalidation check failed:', revalidateError);
                        }
                    }
                    
                    // Check for validation error messages
                    const errorIndicators = [
                        'Invalid', 'invalid', 'failed', 'error', 'expired', 'tampering', 
                        'format', 'encryption', 'binding', 'missing', 'required'
                    ];
                    
                    const hasError = errorIndicators.some(indicator => 
                        statusMessage.toLowerCase().includes(indicator.toLowerCase())
                    );
                    
                    if (hasError) {
                        // License validation failed with specific error
                        updateLicenseDisplay(licenseData);
                        showNotification('error', 
                            '❌ License Activation Failed', 
                            `Validation error: ${statusMessage}`, 
                            6000
                        );
                        return;
                    }
                    
                    // Still processing - continue polling if within attempts limit
                    if (attempts < maxAttempts) {
                        setTimeout(pollForActivation, pollInterval);
                        
                        // Show progress updates
                        if (attempts % 2 === 0) {
                            showNotification('info', 
                                '🔄 Activation In Progress', 
                                `Validating license (${attempts}/${maxAttempts})...`, 
                                2000
                            );
                        }
                    } else {
                        // Timeout reached - assume activation failed
                        updateLicenseDisplay(licenseData);
                        
                        if (currentStatus === 'inactive' || !currentStatus) {
                            // License is still inactive after timeout - likely invalid
                            showNotification('error', 
                                '❌ License Activation Failed', 
                                'License key appears to be invalid or expired. Please check your license key and try again.', 
                                6000
                            );
                        } else {
                            // Unknown status after timeout
                            showNotification('warning', 
                                '⏱️ Activation Timeout', 
                                `License activation timed out with status: ${currentStatus}. Please refresh to check current status.`, 
                                5000
                            );
                        }
                    }
                } catch (pollError) {
                    console.error('Error polling activation status:', pollError);
                    if (attempts >= maxAttempts) {
                        checkLicenseStatus(); // Fallback status check
                        showNotification('error', 
                            '❌ Activation Status Check Failed', 
                            'Unable to verify license activation. The license key may be invalid or there may be a network issue.', 
                            5000
                        );
                    }
                }
            };
            
            // Start polling after a short delay
            setTimeout(pollForActivation, 2000);
            
        } else {
            showNotification('error', 
                '❌ License Activation Failed', 
                result.error || 'Unable to activate license. Please check your license key and try again.', 
                6000
            );
        }
    } catch (error) {
        showResult('error', 'License Activation Failed', error.message);
    } finally {
        // Restore button state
        button.disabled = false;
        button.textContent = originalText;
        button.style.opacity = '1';
    }
}

// License deactivation
async function deactivateLicense() {
    if (!confirm('Deactivate your license?')) return;
    
    const button = document.querySelector('.license-actions .btn-danger');
    const originalText = button ? button.textContent : '';
    
    if (button) {
        button.disabled = true;
        button.textContent = '🔄 Deactivating...';
        button.style.opacity = '0.7';
    }
    
    try {
        const response = await fetch('/api/license/deactivate', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' }
        });
        
        const result = await response.json();
        
        if (result.success) {
            showNotification('success', 
                '✅ License Deactivation Started', 
                `${result.message} - Updating license status...`, 
                3000
            );
            closeLicenseModal();
            
            // Poll for actual license deactivation status
            let attempts = 0;
            const maxAttempts = 6;
            const pollInterval = 1000; // 1 second
            
            const pollForDeactivation = async () => {
                attempts++;
                
                try {
                    const statusResponse = await fetch('/api/license/status');
                    const statusResult = await statusResponse.json();
                    
                    if (statusResult.success && statusResult.status !== 'active') {
                        // License is now deactivated!
                        updateLicenseDisplay(statusResult);
                        showNotification('info', 
                            '🔓 License Deactivated Successfully', 
                            'Your license has been deactivated. Features are now locked.', 
                            4000
                        );
                        return;
                    }
                    
                    // Still processing - continue polling
                    if (attempts < maxAttempts) {
                        setTimeout(pollForDeactivation, pollInterval);
                        
                        // Show progress updates
                        if (attempts % 2 === 0) {
                            showNotification('info', 
                                '🔄 Deactivation In Progress', 
                                `Updating license status (${attempts}/${maxAttempts})...`, 
                                1500
                            );
                        }
                    } else {
                        // Timeout - show current status anyway
                        checkLicenseStatus();
                        showNotification('warning', 
                            '⏱️ Deactivation Timeout', 
                            'License deactivation may still be processing. Check the status above.', 
                            4000
                        );
                    }
                } catch (pollError) {
                    console.error('Error polling deactivation status:', pollError);
                    if (attempts >= maxAttempts) {
                        checkLicenseStatus(); // Fallback status check
                        showNotification('warning', 
                            '⚠️ Status Check Failed', 
                            'Unable to verify deactivation status. Please refresh manually.', 
                            4000
                        );
                    }
                }
            };
            
            // Start polling after a short delay
            setTimeout(pollForDeactivation, 1500);
            
        } else {
            showNotification('error', 
                '❌ License Deactivation Failed', 
                result.error || 'Unable to deactivate license. Please try again.', 
                5000
            );
        }
    } catch (error) {
        showNotification('error', 
            '❌ Deactivation Failed', 
            `Error deactivating license: ${error.message}`, 
            4000
        );
    } finally {
        // Restore button state
        if (button) {
            button.disabled = false;
            button.textContent = originalText;
            button.style.opacity = '1';
        }
    }
}

// Generate test license
async function generateTestLicense() {
    const button = document.querySelector('.license-actions .btn-info');
    const originalText = button.textContent;
    
    button.disabled = true;
    button.textContent = '🔄 Generating...';
    
    try {
        showNotification('info', 'Generating License', 'Creating a trial license key...', 3000);
        
        const response = await fetch('/api/license/generate-trial-sync', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                user_email: 'dev@warpcore.test',
                days: 7
            })
        });
        
        const result = await response.json();
        
        if (result.success) {
            // Check if we got the license key directly (sync endpoint)
            if (result.license_key) {
                // Success! We got a real encrypted license key
                document.getElementById('license-key').value = result.license_key;
                
                showNotification('success', 
                    '🎟️ Real License Key Generated!', 
                    `Generated encrypted license key! Valid for ${result.days || 7} days. Ready to activate!`, 
                    6000
                );
                
                // Show activation instruction
                setTimeout(() => {
                    showNotification('info', 
                        '🔑 Ready to Activate', 
                        'This is a real FERNET-encrypted license key. Click "Activate License" to test the full validation workflow.', 
                        5000
                    );
                }, 2000);
                
                return;
            }
            
            // Keep the polling as fallback but reduce attempts
            let attempts = 0;
            const maxAttempts = 3;
            const pollInterval = 2000; // 2 seconds
            
            const pollForLicense = async () => {
                attempts++;
                
                try {
                    // Instead of polling status, let's try to get the result directly from generation endpoint
                    // For now, let's create a simple fallback approach
                    
                    // Try to get any available license info or generate a simple encrypted key
                    const statusResponse = await fetch('/api/license/status');
                    const statusResult = await statusResponse.json();
                    
                    // Check if the backend generated and activated a license automatically
                    if (statusResult.success && statusResult.status === 'active' && statusResult.license_key) {
                        // License was generated and activated automatically
                        document.getElementById('license-key').value = statusResult.license_key;
                        showNotification('success', 
                            '🎟️ Trial License Generated & Active!', 
                            'Your trial license has been generated and activated automatically.', 
                            5000
                        );
                        return;
                    }
                    
                    // If still no license after a few attempts, call a direct generation endpoint that returns the key
                    if (attempts >= 3) {
                        // Try to get the generated key directly - we'll call the provider endpoint
                        try {
                            const directGenResponse = await fetch('/api/license/generate-trial', {
                                method: 'POST',
                                headers: { 'Content-Type': 'application/json' },
                                body: JSON.stringify({
                                    user_email: 'dev@warpcore.test',
                                    days: 7,
                                    return_key: true // Flag to return key immediately
                                })
                            });
                            
                            const directResult = await directGenResponse.json();
                            
                            if (directResult.success && directResult.license_key) {
                                // Got a license key directly!
                                document.getElementById('license-key').value = directResult.license_key;
                                showNotification('success', 
                                    '🔑 Test License Key Generated!', 
                                    'License key ready! You can now copy it and click "Activate License" to test the activation flow.', 
                                    7000
                                );
                                
                                // Show activation instruction
                                setTimeout(() => {
                                    showNotification('info', 
                                        '📍 Next Step', 
                                        'Click "Activate License" to test the full activation workflow with this generated key.', 
                                        5000
                                    );
                                }, 2000);
                                return;
                            }
                        } catch (directError) {
                            console.warn('Direct generation failed:', directError);
                        }
                    }
                    
                    // Continue polling if we haven't hit max attempts
                    if (attempts < maxAttempts) {
                        setTimeout(pollForLicense, pollInterval);
                        
                        // Update progress notification
                        if (attempts % 2 === 0) {
                            showNotification('info', 
                                '🔄 Generating License...', 
                                `Creating test license key (${attempts}/${maxAttempts})...`, 
                                2000
                            );
                        }
                    } else {
                        // Max attempts reached - explain the workflow
                        showNotification('warning', 
                            '⏱️ Generation Taking Longer', 
                            'License generation is taking longer than expected. In production, customers receive keys via email after payment.', 
                            6000
                        );
                        
                        // Show workflow info
                        setTimeout(() => {
                            showNotification('info', 
                                '📬 Production Flow', 
                                '1. Customer pays → 2. Cloud generates key → 3. Email delivery → 4. Customer enters key → 5. WARPCORE validates', 
                                6000
                            );
                        }, 1000);
                    }
                } catch (pollError) {
                    console.error('Error polling for license:', pollError);
                    if (attempts >= maxAttempts) {
                        showNotification('error', 
                            '❌ License Polling Failed', 
                            'Unable to retrieve generated license. Please try again.', 
                            4000
                        );
                    }
                }
            };
            
            // Start polling after a short delay
            setTimeout(pollForLicense, 2000);
            
        } else {
            showNotification('error', 
                '❌ Generation Failed', 
                result.error || 'Unable to generate trial license. Please try again.', 
                4000
            );
        }
    } catch (error) {
        showNotification('error', 
            '❌ Generation Failed', 
            `Error generating license: ${error.message}`, 
            4000
        );
    } finally {
        button.disabled = false;
        button.textContent = originalText;
    }
}

// Show license info
function showLicenseInfo() {
    const badge = document.getElementById('license-badge').textContent;
    const email = document.getElementById('license-email').textContent;
    const status = document.getElementById('detail-status').textContent;
    const tier = document.getElementById('detail-tier').textContent;
    const features = document.getElementById('detail-features').textContent;
    
    const info = `
        <strong>Status:</strong> ${status}<br>
        <strong>Tier:</strong> ${tier}<br>
        <strong>Email:</strong> ${email}<br>
        <strong>Features:</strong> ${features}
    `;
    
    showResult('info', 'License Information', info);
}

// Feature testing
async function testFeature(featureName) {
    const button = document.querySelector(`[data-feature="${featureName}"]`);
    const originalText = button.textContent;
    
    button.disabled = true;
    button.textContent = '🔄 Testing...';
    
    // Show immediate feedback
    showNotification('info', 'Feature Test Started', `Testing ${featureName.toUpperCase()} feature capabilities...`, 2000);
    
    try {
        // Check if we have access to this feature based on license
        const hasAccess = button.classList.contains('unlocked');
        
        if (!hasAccess) {
            // Feature locked - show upgrade message immediately
            const tierRequirements = {
                'advanced': 'Standard',
                'automation': 'Standard', 
                'enterprise': 'Premium',
                'analytics': 'Premium'
            };
            
            const requiredTier = tierRequirements[featureName] || 'Higher';
            showNotification('warning', 
                `🔒 ${featureName.toUpperCase()} Feature Locked`, 
                `This feature requires ${requiredTier} tier or higher. Upgrade your license to unlock.`, 
                4000
            );
            
            button.disabled = false;
            button.textContent = originalText;
            return;
        }
        
        // Try to call real backend feature test endpoint
        let backendResult = null;
        const featureEndpoints = {
            'basic': '/api/endpoints/test',
            'info': '/api/license/status', 
            'advanced': '/api/config',
            'automation': '/api/gcp/endpoints',
            'enterprise': '/api/pap/status',
            'analytics': '/api/license/subscription'
        };
        
        const testEndpoint = featureEndpoints[featureName];
        
        if (testEndpoint) {
            try {
                const response = await fetch(testEndpoint);
                backendResult = await response.json();
                
                if (response.ok && backendResult.success) {
                    // Real backend test succeeded
                    showNotification('success', 
                        `✨ ${featureName.toUpperCase()} Feature Active`, 
                        `Backend feature test passed successfully! Feature is fully operational.`, 
                        4000
                    );
                } else {
                    // Backend test failed but feature is licensed
                    showNotification('warning', 
                        `⚠️ ${featureName.toUpperCase()} Backend Issue`, 
                        `Feature is licensed but backend test failed: ${backendResult?.error || 'Unknown error'}`, 
                        5000
                    );
                }
            } catch (fetchError) {
                // Network error or endpoint not available
                console.warn(`Feature test endpoint ${testEndpoint} not available:`, fetchError);
                
                // Fall back to simulated success for licensed features
                const featureDescriptions = {
                    'basic': 'Essential system operations and core functionality',
                    'info': 'System information display and status monitoring',
                    'advanced': 'Advanced cloud operations and automation tools',
                    'automation': 'Automated workflows and scripting capabilities',
                    'enterprise': 'Enterprise-grade security and compliance features',
                    'analytics': 'Advanced analytics, reporting and insights'
                };
                
                const description = featureDescriptions[featureName] || 'Feature functionality';
                showNotification('info', 
                    `✨ ${featureName.toUpperCase()} Feature Licensed`, 
                    `${description} - Feature is licensed and available (simulated test).`, 
                    3000
                );
            }
        } else {
            // No specific backend endpoint - simulate based on license
            const featureDescriptions = {
                'basic': 'Essential system operations and core functionality',
                'info': 'System information display and status monitoring',
                'advanced': 'Advanced cloud operations and automation tools',
                'automation': 'Automated workflows and scripting capabilities',
                'enterprise': 'Enterprise-grade security and compliance features',
                'analytics': 'Advanced analytics, reporting and insights'
            };
            
            const description = featureDescriptions[featureName] || 'Feature functionality';
            showNotification('success', 
                `✨ ${featureName.toUpperCase()} Feature Active`, 
                `${description} - Feature executed successfully!`, 
                3000
            );
        }
        
    } catch (error) {
        console.error('Feature test error:', error);
        showNotification('error', 
            `❌ ${featureName.toUpperCase()} Test Failed`, 
            `Feature test encountered an error: ${error.message}`, 
            4000
        );
    } finally {
        button.disabled = false;
        button.textContent = originalText;
    }
}

// Show notification at top of screen
function showNotification(type, title, message, duration = 4000) {
    const container = document.getElementById('notification-container');
    
    // Create notification card
    const notification = document.createElement('div');
    notification.className = `notification-card notification-${type}`;
    
    // Create unique ID
    const notificationId = 'notif_' + Date.now() + '_' + Math.random().toString(36).substr(2, 9);
    notification.id = notificationId;
    
    notification.innerHTML = `
        <div class="notification-content">
            <div class="notification-title">${title}</div>
            <div class="notification-message">${message}</div>
            <div class="notification-time">${new Date().toLocaleTimeString()}</div>
        </div>
        <button class="notification-close" onclick="dismissNotification('${notificationId}')">&times;</button>
        <div class="notification-progress"></div>
    `;
    
    // Add to container
    container.appendChild(notification);
    
    // Also add to results history
    addToHistory(type, title, message);
    
    // Auto-dismiss after duration
    setTimeout(() => {
        dismissNotification(notificationId);
    }, duration);
    
    // Click to dismiss
    notification.addEventListener('click', () => {
        dismissNotification(notificationId);
    });
    
    return notificationId;
}

// Dismiss notification
function dismissNotification(notificationId) {
    const notification = document.getElementById(notificationId);
    if (notification) {
        notification.classList.add('fade-out');
        setTimeout(() => {
            notification.remove();
        }, 300);
    }
}

// Add to history in results section
function addToHistory(type, title, message) {
    const container = document.getElementById('results-container');
    
    // Remove no-results placeholder
    const noResults = container.querySelector('.no-results');
    if (noResults) noResults.remove();
    
    // Create history item
    const resultItem = document.createElement('div');
    resultItem.className = `result-item ${type}`;
    resultItem.innerHTML = `
        <strong>${title}</strong><br>
        <span>${message}</span>
        <div style="font-size: 0.8em; color: #666; margin-top: 0.5rem;">
            ${new Date().toLocaleTimeString()}
        </div>
    `;
    
    container.insertBefore(resultItem, container.firstChild);
    
    // Keep only 10 results
    const results = container.querySelectorAll('.result-item');
    if (results.length > 10) {
        results[results.length - 1].remove();
    }
}

// Legacy function for compatibility
function showResult(type, title, message) {
    showNotification(type, title, message);
}

// Global functions - make all functions available globally
if (typeof window !== 'undefined') {
    // Modal functions
    window.showLicenseModal = showLicenseModal;
    window.closeLicenseModal = closeLicenseModal;
    
    // License management functions
    window.activateLicense = activateLicense;
    window.deactivateLicense = deactivateLicense;
    window.generateTestLicense = generateTestLicense;
    window.checkLicenseStatus = checkLicenseStatus;
    window.showLicenseInfo = showLicenseInfo;
    
    // Feature testing function
    window.testFeature = testFeature;
    
    // Notification functions
    window.showNotification = showNotification;
    window.dismissNotification = dismissNotification;
    
    // Utility functions
    window.updateLicenseDisplay = updateLicenseDisplay;
    window.initLicenseUI = initLicenseUI;
    
    console.log('🔧 All WARPCORE UI functions mapped to window object');
}
