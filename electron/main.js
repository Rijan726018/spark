'use strict';

const { app, BrowserWindow, ipcMain, shell, Menu } = require('electron');
const path = require('path');
const { spawn } = require('child_process');

const isDev = process.argv.includes('--dev');
let mainWindow = null;
let pythonProcess = null;
let pythonReady = false;

// ─── Python Backend ────────────────────────────────────────────────────────────

function startPythonBackend() {
  const projectRoot = path.join(__dirname, '..');
  const pythonExe = path.join(projectRoot, '.venv312', 'Scripts', 'python.exe');
  const serverScript = path.join(projectRoot, 'server', 'main.py');

  console.log('[Electron] Starting Python backend...');
  console.log('[Electron] Python exe:', pythonExe);
  console.log('[Electron] Server script:', serverScript);

  pythonProcess = spawn(pythonExe, [serverScript], {
    cwd: projectRoot,
    stdio: ['ignore', 'pipe', 'pipe'],
    windowsHide: true,
  });

  pythonProcess.stdout.on('data', (data) => {
    const msg = data.toString().trim();
    console.log('[Python]', msg);
    // Signal readiness when uvicorn prints "Application startup complete"
    if (msg.includes('Application startup complete') || msg.includes('Uvicorn running')) {
      pythonReady = true;
    }
  });

  pythonProcess.stderr.on('data', (data) => {
    const msg = data.toString().trim();
    // uvicorn logs to stderr — treat info lines as non-errors
    if (msg.includes('INFO') || msg.includes('startup')) {
      console.log('[Python INFO]', msg);
      if (msg.includes('Application startup complete') || msg.includes('Uvicorn running')) {
        pythonReady = true;
      }
    } else {
      console.error('[Python ERR]', msg);
    }
  });

  pythonProcess.on('close', (code) => {
    console.log('[Python] Process exited with code', code);
    pythonProcess = null;
  });

  pythonProcess.on('error', (err) => {
    console.error('[Python] Failed to start:', err.message);
  });
}

function killPythonBackend() {
  if (pythonProcess) {
    console.log('[Electron] Killing Python backend...');
    try {
      // On Windows, use taskkill to kill the entire process tree
      const { execSync } = require('child_process');
      execSync(`taskkill /PID ${pythonProcess.pid} /F /T`, { windowsHide: true });
    } catch (e) {
      pythonProcess.kill('SIGTERM');
    }
    pythonProcess = null;
  }
}

// ─── Window Creation ───────────────────────────────────────────────────────────

function createWindow() {
  // Suppress default menu
  Menu.setApplicationMenu(null);

  mainWindow = new BrowserWindow({
    width: 1600,
    height: 1000,
    minWidth: 1200,
    minHeight: 700,
    backgroundColor: '#000000',
    titleBarStyle: 'hidden',
    titleBarOverlay: {
      color: '#0a0a0a',
      symbolColor: '#f5f5f7',
      height: 32,
    },
    webPreferences: {
      preload: path.join(__dirname, 'preload.js'),
      contextIsolation: true,
      nodeIntegration: false,
      webSecurity: !isDev,   // relax for dev HMR
      allowRunningInsecureContent: isDev,
    },
    icon: path.join(__dirname, '..', 'assets', 'icon.ico'),
    title: 'NEXUS ALGO TERMINAL v3.0',
    show: false,             // show after ready-to-show
  });

  // Show when content is ready (avoids white flash)
  mainWindow.once('ready-to-show', () => {
    mainWindow.show();
    if (isDev) mainWindow.webContents.openDevTools({ mode: 'detach' });
  });

  if (isDev) {
    console.log('[Electron] Dev mode — loading http://localhost:3000');
    mainWindow.loadURL('http://localhost:3000').catch((err) => {
      console.error('[Electron] Could not load Vite dev server:', err.message);
      // Retry in 2 seconds
      setTimeout(() => mainWindow.loadURL('http://localhost:3000').catch(console.error), 2000);
    });
  } else {
    const indexPath = path.join(__dirname, '..', 'frontend', 'dist', 'index.html');
    console.log('[Electron] Prod mode — loading', indexPath);
    mainWindow.loadFile(indexPath);
  }

  mainWindow.on('closed', () => {
    mainWindow = null;
  });
}

// ─── App Lifecycle ─────────────────────────────────────────────────────────────

app.whenReady().then(() => {
  startPythonBackend();

  // Give Python backend time to bind its port before window tries to connect
  const PYTHON_WAIT_MS = isDev ? 2000 : 3000;
  setTimeout(createWindow, PYTHON_WAIT_MS);

  app.on('activate', () => {
    if (BrowserWindow.getAllWindows().length === 0) createWindow();
  });
});

app.on('window-all-closed', () => {
  killPythonBackend();
  if (process.platform !== 'darwin') app.quit();
});

app.on('before-quit', () => {
  killPythonBackend();
});

// Handle renderer asking to reload (useful in dev)
app.on('web-contents-created', (_, wc) => {
  wc.on('before-input-event', (event, input) => {
    if (input.type === 'keyDown' && input.key === 'F5') {
      wc.reload();
    }
    if (input.type === 'keyDown' && input.key === 'F12') {
      wc.openDevTools({ mode: 'detach' });
    }
  });
});

// ─── IPC Handlers ─────────────────────────────────────────────────────────────

ipcMain.handle('get-version', () => app.getVersion());

ipcMain.handle('open-external', (_, url) => {
  shell.openExternal(url);
});

ipcMain.handle('is-dev', () => isDev);

ipcMain.handle('python-status', () => ({
  running: pythonProcess !== null,
  ready: pythonReady,
  pid: pythonProcess ? pythonProcess.pid : null,
}));

ipcMain.handle('window-minimize', () => {
  if (mainWindow) mainWindow.minimize();
});

ipcMain.handle('window-maximize', () => {
  if (mainWindow) {
    if (mainWindow.isMaximized()) mainWindow.unmaximize();
    else mainWindow.maximize();
  }
});

ipcMain.handle('window-close', () => {
  if (mainWindow) mainWindow.close();
});
