from google.adk import Agent
from google.adk.runners import InMemoryRunner
from google.genai import types

from app.executor.browser import BrowserExecutor
from app.state.firestore import FireStoreClient
from app.agents.tools import (
    click_button,
    finish,
    type_text,
    scroll_page,
    extract_page_content,
    ask_customer_for_input
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
- You MUST only use the EXACT text or placeholder text visibly written on the CURRENT screenshot.
- DO NOT hallucinate, guess, or assume element names based on common UI patterns. For example, if a search bar says "Search Amazon.in", your target MUST be exactly "Search Amazon.in", not "Search" or "Search for products...".
- **EMPTY INPUT BOXES**: When using the `type_text` tool, your `target` argument MUST be the visible label or placeholder text INSIDE the empty box (e.g. "Email or phone"). NEVER set the `target` argument to the text you *want* to type (e.g. do not set target to "thisisswastik@gmail.com").
- Look closely at the provided image BEFORE deciding on the target text.
- Your target string MUST perfectly match the pixel-visible text shown on the screenshot.

STATE & NAVIGATION RULES:
- If you perform an action (like click_button) and the NEXT screenshot looks completely identical, DO NOT click the same button again. The action failed or the element is not functional.
- If you are stuck or need to see more content (like products below the fold), use `scroll_page`. This is highly critical on ecommerce websites.
- If you are trying to click the "Search" button but the page isn't navigating, try typing and hitting enter, or try clicking a different element. Do NOT endlessly loop clicking "Search".
- VERY IMPORTANT: NEVER call two `click_button` tools in the same step if the second click depends on the first one (for example, clicking a Sort button to open a dropdown, and then clicking the Low to High option in the dropdown). Playwright will immediately fail because the dropdown hasn't rendered yet. Execute the FIRST click, await the new screenshot, THEN execute the second click.
- Only call finish when you have visually verified the final results on the screen.
- NEVER call finish in the same step as click_button or type_text. Wait for the next screen screenshot to observe the effects of your action.
- Use `extract_page_content` ONLY if you need to fetch the raw textual DOM dump of the current screen to read massive amounts of pricing or text data that is hard to see.
- If you hit a Login screen or a prompt for a password / 2FA code, and you do not know the credentials, IMMEDIATELY call `ask_customer_for_input`. Wait for the user to provide the credentials. DO NOT guess credentials.
- **INTERVENTION RESPONSES**: When `ask_customer_for_input` returns the user's string (e.g., "my_username, my_password"), you MUST extract those exact values and use them as the `text` argument in your subsequent `type_text` tool calls. NEVER type "dummy_username" or fake data.
""",
            tools=[click_button, type_text, scroll_page, extract_page_content, ask_customer_for_input, finish],
        )

        # Proper runner setup
        self.runner = InMemoryRunner(
            agent=self.agent,
            app_name="vision_app",
        )

        # Enable automatic session creation
        self.runner.auto_create_session = True

    def run(self, url: str, goal: str, session_id: str):
        self.browser.open(url)

        user_id = "user_1"

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
                    enter_pressed = tool_args.get("enter", False)
                    self.browser.type_by_placeholder(tool_args.get("target"), tool_args.get("text"), enter=enter_pressed)
                    result = f"Typed into {tool_args.get('target')}" + (" and pressed Enter." if enter_pressed else ".")

                elif tool_name == "scroll_page":
                    self.browser.scroll()
                    result = "Scrolled page"

                elif tool_name == "ask_customer_for_input":
                    question = tool_args.get("question", "Input required:")
                    print(f"Pausing autonomous loop for user input: {question}")
                    
                    fs = FireStoreClient()
                    
                    # Create the intervention document
                    import datetime
                    intervention_ref = fs.db.collection('interventions').document(session_id)
                    intervention_ref.set({
                        "session_id": session_id,
                        "question": question,
                        "response": None,
                        "status": "pending",
                        "created_at": datetime.datetime.now(datetime.timezone.utc)
                    })
                    
                    # Sleep-poll until Streamlit UI writes the response into Firestore
                    import time
                    while True:
                        doc = intervention_ref.get()
                        if doc.exists:
                            data = doc.to_dict()
                            if data.get("status") == "resolved" and data.get("response"):
                                answer = data.get("response")
                                break
                        time.sleep(2) # Poll every 2 seconds
                        
                    result = f"User responded: {answer}"

                elif tool_name == "extract_page_content":
                    content = self.browser.extract_content()
                    result = f"Page content extracted: {content[:1500]}..." # Truncate to avoid context window explosion
                    print(f"Extracted content length: {len(content)}")

                elif tool_name == "finish":
                    return True

                else:
                    result = f"Unknown tool {tool_name}"



        return False