"""
LLM Tool Invocation Accuracy Tests
Measures how well the LLM calls the correct tools with correct arguments
"""

import json
import asyncio
import websockets
import os
import sys
from pathlib import Path
from typing import Dict, List, Any, Optional
from collections import defaultdict

sys.path.insert(0, str(Path(__file__).parent.parent))

# WebSocket configuration
WS_URL = "ws://localhost:8000/ws/chat"
TEST_DATA_PATH = os.path.join(os.path.dirname(__file__), "data", "tool_invocation_test_utterances.json")
REPORT_PATH = os.path.join(os.path.dirname(__file__), "..", "reports", "tool_invocation_accuracy_report.json")


class LLMToolInvocationTester:
    """Test LLM tool invocation accuracy"""
    
    def __init__(self):
        self.results = {
            "timestamp": "2026-04-25",
            "total_tests": 0,
            "passed": 0,
            "failed": 0,
            "by_category": defaultdict(lambda: {"total": 0, "passed": 0, "failed": 0}),
            "test_details": [],
            "summary_by_tool": {}
        }
        self.user_id = "eval_tester_001"
    
    async def get_chatbot_response(self, message: str) -> str:
        """Send message to chatbot and get response"""
        try:
            async with websockets.connect(WS_URL, ping_interval=None) as ws:
                await ws.recv()  # hello message
                await ws.send(json.dumps({
                    "message": message,
                    "user_id": self.user_id,
                    "city": "Paris"
                }))
                
                response_text = ""
                while True:
                    resp = json.loads(await ws.recv())
                    if resp["type"] == "final":
                        response_text = resp["message"]
                        break
                
                return response_text
        except Exception as e:
            print(f"WebSocket error: {e}")
            return f"ERROR: {str(e)}"
    
    def extract_tool_calls(self, response: str) -> List[Dict[str, Any]]:
        """Extract tool calls from response text"""
        import re
        
        tool_calls = []
        
        # Pattern: [TOOL_CALL: tool_name {...}]
        pattern = r'\[TOOL_CALL:\s*(\w+)\s*(\{.+?\})\]'
        
        matches = re.finditer(pattern, response, re.DOTALL)
        for match in matches:
            tool_name = match.group(1)
            args_str = match.group(2)
            
            try:
                # Find matching braces
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
                    arguments = json.loads(args_str)
                    
                    tool_calls.append({
                        "tool": tool_name,
                        "arguments": arguments
                    })
            except json.JSONDecodeError:
                pass
        
        return tool_calls
    
    def check_tool_correctness(self, actual_tool: str, expected_tool: str) -> bool:
        """Check if actual tool matches expected tool"""
        return actual_tool.lower() == expected_tool.lower()
    
    def check_arguments_correctness(self, actual_args: Dict, expected_args: Dict) -> bool:
        """Check if actual arguments match expected (handle 'from_context' values)"""
        for key, expected_value in expected_args.items():
            if expected_value == "from_context":
                # Skip context-dependent arguments
                continue
            
            if key not in actual_args:
                return False
            
            actual_value = actual_args[key]
            
            # Allow case-insensitive string matching for city names
            if isinstance(expected_value, str) and isinstance(actual_value, str):
                if actual_value.lower() != expected_value.lower():
                    return False
            else:
                if actual_value != expected_value:
                    return False
        
        return True
    
    async def run_test(self, test_case: Dict[str, Any]) -> Dict[str, Any]:
        """Run a single test case"""
        result = {
            "test_id": test_case["utterance_id"],
            "user_message": test_case["user_message"],
            "expected_tool": test_case["expected_tool"],
            "expected_arguments": test_case["expected_arguments"],
            "actual_tool": None,
            "actual_arguments": None,
            "tool_correct": False,
            "arguments_correct": False,
            "overall_pass": False,
            "details": ""
        }
        
        try:
            # Get chatbot response
            response = await self.get_chatbot_response(test_case["user_message"])
            
            # Extract tool calls
            tool_calls = self.extract_tool_calls(response)
            
            if len(tool_calls) == 0:
                result["details"] = "No tool call detected"
            else:
                # Use first tool call
                actual_call = tool_calls[0]
                result["actual_tool"] = actual_call["tool"]
                result["actual_arguments"] = actual_call["arguments"]
                
                # Check tool correctness
                result["tool_correct"] = self.check_tool_correctness(
                    actual_call["tool"],
                    test_case["expected_tool"]
                )
                
                # Check arguments
                if result["tool_correct"]:
                    result["arguments_correct"] = self.check_arguments_correctness(
                        actual_call["arguments"],
                        test_case["expected_arguments"]
                    )
                
                # Overall pass
                result["overall_pass"] = result["tool_correct"] and result["arguments_correct"]
                
                if result["overall_pass"]:
                    result["details"] = "✅ PASS"
                else:
                    if not result["tool_correct"]:
                        result["details"] += f"Wrong tool (got {actual_call['tool']}). "
                    if not result["arguments_correct"]:
                        result["details"] += f"Arguments mismatch. "
        
        except Exception as e:
            result["details"] = f"ERROR: {str(e)}"
        
        return result
    
    async def run_all_tests(self, test_data: Dict[str, Any]) -> None:
        """Run all test cases"""
        # Collect all test cases
        all_tests = []
        
        test_categories = [
            ("crm_tool_utterances", "CRM"),
            ("weather_tool_utterances", "Weather"),
            ("budget_tool_utterances", "Budget"),
            ("flights_tool_utterances", "Flights"),
            ("hotels_tool_utterances", "Hotels"),
        ]
        
        for key, category in test_categories:
            for test_case in test_data.get(key, []):
                test_case["category"] = category
                all_tests.append(test_case)
        
        # Run tests
        self.results["total_tests"] = len(all_tests)
        
        for i, test_case in enumerate(all_tests, 1):
            print(f"Running test {i}/{len(all_tests)}: {test_case['utterance_id']}")
            
            result = await self.run_test(test_case)
            self.results["test_details"].append(result)
            
            category = test_case.get("category", "unknown")
            self.results["by_category"][category]["total"] += 1
            
            if result["overall_pass"]:
                self.results["passed"] += 1
                self.results["by_category"][category]["passed"] += 1
            else:
                self.results["failed"] += 1
                self.results["by_category"][category]["failed"] += 1
    
    def run_false_positive_tests(self, test_data: Dict[str, Any]) -> None:
        """Check for false positive tool calls (this would need LLM integration)"""
        false_positive_tests = test_data.get("false_positive_tests", [])
        
        results = []
        for test in false_positive_tests:
            results.append({
                "test_id": test["utterance_id"],
                "user_message": test["user_message"],
                "should_call_tool": test["should_call_tool"],
                "note": f"Avoid {test['incorrect_tool']} call: {test['criteria']}"
            })
        
        return results
    
    def generate_report(self, test_data: Dict[str, Any]) -> Dict[str, Any]:
        """Generate comprehensive report"""
        report = {
            "title": "LLM Tool Invocation Accuracy Report",
            "timestamp": self.results["timestamp"],
            "summary": {
                "total_tests": self.results["total_tests"],
                "passed": self.results["passed"],
                "failed": self.results["failed"],
                "pass_rate": f"{(self.results['passed'] / self.results['total_tests'] * 100):.1f}%" if self.results["total_tests"] > 0 else "0%",
            },
            "by_category": {},
            "failures": [],
            "false_positive_tests": self.run_false_positive_tests(test_data),
            "recommendations": []
        }
        
        # Add category results
        for category, stats in self.results["by_category"].items():
            pass_rate = (stats["passed"] / stats["total"] * 100) if stats["total"] > 0 else 0
            report["by_category"][category] = {
                "total": stats["total"],
                "passed": stats["passed"],
                "failed": stats["failed"],
                "pass_rate": f"{pass_rate:.1f}%"
            }
        
        # Add failures
        for test in self.results["test_details"]:
            if not test["overall_pass"]:
                report["failures"].append({
                    "test_id": test["test_id"],
                    "user_message": test["user_message"],
                    "expected": {
                        "tool": test["expected_tool"],
                        "arguments": test["expected_arguments"]
                    },
                    "actual": {
                        "tool": test["actual_tool"],
                        "arguments": test["actual_arguments"]
                    },
                    "issue": test["details"]
                })
        
        # Add recommendations based on results
        if report["summary"]["pass_rate"] < "80%":
            report["recommendations"].append(
                "Tool invocation accuracy is below 80%. Consider improving LLM prompt with clearer tool definitions."
            )
        
        if len(report["failures"]) > 5:
            failing_tools = defaultdict(int)
            for failure in report["failures"]:
                failing_tools[failure["expected"]["tool"]] += 1
            
            for tool, count in failing_tools.items():
                if count > 2:
                    report["recommendations"].append(
                        f"Tool '{tool}' is failing frequently. Review its schema and examples in the prompt."
                    )
        
        return report


async def main():
    """Main test runner"""
    print("="*60)
    print("LLM Tool Invocation Accuracy Tester")
    print("="*60)
    
    # Load test data
    if not os.path.exists(TEST_DATA_PATH):
        print(f"Test data not found at {TEST_DATA_PATH}")
        return
    
    with open(TEST_DATA_PATH, 'r') as f:
        test_data = json.load(f)
    
    # Create tester
    tester = LLMToolInvocationTester()
    
    # Check if WebSocket is available
    try:
        async with websockets.connect(WS_URL, ping_interval=None) as ws:
            await ws.recv()
            print(f"✅ Connected to chatbot at {WS_URL}")
    except Exception as e:
        print(f"❌ Cannot connect to chatbot: {e}")
        print("Make sure the chatbot WebSocket server is running")
        print("Example: python app_voice.py")
        return
    
    # Run tests (limited to first 5 for demo)
    print(f"\nRunning {min(5, len(test_data['crm_tool_utterances']))} sample tests...")
    
    sample_tests = test_data["crm_tool_utterances"][:5]
    for test in sample_tests:
        result = await tester.run_test(test)
        tester.results["total_tests"] += 1
        if result["overall_pass"]:
            tester.results["passed"] += 1
            print(f"  ✅ {result['test_id']}")
        else:
            tester.results["failed"] += 1
            print(f"  ❌ {result['test_id']}: {result['details']}")
        tester.results["test_details"].append(result)
    
    # Generate report
    report = tester.generate_report(test_data)
    
    # Save report
    os.makedirs(os.path.dirname(REPORT_PATH), exist_ok=True)
    with open(REPORT_PATH, 'w') as f:
        json.dump(report, f, indent=2)
    
    print(f"\n{'='*60}")
    print(f"Test Results:")
    print(f"  Total: {tester.results['total_tests']}")
    print(f"  Passed: {tester.results['passed']}")
    print(f"  Failed: {tester.results['failed']}")
    print(f"  Pass Rate: {report['summary']['pass_rate']}")
    print(f"\nReport saved to: {REPORT_PATH}")
    print(f"{'='*60}\n")


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n\nTest interrupted")
