import unittest
import sys
from pathlib import Path
from unittest.mock import MagicMock

sys.path.insert(0, str(Path(__file__).parent.parent / "backend"))

from agent import Agent
from llm_wrapper import SimpleContent, SimplePart

class HistoryTests(unittest.TestCase):
    def setUp(self):
        self.mock_client = MagicMock()
        # Mock reconstruct_content behavior
        def mock_reconstruct(data):
            return SimpleContent(role=data["role"], parts=[SimplePart(text=p.get("text")) for p in data["parts"]])
        
        self.mock_client.reconstruct_content.side_effect = mock_reconstruct
        self.mock_client.create_system_content.side_effect = lambda t: SimpleContent(role="system", parts=[SimplePart(text=t)])
        self.mock_client.create_user_content.side_effect = lambda t: SimpleContent(role="user", parts=[SimplePart(text=t)])
        
        self.agent = Agent(system_prompt="You are a helpful assistant.", client=self.mock_client)

    def test_reconstruct_history(self):
        # Mock history data as it would come from the frontend
        history_data = [
            {
                "role": "user",
                "parts": [{"text": "Hello"}]
            },
            {
                "role": "model",
                "parts": [{"text": "Hi there!"}]
            }
        ]

        # Mock generate to return a simple response
        mock_response = MagicMock()
        mock_response.content = SimpleContent(role="model", parts=[SimplePart(text="I am good!")])
        mock_response.function_calls = []
        self.mock_client.generate.return_value = mock_response

        # Run the agent with history
        contents = list(self.agent.run(prompt="How are you?", history=history_data, max_steps=1))
        # Get final history from 'done' event
        final_history = next(e['history'] for e in contents if e['type'] == 'done')

        # Check that reconstruct_content was called for history items
        self.assertEqual(self.mock_client.reconstruct_content.call_count, 2)

        # Check that generate was called with the reconstructed history + system prompt + new prompt
        # contents[0] = system, contents[1] = user hello, contents[2] = model hi, contents[3] = user how are you, contents[4] = model good
        self.assertEqual(len(final_history), 5)
        self.assertEqual(final_history[0].role, "system")
        self.assertEqual(final_history[1].role, "user")
        self.assertEqual(final_history[1].parts[0].text, "Hello")
        self.assertEqual(final_history[2].role, "model")
        self.assertEqual(final_history[2].parts[0].text, "Hi there!")
        self.assertEqual(final_history[3].role, "user")
        self.assertEqual(final_history[3].parts[0].text, "How are you?")
    def test_skip_system_prompt_in_history(self):
        # Mock history that includes a system message (should be skipped)
        history_data = [
            {
                "role": "system",
                "parts": [{"text": "You are a helpful assistant."}]
            },
            {
                "role": "user",
                "parts": [{"text": "Hello"}]
            },
            {
                "role": "model",
                "parts": [{"text": "Hi!"}]
            }
        ]

        # Mock generate to return a simple response
        mock_response = MagicMock()
        mock_response.content = SimpleContent(role="model", parts=[SimplePart(text="How can I help?")])
        mock_response.function_calls = []
        self.mock_client.generate.return_value = mock_response

        # Run the agent with history containing system message
        contents = list(self.agent.run(prompt="What can you do?", history=history_data, max_steps=1))
        # Get final history from 'done' event
        final_history = next(e['history'] for e in contents if e['type'] == 'done')

        # System message from history should be skipped, only fresh system prompt added
        # contents[0] = system (fresh), contents[1] = user hello, contents[2] = model hi, contents[3] = user new, contents[4] = model response
        self.assertEqual(len(final_history), 5)
        self.assertEqual(final_history[0].role, "system")
        self.assertEqual(final_history[1].role, "user")
        self.assertEqual(final_history[1].parts[0].text, "Hello")
        self.assertEqual(final_history[2].role, "model")

        # Verify reconstruct_content was called only 2 times (user + model, NOT system)
        self.assertEqual(self.mock_client.reconstruct_content.call_count, 2)

if __name__ == "__main__":
    unittest.main()
