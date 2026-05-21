import { Component, ErrorInfo, ReactNode } from 'react'

interface Props {
  children: ReactNode
}

interface State {
  hasError: boolean
  error: Error | null
  errorInfo: ErrorInfo | null
}

export class ErrorBoundary extends Component<Props, State> {
  constructor(props: Props) {
    super(props)
    this.state = { hasError: false, error: null, errorInfo: null }
  }

  static getDerivedStateFromError(error: Error): Partial<State> {
    return { hasError: true, error }
  }

  componentDidCatch(error: Error, errorInfo: ErrorInfo) {
    this.setState({ errorInfo })
    console.error('ErrorBoundary caught:', error, errorInfo)
  }

  render() {
    if (this.state.hasError) {
      return (
        <div style={{ padding: '2rem', fontFamily: 'monospace', background: '#1e293b', color: '#f8fafc', minHeight: '100vh' }}>
          <h1 style={{ color: '#f87171', fontSize: '1.5rem', marginBottom: '1rem' }}>Something went wrong</h1>
          <pre style={{ background: '#0f172a', padding: '1rem', borderRadius: '0.5rem', overflow: 'auto', fontSize: '0.85rem', whiteSpace: 'pre-wrap' }}>
            {this.state.error?.message}
            {'\n\n'}
            {this.state.error?.stack}
          </pre>
          <details style={{ marginTop: '1rem' }}>
            <summary style={{ cursor: 'pointer', color: '#94a3b8' }}>Component Stack</summary>
            <pre style={{ background: '#0f172a', padding: '1rem', borderRadius: '0.5rem', overflow: 'auto', fontSize: '0.75rem', marginTop: '0.5rem', whiteSpace: 'pre-wrap' }}>
              {this.state.errorInfo?.componentStack}
            </pre>
          </details>
          <button 
            onClick={() => { this.setState({ hasError: false, error: null, errorInfo: null }); window.location.href = '/login' }}
            style={{ marginTop: '1rem', padding: '0.5rem 1rem', background: '#3b82f6', color: 'white', border: 'none', borderRadius: '0.5rem', cursor: 'pointer' }}
          >
            Go to Login
          </button>
        </div>
      )
    }

    return this.props.children
  }
}
