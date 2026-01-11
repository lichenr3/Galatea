import { ipcRenderer } from 'electron';

// --------- Expose some API to the Renderer process ---------
window.addEventListener('message', (event) => {
  if (event.data === 'get-electron-api') {
    window.postMessage({ type: 'electron-api', api: 'available' }, '*');
  }
});

// For simplicity, we can also use window.electron if contextIsolation is false
// but let's just make sure ipcRenderer is available if needed.
// However, since we set nodeIntegration: true and contextIsolation: false,
// we can directly use require('electron').ipcRenderer in the renderer.

