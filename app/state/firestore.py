# firestore session management 
import os
from google.cloud import firestore
from google.oauth2 import service_account
import uuid 
import time

BASE_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
KEY_PATH = os.path.join(BASE_DIR, "firestore_keys.json")
CERT_PATH = os.path.join(BASE_DIR, "system_certs.pem")

# Ensure gRPC can access Windows certificates (fix for corporate proxies/Zscaler)
if not os.environ.get('GRPC_DEFAULT_SSL_ROOTS_FILE_PATH'):
    try:
        if not os.path.exists(CERT_PATH):
            import ssl
            import certifi
            with open(CERT_PATH, 'w', encoding='utf-8') as f:
                with open(certifi.where(), 'r', encoding='utf-8') as certifi_f:
                    f.write(certifi_f.read() + '\n')
                for storename in ['CA', 'ROOT']:
                    for cert, encoding, trust in ssl.enum_certificates(storename):
                        if encoding == 'x509_asn':
                            import base64
                            f.write('-----BEGIN CERTIFICATE-----\n')
                            der_b64 = base64.b64encode(cert).decode('ascii')
                            for i in range(0, len(der_b64), 64):
                                f.write(der_b64[i:i+64] + '\n')
                            f.write('-----END CERTIFICATE-----\n')
    except Exception as e:
        print(f"Warning: Could not extract system certs: {e}")
    
    os.environ['GRPC_DEFAULT_SSL_ROOTS_FILE_PATH'] = CERT_PATH

class FireStoreClient:
    def __init__(self):
        if os.path.exists(KEY_PATH):
            credentials = service_account.Credentials.from_service_account_file(KEY_PATH)
            self.db = firestore.Client(credentials=credentials)
        else:
            # Fallback to Application Default Credentials
            self.db = firestore.Client()

    def create_session(self, goal: str, url: str):
        session_id = str(uuid.uuid4())
        session_data = {
            "goal":goal,
            "url":url,
            "start_time":time.time(),
            "status":"running"
        }
        self.db.collection("sessions").document(session_id).set(session_data)
        return session_id

    def log_step(self, session_id:str, step_number:int, action:str, arguments:dict, screenshot:str, result:str):
        step_data ={
            "step_number": step_number,
            "action":action,
            "arguments":arguments,
            "screenshot":screenshot,
            "result":result,
            "timestamp":time.time()
        }

        self.db.collection("sessions").document(session_id).collection("steps").add(step_data)
    
    def end_session(self, session_id:str):
        self.db.collection("sessions").document(session_id).update({
            "status":"completed",
            "end_time": time.time()
        })

        


    
