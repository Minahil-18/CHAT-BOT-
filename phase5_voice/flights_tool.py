"""
Flight Booking Tool
Search for flight options and prices
"""

from typing import Dict, Any, List
from datetime import datetime

class FlightBookingTool:
    """Flight search and booking tool"""
    
    # Mock flight database with realistic prices
    FLIGHTS_DB = {
        "paris": [
            {"airline": "Air France", "price": 580, "duration": "2h 30m", "departure": "10:00", "arrival": "12:30"},
            {"airline": "Ryanair", "price": 120, "duration": "3h 15m", "departure": "14:30", "arrival": "17:45"},
            {"airline": "Lufthansa", "price": 450, "duration": "2h 20m", "departure": "08:00", "arrival": "10:20"},
        ],
        "istanbul": [
            {"airline": "Turkish Airlines", "price": 480, "duration": "2h 45m", "departure": "11:00", "arrival": "14:45"},
            {"airline": "Pegasus", "price": 140, "duration": "3h 30m", "departure": "15:00", "arrival": "18:30"},
            {"airline": "Lufthansa", "price": 420, "duration": "2h 50m", "departure": "09:30", "arrival": "13:20"},
        ],
        "tokyo": [
            {"airline": "ANA", "price": 980, "duration": "13h 30m", "departure": "20:00", "arrival": "14:30+1"},
            {"airline": "Japan Airlines", "price": 1050, "duration": "13h 15m", "departure": "22:00", "arrival": "16:15+1"},
            {"airline": "Cathay Pacific", "price": 850, "duration": "14h 20m", "departure": "14:00", "arrival": "11:20+1"},
        ],
        "dubai": [
            {"airline": "Emirates", "price": 650, "duration": "6h 30m", "departure": "10:00", "arrival": "16:30"},
            {"airline": "Flydubai", "price": 380, "duration": "7h 15m", "departure": "08:00", "arrival": "15:15"},
            {"airline": "Air Arabia", "price": 250, "duration": "7h 45m", "departure": "12:00", "arrival": "19:45"},
        ],
        "bangkok": [
            {"airline": "Thai Airways", "price": 780, "duration": "10h 30m", "departure": "19:00", "arrival": "06:30+1"},
            {"airline": "AirAsia", "price": 350, "duration": "12h 15m", "departure": "23:00", "arrival": "12:15+1"},
            {"airline": "Emirates", "price": 680, "duration": "10h 45m", "departure": "17:00", "arrival": "05:45+1"},
        ],
        "london": [
            {"airline": "British Airways", "price": 620, "duration": "2h 15m", "departure": "07:00", "arrival": "09:15"},
            {"airline": "Ryanair", "price": 89, "duration": "2h 45m", "departure": "13:00", "arrival": "15:45"},
            {"airline": "Lufthansa", "price": 480, "duration": "2h 30m", "departure": "10:30", "arrival": "12:45"},
        ],
        "new york": [
            {"airline": "American", "price": 850, "duration": "8h 30m", "departure": "15:00", "arrival": "00:30+1"},
            {"airline": "Delta", "price": 920, "duration": "8h 15m", "departure": "13:00", "arrival": "22:15"},
            {"airline": "Norse", "price": 350, "duration": "9h 00m", "departure": "18:00", "arrival": "03:00+1"},
        ],
        "lahore": [
            {"airline": "Pakistan Airlines", "price": 280, "duration": "4h 30m", "departure": "10:00", "arrival": "14:30"},
            {"airline": "FlyDubai", "price": 250, "duration": "5h 15m", "departure": "14:00", "arrival": "19:15"},
            {"airline": "Turkish Airlines", "price": 350, "duration": "4h 45m", "departure": "11:30", "arrival": "16:15"},
        ],
        "islamabad": [
            {"airline": "Pakistan Airlines", "price": 270, "duration": "4h 30m", "departure": "09:30", "arrival": "14:00"},
            {"airline": "SereneAir", "price": 200, "duration": "5h 00m", "departure": "13:00", "arrival": "18:00"},
            {"airline": "Turkish Airlines", "price": 330, "duration": "4h 45m", "departure": "12:00", "arrival": "16:45"},
        ],
        "hong kong": [
            {"airline": "Cathay Pacific", "price": 920, "duration": "12h 15m", "departure": "21:00", "arrival": "13:15+1"},
            {"airline": "Hong Kong Airlines", "price": 850, "duration": "12h 30m", "departure": "19:30", "arrival": "11:00+1"},
            {"airline": "Air Asia", "price": 480, "duration": "13h 45m", "departure": "23:00", "arrival": "14:45+1"},
        ],
        "sri lanka": [
            {"airline": "SriLankan Airlines", "price": 620, "duration": "7h 30m", "departure": "16:00", "arrival": "23:30"},
            {"airline": "Emirates", "price": 720, "duration": "6h 45m", "departure": "14:00", "arrival": "20:45"},
            {"airline": "Air Asia", "price": 380, "duration": "8h 15m", "departure": "18:00", "arrival": "02:15+1"},
        ],
        "barcelona": [
            {"airline": "Iberia", "price": 520, "duration": "2h 45m", "departure": "09:00", "arrival": "11:45"},
            {"airline": "Ryanair", "price": 110, "duration": "3h 15m", "departure": "15:00", "arrival": "18:15"},
            {"airline": "Vueling", "price": 180, "duration": "2h 50m", "departure": "12:30", "arrival": "15:20"},
        ],
        "singapore": [
            {"airline": "Singapore Airlines", "price": 820, "duration": "11h 30m", "departure": "22:00", "arrival": "13:30+1"},
            {"airline": "Changi Airlines", "price": 750, "duration": "11h 45m", "departure": "20:30", "arrival": "12:15+1"},
            {"airline": "Scoot", "price": 420, "duration": "12h 30m", "departure": "23:30", "arrival": "14:00+1"},
        ],
        "seoul": [
            {"airline": "Korean Air", "price": 920, "duration": "12h 00m", "departure": "20:00", "arrival": "12:00+1"},
            {"airline": "Asiana", "price": 900, "duration": "12h 15m", "departure": "19:30", "arrival": "11:45+1"},
            {"airline": "Air Asia X", "price": 480, "duration": "13h 30m", "departure": "21:00", "arrival": "13:30+1"},
        ],
        "andros": [
            {"airline": "Hellenic Airways", "price": 380, "duration": "5h 30m", "departure": "08:00", "arrival": "13:30"},
            {"airline": "Sky Express", "price": 350, "duration": "5h 45m", "departure": "10:00", "arrival": "15:45"},
            {"airline": "Air Santorini", "price": 320, "duration": "6h 00m", "departure": "11:30", "arrival": "17:30"},
        ],
        "fraser island": [
            {"airline": "Qantas", "price": 580, "duration": "2h 45m", "departure": "08:00", "arrival": "10:45"},
            {"airline": "Virgin Australia", "price": 520, "duration": "2h 50m", "departure": "13:00", "arrival": "15:50"},
            {"airline": "Regional Express", "price": 350, "duration": "3h 30m", "departure": "14:30", "arrival": "18:00"},
        ],
        "rio": [
            {"airline": "TAP Air Portugal", "price": 780, "duration": "9h 45m", "departure": "17:00", "arrival": "03:45+1"},
            {"airline": "LATAM", "price": 820, "duration": "9h 30m", "departure": "18:00", "arrival": "03:30+1"},
            {"airline": "Avianca", "price": 650, "duration": "10h 15m", "departure": "19:30", "arrival": "05:45+1"},
        ],
    }
    
    
    def _find_city(self, city_name: str) -> str:
        """Find city in database with fuzzy matching"""
        city_lower = city_name.lower().strip()
        
        if city_lower in self.FLIGHTS_DB:
            return city_lower
        
        # Try partial match
        for city in self.FLIGHTS_DB.keys():
            city_words = city.split()
            for word in city_words:
                if word.startswith(city_lower) or city_lower in city:
                    return city
        
        # Check prefix match
        for city in self.FLIGHTS_DB.keys():
            if city_lower.startswith(city) or city.startswith(city_lower):
                return city
        
        return None
    
    def search_flights(self, from_city: str, to_city: str, departure_date: str, 
                      passengers: int = 1, trip_type: str = "round_trip") -> Dict[str, Any]:
        """
        Search for flight options
        
        Args:
            from_city: Departure city
            to_city: Destination city
            departure_date: Date in YYYY-MM-DD format
            passengers: Number of passengers
            trip_type: "one_way" or "round_trip"
        
        Returns:
            Dictionary with flight options or error
        """
        
        to_city_lower = to_city.lower()
        
        # Validate date format
        try:
            departure = datetime.strptime(departure_date, "%Y-%m-%d")
            # Allow today and future dates, reject past dates only
            if departure.date() < datetime.now().date():
                return {"error": "Departure date must be today or in the future"}
        except ValueError:
            return {"error": "Date format must be YYYY-MM-DD"}
        
        # Find destination with fuzzy matching
        actual_to_city = self._find_city(to_city_lower)
        
        # Check if destination has flights
        if actual_to_city is None:
            return {
                "error": f"No flights found to '{to_city}'",
                "available_destinations": list(self.FLIGHTS_DB.keys())
            }
        
        if passengers < 1 or passengers > 9:
            return {"error": "Passengers must be between 1 and 9"}
        
        flights = self.FLIGHTS_DB[actual_to_city]
        
        # Apply passenger count to prices
        processed_flights = []
        for flight in flights:
            flight_copy = flight.copy()
            flight_copy["price_per_person"] = flight["price"]
            flight_copy["total_price"] = flight["price"] * passengers
            processed_flights.append(flight_copy)
        
        # Sort by price
        processed_flights.sort(key=lambda x: x["price_per_person"])
        
        result = {
            "from": from_city,
            "to": to_city,
            "departure_date": departure_date,
            "passengers": passengers,
            "trip_type": trip_type,
            "options": processed_flights,
            "lowest_price": processed_flights[0]["price_per_person"] if processed_flights else 0,
            "lowest_total": processed_flights[0]["total_price"] if processed_flights else 0,
            "currency": "USD"
        }
        
        if trip_type == "round_trip":
            result["note"] = "Prices shown are for round-trip flights"
        
        return result


# Tool definition for LLM
FLIGHT_TOOLS = [
    {
        "name": "search_flights",
        "description": "Search for available flights and prices to a destination",
        "input_schema": {
            "type": "object",
            "properties": {
                "from_city": {
                    "type": "string",
                    "description": "Departure city (user's location)"
                },
                "to_city": {
                    "type": "string",
                    "description": "Destination city"
                },
                "departure_date": {
                    "type": "string",
                    "description": "Departure date in YYYY-MM-DD format"
                },
                "passengers": {
                    "type": "integer",
                    "description": "Number of passengers (default: 1)"
                },
                "trip_type": {
                    "type": "string",
                    "enum": ["one_way", "round_trip"],
                    "description": "Type of trip"
                }
            },
            "required": ["from_city", "to_city", "departure_date"]
        }
    }
]
