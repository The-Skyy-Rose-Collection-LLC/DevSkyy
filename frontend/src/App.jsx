import React from 'react'
import ModernApp from './components/ModernApp'
import ErrorBoundary from './components/ErrorBoundary'
import './index.css'

function App() {
  return (
    <ErrorBoundary>
      <ModernApp />
    </ErrorBoundary>
  )
}

export default App