// src/main.tsx
import React from 'react'
import ReactDOM from 'react-dom/client'
import App from './App' // 确保这里引入了 App
import './index.css'    // 下一步我们会创建这个全局样式

ReactDOM.createRoot(document.getElementById('root')!).render(
  <React.StrictMode>
    <App />
  </React.StrictMode>,
)