# testing the firestore 
from google.cloud import firestore
from google.oauth2 import service_account

credentials = service_account.Credentials.from_service_account_file('firestore_keys.json')
db = firestore.Client(credentials=credentials)

doc_ref = db.collection("sessions").document("python_test")

doc_ref.set({
    "goal":"test connection",
    "status":"running"
})

print("Firestore connected")
