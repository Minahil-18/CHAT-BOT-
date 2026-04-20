"""
Travel Budget Calculator Tool
Estimates trip costs based on destination, duration, and travel style
"""

from typing import Dict, Any

class BudgetCalculatorTool:
    """Calculate estimated trip costs"""
    
    # Average costs per day by city (in USD)
    CITY_COSTS = {
        "paris": {"accommodation": 120, "food": 50, "activities": 30},
        "istanbul": {"accommodation": 50, "food": 20, "activities": 15},
        "tokyo": {"accommodation": 100, "food": 40, "activities": 25},
        "dubai": {"accommodation": 150, "food": 40, "activities": 50},
        "bangkok": {"accommodation": 40, "food": 15, "activities": 20},
        "london": {"accommodation": 130, "food": 45, "activities": 25},
        "new york": {"accommodation": 150, "food": 60, "activities": 40},
        "barcelona": {"accommodation": 90, "food": 35, "activities": 20},
        "rio": {"accommodation": 80, "food": 30, "activities": 25},
        "lahore": {"accommodation": 30, "food": 10, "activities": 10},
        "islamabad": {"accommodation": 40, "food": 12, "activities": 12},
        "singapore": {"accommodation": 100, "food": 30, "activities": 25},
        "hong kong": {"accommodation": 120, "food": 35, "activities": 20},
        "seoul": {"accommodation": 80, "food": 25, "activities": 18},
        "sri lanka": {"accommodation": 45, "food": 18, "activities": 15},
        "andros": {"accommodation": 110, "food": 40, "activities": 22},
        "fraser island": {"accommodation": 140, "food": 45, "activities": 35},
    }
    
    # Budget level multipliers
    BUDGET_MULTIPLIERS = {
        "budget": 0.7,
        "moderate": 1.0,
        "luxury": 1.8
    }
    
    # Flight cost estimates (round trip from major hub)
    FLIGHT_COSTS = {
        "paris": 600,
        "istanbul": 500,
        "tokyo": 1000,
        "dubai": 700,
        "bangkok": 800,
        "london": 650,
        "new york": 900,
        "barcelona": 650,
        "rio": 900,
        "lahore": 400,
        "islamabad": 450,
        "singapore": 900,
        "hong kong": 950,
        "seoul": 850,
        "sri lanka": 700,
        "andros": 550,
        "fraser island": 650,
    }
    
    
    def _find_city(self, city_name: str) -> str:
        """Find city in database with fuzzy matching
        
        Handles variations like:
        - "fraser" -> "fraser island"
        - "rio" -> "rio"
        - "hong kong" -> "hong kong"
        """
        city_lower = city_name.lower().strip()
        
        # Exact match
        if city_lower in self.CITY_COSTS:
            return city_lower
        
        # Try to find by partial match
        for city in self.CITY_COSTS.keys():
            # Check if any word in the city name starts with the query
            city_words = city.split()
            for word in city_words:
                if word.startswith(city_lower) or city_lower in city:
                    return city
        
        # Check if query starts with any city name
        for city in self.CITY_COSTS.keys():
            if city_lower.startswith(city) or city.startswith(city_lower):
                return city
        
        return None
    
    def calculate_trip_budget(self, destination: str, duration_days: int, 
                             num_travelers: int = 1, budget_level: str = "moderate") -> Dict[str, Any]:
        """
        Calculate estimated trip budget
        
        Args:
            destination: City name
            duration_days: Number of days for the trip
            num_travelers: Number of people traveling
            budget_level: "budget", "moderate", or "luxury"
        
        Returns:
            Dictionary with cost breakdown
        """
        
        destination_lower = destination.lower()
        
        # Try to find city with fuzzy matching
        actual_city = self._find_city(destination_lower)
        
        # Get base costs for destination
        if actual_city is None:
            return {
                "error": f"Destination '{destination}' not found in database",
                "available_cities": list(self.CITY_COSTS.keys())
            }
        
        # Validate duration
        if duration_days < 1 or duration_days > 365:
            return {"error": "Duration must be between 1 and 365 days"}
        
        # Validate budget level
        if budget_level not in self.BUDGET_MULTIPLIERS:
            return {
                "error": f"Budget level must be one of: {list(self.BUDGET_MULTIPLIERS.keys())}"
            }
        
        if num_travelers < 1:
            return {"error": "Number of travelers must be at least 1"}
        
        # Get base daily costs
        daily_costs = self.CITY_COSTS[actual_city]
        multiplier = self.BUDGET_MULTIPLIERS[budget_level]
        
        # Calculate components
        accommodation = daily_costs["accommodation"] * duration_days * multiplier
        food = daily_costs["food"] * duration_days * multiplier
        activities = daily_costs["activities"] * duration_days * multiplier
        flight = self.FLIGHT_COSTS.get(actual_city, 700)
        
        # Apply group discounts
        if num_travelers > 1:
            accommodation *= (1 - 0.05 * (num_travelers - 1))  # 5% per extra person
            flight *= num_travelers
        else:
            flight *= 1  # Single traveler
        
        # Calculate totals
        subtotal = accommodation + food + activities + flight
        taxes_fees = subtotal * 0.1  # 10% for visa, taxes, etc
        total = subtotal + taxes_fees
        
        return {
            "destination": destination,
            "duration_days": duration_days,
            "num_travelers": num_travelers,
            "budget_level": budget_level,
            "breakdown": {
                "flights": round(flight, 2),
                "accommodation": round(accommodation, 2),
                "food": round(food, 2),
                "activities": round(activities, 2),
                "taxes_visa_fees": round(taxes_fees, 2)
            },
            "subtotal": round(subtotal, 2),
            "total": round(total, 2),
            "per_person_total": round(total / num_travelers, 2),
            "per_day_per_person": round((total / num_travelers / duration_days), 2),
            "recommendations": self._get_recommendations(budget_level, total / num_travelers / duration_days)
        }
    
    def _get_recommendations(self, budget_level: str, daily_rate: float) -> str:
        """Get packing and budget recommendations"""
        
        recommendations = {
            "budget": "Pack light, use public transport, eat at local restaurants, stay in hostels or budget hotels",
            "moderate": "Balance comfort and cost, use mix of public/taxi transport, eat mix of restaurants, stay in mid-range hotels",
            "luxury": "Enjoy premium accommodations, private transport, fine dining, and exclusive experiences"
        }
        
        return recommendations.get(budget_level, "Travel responsibly within your means")


# Tool definition for LLM
BUDGET_TOOLS = [
    {
        "name": "calculate_trip_budget",
        "description": "Calculate estimated trip costs including flights, accommodation, food, and activities",
        "input_schema": {
            "type": "object",
            "properties": {
                "destination": {
                    "type": "string",
                    "description": "Travel destination city"
                },
                "duration_days": {
                    "type": "integer",
                    "description": "Number of days for the trip"
                },
                "num_travelers": {
                    "type": "integer",
                    "description": "Number of people traveling (default: 1)"
                },
                "budget_level": {
                    "type": "string",
                    "enum": ["budget", "moderate", "luxury"],
                    "description": "Travel budget level"
                }
            },
            "required": ["destination", "duration_days"]
        }
    }
]
