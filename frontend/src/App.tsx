import React, { Suspense, lazy } from 'react'
import { BrowserRouter as Router, Routes, Route } from 'react-router-dom'
import './styles/App.css'

// Lazy load components for better performance
const FuturisticAvatarDashboard = lazy(() => import('./components/Avatar/FuturisticAvatarDashboard'))
const ModernApp = lazy(() => import('./components/ModernApp'))

// Loading component
const LoadingFallback: React.FC = () => (
  <div className="flex items-center justify-center min-h-screen bg-gradient-to-br from-purple-900 via-black to-blue-900">
    <div className="animate-spin rounded-full h-16 w-16 border-t-2 border-b-2 border-purple-500"></div>
  </div>
)

function App() {
  return (
    <Router>
      <div className="App">
        <Suspense fallback={<LoadingFallback />}>
          <Routes>
            <Route path="/" element={<ModernApp />} />
            <Route path="/avatar/:userId" element={<FuturisticAvatarDashboard />} />
            <Route path="/dashboard" element={<ModernApp />} />
          </Routes>
        </Suspense>
      </div>
    </Router>
  )
}

export default App
