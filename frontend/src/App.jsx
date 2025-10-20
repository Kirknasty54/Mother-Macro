import React from 'react'
import { BrowserRouter as Router, Routes, Route, Navigate } from 'react-router-dom'
import Login from './components/Login'
import CaloriePreferences from './components/CaloriePreferences'
import './App.css'
import Register from "./components/Register.jsx";
import MealPlan from "./components/MealPlan.jsx";
import Generating from "./components/Generating.jsx";
import { useAuth } from './context/AuthProvider.jsx'

// Protected route wrapper - only accessible when logged in
function ProtectedRoute({ children }) {
    const { user } = useAuth()
    return user ? children : <Navigate to="/login" replace />
}

// Public route wrapper - only accessible when NOT logged in
function PublicRoute({ children }) {
    const { user } = useAuth()
    return !user ? children : <Navigate to="/preferences" replace />
}

function App() {
    return (
        <Router>
            <div className={"antialiased"}>
                <Routes>
                    {/* Redirect root based on auth status */}
                    <Route path="/" element={<Navigate to="/login" replace />} />

                    {/* Public routes - redirect to preferences if logged in */}
                    <Route path="/login" element={<PublicRoute><Login /></PublicRoute>} />
                    <Route path="/register" element={<PublicRoute><Register /></PublicRoute>} />

                    {/* Protected routes - redirect to login if not logged in */}
                    <Route path="/preferences" element={<ProtectedRoute><CaloriePreferences /></ProtectedRoute>} />
                    <Route path="/mealplan" element={<ProtectedRoute><MealPlan /></ProtectedRoute>} />
                    <Route path="/generating" element={<ProtectedRoute><Generating /></ProtectedRoute>} />
                </Routes>
            </div>
        </Router>
    )
}

export default App
