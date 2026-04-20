"""
Tool Orchestrator
Manages tool registration, detection, parsing, and execution
"""

import json
import asyncio
import re
from typing import Dict, List, Any, Optional, Callable
from dataclasses import dataclass

# Import all tools
from crm_tool import CRMTool, CRM_TOOLS
from weather_tool import WeatherTool, WEATHER_TOOLS
from budget_tool import BudgetCalculatorTool, BUDGET_TOOLS
from flights_tool import FlightBookingTool, FLIGHT_TOOLS
from hotels_tool import HotelFinderTool, HOTEL_TOOLS


@dataclass
class ToolCall:
    """Represents a tool call request"""
    tool_name: str
    arguments: Dict[str, Any]
    raw_text: str = ""


class ToolOrchestrator:
    """Manages all tools, their registration, and execution"""
    
    def __init__(self, db_path: str = "data/users.db"):
        """Initialize orchestrator with all tools"""
        
        # Initialize tool instances
        self.crm = CRMTool(db_path)
        self.weather = WeatherTool()
        self.budget = BudgetCalculatorTool()
        self.flights = FlightBookingTool()
        self.hotels = HotelFinderTool()
        
        # Tool registry: maps tool name to function
        self.tool_registry: Dict[str, Callable] = {
            # CRM tools
            "create_user": self.crm.create_user,
            "get_user": self.crm.get_user,
            "update_user": self.crm.update_user,
            "add_trip": self.crm.add_trip,
            "get_user_trips": self.crm.get_user_trips,
            
            # Weather tools
            "get_weather": self.weather.get_weather,
            
            # Budget tools
            "calculate_trip_budget": self.budget.calculate_trip_budget,
            
            # Flight tools
            "search_flights": self.flights.search_flights,
            
            # Hotel tools
            "search_hotels": self.hotels.search_hotels,
        }
        
        # All tool schemas for LLM
        self.all_tools = CRM_TOOLS + WEATHER_TOOLS + BUDGET_TOOLS + FLIGHT_TOOLS + HOTEL_TOOLS
    
    def get_tool_schemas(self) -> List[Dict[str, Any]]:
        """Get all tool schemas for LLM instruction"""
        return self.all_tools
    
    def detect_tool_call(self, text: str) -> Optional[ToolCall]:
        """
        Detect if text contains a tool call request
        
        Looks for patterns like:
        - [TOOL_CALL: tool_name {...}]  (with single or double quotes)
        - {"tool": "name", "arguments": {...}}
        - tool_name({...})
        """
        
        # Pattern 1: [TOOL_CALL: tool_name with args] - Handle nested braces and quotes
        # Use a more robust pattern that handles nested structures
        match = re.search(r'\[TOOL_CALL:\s*(\w+)\s*(\{.+\})\]', text)
        if match:
            tool_name = match.group(1)
            args_str = match.group(2)
            
            # Find matching closing brace for better parsing
            brace_count = 0
            end_idx = 0
            for i, char in enumerate(args_str):
                if char == '{':
                    brace_count += 1
                elif char == '}':
                    brace_count -= 1
                    if brace_count == 0:
                        end_idx = i + 1
                        break
            
            if end_idx > 0:
                args_str = args_str[:end_idx]
            
            # Convert Python dict syntax (single quotes) to JSON (double quotes)
            try:
                # Try direct JSON first
                args = json.loads(args_str)
                return ToolCall(tool_name=tool_name, arguments=args, raw_text=text)
            except:
                # If that fails, convert single quotes to double quotes
                try:
                    args_json = args_str.replace("'", '"')
                    args = json.loads(args_json)
                    return ToolCall(tool_name=tool_name, arguments=args, raw_text=text)
                except:
                    pass
        
        # Pattern 2: JSON format tool call - {"tool": "name", "arguments": {...}}
        match = re.search(r'\{"[^"]*tool[^"]*":\s*"(\w+)"', text)
        if match:
            tool_name = match.group(1)
            # Extract full JSON object
            brace_pos = text.find('{')
            if brace_pos != -1:
                brace_count = 0
                end_idx = 0
                for i in range(brace_pos, len(text)):
                    if text[i] == '{':
                        brace_count += 1
                    elif text[i] == '}':
                        brace_count -= 1
                        if brace_count == 0:
                            end_idx = i + 1
                            break
                if end_idx > 0:
                    args_str = text[brace_pos:end_idx]
                    try:
                        args = json.loads(args_str)
                        return ToolCall(tool_name=tool_name, arguments=args, raw_text=text)
                    except:
                        pass
        
        # Pattern 3: Function call format: tool_name({"arg": "value"}) or tool_name({'arg': 'value'})
        match = re.search(r'(\w+)\s*\(\s*(\{.+\})\s*\)', text, re.DOTALL)
        if match:
            tool_name = match.group(1)
            args_str = match.group(2)
            
            if tool_name in self.tool_registry:
                try:
                    # Try direct JSON first
                    args = json.loads(args_str)
                    return ToolCall(tool_name=tool_name, arguments=args, raw_text=text)
                except:
                    # Convert single quotes to double quotes
                    try:
                        args_json = args_str.replace("'", '"')
                        args = json.loads(args_json)
                        return ToolCall(tool_name=tool_name, arguments=args, raw_text=text)
                    except:
                        pass
        
        return None
    
    def detect_all_tool_calls(self, text: str) -> List[ToolCall]:
        """Detect ALL tool calls in text, not just the first one"""
        results = []
        temp_text = text
        
        while True:
            match = re.search(r'\[TOOL_CALL:\s*(\w+)\s*(\{.+\})\]', temp_text)
            if not match:
                break
            
            tool_name = match.group(1)
            args_str = match.group(2)
            
            # Find matching closing brace
            brace_count = 0
            end_idx = 0
            for i, char in enumerate(args_str):
                if char == '{':
                    brace_count += 1
                elif char == '}':
                    brace_count -= 1
                    if brace_count == 0:
                        end_idx = i + 1
                        break
            
            if end_idx > 0:
                args_str = args_str[:end_idx]
            
            try:
                args = json.loads(args_str)
                results.append(ToolCall(tool_name=tool_name, arguments=args, raw_text=text))
            except:
                try:
                    args_json = args_str.replace("'", '"')
                    args = json.loads(args_json)
                    results.append(ToolCall(tool_name=tool_name, arguments=args, raw_text=text))
                except:
                    pass
            
            # Remove this match and continue searching
            start_pos = temp_text.find('[TOOL_CALL:')
            end_pos = temp_text.find(']', start_pos) + 1
            temp_text = temp_text[:start_pos] + temp_text[end_pos:]
        
        return results
    
    def execute_tool(self, tool_call: ToolCall) -> Dict[str, Any]:
        """
        Execute a tool call synchronously
        
        Returns result or error message
        """
        
        tool_name = tool_call.tool_name
        arguments = tool_call.arguments
        
        # Check if tool exists
        if tool_name not in self.tool_registry:
            return {
                "error": f"Tool '{tool_name}' not found",
                "available_tools": list(self.tool_registry.keys())
            }
        
        try:
            tool_func = self.tool_registry[tool_name]
            
            # Execute the tool function directly (tools are synchronous)
            result = tool_func(**arguments)
            
            return {
                "success": True,
                "tool": tool_name,
                "result": result
            }
        
        except TypeError as e:
            return {
                "error": f"Invalid arguments for '{tool_name}': {str(e)}",
                "tool": tool_name,
                "expected_args": self._get_tool_schema(tool_name)
            }
        
        except Exception as e:
            return {
                "error": f"Tool execution failed: {str(e)}",
                "tool": tool_name
            }
    
    def _get_tool_schema(self, tool_name: str) -> Optional[Dict]:
        """Get schema for a specific tool"""
        for tool in self.all_tools:
            if tool.get("name") == tool_name:
                return tool.get("input_schema")
        return None
    
    async def execute_tool_call(self, tool_call: ToolCall) -> str:
        """
        Execute tool and format result as string for LLM
        
        Returns formatted result string
        """
        
        result = self.execute_tool(tool_call)
        
        # Format result for LLM
        if result.get("success"):
            content = result.get("result", {})
            if isinstance(content, dict):
                # Pretty print dict results
                formatted = json.dumps(content, indent=2, default=str)
                return f"Tool '{result.get('tool')}' executed successfully:\n{formatted}"
            else:
                return f"Tool result: {str(content)}"
        else:
            error = result.get("error", "Unknown error")
            return f"Tool execution error: {error}"
    
    def parse_and_detect_tools(self, text: str) -> List[ToolCall]:
        """
        Parse text and detect all tool calls
        Useful for LLM responses with multiple tool calls
        """
        
        tool_calls = []
        
        # Find all tool call patterns
        patterns = [
            r'\[TOOL_CALL:\s*(\w+)\s*\{([^}]+)\}\]',
            r'(\w+)\s*\(\s*(\{[^}]+\})\s*\)',
        ]
        
        for pattern in patterns:
            matches = re.finditer(pattern, text)
            for match in matches:
                try:
                    tool_name = match.group(1)
                    if tool_name in self.tool_registry:
                        args_str = match.group(2)
                        args = json.loads(args_str) if args_str.startswith('{') else {}
                        tool_calls.append(ToolCall(
                            tool_name=tool_name,
                            arguments=args,
                            raw_text=match.group(0)
                        ))
                except:
                    continue
        
        return tool_calls
    
    async def execute_multiple_tools(self, tool_calls: List[ToolCall]) -> Dict[str, Any]:
        """
        Execute multiple tool calls concurrently
        
        Returns aggregated results
        """
        
        if not tool_calls:
            return {"error": "No tool calls provided"}
        
        # Execute all tools concurrently in worker threads (tools are sync).
        tasks = [asyncio.to_thread(self.execute_tool, tc) for tc in tool_calls]
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        # Process results
        processed = []
        for i, result in enumerate(results):
            if isinstance(result, Exception):
                processed.append({
                    "tool": tool_calls[i].tool_name,
                    "error": str(result)
                })
            else:
                processed.append(result)
        
        return {
            "tool_calls_executed": len(tool_calls),
            "results": processed
        }
    
    def format_tools_for_prompt(self) -> str:
        """
        Format tool definitions for system prompt
        
        Tells LLM what tools are available and how to call them
        """
        
        prompt = "You have access to the following tools:\n\n"
        
        for tool in self.all_tools:
            prompt += f"### {tool['name']}\n"
            prompt += f"Description: {tool['description']}\n"
            prompt += f"Input schema: {json.dumps(tool['input_schema'], indent=2)}\n"
            prompt += f"To use this tool, format your response as:\n"
            prompt += f"[TOOL_CALL: {tool['name']} {{'arg1': 'value1', 'arg2': 'value2'}}]\n\n"
        
        prompt += "\nWhen you need to use a tool:\n"
        prompt += "1. Identify which tool is needed\n"
        prompt += "2. Prepare arguments according to the schema\n"
        prompt += "3. Format as [TOOL_CALL: tool_name {args}]\n"
        prompt += "4. I will execute the tool and provide results\n"
        prompt += "5. Use the tool result to formulate your response\n"
        
        return prompt
    
    def format_tool_result_for_prompt(self, result: Dict[str, Any]) -> str:
        """
        Format tool result for inclusion in system prompt
        
        Makes it clear to LLM what the tool returned
        """
        
        if result.get("success"):
            content = result.get("result", {})
            return f"Tool '{result.get('tool')}' result:\n{json.dumps(content, indent=2, default=str)}"
        else:
            return f"Tool error: {result.get('error')}"


# Helper function for easy tool execution
async def execute_tool_from_text(text: str, orchestrator: ToolOrchestrator) -> Optional[str]:
    """
    Utility function to detect and execute tool from text
    
    Usage:
        orchestrator = ToolOrchestrator()
        result = await execute_tool_from_text(llm_response, orchestrator)
    """
    
    tool_call = orchestrator.detect_tool_call(text)
    if tool_call:
        return await orchestrator.execute_tool_call(tool_call)
    
    return None
