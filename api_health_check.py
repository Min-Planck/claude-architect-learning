import os
from dotenv import load_dotenv
import anthropic

load_dotenv()
client = anthropic.Anthropic()

MODEL = os.environ.get("MODEL", "claude-haiku-4-5")
response = client.messages.create(
    model=MODEL, 
    max_tokens=100, 
    messages=[
        {"role": "user", "content": "Say Hello in 1 word."},
    ]
)

print(response)