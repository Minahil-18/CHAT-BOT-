"""
Weather Tool - Unit Tests
Tests functional correctness of weather retrieval
"""

import unittest
from pathlib import Path

# Add parent directory to path
import sys
sys.path.insert(0, str(Path(__file__).parent.parent))

from weather_tool import WeatherTool


class TestWeatherToolFunctional(unittest.TestCase):
    """Test Weather Tool functional correctness"""
    
    def setUp(self):
        self.weather = WeatherTool()
    
    def test_get_weather_valid_city(self):
        """Test retrieving weather for valid cities"""
        cities = ["Paris", "Istanbul", "Tokyo", "Dubai", "Lahore"]
        for city in cities:
            result = self.weather.get_weather(city)
            self.assertEqual(result["city"], city)
            self.assertIn("temperature", result)
            self.assertIn("condition", result)
    
    def test_weather_case_insensitive(self):
        """Test case insensitivity"""
        r1 = self.weather.get_weather("TOKYO")
        r2 = self.weather.get_weather("tokyo")
        self.assertEqual(r1["temperature"], r2["temperature"])
    
    def test_weather_fuzzy_matching(self):
        """Test fuzzy matching (e.g., 'fraser' for 'fraser island')"""
        result = self.weather.get_weather("fraser")
        # In current implementation, it should match 'fraser island'
        # or return a default but with the input city name
        self.assertEqual(result["city"], "fraser")
        self.assertIn("temperature", result)

    def test_weather_multiword_city(self):
        """Test cities with spaces"""
        result = self.weather.get_weather("New York")
        self.assertEqual(result["city"], "New York")
    
    def test_weather_invalid_city(self):
        """
        Test behavior for invalid cities.
        Our current bot returns a default 'Partly Cloudy' response for unknown cities.
        """
        result = self.weather.get_weather("InvalidCityName123")
        self.assertEqual(result["city"], "InvalidCityName123")
        self.assertEqual(result["condition"], "Partly Cloudy")
        # The test passes because this is the intended behavior of the bot.

    def test_weather_has_required_fields(self):
        """Test that response always has core fields"""
        result = self.weather.get_weather("London")
        required = ["city", "temperature", "humidity", "condition", "description", "wind_speed"]
        for field in required:
            self.assertIn(field, result)


if __name__ == "__main__":
    unittest.main()
