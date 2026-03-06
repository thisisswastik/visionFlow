from google.adk import Agent
from google.adk.runners import InMemoryRunner
from google.genai import types

from app.executor.browser import BrowserExecutor
from app.agents.tools import (
    click_button,
    finish,
    type_text,
    scroll_page,
)


import app.agents.tools as agent_tools

class VisionADKAgent:
    def __init__(self, api_key: str, headless: bool = False):
        self.browser = BrowserExecutor(headless=headless)
        agent_tools.browser_instance = self.browser

        self.agent = Agent(
            name="vision_ui_agent",
            model="gemini-2.5-flash",
            description="""
You are a strict UI automation agent.

CRITICAL RULES FOR TARGETING:
- You MUST only use the EXACT text or placeholder text visibly written on the screen.
- Do NOT hallucinate names like "Username" if the screen says "Email". 
- Do NOT guess button actions. If the button says "Login", the target MUST be "Login", NOT "Sign in".
- Your target string MUST perfectly match the pixel-visible text shown on the screenshot.

Rules for tools:
- Use click_button to click visible buttons.
- Use type_text to fill inputs.
- Use scroll_page if needed.
- Only call finish when you have visually verified the final results on the screen.
- NEVER call finish in the same step as click_button or type_text. Wait for the next screen screenshot to observe the effects of your action before deciding if the goal is complete.
""",
            tools=[click_button, type_text, scroll_page, finish],
        )

        # Proper runner setup
        self.runner = InMemoryRunner(
            agent=self.agent,
            app_name="vision_app",
        )

        # Enable automatic session creation
        self.runner.auto_create_session = True

    def run(self, url: str, goal: str):
        self.browser.open(url)

        user_id = "user_1"
        session_id = "vision_session"

        # Initial goal message
        events = self.runner.run(
            user_id=user_id,
            session_id=session_id,
            new_message=types.UserContent(
                parts=[types.Part(text=goal)]
            ),
        )

        self._process_events(events, user_id, session_id)

        for step in range(10):
            print(f"\n===== STEP {step+1} =====")

            screenshot_path = f"screenshots/adk_step_{step+1}.png"
            self.browser.screenshot(screenshot_path)

            with open(screenshot_path, "rb") as f:
                image_bytes = f.read()

            events = self.runner.run(
                user_id=user_id,
                session_id=session_id,
                new_message=types.UserContent(
                    parts=[
                        types.Part(text="Current screen:"),
                        types.Part(
                            inline_data=types.Blob(
                                mime_type="image/png",
                                data=image_bytes,
                            )
                        ),
                    ]
                ),
            )

            finished = self._process_events(events, user_id, session_id)

            if finished:
                print("✅ Goal completed.")
                if not self.browser.browser.contexts[0].pages[0].is_closed(): # Just check if browser is still active
                    print("Waiting for 15 seconds to let you view the results...")
                    import time
                    time.sleep(15)
                self.browser.close()
                return

        print("Waiting for 15 seconds to let you view the final state...")
        import time
        time.sleep(15)
        self.browser.close()

    def _process_events(self, events, user_id, session_id):
        """
        Handle ADK event stream.
        Execute tools.
        Send tool responses back to agent.
        """

        for event in events:
            function_calls = event.get_function_calls()

            if not function_calls:
                continue

            for call in function_calls:
                tool_name = call.name
                tool_args = call.args or {}

                print(f"🧠 Model decided to call tool:")
                print(f"Tool: {tool_name}")
                print(f"Arguments: {tool_args}\n")

                if tool_name == "click_button":
                    self.browser.click_by_text(tool_args.get("target"))
                    self.browser.page.wait_for_timeout(500)
                    result = f"Clicked {tool_args.get('target')}"

                elif tool_name == "type_text":
                    self.browser.type_by_placeholder(tool_args.get("target"), tool_args.get("text"))
                    result = f"Typed into {tool_args.get('target')}"

                elif tool_name == "scroll_page":
                    self.browser.scroll()
                    result = "Scrolled page"

                elif tool_name == "finish":
                    return True

                else:
                    result = f"Unknown tool {tool_name}"



        return False