import os
from dotenv import load_dotenv
from anthropic import Anthropic

# Load environment variables
load_dotenv()

# Initialize Anthropic client
client = Anthropic(api_key=os.getenv("ANTHROPIC_API_KEY"))

# Test the connection
try:
    response = client.messages.create(
        model=os.getenv("CLAUDE_MODEL"),
        max_tokens=100,
        messages=[
            {"role": "user", "content": "Hello! Just testing the API connection. Please respond with 'API connection successful!'"}
        ]
    )
    print("✅ Success!")
    print("Response:", response.content[0].text)
except Exception as e:
    print("❌ Error:", str(e))