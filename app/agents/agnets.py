# app/agents/agent.py

from app.executor.browser import BrowserExecutor
from app.ai.gemini_client import GeminiClient
from app.schemas import AgentResponse, ActionType
import time
from app.telemetry.phoenix import tracer
from app.state.firestore import FireStoreClient
from app.storage.cloudinary_uploader import CloudinaryUploader



class VisionAgent:
    def __init__(self, api_key: str, headless: bool = False):
        self.browser = BrowserExecutor(headless=headless)
        self.gemini = GeminiClient(api_key=api_key)
        self.max_steps = 10
        self.firestore = FireStoreClient()
        self.image_uploader = CloudinaryUploader()

    def run(self, url: str, goal: str):
        print("Opening URL...")
        self.browser.open(url)

        previous_actions = []
        session_id = self.firestore.create_session(goal, url)

        for step in range(1, self.max_steps + 1):
            print(f"\n===== STEP {step} =====")

            with tracer.start_as_current_span("agent_step") as span:
                span.set_attribute("goal", goal)
                span.set_attribute("step", step)

                screenshot_path = f"screenshots/step_{step}.png"
                self.browser.screenshot(screenshot_path)

                image_url = self.image_uploader.upload_image(screenshot_path)

                print("Analyzing screenshot...")
                response: AgentResponse = self.gemini.reason(
                    image_path=image_url,
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
                with tracer.start_as_current_span("tool_call") as tool_span:
                    tool_span.set_attribute("tool_name", str(action.action_type.value))
                    args_dict = {"target": action.target_description}
                    if action.text:
                        args_dict["text"] = action.text
                    tool_span.set_attribute("args", str(args_dict))

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

                self.firestore.log_step(
                    session_id=session_id,
                    step_number=step,
                    action=action.action_type.value,
                    arguments={"target": action.target_description, "text": action.text},
                    screenshot=image_url,
                    result=str(response)
                )

        else:
            print("⚠️ Max steps reached. Stopping to prevent infinite loop.")

        print("Closing browser.")
        self.browser.close()
        self.firestore.end_session(session_id)
