// WARPCORE Dashboard Main Controller

class WARPCOREDashboard {
    constructor() {
        this.isInitialized = false;
        this.errorCount = 0;
        this.maxRetries = 3;
        this.init();
    }

    async init() {
        try {
            // Wait for other components to initialize
            await this.waitForDependencies();
            
            // Add keyboard shortcuts
            this.addKeyboardShortcuts();
            
            // Add manual refresh button
            this.addRefreshControls();
            
            // Initialize real-time updates
            this.initializeRealTimeUpdates();
            
            this.isInitialized = true;
            console.log('WARPCORE Dashboard initialized successfully');
            
        } catch (error) {
            console.error('Dashboard initialization failed:', error);
            this.handleInitializationError(error);
        }
    }

    async waitForDependencies() {
        // Wait for chart manager and data loader to be available
        let attempts = 0;
        const maxAttempts = 50;
        
        while ((!window.chartManager || !window.dataLoader) && attempts < maxAttempts) {
            await new Promise(resolve => setTimeout(resolve, 100));
            attempts++;
        }
        
        if (!window.chartManager || !window.dataLoader) {
            throw new Error('Required dependencies not loaded');
        }
    }

    addKeyboardShortcuts() {
        document.addEventListener('keydown', (e) => {
            // Ctrl/Cmd + R for refresh
            if ((e.ctrlKey || e.metaKey) && e.key === 'r') {
                e.preventDefault();
                this.manualRefresh();
            }
            
            // F5 for full refresh
            if (e.key === 'F5') {
                e.preventDefault();
                this.fullRefresh();
            }
        });
    }

    addRefreshControls() {
        // Add refresh button to header
        const headerContent = document.querySelector('.header-content');
        const refreshButton = document.createElement('button');
        refreshButton.className = 'refresh-button';
        refreshButton.innerHTML = '🔄 Refresh';
        refreshButton.onclick = () => this.manualRefresh();
        
        // Add styles for refresh button
        refreshButton.style.cssText = `
            background: rgba(0, 212, 255, 0.2);
            border: 1px solid rgba(0, 212, 255, 0.3);
            color: #00d4ff;
            padding: 8px 16px;
            border-radius: 6px;
            cursor: pointer;
            font-size: 0.9rem;
            transition: all 0.3s ease;
            margin-left: 15px;
        `;
        
        refreshButton.addEventListener('mouseover', () => {
            refreshButton.style.background = 'rgba(0, 212, 255, 0.3)';
            refreshButton.style.transform = 'translateY(-1px)';
        });
        
        refreshButton.addEventListener('mouseout', () => {
            refreshButton.style.background = 'rgba(0, 212, 255, 0.2)';
            refreshButton.style.transform = 'translateY(0)';
        });
        
        headerContent.appendChild(refreshButton);
    }

    initializeRealTimeUpdates() {
        // Listen for data updates
        document.addEventListener('dataUpdated', (e) => {
            this.handleDataUpdate(e.detail);
        });
        
        // Monitor system performance
        this.startPerformanceMonitoring();
    }

    startPerformanceMonitoring() {
        setInterval(() => {
            if (performance.memory) {
                const memoryInfo = performance.memory;
                if (memoryInfo.usedJSHeapSize > 50 * 1024 * 1024) { // 50MB
                    console.warn('High memory usage detected:', memoryInfo.usedJSHeapSize / 1024 / 1024, 'MB');
                }
            }
        }, 30000); // Check every 30 seconds
    }

    async manualRefresh() {
        const refreshButton = document.querySelector('.refresh-button');
        if (refreshButton) {
            refreshButton.innerHTML = '⟳ Refreshing...';
            refreshButton.disabled = true;
        }
        
        try {
            await window.dataLoader.refresh();
            this.showNotification('Dashboard refreshed successfully', 'success');
        } catch (error) {
            console.error('Manual refresh failed:', error);
            this.showNotification('Refresh failed', 'error');
        } finally {
            if (refreshButton) {
                refreshButton.innerHTML = '🔄 Refresh';
                refreshButton.disabled = false;
            }
        }
    }

    async fullRefresh() {
        // Clear all data and reinitialize
        try {
            window.chartManager.destroyCharts();
            window.chartManager = new ChartManager();
            await window.dataLoader.refresh();
            this.showNotification('Full refresh completed', 'success');
        } catch (error) {
            console.error('Full refresh failed:', error);
            this.showNotification('Full refresh failed', 'error');
        }
    }

    handleDataUpdate(data) {
        // Update charts if data is available
        if (data && data.visualization_dashboard_data) {
            window.chartManager.updateAllCharts(data.visualization_dashboard_data);
        }
        
        // Update page title with workflow status
        if (data && data.workflow_analytics) {
            const status = data.workflow_analytics.workflow_status || 'Unknown';
            const completion = data.workflow_analytics.completion_percentage || 0;
            document.title = `WARPCORE Analytics - ${status} (${completion}%)`;
        }
    }

    handleInitializationError(error) {
        this.errorCount++;
        
        if (this.errorCount <= this.maxRetries) {
            console.log(`Retrying initialization (attempt ${this.errorCount}/${this.maxRetries})`);
            setTimeout(() => this.init(), 2000);
        } else {
            this.showFatalError(error);
        }
    }

    showFatalError(error) {
        const dashboard = document.querySelector('.dashboard-container');
        dashboard.innerHTML = `
            <div class="error-container" style="
                text-align: center;
                padding: 50px;
                color: #ef4444;
            ">
                <h2>Dashboard Initialization Failed</h2>
                <p>Unable to load WARPCORE Analytics Dashboard</p>
                <details style="margin-top: 20px; text-align: left;">
                    <summary>Error Details</summary>
                    <pre style="background: rgba(255,255,255,0.1); padding: 10px; border-radius: 4px; margin-top: 10px;">
                        ${error.stack || error.message}
                    </pre>
                </details>
                <button onclick="location.reload()" style="
                    margin-top: 20px;
                    padding: 10px 20px;
                    background: #ef4444;
                    color: white;
                    border: none;
                    border-radius: 6px;
                    cursor: pointer;
                ">Reload Page</button>
            </div>
        `;
    }

    showNotification(message, type = 'info') {
        // Create notification element
        const notification = document.createElement('div');
        notification.className = `notification notification-${type}`;
        notification.textContent = message;
        
        // Style notification
        notification.style.cssText = `
            position: fixed;
            top: 20px;
            right: 20px;
            padding: 12px 20px;
            border-radius: 6px;
            color: white;
            font-weight: 500;
            z-index: 9999;
            transform: translateX(100%);
            transition: transform 0.3s ease;
            max-width: 300px;
        `;
        
        // Set background color based on type
        const colors = {
            success: '#10b981',
            error: '#ef4444',
            warning: '#f59e0b',
            info: '#00d4ff'
        };
        notification.style.background = colors[type] || colors.info;
        
        // Add to page
        document.body.appendChild(notification);
        
        // Animate in
        setTimeout(() => {
            notification.style.transform = 'translateX(0)';
        }, 100);
        
        // Remove after delay
        setTimeout(() => {
            notification.style.transform = 'translateX(100%)';
            setTimeout(() => {
                if (notification.parentNode) {
                    notification.parentNode.removeChild(notification);
                }
            }, 300);
        }, 3000);
    }

    // Analytics tracking methods
    trackEvent(eventName, properties = {}) {
        console.log('Dashboard Event:', eventName, properties);
    }

    trackPerformance(metricName, value) {
        console.log('Performance Metric:', metricName, value);
    }

    // Utility methods
    formatBytes(bytes) {
        if (bytes === 0) return '0 Bytes';
        const k = 1024;
        const sizes = ['Bytes', 'KB', 'MB', 'GB'];
        const i = Math.floor(Math.log(bytes) / Math.log(k));
        return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i];
    }

    formatDuration(minutes) {
        if (minutes < 60) {
            return `${minutes.toFixed(1)}m`;
        }
        const hours = Math.floor(minutes / 60);
        const remainingMinutes = minutes % 60;
        return `${hours}h ${remainingMinutes.toFixed(0)}m`;
    }

    // Debug methods
    getDebugInfo() {
        return {
            initialized: this.isInitialized,
            errorCount: this.errorCount,
            chartManagerLoaded: !!window.chartManager,
            dataLoaderLoaded: !!window.dataLoader,
            memoryUsage: performance.memory ? {
                used: this.formatBytes(performance.memory.usedJSHeapSize),
                total: this.formatBytes(performance.memory.totalJSHeapSize),
                limit: this.formatBytes(performance.memory.jsHeapSizeLimit)
            } : 'Not available'
        };
    }
}

// Add debug methods to window for console access
window.debugDashboard = {
    refresh: () => window.dashboard?.manualRefresh(),
    fullRefresh: () => window.dashboard?.fullRefresh(),
    info: () => window.dashboard?.getDebugInfo(),
    notification: (msg, type) => window.dashboard?.showNotification(msg, type)
};

// Initialize dashboard when DOM is ready
document.addEventListener('DOMContentLoaded', () => {
    window.dashboard = new WARPCOREDashboard();
});

// Add global error handling
window.addEventListener('error', (e) => {
    console.error('Global error:', e.error);
    if (window.dashboard) {
        window.dashboard.showNotification('An error occurred', 'error');
    }
});

window.addEventListener('unhandledrejection', (e) => {
    console.error('Unhandled promise rejection:', e.reason);
    if (window.dashboard) {
        window.dashboard.showNotification('Promise rejection occurred', 'warning');
    }
});