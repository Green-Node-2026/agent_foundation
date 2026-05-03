from pydantic import BaseModel, Field, create_model
from .calculator import calculator
from .weather import get_weather_by_city


def register_tools(agent):
    """Register all available tools with the agent"""

    # Tool 1: Calculator
    CalculatorInput = create_model(
        'CalculatorInput',
        expression=(str, Field(..., description="A math expression such as '2+2' or '(15*3)/5'"))
    )

    @agent.toolCall(args_schema=CalculatorInput)
    def calculate(expression: str) -> dict:
        """Calculate a basic math expression."""
        try:
            result = str(calculator(expression))
            return {"expression": expression, "result": result}
        except Exception as e:
            return {"expression": expression, "result": str(e)}

    # Tool 2: Weather
    WeatherInput = create_model(
        'WeatherInput',
        location=(str, Field(..., description="City name like 'Hanoi', 'Ho Chi Minh', 'Saigon', 'HCM'"))
    )

    @agent.toolCall(args_schema=WeatherInput)
    def get_weather(location: str) -> dict:
        """Get current weather for a location.

        Common aliases:
        - HCM, Ho Chi Minh, Saigon → Ho Chi Minh City
        - HN, Hanoi → Hanoi
        - DN, Danang → Da Nang

        If the user gives an abbreviation or nickname, expand it to the full city name.
        """
        return get_weather_by_city(location)
    