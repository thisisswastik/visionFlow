import streamlit as st
import pandas as pd
from datetime import datetime

import os
import sys
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
from app.state.firestore import FireStoreClient

def render():
    st.markdown("<h1 class='main-header'>Session History</h1>", unsafe_allow_html=True)
    st.write("Browse past autonomous web interactions.")

    firestore = FireStoreClient()
    sessions = firestore.get_sessions(limit=50)

    if not sessions:
        st.info("No past sessions found. Run a task from the Agent Control panel to generate history.")
        return

    # Convert to dataframe for clean display
    df_data = []
    session_map = {} # Quick lookup to view click actions
    
    for s in sessions:
        start_ts = s.get("start_time", 0)
        if isinstance(start_ts, (int, float)):
            dt_repr = datetime.fromtimestamp(start_ts).strftime('%Y-%m-%d %H:%M:%S') if start_ts else "Unknown"
        elif hasattr(start_ts, 'strftime'):
            dt_repr = start_ts.strftime('%Y-%m-%d %H:%M:%S')
        else:
            dt_repr = str(start_ts)
        
        status = s.get("status", "unknown")
        
        df_data.append({
            "Session ID": s.get("id"),
            "Goal": s.get("goal"),
            "Target URL": s.get("url"),
            "Start Time": dt_repr,
            "Status": status
        })
        session_map[s.get("id")] = s

    df = pd.DataFrame(df_data)

    # We use a selectbox to pick a session for quick replay viewing, 
    # but Streamlit's st.dataframe doesn't have native click handlers easily. 
    # An alternative is standard iterating cards with buttons.
    
    selected = st.selectbox("Select a session to view details", options=["Select..."] + list(df['Session ID']))
    
    st.dataframe(
        df, 
        hide_index=True,
    )

    if selected and selected != "Select...":
        st.session_state.selected_session_id = selected
        st.success(f"Selected session {selected}. Navigate to 'Session Replay' to view steps.")
        if st.button("Jump to Replay"):
            st.session_state.force_page = "Session Replay"
            # Note: A real jump requires either multipage app structure or rerunning the radio button selection.
            # As a simple hack, users just click the sidebar manually after selection.
            st.rerun()
