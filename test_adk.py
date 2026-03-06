from dotenv import load_dotenv
import os
from app.agents.adk_agent import VisionADKAgent

load_dotenv()

agent = VisionADKAgent(
    api_key=os.getenv("GEMINI_API_KEY"),
    headless=False
)

agent.run(
    url="https://chatgpt.com/",
    goal="ask for capital of france"
)