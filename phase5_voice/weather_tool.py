"""
Weather Tool - Get current weather for travel destinations
Uses mock data for demo
"""

from typing import Dict, Any, Optional

class WeatherTool:
    """Weather information for travel planning"""
    
    def __init__(self, api_key: str = "demo"):
        self.api_key = api_key
        self.base_url = "https://api.openweathermap.org/data/2.5/weather"
        self.units = "metric"  # Celsius
    
    def _find_city(self, city_name: str) -> str:
        """Find city in database with fuzzy matching"""
        city_lower = city_name.lower().strip()
        
        mock_data_keys = {
            "paris", "istanbul", "tokyo", "dubai", "bangkok", "london", "lahore",
            "islamabad", "new york", "hong kong", "sri lanka", "barcelona", 
            "singapore", "seoul", "andros", "fraser island", "rio"
        }
        
        if city_lower in mock_data_keys:
            return city_lower
        
        # Try partial match
        for city in mock_data_keys:
            city_words = city.split()
            for word in city_words:
                if word.startswith(city_lower) or city_lower in city:
                    return city
        
        # Check prefix match
        for city in mock_data_keys:
            if city_lower.startswith(city) or city.startswith(city_lower):
                return city
        
        return None
    
    def get_weather(self, city: str, country_code: str = "") -> Dict[str, Any]:
        """
        Get current weather for a city
        
        Args:
            city: City name (e.g., "Paris", "Istanbul")
            country_code: ISO 3166 country code (optional, e.g., "FR", "TR")
        
        Returns:
            Dictionary with weather info or error message
        """
        
        # Return mock data (demo mode)
        return self._get_mock_weather(city)
    
    def _parse_weather(self, data: Dict) -> Dict[str, Any]:
        """Parse OpenWeatherMap API response"""
        try:
            main = data.get("main", {})
            weather = data.get("weather", [{}])[0]
            
            return {
                "city": data.get("name"),
                "country": data.get("sys", {}).get("country"),
                "temperature": main.get("temp"),
                "feels_like": main.get("feels_like"),
                "humidity": main.get("humidity"),
                "pressure": main.get("pressure"),
                "description": weather.get("description"),
                "condition": weather.get("main"),
                "wind_speed": data.get("wind", {}).get("speed"),
                "clouds": data.get("clouds", {}).get("all"),
                "rain_chance": data.get("rain", {}).get("1h", 0),
                "visibility": data.get("visibility")
            }
        except Exception as e:
            return {"error": f"Error parsing weather data: {str(e)}"}
    
    def _get_mock_weather(self, city: str) -> Dict[str, Any]:
        """Return mock weather data for demo/testing"""
        
        mock_data = {
            "paris": {"temperature": 18, "humidity": 65, "condition": "Partly Cloudy", "description": "partly cloudy", "wind_speed": 12},
            "istanbul": {"temperature": 22, "humidity": 70, "condition": "Sunny", "description": "clear sky", "wind_speed": 8},
            "tokyo": {"temperature": 25, "humidity": 75, "condition": "Rainy", "description": "light rain", "wind_speed": 15},
            "dubai": {"temperature": 38, "humidity": 45, "condition": "Sunny", "description": "clear sky", "wind_speed": 5},
            "bangkok": {"temperature": 32, "humidity": 80, "condition": "Thunderstorm", "description": "thunderstorm with rain", "wind_speed": 20},
            "london": {"temperature": 15, "humidity": 70, "condition": "Rainy", "description": "light rain", "wind_speed": 14},
            "lahore": {"temperature": 28, "humidity": 75, "condition": "Hot & Humid", "description": "partly cloudy, hot", "wind_speed": 10},
            "islamabad": {"temperature": 26, "humidity": 65, "condition": "Sunny", "description": "clear sky", "wind_speed": 9},
            "new york": {"temperature": 20, "humidity": 60, "condition": "Cloudy", "description": "overcast clouds", "wind_speed": 10},
            "hong kong": {"temperature": 28, "humidity": 80, "condition": "Humid", "description": "humid subtropical", "wind_speed": 12},
            "sri lanka": {"temperature": 30, "humidity": 85, "condition": "Tropical", "description": "tropical rain", "wind_speed": 14},
            "barcelona": {"temperature": 21, "humidity": 68, "condition": "Sunny", "description": "clear sky", "wind_speed": 11},
            "singapore": {"temperature": 31, "humidity": 78, "condition": "Humid", "description": "humid tropical", "wind_speed": 8},
            "seoul": {"temperature": 19, "humidity": 62, "condition": "Partly Cloudy", "description": "partly cloudy", "wind_speed": 13},
            "andros": {"temperature": 27, "humidity": 72, "condition": "Sunny", "description": "clear sky", "wind_speed": 7},
            "fraser island": {"temperature": 26, "humidity": 70, "condition": "Sunny", "description": "clear sky", "wind_speed": 9},
            "rio": {"temperature": 32, "humidity": 70, "condition": "Sunny", "description": "sunny and warm", "wind_speed": 11},
        }
        
        city_lower = city.lower()
        
        # Try fuzzy matching
        actual_city = self._find_city(city_lower)
        
        if actual_city is not None:
            return {
                "city": city,
                "country": "Demo",
                **mock_data[actual_city],
                "feels_like": mock_data[actual_city]["temperature"] - 1,
                "pressure": 1013,
                "clouds": 30,
                "rain_chance": 10,
                "visibility": 10000
            }
        
        return {
            "city": city,
            "country": "Demo",
            "temperature": 20,
            "humidity": 65,
            "condition": "Partly Cloudy",
            "description": "partly cloudy",
            "wind_speed": 10,
            "feels_like": 19,
            "pressure": 1013,
            "clouds": 40,
            "rain_chance": 0,
            "visibility": 10000
        }


# Tool definition for LLM
WEATHER_TOOLS = [
    {
        "name": "get_weather",
        "description": "Get current weather information for a travel destination. Useful for trip planning and packing advice.",
        "input_schema": {
            "type": "object",
            "properties": {
                "city": {
                    "type": "string",
                    "description": "City name (e.g., 'Paris', 'Istanbul', 'Tokyo')"
                },
                "country_code": {
                    "type": "string",
                    "description": "Optional ISO country code (e.g., 'FR', 'TR')"
                }
            },
            "required": ["city"]
        }
    }
]
