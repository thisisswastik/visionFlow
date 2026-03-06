# VisionFlow

VisionFlow is a Python-based multimodal browser agent that autonomously interacts with real-world dynamic websites. It leverages **Google Gemini Vision** for reasoning and **Playwright** for robust browser automation.

By combining visual understanding with programmatic browser control, VisionFlow can accomplish tasks on complex web applications that use dynamic rendering, consent modals, and obscured elements (e.g., ChatGPT, Amazon).

## Features

- **Multimodal Reasoning:** Uses `gemini-2.5-flash` to visually analyze the state of the web page and determine the next logical action.
- **Robust DOM Grounding:** Intelligently locates target elements using multiple fallback locators (Placeholders, ARIA labels, Roles, internal names, and strict text).
- **Auto-Dismiss Overlays:** Automatically detects and clears common cookie banners and consent frameworks ("Accept All", "Continue", etc.) before interacting.
- **JavaScript Fallbacks & Retries:** Bypasses strict Playwright visibility constraints using native JavaScript `.evaluate()` clicks and typing injections, complete with auto-retry and scroll-safety logic.
- **Observability:** 
  - Trace logs uploaded to **Arize Phoenix**.
  - Step logs and session history stored in **Google Cloud Firestore**.
  - Visual debug screenshots uploaded to **Cloudinary**.

## Prerequisites

- Python 3.10+
- [Git](https://git-scm.com/)
- API Keys for Google Gemini, Cloudinary, and Firestore

## Installation

1. Clone the repository:
   ```bash
   git clone https://github.com/thisisswastik/visionFlow.git
   cd visionFlow
   ```

2. Create a virtual environment and install dependencies:
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: .\venv\Scripts\activate
   pip install -r requirements.txt
   playwright install chromium
   ```

3. Set up environment variables. Create a `.env` file in the root directory:
   ```env
   GEMINI_API_KEY=your_gemini_api_key
   CLOUDINARY_URL=your_cloudinary_url
   FIRESTORE_PROJECT_ID=your_firestore_project_id
   ```
   *(Ensure your `firestore_keys.json` is appropriately placed and scoped)*

## Usage

The system features a complete Streamlit dashboard to control and monitor the agent. Run the dashboard using:

```bash
streamlit run ui/dashboard.py
```

This will launch a local web server (typically on `http://localhost:8501`) where you can:
1. Input target URLs and logical goals.
2. Watch a real-time feed of the agent's actions, reasons, and screenshots.
3. Browse and step through complete historical interactions via the Replay tab.

## Docker

A `Dockerfile` is provided for isolated execution, leveraging the official Playwright image to ensure all OS-level browser dependencies are met.

```bash
docker build -t visionflow .
docker run --env-file .env visionflow
```

## Architecture

- **`BrowserExecutor` (`app/executor/browser.py`):** The core wrapper around Playwright handling robust page interactions, modality bypassing, and screenshot capture.
- **`VisionADKAgent` (`app/agents/adk_agent.py`):** Integrates with the Google ADK, providing the system prompt and tool definitions (`click_button`, `type_text`, `finish`).
- **`GeminiClient` (`app/ai/gemini_client.py`):** Interacts natively with the Gemini API for visual reasoning.
