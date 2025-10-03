import React from 'react';
import { BrowserRouter as Router, Routes, Route } from 'react-router-dom';
import FuturisticAvatarDashboard from './components/Avatar/FuturisticAvatarDashboard';
import './styles/App.css';

function App() {
  return (
    <Router>
      <div className="App">
        <Routes>
          <Route path="/" element={<FuturisticAvatarDashboard userId="user123" />} />
          <Route path="/avatar" element={<FuturisticAvatarDashboard userId="user123" />} />
        </Routes>
      </div>
    </Router>
  );
}

export default App;
