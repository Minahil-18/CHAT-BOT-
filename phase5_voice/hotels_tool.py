"""
Hotel Finder Tool
Search for available hotels with prices and ratings
"""

from typing import Dict, Any, List
from datetime import datetime, timedelta

class HotelFinderTool:
    """Hotel search tool"""
    
    # Mock hotel database
    HOTELS_DB = {
        "paris": [
            {"name": "Le Marais Boutique", "rating": 4.8, "price_per_night": 180, "rooms": 45, "amenities": ["WiFi", "Restaurant", "Bar", "Gym"]},
            {"name": "Eiffel Tower View", "rating": 4.5, "price_per_night": 220, "rooms": 38, "amenities": ["WiFi", "Restaurant", "Parking", "Spa"]},
            {"name": "Budget Paris", "rating": 4.0, "price_per_night": 65, "rooms": 120, "amenities": ["WiFi", "Breakfast", "Reception 24h"]},
            {"name": "Luxury Palace", "rating": 5.0, "price_per_night": 450, "rooms": 20, "amenities": ["WiFi", "Restaurant", "Spa", "Concierge", "Pool"]},
        ],
        "istanbul": [
            {"name": "Golden Horn View", "rating": 4.7, "price_per_night": 95, "rooms": 60, "amenities": ["WiFi", "Restaurant", "Rooftop"]},
            {"name": "Sultanahmet Classic", "rating": 4.4, "price_per_night": 75, "rooms": 80, "amenities": ["WiFi", "Breakfast", "Garden"]},
            {"name": "Budget Istanbul", "rating": 3.9, "price_per_night": 30, "rooms": 150, "amenities": ["WiFi", "Lounge", "Reception"]},
            {"name": "Bosphorus Luxury", "rating": 4.9, "price_per_night": 280, "rooms": 35, "amenities": ["WiFi", "Restaurant", "Spa", "Terrace"]},
        ],
        "tokyo": [
            {"name": "Shibuya Modern", "rating": 4.6, "price_per_night": 120, "rooms": 70, "amenities": ["WiFi", "Restaurant", "Gym", "Spa"]},
            {"name": "Asakusa Traditional", "rating": 4.3, "price_per_night": 85, "rooms": 50, "amenities": ["WiFi", "Breakfast", "Garden"]},
            {"name": "Budget Tokyo", "rating": 3.8, "price_per_night": 40, "rooms": 100, "amenities": ["WiFi", "Shared Kitchen"]},
            {"name": "Imperial Tokyo", "rating": 5.0, "price_per_night": 350, "rooms": 25, "amenities": ["WiFi", "Restaurant", "Spa", "Concierge"]},
        ],
        "dubai": [
            {"name": "Marina Tower", "rating": 4.7, "price_per_night": 150, "rooms": 90, "amenities": ["WiFi", "Pool", "Restaurant", "Gym"]},
            {"name": "Downtown Dubai", "rating": 4.5, "price_per_night": 130, "rooms": 75, "amenities": ["WiFi", "Pool", "Gym"]},
            {"name": "Budget Dubai", "rating": 3.9, "price_per_night": 50, "rooms": 120, "amenities": ["WiFi", "Breakfast"]},
            {"name": "Burj Khalifa Luxury", "rating": 4.9, "price_per_night": 320, "rooms": 40, "amenities": ["WiFi", "Pool", "Spa", "Fine Dining"]},
        ],
        "bangkok": [
            {"name": "Sukhumvit Plaza", "rating": 4.5, "price_per_night": 60, "rooms": 100, "amenities": ["WiFi", "Restaurant", "Pool"]},
            {"name": "Old City Charm", "rating": 4.3, "price_per_night": 45, "rooms": 80, "amenities": ["WiFi", "Breakfast", "Rooftop"]},
            {"name": "Budget Bangkok", "rating": 3.8, "price_per_night": 20, "rooms": 200, "amenities": ["WiFi", "Air Con"]},
            {"name": "Riverside Luxury", "rating": 4.8, "price_per_night": 250, "rooms": 50, "amenities": ["WiFi", "Pool", "Spa", "Restaurant"]},
        ],
        "london": [
            {"name": "West End Hotel", "rating": 4.6, "price_per_night": 140, "rooms": 85, "amenities": ["WiFi", "Restaurant", "Bar"]},
            {"name": "South Kensington", "rating": 4.4, "price_per_night": 120, "rooms": 60, "amenities": ["WiFi", "Gym", "Breakfast"]},
            {"name": "Budget London", "rating": 3.9, "price_per_night": 55, "rooms": 110, "amenities": ["WiFi", "Reception"]},
            {"name": "Five Star Mayfair", "rating": 5.0, "price_per_night": 400, "rooms": 30, "amenities": ["WiFi", "Spa", "Fine Dining", "Concierge"]},
        ],
        "lahore": [
            {"name": "Pearl Continental", "rating": 4.7, "price_per_night": 110, "rooms": 80, "amenities": ["WiFi", "Restaurant", "Pool", "Gym"]},
            {"name": "Serena Hotel", "rating": 4.6, "price_per_night": 95, "rooms": 70, "amenities": ["WiFi", "Restaurant", "Spa", "Terrace"]},
            {"name": "Budget Lahore", "rating": 3.9, "price_per_night": 35, "rooms": 120, "amenities": ["WiFi", "Breakfast"]},
            {"name": "Avari Lahore Luxury", "rating": 4.9, "price_per_night": 280, "rooms": 45, "amenities": ["WiFi", "Pool", "Spa", "Restaurant", "Concierge"]},
        ],
        "islamabad": [
            {"name": "Margalla View Hotel", "rating": 4.7, "price_per_night": 105, "rooms": 75, "amenities": ["WiFi", "Restaurant", "Garden", "Gym"]},
            {"name": "Pearl Continent", "rating": 4.5, "price_per_night": 98, "rooms": 65, "amenities": ["WiFi", "Pool", "Spa", "Restaurant"]},
            {"name": "Budget Islamabad", "rating": 3.8, "price_per_night": 40, "rooms": 100, "amenities": ["WiFi", "Breakfast"]},
            {"name": "Serena Islamabad", "rating": 4.8, "price_per_night": 270, "rooms": 50, "amenities": ["WiFi", "Pool", "Spa", "Fine Dining"]},
        ],
        "hong kong": [
            {"name": "Star City Hotel", "rating": 4.6, "price_per_night": 180, "rooms": 90, "amenities": ["WiFi", "Pool", "Restaurant", "Gym"]},
            {"name": "Victoria Peak View", "rating": 4.5, "price_per_night": 160, "rooms": 70, "amenities": ["WiFi", "Restaurant", "Bar"]},
            {"name": "Budget HK", "rating": 3.9, "price_per_night": 65, "rooms": 130, "amenities": ["WiFi", "Hostel"]},
            {"name": "Mandarin Oriental", "rating": 5.0, "price_per_night": 450, "rooms": 35, "amenities": ["WiFi", "Pool", "Spa", "Fine Dining"]},
        ],
        "sri lanka": [
            {"name": "Coral House", "rating": 4.6, "price_per_night": 95, "rooms": 60, "amenities": ["WiFi", "Beach Access", "Restaurant"]},
            {"name": "Colombo Elegant", "rating": 4.4, "price_per_night": 85, "rooms": 50, "amenities": ["WiFi", "Gym", "Pool"]},
            {"name": "Budget Sri Lanka", "rating": 3.8, "price_per_night": 30, "rooms": 100, "amenities": ["WiFi", "Breakfast"]},
            {"name": "Galle Luxury Fort", "rating": 4.9, "price_per_night": 320, "rooms": 40, "amenities": ["WiFi", "Pool", "Spa", "Historic"]},
        ],
        "barcelona": [
            {"name": "Sagrada Familia View", "rating": 4.6, "price_per_night": 150, "rooms": 80, "amenities": ["WiFi", "Restaurant", "Terrace"]},
            {"name": "Gothic Quarter", "rating": 4.4, "price_per_night": 130, "rooms": 65, "amenities": ["WiFi", "Gym", "Historic"]},
            {"name": "Budget Barcelona", "rating": 3.9, "price_per_night": 50, "rooms": 120, "amenities": ["WiFi", "Reception"]},
            {"name": "Park Hotel Luxury", "rating": 5.0, "price_per_night": 380, "rooms": 30, "amenities": ["WiFi", "Spa", "Fine Dining"]},
        ],
        "singapore": [
            {"name": "Marina Bay Grand", "rating": 4.7, "price_per_night": 200, "rooms": 100, "amenities": ["WiFi", "Pool", "Restaurant", "Gym"]},
            {"name": "Orchard Road Boutique", "rating": 4.5, "price_per_night": 170, "rooms": 75, "amenities": ["WiFi", "Spa", "Lounge"]},
            {"name": "Budget Singapore", "rating": 3.8, "price_per_night": 60, "rooms": 140, "amenities": ["WiFi", "Breakfast"]},
            {"name": "Raffles Singapore", "rating": 5.0, "price_per_night": 500, "rooms": 40, "amenities": ["WiFi", "Pool", "Spa", "Heritage"]},
        ],
        "seoul": [
            {"name": "Myeongdong Plaza", "rating": 4.6, "price_per_night": 130, "rooms": 85, "amenities": ["WiFi", "Restaurant", "Shopping"]},
            {"name": "Hanbok House", "rating": 4.4, "price_per_night": 110, "rooms": 60, "amenities": ["WiFi", "Traditional", "Tea House"]},
            {"name": "Budget Seoul", "rating": 3.9, "price_per_night": 45, "rooms": 110, "amenities": ["WiFi", "Breakfast"]},
            {"name": "Gangnam Luxury", "rating": 5.0, "price_per_night": 360, "rooms": 45, "amenities": ["WiFi", "Spa", "Fine Dining"]},
        ],
        "andros": [
            {"name": "Island Breeze", "rating": 4.7, "price_per_night": 120, "rooms": 50, "amenities": ["Beach", "Restaurant", "WiFi"]},
            {"name": "Cycladic View", "rating": 4.5, "price_per_night": 100, "rooms": 40, "amenities": ["WiFi", "Pool", "Terrace"]},
            {"name": "Budget Andros", "rating": 3.8, "price_per_night": 45, "rooms": 70, "amenities": ["WiFi", "Basic"]},
            {"name": "Andros Luxury Resort", "rating": 4.9, "price_per_night": 280, "rooms": 30, "amenities": ["Beach", "Pool", "Spa", "Restaurant"]},
        ],
        "fraser island": [
            {"name": "Kingfisher Bay Resort", "rating": 4.7, "price_per_night": 200, "rooms": 100, "amenities": ["Beach", "Restaurant", "WiFi", "Eco-resort"]},
            {"name": "Eurong Beach Resort", "rating": 4.5, "price_per_night": 180, "rooms": 80, "amenities": ["Beach", "Pool", "Restaurant"]},
            {"name": "Budget Fraser", "rating": 3.8, "price_per_night": 60, "rooms": 120, "amenities": ["WiFi", "Basic"]},
            {"name": "Sanctuary Resort Luxury", "rating": 4.9, "price_per_night": 350, "rooms": 40, "amenities": ["Beach", "Pool", "Spa", "Fine Dining"]},
        ],
        "rio": [
            {"name": "Copacabana Palace", "rating": 4.8, "price_per_night": 220, "rooms": 95, "amenities": ["Beach", "Restaurant", "Pool", "Bar"]},
            {"name": "Ipanema Boutique", "rating": 4.5, "price_per_night": 180, "rooms": 70, "amenities": ["WiFi", "Restaurant", "Beach"]},
            {"name": "Budget Rio", "rating": 3.8, "price_per_night": 55, "rooms": 130, "amenities": ["WiFi", "Breakfast"]},
            {"name": "Christ Redeemer Luxury", "rating": 4.9, "price_per_night": 400, "rooms": 35, "amenities": ["Mountain View", "Spa", "Fine Dining"]},
        ],
    }
    
    
    def _find_city(self, city_name: str) -> str:
        """Find city in database with fuzzy matching"""
        city_lower = city_name.lower().strip()
        
        if city_lower in self.HOTELS_DB:
            return city_lower
        
        # Try partial match
        for city in self.HOTELS_DB.keys():
            city_words = city.split()
            for word in city_words:
                if word.startswith(city_lower) or city_lower in city:
                    return city
        
        # Check prefix match
        for city in self.HOTELS_DB.keys():
            if city_lower.startswith(city) or city.startswith(city_lower):
                return city
        
        return None
    
    def search_hotels(self, city: str, check_in: str = None, check_out: str = None, 
                     guests: int = 1, price_range: str = "luxury") -> Dict[str, Any]:
        """
        Search for hotels
        
        Args:
            city: Hotel destination city
            check_in: Check-in date (YYYY-MM-DD) - optional, defaults to today+1
            check_out: Check-out date (YYYY-MM-DD) - optional, defaults to check_in+3
            guests: Number of guests
            price_range: "budget", "moderate", or "luxury"
        
        Returns:
            Dictionary with hotel options or error
        """
        
        city_lower = city.lower()
        
        # If dates not provided, use defaults
        if check_in is None:
            check_in = (datetime.now() + timedelta(days=1)).strftime("%Y-%m-%d")
        if check_out is None:
            check_out = (datetime.now() + timedelta(days=4)).strftime("%Y-%m-%d")
        
        # Validate dates
        try:
            checkin = datetime.strptime(check_in, "%Y-%m-%d")
            checkout = datetime.strptime(check_out, "%Y-%m-%d")
            
            if checkin < datetime.now():
                return {"error": "Check-in date must be in the future"}
            if checkout <= checkin:
                return {"error": "Check-out date must be after check-in"}
        except ValueError:
            return {"error": "Date format must be YYYY-MM-DD"}
        
        # Find city with fuzzy matching
        actual_city = self._find_city(city_lower)
        
        # Check if city has hotels
        if actual_city is None:
            return {
                "error": f"No hotels found in '{city}'",
                "available_cities": list(self.HOTELS_DB.keys())
            }
        
        if guests < 1 or guests > 10:
            return {"error": "Guests must be between 1 and 10"}
        
        nights = (checkout - checkin).days
        if nights < 1:
            return {"error": "Must stay at least 1 night"}
        
        hotels = self.HOTELS_DB[actual_city]
        
        # Filter by price range
        price_filters = {
            "budget": lambda h: h["price_per_night"] < 70,
            "moderate": lambda h: 70 <= h["price_per_night"] < 200,
            "luxury": lambda h: h["price_per_night"] >= 200
        }
        
        if price_range not in price_filters:
            return {"error": f"Price range must be one of: {list(price_filters.keys())}"}
        
        filter_func = price_filters[price_range]
        filtered_hotels = [h for h in hotels if filter_func(h)]
        
        # Calculate prices and availability
        processed_hotels = []
        for hotel in filtered_hotels:
            if hotel["rooms"] > 0:
                total_price = hotel["price_per_night"] * nights
                processed_hotels.append({
                    "name": hotel["name"],
                    "rating": hotel["rating"],
                    "price_per_night": hotel["price_per_night"],
                    "total_stay_price": total_price,
                    "price_per_guest": total_price / guests,
                    "available_rooms": hotel["rooms"],
                    "amenities": hotel["amenities"]
                })
        
        # Sort by rating
        processed_hotels.sort(key=lambda x: x["rating"], reverse=True)
        
        return {
            "city": city,
            "check_in": check_in,
            "check_out": check_out,
            "nights": nights,
            "guests": guests,
            "price_range": price_range,
            "hotels": processed_hotels,
            "total_options": len(processed_hotels),
            "currency": "USD"
        }


# Tool definition for LLM
HOTEL_TOOLS = [
    {
        "name": "search_hotels",
        "description": "Search for available hotels with prices, ratings, and amenities. Dates are optional - defaults to next 3 days.",
        "input_schema": {
            "type": "object",
            "properties": {
                "city": {
                    "type": "string",
                    "description": "Hotel destination city"
                },
                "check_in": {
                    "type": "string",
                    "description": "Check-in date in YYYY-MM-DD format (optional, defaults to tomorrow)"
                },
                "check_out": {
                    "type": "string",
                    "description": "Check-out date in YYYY-MM-DD format (optional, defaults to check_in+3 days)"
                },
                "guests": {
                    "type": "integer",
                    "description": "Number of guests (default: 1)"
                },
                "price_range": {
                    "type": "string",
                    "enum": ["budget", "moderate", "luxury"],
                    "description": "Price range preference (default: luxury)"
                }
            },
            "required": ["city"]
        }
    }
]
