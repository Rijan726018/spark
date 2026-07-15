'use strict';

const { contextBridge, ipcRenderer } = require('electron');

// Expose a controlled subset of Electron APIs to the renderer
contextBridge.exposeInMainWorld('electronAPI', {
  // App info
  getVersion: () => ipcRenderer.invoke('get-version'),
  isDev: () => ipcRenderer.invoke('is-dev'),
  platform: process.platform,

  // External links
  openExternal: (url) => ipcRenderer.invoke('open-external', url),

  // Python backend status
  pythonStatus: () => ipcRenderer.invoke('python-status'),

  // Custom window controls (for frameless titlebar buttons)
  minimize: () => ipcRenderer.invoke('window-minimize'),
  maximize: () => ipcRenderer.invoke('window-maximize'),
  close: () => ipcRenderer.invoke('window-close'),
});
