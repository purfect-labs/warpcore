const { app, BrowserWindow, Menu, dialog, shell } = require('electron');
const { spawn } = require('child_process');
const path = require('path');
const fs = require('fs');

class waRpcoRENativeApp {
    constructor() {
        this.mainWindow = null;
        this.waRPCOReProcess = null;
        this.serverPort = 8000; // Use standard waRpcoRE port
        this.serverReady = false;
        
        app.whenReady().then(() => this.init());
        app.on('window-all-closed', () => this.quit());
        app.on('activate', () => this.createWindow());
        app.on('before-quit', () => this.cleanup());
    }

    async init() {
        console.log('🚀 waRpcoRE Unified Native App Starting...');
        
        await this.startwaRpcoREServer();
        await this.waitForServer();
        this.createWindow();
        this.setupMenu();
    }

    async startwaRpcoREServer() {
        console.log('⚙️ Starting waRpcoRE server...');
        
        try {
            const executablePath = this.getwaRpcoREExecutablePath();
            console.log(`waRpcoRE Executable: ${executablePath}`);
            
            if (!fs.existsSync(executablePath)) {
                throw new Error(`waRpcoRE executable not found: ${executablePath}`);
            }

            // Start waRpcoRE process with default port (8000)
            this.waRPCOReProcess = spawn(executablePath, [], {
                env: process.env,
                detached: false
            });
            
            this.waRPCOReProcess.stdout.on('data', (data) => {
                const output = data.toString().trim();
                console.log(`[waRpcoRE] ${output}`);
                if (output.includes('Uvicorn running')) {
                    this.serverReady = true;
                }
            });
            
            this.waRPCOReProcess.stderr.on('data', (data) => {
                console.error(`[waRpcoRE Error] ${data.toString().trim()}`);
            });
            
            this.waRPCOReProcess.on('exit', (code) => {
                console.log(`waRpcoRE process exited with code ${code}`);
            });
            
            console.log('✅ waRpcoRE server process started');
            
        } catch (error) {
            console.error('❌ Failed to start waRpcoRE server:', error);
            dialog.showErrorBox('Server Error', `Failed to start waRpcoRE server: ${error.message}`);
        }
    }

    getwaRpcoREExecutablePath() {
        if (app.isPackaged) {
            return path.join(process.resourcesPath, 'waRPCORe_app');
        } else {
            // Development mode - use the built executable
            return path.join(__dirname, 'resources', 'waRPCORe_app');
        }
    }

    async waitForServer() {
        console.log('⏳ Waiting for waRpcoRE server...');
        
        for (let i = 0; i < 150; i++) {
            try {
                await this.checkServerHealth();
                console.log('✅ waRpcoRE server is ready!');
                return;
            } catch (error) {
                await this.sleep(100);
            }
        }
        console.error('❌ waRpcoRE server failed to start');
    }

    checkServerHealth() {
        return new Promise((resolve, reject) => {
            const http = require('http');
            const req = http.get(`http://127.0.0.1:${this.serverPort}/api/status`, (res) => {
                if (res.statusCode === 200) {
                    resolve();
                } else {
                    reject(new Error(`Server returned ${res.statusCode}`));
                }
                req.destroy();
            });
            
            req.on('error', reject);
            req.setTimeout(1000, () => {
                req.destroy();
                reject(new Error('Request timeout'));
            });
        });
    }

    sleep(ms) {
        return new Promise(resolve => setTimeout(resolve, ms));
    }

    createWindow() {
        if (this.mainWindow) {
            this.mainWindow.show();
            return;
        }

        this.mainWindow = new BrowserWindow({
            width: 1400,
            height: 900,
            minWidth: 1000,
            minHeight: 600,
            titleBarStyle: 'default',
            webPreferences: {
                nodeIntegration: false,
                contextIsolation: true,
                preload: path.join(__dirname, 'preload.js')
            },
            show: false
        });

        this.mainWindow.loadURL(`http://127.0.0.1:${this.serverPort}`);
        
        this.mainWindow.once('ready-to-show', () => {
            this.mainWindow.show();
            console.log('✅ waRpcoRE window ready');
        });
        
        this.mainWindow.on('closed', () => {
            this.mainWindow = null;
        });
    }

    setupMenu() {
        const template = [
            {
                label: 'waRpcoRE',
                submenu: [
                    { role: 'about' },
                    { type: 'separator' },
                    { role: 'quit' }
                ]
            },
            {
                label: 'Edit',
                submenu: [
                    { role: 'copy' },
                    { role: 'paste' },
                    { role: 'selectall' }
                ]
            },
            {
                label: 'View',
                submenu: [
                    { role: 'reload' },
                    { role: 'toggledevtools' },
                    { type: 'separator' },
                    { role: 'togglefullscreen' }
                ]
            }
        ];
        
        Menu.setApplicationMenu(Menu.buildFromTemplate(template));
    }

    cleanup() {
        if (this.waRPCOReProcess) {
            this.waRPCOReProcess.kill();
        }
    }

    quit() {
        this.cleanup();
        if (process.platform !== 'darwin') {
            app.quit();
        }
    }
}

new waRpcoRENativeApp();
