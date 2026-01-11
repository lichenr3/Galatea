import React from 'react';
import './WindowControls.css';

interface WindowControlsProps {
  isPetMode?: boolean;
}

export const WindowControls: React.FC<WindowControlsProps> = ({ isPetMode = false }) => {
  const handleMinimize = () => {
    try {
      const electron = (window as any).require?.('electron');
      if (electron?.ipcRenderer) {
        electron.ipcRenderer.send('window-minimize');
      }
    } catch (error) {
      console.error('Failed to minimize window:', error);
    }
  };

  const handleClose = () => {
    try {
      const electron = (window as any).require?.('electron');
      if (electron?.ipcRenderer) {
        electron.ipcRenderer.send('window-close');
      }
    } catch (error) {
      console.error('Failed to close window:', error);
    }
  };

  if (isPetMode) {
    return null;
  }

  return (
    <div className="window-controls-inline" style={{ WebkitAppRegion: 'no-drag' } as any}>
      <button 
        className="win-btn minimize" 
        onClick={handleMinimize}
        title="最小化"
      >
        <svg width="12" height="12" viewBox="0 0 12 12">
          <rect x="2" y="6" width="8" height="1" fill="currentColor" />
        </svg>
      </button>
      
      <button 
        className="win-btn close" 
        onClick={handleClose}
        title="关闭"
      >
        <svg width="12" height="12" viewBox="0 0 12 12">
          <path d="M3 3l6 6m0-6L3 9" stroke="currentColor" strokeWidth="1.2" strokeLinecap="round" />
        </svg>
      </button>
    </div>
  );
};
