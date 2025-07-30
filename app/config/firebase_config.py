import os
import firebase_admin
from firebase_admin import credentials, firestore, auth
from dotenv import load_dotenv

load_dotenv()

class FirebaseConfig:
    def __init__(self):
        self.project_id = os.getenv('PROJECT_ID')
        self.credentials_path = os.getenv('GOOGLE_APPLICATION_CREDENTIALS')
        self._initialize_firebase()
    
    def _initialize_firebase(self):
        """Initialize Firebase Admin SDK"""
        try:
            if not firebase_admin._apps:
                cred = credentials.Certificate(self.credentials_path)
                firebase_admin.initialize_app(cred, {
                    'projectId': self.project_id,
                })
            
            self.db = firestore.client()
            self.auth = auth
            print("✅ Firebase initialized successfully")
        except Exception as e:
            print(f"❌ Firebase initialization error: {e}")
            raise

# Global instance
firebase_config = FirebaseConfig()

# Export db and auth for direct import in other modules
db = firebase_config.db
auth_client = firebase_config.auth
