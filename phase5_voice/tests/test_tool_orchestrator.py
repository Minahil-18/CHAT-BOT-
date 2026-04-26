"""
Tool Orchestrator - Unit Tests
Tests tool detection, parsing, and execution
"""

import unittest
import json
import asyncio
from pathlib import Path

# Add parent directory to path
import sys
sys.path.insert(0, str(Path(__file__).parent.parent))

from tool_orchestrator import ToolOrchestrator, ToolCall


class TestToolOrchestrator(unittest.TestCase):
    """Test Tool Orchestrator integration"""
    
    def setUp(self):
        self.orchestrator = ToolOrchestrator()
    
    def test_detect_tool_call_standard(self):
        """Test detecting [TOOL_CALL: name {args}] format"""
        text = "I should check the weather. [TOOL_CALL: get_weather {\"city\": \"Paris\"}]"
        call = self.orchestrator.detect_tool_call(text)
        
        self.assertIsNotNone(call)
        self.assertEqual(call.tool_name, "get_weather")
        self.assertEqual(call.arguments["city"], "Paris")
    
    def test_execute_weather_tool(self):
        """Test executing weather tool through orchestrator"""
        call = ToolCall(tool_name="get_weather", arguments={"city": "Tokyo"})
        result = self.orchestrator.execute_tool(call)
        
        self.assertTrue(result["success"])
        self.assertEqual(result["result"]["city"], "Tokyo")

    def test_execute_budget_tool(self):
        """Test executing budget tool with correct args"""
        call = ToolCall(tool_name="calculate_trip_budget", arguments={
            "destination": "Paris", 
            "duration_days": 5,
            "budget_level": "luxury"
        })
        result = self.orchestrator.execute_tool(call)
        
        self.assertTrue(result["success"])
        self.assertEqual(result["result"]["budget_level"], "luxury")

    def test_execute_flights_tool(self):
        """Test executing flights tool with correct args"""
        call = ToolCall(tool_name="search_flights", arguments={
            "from_city": "London",
            "to_city": "Istanbul",
            "departure_date": "2026-12-01"
        })
        result = self.orchestrator.execute_tool(call)
        
        self.assertTrue(result["success"])
        self.assertEqual(result["result"]["to"], "Istanbul")

    def test_invalid_tool_name(self):
        """Test handling of unknown tool name"""
        call = ToolCall(tool_name="nonexistent_tool", arguments={})
        result = self.orchestrator.execute_tool(call)
        self.assertFalse(result.get("success", False))
        self.assertIn("error", result)


if __name__ == "__main__":
    unittest.main()
