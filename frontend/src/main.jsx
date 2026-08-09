import React, { StrictMode, Component } from 'react'
import { createRoot } from 'react-dom/client'
import './index.css'
import App from './App.jsx'

class ErrorBoundary extends Component {
  constructor(props) {
    super(props);
    this.state = { hasError: false, error: null };
  }

  static getDerivedStateFromError(error) {
    return { hasError: true, error };
  }

  componentDidCatch(error, errorInfo) {
    console.error("JARVIS React Error Boundary caught error:", error, errorInfo);
  }

  render() {
    if (this.state.hasError) {
      return (
        <div style={{ padding: 24, color: '#f87171', background: '#09090b', fontFamily: 'monospace', fontSize: 13, minHeight: '100vh' }}>
          <h2 style={{ fontSize: 16, color: '#fca5a5' }}>⚠️ JARVIS UI Render Error</h2>
          <p style={{ marginTop: 8, color: '#e4e4e7' }}>{this.state.error && this.state.error.toString()}</p>
          <pre style={{ background: '#18181b', padding: 12, borderRadius: 8, marginTop: 12, overflowX: 'auto', fontSize: 11, color: '#a1a1aa' }}>
            {this.state.error && this.state.error.stack}
          </pre>
          <button
            onClick={() => {
              localStorage.clear();
              window.location.reload();
            }}
            style={{ padding: '8px 16px', marginTop: 16, cursor: 'pointer', background: '#27272a', border: '1px solid #3f3f46', color: '#f4f4f5', borderRadius: 6 }}
          >
            Reset LocalStorage & Reload HUD
          </button>
        </div>
      );
    }
    return this.props.children;
  }
}

createRoot(document.getElementById('root')).render(
  <StrictMode>
    <ErrorBoundary>
      <App />
    </ErrorBoundary>
  </StrictMode>,
)
