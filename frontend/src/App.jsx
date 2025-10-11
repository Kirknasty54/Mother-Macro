import React from 'react'
import { BrowserRouter as Router, Routes, Route, Navigate } from 'react-router-dom'
import Login from './components/Login'
import CaloriePreferences from './components/CaloriePreferences'
import './App.css'

function App() {
  return (
    <Router>
      <div className="App">
        <Routes>
          {/* Redirect root path to login */}
          <Route path="/" element={<Navigate to="/login" replace />} />
          
          {/* Login page */}
          <Route path="/login" element={<Login />} />
          
          {/* Calorie preferences page */}
          <Route path="/preferences" element={<CaloriePreferences />} />
        </Routes>
      </div>
    </Router>
  )
}

export default App
