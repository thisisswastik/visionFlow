import streamlit as st
import os
import sys

sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
from app.state.firestore import FireStoreClient

def render():
    st.markdown("<h1 class='main-header'>Session Replay</h1>", unsafe_allow_html=True)
    
    session_id = st.session_state.get("selected_session_id")

    if not session_id:
        st.info("No session selected. Please go to the 'Session History' tab and select a run to replay.")
        return

    st.write(f"Replaying session: `{session_id}`")
    
    firestore = FireStoreClient()
    steps = firestore.get_session_steps(session_id)

    if not steps:
        st.warning("No steps recorded for this session yet.")
        return

    st.markdown("---")

    for step in steps:
        st.markdown("<div class='step-card'>", unsafe_allow_html=True)
        
        step_num = step.get('step_number', '?')
        action = step.get('action', 'Unknown')
        timestamp = step.get('timestamp', 'N/A')
        
        st.markdown(f"### Step {step_num}")
        
        col1, col2 = st.columns([1, 1])
        
        with col1:
            st.markdown(f"**Action Executed:** `{action}`")
            args = step.get('arguments', {})
            if args:
                st.json(args)
                
            res = step.get("result", "")
            if res:
                with st.expander("View Agent Output Pipeline"):
                    st.text(res)
                    
            st.markdown(f"<small>Timestamp: {timestamp}</small>", unsafe_allow_html=True)

        with col2:
            screenshot_url = step.get("screenshot")
            if screenshot_url:
                st.image(screenshot_url, caption=f"View at Step {step_num}", use_container_width=True)
            else:
                st.info("No screenshot captured for this step.")
                
        st.markdown("</div>", unsafe_allow_html=True)
