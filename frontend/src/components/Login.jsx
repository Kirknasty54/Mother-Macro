import React, { useState } from 'react';
import { useNavigate } from 'react-router-dom';

const Login = () => {
  const [formData, setFormData] = useState({
    username: '',
    password: ''
  });
  const navigate = useNavigate();

  const handleChange = (e) => {
    setFormData({
      ...formData,
      [e.target.name]: e.target.value
    });
  };

  const handleSubmit = (e) => {
    e.preventDefault();
    // Simple validation - in a real app, you'd authenticate with a backend
    if (formData.username && formData.password) {
      // Navigate to calorie preferences page
      navigate('/preferences');
    } else {
      alert('Please fill in both username and password');
    }
  };

  return (
    <div className="min-h-screen bg-gradient-to-br from-beige-50 to-sage-100 flex items-center justify-center px-4">
      <div className="max-w-md w-full space-y-8">
        {/* Header */}
        <div className="text-center">
          <h2 className="mt-6 text-4xl font-bold text-sage-800">
            HealthEats
          </h2>
          <p className="mt-2 text-lg text-sage-600">
            Your journey to healthy eating starts here
          </p>
        </div>

        {/* Login Form */}
        <form className="mt-8 space-y-6" onSubmit={handleSubmit}>
          <div className="bg-white rounded-lg shadow-lg p-8 space-y-6">
            <div>
              <label htmlFor="username" className="block text-sm font-medium text-sage-700 mb-2">
                Username
              </label>
              <input
                id="username"
                name="username"
                type="text"
                required
                value={formData.username}
                onChange={handleChange}
                className="w-full px-4 py-3 border border-sage-200 rounded-lg focus:ring-2 focus:ring-sage-500 focus:border-sage-500 transition-colors"
                placeholder="Enter your username"
              />
            </div>

            <div>
              <label htmlFor="password" className="block text-sm font-medium text-sage-700 mb-2">
                Password
              </label>
              <input
                id="password"
                name="password"
                type="password"
                required
                value={formData.password}
                onChange={handleChange}
                className="w-full px-4 py-3 border border-sage-200 rounded-lg focus:ring-2 focus:ring-sage-500 focus:border-sage-500 transition-colors"
                placeholder="Enter your password"
              />
            </div>

            <button
              type="submit"
              className="w-full bg-sage-600 hover:bg-sage-700 text-white font-medium py-3 px-4 rounded-lg transition-colors focus:ring-2 focus:ring-sage-500 focus:ring-offset-2"
            >
              Sign In
            </button>
          </div>
        </form>

        {/* Footer */}
        <div className="text-center">
          <p className="text-sm text-sage-500">
            Don't have an account?{' '}
            <a href="#" className="font-medium text-sage-600 hover:text-sage-500 transition-colors">
              Sign up here
            </a>
          </p>
        </div>
      </div>
    </div>
  );
};

export default Login;