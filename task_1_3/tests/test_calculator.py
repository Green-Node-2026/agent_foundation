import unittest

from calculator import calculator
from main import calculate


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
        self.assertEqual(
            calculate("4 + 99 / 5"),
            {"expression": "4 + 99 / 5", "result": "23.8"},
        )

    def test_tool_wrapper_returns_error_payload(self):
        self.assertEqual(
            calculate("5 / 0"),
            {"expression": "5 / 0", "result": "Division by zero"},
        )


if __name__ == "__main__":
    unittest.main()
