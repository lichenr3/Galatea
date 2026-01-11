import { app, BrowserWindow, ipcMain } from 'electron';
import path from 'node:path';
import { fileURLToPath } from 'node:url';

const __dirname = path.dirname(fileURLToPath(import.meta.url));

// The built directory structure
// |- dist
//   |- electron
//     |- main.js
//     |- preload.mjs
// |- dist-electron
//   |- main.js
//   |- preload.mjs

process.env.APP_ROOT = path.join(__dirname, '..');

export const VITE_DEV_SERVER_URL = process.env['VITE_DEV_SERVER_URL'];
export const MAIN_DIST = path.join(process.env.APP_ROOT, 'dist-electron');
export const RENDERER_DIST = path.join(process.env.APP_ROOT, 'dist');

process.env.VITE_PUBLIC = VITE_DEV_SERVER_URL ? path.join(process.env.APP_ROOT, 'public') : RENDERER_DIST;

let win: BrowserWindow | null = null;

function createWindow() {
  win = new BrowserWindow({
    width: 1200,
    height: 800,
    transparent: true,    // 允许透明
    frame: false,          // 无边框
    icon: path.join(process.env.VITE_PUBLIC!, 'vite.svg'),
    webPreferences: {
      preload: path.join(__dirname, 'preload.js'),
      nodeIntegration: true,
      contextIsolation: false,
    },
  });

  // Test active push message to Renderer-process.
  win.webContents.on('did-finish-load', () => {
    win?.webContents.send('main-process-message', (new Date()).toLocaleString());
  });

  if (VITE_DEV_SERVER_URL) {
    win.loadURL(VITE_DEV_SERVER_URL);
  } else {
    win.loadFile(path.join(RENDERER_DIST, 'index.html'));
  }
}

// Quit when all windows are closed, except on macOS. There, it's common
// for applications and their menu bar to stay active until the user quits
// explicitly with Cmd + Q.
app.on('window-all-closed', () => {
  if (process.platform !== 'darwin') {
    app.quit();
    win = null;
  }
});

app.on('activate', () => {
  if (BrowserWindow.getAllWindows().length === 0) {
    createWindow();
  }
});

  app.whenReady().then(createWindow);

  // IPC Handlers for Window Controls
  ipcMain.on('window-minimize', (event) => {
    const senderWin = BrowserWindow.fromWebContents(event.sender);
    if (senderWin) {
      senderWin.minimize();
    }
  });

  ipcMain.on('window-close', (event) => {
    const senderWin = BrowserWindow.fromWebContents(event.sender);
    if (senderWin) {
      senderWin.close();
    }
  });

  // IPC Handlers for Desktop Pet Mode
  ipcMain.on('set-window-pet-mode', (event, isPetMode, isMinimized) => {
    const senderWin = BrowserWindow.fromWebContents(event.sender);
    if (!senderWin) return;

    console.log(`[Main] set-window-pet-mode: pet=${isPetMode}, min=${isMinimized}`);
    
    if (senderWin.isMaximized()) {
      senderWin.unmaximize();
    }

    if (isMinimized) {
      // ✅ 最小化（悬浮球）模式
      senderWin.setResizable(false); // 禁止调整大小，保持圆形
      senderWin.setMinimumSize(60, 60);
      senderWin.setSize(60, 60);
      senderWin.setAlwaysOnTop(true, 'screen-saver');
    } else if (isPetMode) {
      // ✅ 桌宠（聊天框）模式
      senderWin.setResizable(true);
      senderWin.setMinimumSize(100, 100); 
      senderWin.setSize(350, 450);
      senderWin.setAlwaysOnTop(true, 'screen-saver');
      senderWin.show();
    } else {
      // ✅ 正常模式
      senderWin.setAlwaysOnTop(false);
      senderWin.setMinimumSize(800, 600);
      senderWin.setSize(1200, 800);
      senderWin.center();
    }
  });

