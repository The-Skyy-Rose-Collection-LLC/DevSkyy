'use client'

import { Component, type ErrorInfo, type ReactNode } from 'react'

interface Props {
  children: ReactNode
  fallbackTitle?: string
}

interface State {
  hasError: boolean
  error: Error | null
}

export class WPErrorBoundary extends Component<Props, State> {
  constructor(props: Props) {
    super(props)
    this.state = { hasError: false, error: null }
  }

  static getDerivedStateFromError(error: Error): State {
    return { hasError: true, error }
  }

  componentDidCatch(error: Error, info: ErrorInfo) {
    console.error('[WPErrorBoundary]', error, info.componentStack)
  }

  private handleRetry = () => {
    this.setState({ hasError: false, error: null })
  }

  render() {
    if (!this.state.hasError) return this.props.children

    return (
      <div className="flex flex-col items-center justify-center min-h-[300px] rounded-lg border border-gray-800 bg-gray-900/50 p-8 text-center">
        <div className="mb-4 rounded-full bg-rose-500/10 p-3">
          <svg className="h-8 w-8 text-rose-500" fill="none" viewBox="0 0 24 24" stroke="currentColor">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 9v2m0 4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
          </svg>
        </div>
        <h3 className="text-lg font-semibold text-white mb-1">
          {this.props.fallbackTitle ?? 'Something went wrong'}
        </h3>
        <p className="text-sm text-gray-400 mb-4">
          The WordPress panel encountered an error.
        </p>
        {process.env.NODE_ENV === 'development' && this.state.error && (
          <pre className="mb-4 max-w-md overflow-auto rounded bg-gray-800 p-3 text-left text-xs text-red-400">
            {this.state.error.message}
          </pre>
        )}
        <button
          onClick={this.handleRetry}
          className="rounded-md bg-rose-500 px-4 py-2 text-sm font-medium text-white hover:bg-rose-600 transition-colors"
        >
          Try Again
        </button>
      </div>
    )
  }
}
