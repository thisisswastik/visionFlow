import streamlit as st
import threading
import time
import os
from dotenv import load_dotenv

import sys
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
from app.agents.adk_agent import VisionADKAgent
from app.state.firestore import FireStoreClient

load_dotenv()

# Global to hold the background thread purely to prevent GC
_agent_thread = None

def run_agent_in_background(url: str, goal: str):
    try:
        agent = VisionADKAgent(
            api_key=os.getenv("GEMINI_API_KEY"),
            headless=True # Always headless in UI
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
        with col2:
            st.write("")
            st.write("")
            run_btn = st.button("🚀 Run Agent", use_container_width=True, type="primary")
        st.markdown("</div>", unsafe_allow_html=True)

    # State tracking
    if "current_live_session" not in st.session_state:
        st.session_state.current_live_session = None

    if run_btn and url and goal:
        # Give firestore a second to register the session create via the agent thread
        st.session_state.current_live_session = "loading"
        
        global _agent_thread
        _agent_thread = threading.Thread(target=run_agent_in_background, args=(url, goal), daemon=True)
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
            
            # Auto-Refresh if not completed
            # To actually auto-refresh streamit without a heavy loop, we use a button or st_autorefresh.
            # Here we just offer a manual refresh to keep it simple and stable, or use a short sleep/rerun loop.
            
            col1, col2 = st.columns(2)
            with col1:
                if st.button("🔄 Refresh Live Feed"):
                    st.rerun()
            with col2:
                if st.button("🛑 Stop Monitoring"):
                    st.session_state.current_live_session = None
                    st.rerun()
