import unittest
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent / "backend"))

from tools.calculator import calculator
from agent import Agent
from llm_wrapper import LLMWrapper


def get_calculate_function():
    """Helper to get the calculate function from registry"""
    class MockClient:
        def create_system_content(self, prompt): pass
        def create_user_content(self, prompt): pass
        def create_tool_response_content(self, parts): pass
        def create_tool_response_part(self, call, response): pass
        def generate(self, contents, tool_definitions): pass

    agent = Agent(system_prompt="", client=MockClient())

    from tools.registry import register_tools
    register_tools(agent)

    return agent.tool_registry["calculate"]


class CalculatorTests(unittest.TestCase):
    def test_happy_case_addition_and_division(self):
        self.assertEqual(calculator("4 + 99 / 5"), 23.8)

    def test_happy_case_parentheses(self):
        self.assertEqual(calculator("(15 * 3) / 5"), 9.0)

    def test_whitespace_is_ignored(self):
        self.assertEqual(calculator(" 2 + 3 * 4 "), 14.0)

    def test_invalid_character_raises_value_error(self):
        with self.assertRaisesRegex(ValueError, "Invalid character"):
            calculator("2 + a")

    def test_invalid_number_raises_value_error(self):
        with self.assertRaisesRegex(ValueError, "Invalid number"):
            calculator(".")

    def test_division_by_zero_raises_zero_division_error(self):
        with self.assertRaisesRegex(ZeroDivisionError, "Division by zero"):
            calculator("5 / 0")

    def test_unmatched_parenthesis_raises_value_error(self):
        with self.assertRaisesRegex(ValueError, "Expected TokenType.RPAREN"):
            calculator("(2 + 3")

    def test_tool_wrapper_returns_result_payload(self):
        calculate = get_calculate_function()
        self.assertEqual(
            calculate("4 + 99 / 5"),
            {"expression": "4 + 99 / 5", "result": "23.8"},
        )

    def test_tool_wrapper_returns_error_payload(self):
        calculate = get_calculate_function()
        self.assertEqual(
            calculate("5 / 0"),
            {"expression": "5 / 0", "result": "Division by zero"},
        )


if __name__ == "__main__":
    unittest.main()
