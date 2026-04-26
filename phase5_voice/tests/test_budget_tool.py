"""
Travel Budget Calculator - Unit Tests
Tests functional correctness of budget estimates
"""

import unittest
import os
import json
from pathlib import Path

# Add parent directory to path
import sys
sys.path.insert(0, str(Path(__file__).parent.parent))

from budget_tool import BudgetCalculatorTool


class TestBudgetToolFunctional(unittest.TestCase):
    """Test Budget Calculator functional correctness"""
    
    def setUp(self):
        self.budget = BudgetCalculatorTool()
    
    def test_calculate_budget_basic(self):
        """Test basic budget calculation"""
        result = self.budget.calculate_trip_budget(
            destination="Paris",
            duration_days=5,
            num_travelers=1,
            budget_level="moderate"
        )
        
        self.assertIn("total", result)
        self.assertEqual(result["destination"], "Paris")
        self.assertEqual(result["duration_days"], 5)
        self.assertEqual(result["budget_level"], "moderate")
    
    def test_calculate_budget_multiple_days(self):
        """Test budget increases with duration"""
        r1 = self.budget.calculate_trip_budget("Tokyo", 3, 1, "moderate")
        r2 = self.budget.calculate_trip_budget("Tokyo", 7, 1, "moderate")
        
        self.assertTrue(r2["total"] > r1["total"])
        # Daily breakdown should be consistent
        self.assertEqual(r1["num_travelers"], 1)

    def test_budget_level_comparison(self):
        """Test that luxury > moderate > budget"""
        dest = "London"
        days = 5
        
        r_budget = self.budget.calculate_trip_budget(dest, days, 1, "budget")
        r_moderate = self.budget.calculate_trip_budget(dest, days, 1, "moderate")
        r_luxury = self.budget.calculate_trip_budget(dest, days, 1, "luxury")
        
        self.assertTrue(r_luxury["total"] > r_moderate["total"])
        self.assertTrue(r_moderate["total"] > r_budget["total"])

    def test_budget_all_supported_cities(self):
        """Test budget calculation for all supported cities"""
        cities = ["Paris", "Istanbul", "Tokyo", "Dubai", "Bangkok", "London", "Lahore"]
        for city in cities:
            result = self.budget.calculate_trip_budget(city, 3, 1, "moderate")
            self.assertIn("total", result)
            self.assertNotIn("error", result)

    def test_budget_invalid_destination(self):
        """Test handling of invalid destination"""
        result = self.budget.calculate_trip_budget("InvalidCity123", 5, 1, "moderate")
        self.assertIn("error", result)
        self.assertIn("available_cities", result)

    def test_budget_invalid_style(self):
        """Test handling of invalid budget level"""
        result = self.budget.calculate_trip_budget("Paris", 5, 1, "invalid_style")
        self.assertIn("error", result)

    def test_budget_zero_days(self):
        """Test handling of zero duration"""
        result = self.budget.calculate_trip_budget("Paris", 0, 1, "moderate")
        self.assertIn("error", result)

    def test_budget_negative_days(self):
        """Test handling of negative duration"""
        result = self.budget.calculate_trip_budget("Paris", -5, 1, "moderate")
        self.assertIn("error", result)

    def test_budget_case_insensitive(self):
        """Test case insensitivity for destination and style"""
        r1 = self.budget.calculate_trip_budget("TOKYO", 5, 1, "luxury")
        r2 = self.budget.calculate_trip_budget("tokyo", 5, 1, "luxury")
        self.assertEqual(r1["total"], r2["total"])

    def test_budget_multiword_cities(self):
        """Test cities with multiple words"""
        cities = ["New York", "Hong Kong", "Sri Lanka", "Fraser Island"]
        for city in cities:
            result = self.budget.calculate_trip_budget(city, 5, 1, "moderate")
            self.assertIn("total", result)

    def test_budget_breakdown_sums_correctly(self):
        """Test that breakdown items sum up to subtotal"""
        result = self.budget.calculate_trip_budget("Dubai", 10, 2, "moderate")
        breakdown = result["breakdown"]
        
        calculated_subtotal = sum(breakdown.values()) - breakdown.get("taxes_visa_fees", 0)
        self.assertAlmostEqual(calculated_subtotal, result["subtotal"], places=1)


if __name__ == "__main__":
    unittest.main()
