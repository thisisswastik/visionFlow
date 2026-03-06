# gemini multimodal wrapper (NEW SDK)
import json
from google import genai
from PIL import Image
from app.schemas import AgentResponse
import re
from app.telemetry.phoenix import tracer
from openinference.semconv.trace import SpanAttributes, OpenInferenceSpanKindValues


class GeminiClient:
    def __init__(self, api_key: str, model_name: str = "gemini-2.5-pro"):
        self.client = genai.Client(api_key=api_key)
        self.model_name = model_name

    def reason(self, image_path: str, goal: str, step: int) -> AgentResponse:
        image = Image.open(image_path)

        prompt = f"""
You are an expert UI automation agent.

Your goal: {goal}
Current step: {step}

Analyze the screenshot and decide the next action.

Return STRICT JSON and ONLY JSON no marking such as :

{{
    "thought": "brief reasoning",
    "next_action": {{
        "action_type": "click|type|scroll|wait",
        "target_description": "description of target element",
        "text": "text to type if type action"
    }},
    "confidence": 0.0,
    "goal_completed": false
}}

STRICT RULE TO FOLLOW:
    When referring to UI elements,
    use the exact visible text on the screen.
    Do not add extra words like "button".

If goal is completed:
- set goal_completed = true
- set next_action = null

CRITICAL RULES:
1. If goal_completed is true, next_action MUST be null.
2. If goal_completed is false, next_action MUST be provided.
3. Never provide next_action when goal_completed is true.
4. Never mark goal_completed true before executing the final action.

If the screenshot shows evidence that the task is complete
(such as success message or confirmation),
set goal_completed to true and next_action to null.
"""

        with tracer.start_as_current_span(name="GeminiClient.reason") as span:
            span.set_attribute(SpanAttributes.OPENINFERENCE_SPAN_KIND, OpenInferenceSpanKindValues.LLM.value)
            span.set_attribute(SpanAttributes.LLM_MODEL_NAME, self.model_name)
            span.set_attribute(SpanAttributes.INPUT_VALUE, prompt)

            response = self.client.models.generate_content(
                model=self.model_name,
                contents=[prompt, image]
            )

            raw_text = response.text.strip()
            span.set_attribute(SpanAttributes.OUTPUT_VALUE, raw_text)

        print("=======RAW LLM RESPONSE===============")
        print(raw_text)
        print("=======END LLM RESPONSE===============")

        match = re.search(r"\{.*\}", raw_text, re.DOTALL)
        if not match:
            raise ValueError(f"No JSON object found in response:\n{raw_text}")
        
        json_str = match.group(0)
        try:
            parsed = json.loads(json_str)
        except json.JSONDecodeError as e:
            raise ValueError(f"Failed to parse JSON response: {e}\n\nRaw response:\n{raw_text}")

        return AgentResponse(**parsed)