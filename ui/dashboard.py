import streamlit as st
from components import agent_control, session_list, session_viewer

st.set_page_config(
    page_title="VisionFlow Dashboard",
    page_icon="🤖",
    layout="wide",
)

# Custom CSS for modern dark styling
st.markdown("""
    <style>
    .stApp {
        background-color: #0E1117;
        color: #FAFAFA;
    }
    .main-header {
        font-family: 'Inter', sans-serif;
        color: #60A5FA;
        font-weight: 700;
        margin-bottom: 20px;
    }
    .status-running {
        color: #34D399; /* Green */
        font-weight: bold;
    }
    .status-completed {
        color: #60A5FA; /* Blue */
        font-weight: bold;
    }
    .step-card {
        background-color: #1E293B;
        color: #F8FAFC;
        padding: 20px;
        border-radius: 12px;
        box-shadow: 0 4px 6px rgba(0,0,0,0.3);
        margin-bottom: 20px;
        border: 1px solid #334155;
    }
    .step-card h3 {
        color: #93C5FD;
    }
    </style>
""", unsafe_allow_html=True)

def main():
    st.sidebar.title("🤖 VisionFlow")
    st.sidebar.markdown("---")
    
    # Simple navigation routing
    page = st.sidebar.radio("Navigation", ["Agent Control", "Session History", "Session Replay"])
    
    st.sidebar.markdown("---")
    st.sidebar.info("VisionFlow uses Gemini Vision to autonomously interact with modern web applications.")

    # Initialize common session state tracking
    if "selected_session_id" not in st.session_state:
        st.session_state.selected_session_id = None

    if page == "Agent Control":
        agent_control.render()
    elif page == "Session History":
        session_list.render()
    elif page == "Session Replay":
        session_viewer.render()

if __name__ == "__main__":
    main()
