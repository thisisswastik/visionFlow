import threading
from typing import Dict, Any

class AgentInterventionStore:
    """ 
    A thread-safe singleton to sync data between the Streamlit main thread 
    and the asynchronous agent background execution thread. 
    """
    _instance = None
    _lock = threading.Lock()

    def __new__(cls):
        with cls._lock:
            if cls._instance is None:
                cls._instance = super(AgentInterventionStore, cls).__new__(cls)
                cls._instance.requests: Dict[str, str] = {}
                cls._instance.responses: Dict[str, str] = {}
                cls._instance.events: Dict[str, threading.Event] = {}
        return cls._instance

store = AgentInterventionStore()
