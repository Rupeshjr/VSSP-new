import os
import json
import firebase_admin
from firebase_admin import credentials, firestore, auth
from dotenv import load_dotenv

# Load .env for local development
load_dotenv()

class FirebaseConfig:
    def __init__(self):
        self._initialize_firebase()

    def _initialize_firebase(self):
        """Initialize Firebase Admin SDK"""
        try:
            if not firebase_admin._apps:
                firebase_json = os.getenv("FIREBASE_CREDENTIALS_JSON")

                if not firebase_json:
                    raise ValueError("FIREBASE_CREDENTIALS_JSON environment variable is missing")

                firebase_dict = json.loads(firebase_json)
                cred = credentials.Certificate(firebase_dict)

                firebase_admin.initialize_app(cred, {
                    'projectId': firebase_dict.get("project_id")
                })

            self.db = firestore.client()
            self.auth = auth
            print("✅ Firebase initialized successfully")

        except Exception as e:
            print(f"❌ Firebase initialization error: {e}")
            raise

# Global instance
firebase_config = FirebaseConfig()

# Export db and auth for use in other modules
db = firebase_config.db
auth_client = firebase_config.auth
