import streamlit as st
import threading
import time
import os
from dotenv import load_dotenv
from streamlit_autorefresh import st_autorefresh

import sys
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
from app.agents.adk_agent import VisionADKAgent
from app.state.firestore import FireStoreClient
from app.state.intervention import store

load_dotenv()

# Global to hold the background thread purely to prevent GC
_agent_thread = None

def run_agent_in_background(url: str, goal: str, headless: bool):
    import asyncio
    import sys
    
    # Playwright requires the ProactorEventLoop on Windows to use subprocesses
    if sys.platform == 'win32':
        asyncio.set_event_loop_policy(asyncio.WindowsProactorEventLoopPolicy())
        
    # Set a new event loop for this specific background thread
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    
    try:
        agent = VisionADKAgent(
            api_key=os.getenv("GEMINI_API_KEY"),
            headless=headless
        )
        agent.run(url=url, goal=goal)
    except Exception as e:
        print(f"Agent crashed: {e}")

def render():
    st.markdown("<h1 class='main-header'>Agent Control Panel</h1>", unsafe_allow_html=True)
    st.write("Launch a new autonomous reasoning session.")

    with st.container():
        st.markdown("<div class='step-card'>", unsafe_allow_html=True)
        col1, col2 = st.columns([3, 1])
        with col1:
            url = st.text_input("Target URL", placeholder="https://www.example.com")
            goal = st.text_input("Agent Goal", placeholder="Navigate to the contact page and extract the email.")
            show_browser = st.checkbox("Show Browser Engine (Disable Headless)", value=True)
        with col2:
            st.write("")
            st.write("")
            run_btn = st.button("🚀 Run Agent", type="primary")
        st.markdown("</div>", unsafe_allow_html=True)

    # State tracking
    if "current_live_session" not in st.session_state:
        st.session_state.current_live_session = None

    if run_btn and url and goal:
        # Give firestore a second to register the session create via the agent thread
        st.session_state.current_live_session = "loading"
        
        global _agent_thread
        _agent_thread = threading.Thread(target=run_agent_in_background, args=(url, goal, not show_browser), daemon=True)
        _agent_thread.start()

        # Wait briefly for session to be registered in Firestore
        time.sleep(2)

        # Get latest session
        firestore = FireStoreClient()
        latest = firestore.get_sessions(limit=1)
        if latest:
            st.session_state.current_live_session = latest[0]["id"]
        else:
            st.error("Failed to initialize session in Firestore.")
            st.session_state.current_live_session = None

    # Live Viewer
    if st.session_state.current_live_session and st.session_state.current_live_session != "loading":
        st.markdown("### Live Execution Monitor")
        session_id = st.session_state.current_live_session
        
        # Polling mechanism 
        firestore = FireStoreClient()
        
        # Placeholder for auto-refresh
        live_container = st.empty()
        
        # We use a simple while loop with st.rerun() or direct renders
        # to fake a live socket.
        with live_container.container():
            steps = firestore.get_session_steps(session_id)
            
            if not steps:
                st.info("Agent is initializing... Waiting for first step.")
            else:
                # Check for active interventions first!
                if session_id in store.requests:
                    question = store.requests[session_id]
                    st.warning(f"⚠️ **AGENT REQUIRES INPUT:** {question}")
                    
                    with st.form(key=f"intervention_form_{session_id}"):
                        user_answer = st.text_input("Your Response:")
                        submit_answer = st.form_submit_button("Provide to Agent")
                        
                        if submit_answer and user_answer:
                            store.responses[session_id] = user_answer
                            if session_id in store.events:
                                store.events[session_id].set() # Wake up parent thread!
                            st.rerun()

                for step in steps:
                    st.markdown("<div class='step-card'>", unsafe_allow_html=True)
                    st.markdown(f"**Step {step.get('step_number', '?')}** - Action: `{step.get('action', 'Unknown')}`")
                    
                    args = step.get('arguments', {})
                    if args:
                        st.write(f"Parameters: {args}")
                        
                    res = step.get("result", "")
                    if res:
                        with st.expander("Model Reasoning / Output"):
                            st.text(res)
                            
                    screenshot = step.get("screenshot")
                    if screenshot:
                        st.image(screenshot, use_container_width=True)
                        
                    st.markdown(f"<small>Time: {step.get('timestamp', 'N/A')}</small>", unsafe_allow_html=True)
                    st.markdown("</div>", unsafe_allow_html=True)
            
            # Auto-Refresh to maintain the live stream
            # The agent background thread creates Firestore steps; we ping to retrieve them.
            # We don't want to refresh endlessly if it's over, but we assume the agent finishes quickly.
            st_autorefresh(interval=2000, limit=200, key="agent_live_feed")
            
            col1, col2 = st.columns(2)
            with col1:
                if st.button("🛑 Stop Monitoring"):
                    st.session_state.current_live_session = None
                    st.rerun()
