from app.ai.gemini_client import GeminiClient
from dotenv import load_dotenv
import os

load_dotenv()

client = GeminiClient(api_key=os.getenv("GEMINI_API_KEY"))

result = client.reason(
    image_path="screenshots/afterlogin.png",
    goal="Click the Login button",
    step=1
)

print(result)


