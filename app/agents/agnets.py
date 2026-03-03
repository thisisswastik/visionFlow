# app/agents/agent.py

from app.executor.browser import BrowserExecutor
from app.ai.gemini_client import GeminiClient
from app.schemas import AgentResponse, ActionType
import time


class VisionAgent:
    def __init__(self, api_key: str, headless: bool = False):
        self.browser = BrowserExecutor(headless=headless)
        self.gemini = GeminiClient(api_key=api_key)
        self.max_steps = 10

    def run(self, url: str, goal: str):
        print("Opening URL...")
        self.browser.open(url)

        previous_actions = []

        for step in range(1, self.max_steps + 1):
            print(f"\n===== STEP {step} =====")

            screenshot_path = f"screenshots/step_{step}.png"
            self.browser.screenshot(screenshot_path)

            print("Analyzing screenshot...")
            response: AgentResponse = self.gemini.reason(
                image_path=screenshot_path,
                goal=goal,
                step=step
            )

            print("Model Response:", response)

            # Goal completed check
            if response.goal_completed:
                print("✅ Goal completed.")
                break

            action = response.next_action

            if not action:
                print("⚠️ No action returned. Stopping.")
                break

            print(f"Executing action: {action.action_type} → {action.target_description}")

            # Loop guard: stop if same action repeats 3 times
            previous_actions.append((action.action_type, action.target_description))
            if len(previous_actions) >= 3 and \
               previous_actions[-1] == previous_actions[-2] == previous_actions[-3]:
                print("⚠️ Repeated same action 3 times. Breaking loop.")
                break

            # Execute action
            if action.action_type == ActionType.CLICK:
                self.browser.click_by_text(action.target_description)

            elif action.action_type == ActionType.TYPE:
                self.browser.type_by_placeholder(
                    action.target_description,
                    action.text
                )

            elif action.action_type == ActionType.SCROLL:
                self.browser.scroll()

            elif action.action_type == ActionType.WAIT:
                self.browser.wait(1)

            # Wait briefly for DOM update
            self.browser.page.wait_for_timeout(500)

            # Save after-action screenshot for debugging
            after_path = f"screenshots/after_click_{step}.png"
            self.browser.screenshot(after_path)

        else:
            print("⚠️ Max steps reached. Stopping to prevent infinite loop.")

        print("Closing browser.")
        self.browser.close()