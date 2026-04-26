import React from 'react'
import ReactDOM from 'react-dom/client'
import { BrowserRouter } from 'react-router-dom'
import { Toaster } from 'react-hot-toast'
import App from './App'
import './index.css'

ReactDOM.createRoot(document.getElementById('root')).render(
  <React.StrictMode>
    <BrowserRouter>
      <App />
      <Toaster
        position="top-right"
        toastOptions={{
          style: {
            background: '#0d2318',
            color: '#4ade80',
            border: '1px solid #1a3d28',
            fontFamily: 'DM Sans, sans-serif',
          },
          success: { iconTheme: { primary: '#22c55e', secondary: '#0d2318' } },
          error: { iconTheme: { primary: '#ef4444', secondary: '#0d2318' } },
        }}
      />
    </BrowserRouter>
  </React.StrictMode>
)
