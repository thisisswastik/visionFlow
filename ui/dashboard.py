import streamlit as st
from components import agent_control, session_list, session_viewer

st.set_page_config(
    page_title="VisionFlow Dashboard",
    page_icon="🤖",
    layout="wide",
)

# Custom CSS for modern styling
st.markdown("""
    <style>
    .stApp {
        background-color: #f7f9fc;
    }
    .main-header {
        font-family: 'Inter', sans-serif;
        color: #1E3A8A;
        font-weight: 700;
    }
    .status-running {
        color: #059669;
        font-weight: bold;
    }
    .status-completed {
        color: #2563EB;
        font-weight: bold;
    }
    .step-card {
        background: white;
        padding: 20px;
        border-radius: 10px;
        box-shadow: 0 4px 6px rgba(0,0,0,0.05);
        margin-bottom: 20px;
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
