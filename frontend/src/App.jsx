import React from 'react'
import { BrowserRouter as Router, Routes, Route, Navigate } from 'react-router-dom'
import Login from './components/Login'
import CaloriePreferences from './components/CaloriePreferences'
import './App.css'
import Register from "./components/Register.jsx";
import MealPlan from "./components/MealPlan.jsx"; // ⬅️ add

function App() {
    return (
        <Router>
            <div className="App">
                <Routes>
                    {/* Redirect root path to login */}
                    <Route path="/" element={<Navigate to="/login" replace />} />

                    {/* Login / Register */}
                    <Route path="/login" element={<Login />} />
                    <Route path="/register" element={<Register />} />

                    {/* Preferences */}
                    <Route path="/preferences" element={<CaloriePreferences />} />

                    {/* Meal plan */}
                    <Route path="/mealplan" element={<MealPlan />} />
                </Routes>
            </div>
        </Router>
    )
}

export default App
