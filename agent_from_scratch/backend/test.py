from llm_wrapper import LLMWrapper
from dotenv import load_dotenv
from openai import OpenAI
import os 
_ = load_dotenv()

api_key = os.getenv("OPENAI_API_KEY")
model = os.getenv("OPENAI_MODEL", "gpt-4.1-mini")
base_url = os.getenv("OPENAI_BASE_URL", None)
client = OpenAI(api_key=api_key, base_url=base_url)

response = client.chat.completions.create(
    model=model,
    messages=[
        {
            "role": "user",
            "content": "Who are you?"
        }
    ]
)

print(response.choices[0].message.content)