"""
Flights and Hotels Tools - Unit Tests
Tests functional correctness of search operations
"""

import unittest
from pathlib import Path
from datetime import datetime, timedelta

# Add parent directory to path
import sys
sys.path.insert(0, str(Path(__file__).parent.parent))

from flights_tool import FlightBookingTool
from hotels_tool import HotelFinderTool


class TestFlightsTool(unittest.TestCase):
    """Test Flights Tool functional correctness"""
    
    def setUp(self):
        self.flights = FlightBookingTool()
        self.tomorrow = (datetime.now() + timedelta(days=1)).strftime("%Y-%m-%d")
    
    def test_search_flights_basic(self):
        """Test basic flight search"""
        result = self.flights.search_flights(
            from_city="London",
            to_city="Paris",
            departure_date=self.tomorrow
        )
        
        self.assertIn("options", result)
        self.assertEqual(result["to"], "Paris")
        self.assertTrue(len(result["options"]) > 0)
    
    def test_search_flights_invalid_date(self):
        """Test flight search with past date"""
        yesterday = (datetime.now() - timedelta(days=1)).strftime("%Y-%m-%d")
        result = self.flights.search_flights("London", "Paris", yesterday)
        self.assertIn("error", result)

    def test_search_flights_invalid_destination(self):
        """Test flight search with unknown destination"""
        result = self.flights.search_flights("London", "Mars", self.tomorrow)
        self.assertIn("error", result)
        self.assertIn("available_destinations", result)

    def test_flight_data_quality(self):
        """Test that flight objects have required fields"""
        result = self.flights.search_flights("London", "Tokyo", self.tomorrow)
        flight = result["options"][0]
        
        required = ["airline", "price", "duration", "departure", "arrival"]
        for field in required:
            self.assertIn(field, flight)


class TestHotelsTool(unittest.TestCase):
    """Test Hotels Tool functional correctness"""
    
    def setUp(self):
        self.hotels = HotelFinderTool()
    
    def test_search_hotels_basic(self):
        """Test basic hotel search"""
        result = self.hotels.search_hotels(city="Paris")
        
        self.assertIn("hotels", result)
        self.assertEqual(result["city"], "Paris")
        self.assertTrue(len(result["hotels"]) > 0)
    
    def test_search_hotels_price_filter(self):
        """Test hotel filtering by price range"""
        result = self.hotels.search_hotels(city="Dubai", price_range="luxury")
        for hotel in result["hotels"]:
            self.assertTrue(hotel["price_per_night"] >= 200)

    def test_hotel_data_quality(self):
        """Test that hotel objects have required fields"""
        result = self.hotels.search_hotels("Istanbul")
        hotel = result["hotels"][0]
        
        required = ["name", "rating", "price_per_night", "amenities"]
        for field in required:
            self.assertIn(field, hotel)


if __name__ == "__main__":
    unittest.main()
