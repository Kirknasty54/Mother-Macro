import React, { useState } from 'react';

const CaloriePreferences = () => {
  const [preferences, setPreferences] = useState({
    dailyCalorieGoal: '',
    activityLevel: 'moderate',
    dietType: 'balanced',
    allergens: [],
    healthGoals: []
  });

  const activityLevels = [
    { value: 'sedentary', label: 'Sedentary (little to no exercise)' },
    { value: 'light', label: 'Light (light exercise 1-3 days/week)' },
    { value: 'moderate', label: 'Moderate (moderate exercise 3-5 days/week)' },
    { value: 'active', label: 'Active (hard exercise 6-7 days/week)' },
    { value: 'very-active', label: 'Very Active (very hard exercise, physical job)' }
  ];

  const dietTypes = [
    { value: 'balanced', label: 'Balanced Diet' },
    { value: 'low-carb', label: 'Low Carb' },
    { value: 'vegetarian', label: 'Vegetarian' },
    { value: 'vegan', label: 'Vegan' },
    { value: 'keto', label: 'Ketogenic' },
    { value: 'mediterranean', label: 'Mediterranean' }
  ];

  const commonAllergens = [
    'Nuts', 'Dairy', 'Gluten', 'Eggs', 'Soy', 'Shellfish', 'Fish'
  ];

  const healthGoalOptions = [
    'Weight Loss', 'Weight Gain', 'Muscle Building', 'Heart Health', 
    'Diabetes Management', 'General Wellness'
  ];

  const handleChange = (e) => {
    const { name, value } = e.target;
    setPreferences(prev => ({
      ...prev,
      [name]: value
    }));
  };

  const handleCheckboxChange = (category, value) => {
    setPreferences(prev => ({
      ...prev,
      [category]: prev[category].includes(value)
        ? prev[category].filter(item => item !== value)
        : [...prev[category], value]
    }));
  };

  const handleSubmit = (e) => {
    e.preventDefault();
    console.log('Preferences saved:', preferences);
    alert('Preferences saved successfully!');
  };

  return (
    <div className="min-h-screen bg-gradient-to-br from-beige-50 to-sage-100 py-8">
      <div className="max-w-4xl mx-auto px-4">
        {/* Header */}
        <div className="text-center mb-8">
          <h1 className="text-4xl font-bold text-sage-800 mb-2">
            Set Your Health Preferences
          </h1>
          <p className="text-lg text-sage-600">
            Tell us about your goals so we can personalize your nutrition journey
          </p>
        </div>

        {/* Main Form */}
        <form onSubmit={handleSubmit} className="bg-white rounded-lg shadow-lg p-8 space-y-8">
          {/* Daily Calorie Goal */}
          <div>
            <label className="block text-lg font-semibold text-sage-700 mb-3">
              Daily Calorie Goal
            </label>
            <input
              type="number"
              name="dailyCalorieGoal"
              value={preferences.dailyCalorieGoal}
              onChange={handleChange}
              className="w-full px-4 py-3 border border-sage-200 rounded-lg focus:ring-2 focus:ring-sage-500 focus:border-sage-500 transition-colors"
              placeholder="e.g., 2000"
              required
            />
            <p className="text-sm text-sage-500 mt-2">
              Enter your target daily calories (typically 1,500-3,000)
            </p>
          </div>

          {/* Activity Level */}
          <div>
            <label className="block text-lg font-semibold text-sage-700 mb-3">
              Activity Level
            </label>
            <div className="space-y-3">
              {activityLevels.map((level) => (
                <label key={level.value} className="flex items-center">
                  <input
                    type="radio"
                    name="activityLevel"
                    value={level.value}
                    checked={preferences.activityLevel === level.value}
                    onChange={handleChange}
                    className="mr-3 h-4 w-4 text-sage-600 focus:ring-sage-500 border-sage-300"
                  />
                  <span className="text-sage-700">{level.label}</span>
                </label>
              ))}
            </div>
          </div>

          {/* Diet Type */}
          <div>
            <label className="block text-lg font-semibold text-sage-700 mb-3">
              Preferred Diet Type
            </label>
            <select
              name="dietType"
              value={preferences.dietType}
              onChange={handleChange}
              className="w-full px-4 py-3 border border-sage-200 rounded-lg focus:ring-2 focus:ring-sage-500 focus:border-sage-500 transition-colors"
            >
              {dietTypes.map((diet) => (
                <option key={diet.value} value={diet.value}>
                  {diet.label}
                </option>
              ))}
            </select>
          </div>

          {/* Allergens */}
          <div>
            <label className="block text-lg font-semibold text-sage-700 mb-3">
              Food Allergies & Restrictions
            </label>
            <div className="grid grid-cols-2 md:grid-cols-3 gap-3">
              {commonAllergens.map((allergen) => (
                <label key={allergen} className="flex items-center">
                  <input
                    type="checkbox"
                    checked={preferences.allergens.includes(allergen)}
                    onChange={() => handleCheckboxChange('allergens', allergen)}
                    className="mr-2 h-4 w-4 text-sage-600 focus:ring-sage-500 border-sage-300 rounded"
                  />
                  <span className="text-sage-700">{allergen}</span>
                </label>
              ))}
            </div>
          </div>

          {/* Health Goals */}
          <div>
            <label className="block text-lg font-semibold text-sage-700 mb-3">
              Health Goals
            </label>
            <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
              {healthGoalOptions.map((goal) => (
                <label key={goal} className="flex items-center">
                  <input
                    type="checkbox"
                    checked={preferences.healthGoals.includes(goal)}
                    onChange={() => handleCheckboxChange('healthGoals', goal)}
                    className="mr-2 h-4 w-4 text-sage-600 focus:ring-sage-500 border-sage-300 rounded"
                  />
                  <span className="text-sage-700">{goal}</span>
                </label>
              ))}
            </div>
          </div>

          {/* Submit Button */}
          <div className="pt-6">
            <button
              type="submit"
              className="w-full bg-sage-600 hover:bg-sage-700 text-white font-medium py-4 px-6 rounded-lg transition-colors focus:ring-2 focus:ring-sage-500 focus:ring-offset-2 text-lg"
            >
              Save My Preferences
            </button>
          </div>
        </form>

        {/* Additional Info */}
        <div className="mt-8 text-center">
          <p className="text-sm text-sage-500">
            You can update these preferences anytime in your profile settings
          </p>
        </div>
      </div>
    </div>
  );
};

export default CaloriePreferences;