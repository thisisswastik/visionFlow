from dotenv import load_dotenv
import os
from app.agents.agnets import VisionAgent

load_dotenv()

agent = VisionAgent(
    api_key=os.getenv("GEMINI_API_KEY"),
    headless=False
)

agent.run(
    url="file:///C:/Users/swastik/Desktop/visionFlow/demo.html",
    goal="Complete the login process"
)
