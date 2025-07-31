import os
import json
import firebase_admin
from firebase_admin import credentials, firestore, auth
from dotenv import load_dotenv

load_dotenv()

class FirebaseConfig:
    def __init__(self):
        self.project_id = os.getenv('PROJECT_ID')

        # Build the credentials dictionary dynamically from environment variables
        self.credentials_dict = {
            "type": os.getenv("TYPE"),
            "project_id": self.project_id,
            "private_key_id": os.getenv("PRIVATE_KEY_ID"),
            # Replace literal \n in private_key with actual newlines
            "private_key": os.getenv("PRIVATE_KEY").replace("\\n", "\n"),
            "client_email": os.getenv("CLIENT_EMAIL"),
            "client_id": os.getenv("CLIENT_ID"),
            "auth_uri": os.getenv("AUTH_URI"),
            "token_uri": os.getenv("TOKEN_URI"),
            "auth_provider_x509_cert_url": os.getenv("AUTH_PROVIDER_X509_CERT_URL"),
            "client_x509_cert_url": os.getenv("CLIENT_X509_CERT_URL"),
            "universe_domain": os.getenv("UNIVERSE_DOMAIN"),
        }
        self._initialize_firebase()

    def _initialize_firebase(self):
        """Initialize Firebase Admin SDK"""
        try:
            if not firebase_admin._apps:
                cred = credentials.Certificate(self.credentials_dict)
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
