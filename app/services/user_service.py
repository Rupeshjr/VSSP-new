from typing import Optional, Dict, Any
from datetime import datetime
from ..config.firebase_config import firebase_config
from google.cloud.firestore_v1 import FieldFilter



class UserService:
    def __init__(self):
        self.db = firebase_config.db
        self.users_collection = self.db.collection('userroles')  # or your actual collection name
    
    async def create_user(self, uid: str, user_data: Dict[str, Any]) -> bool:
        """Create user document in Firestore"""
        try:
            self.users_collection.document(uid).set(user_data)
            return True
        except Exception as e:
            print(f"Error creating user document: {e}")
            return False
    
    async def get_user_by_uid(self, uid: str) -> Optional[Dict[str, Any]]:
        """Get user by UID"""
        try:
            doc = self.users_collection.document(uid).get()
            if doc.exists:
                return doc.to_dict()
            return None
        except Exception as e:
            print(f"Error getting user by UID: {e}")
            return None
    
    async def get_user_by_email(self, email: str) -> Optional[Dict[str, Any]]:
        """Get user by email - searches direct email field with proper matching"""
        try:
            print(f"🔍 DEBUG: Searching for email: '{email}'")
            print(f"🔍 DEBUG: Collection path: {self.users_collection._path}")
            
            # Clean the search email
            clean_search_email = email.strip().strip('"').strip("'")
            print(f"🔍 DEBUG: Clean search email: '{clean_search_email}'")
            
            # Try direct Firestore query first
            query = self.users_collection.where(filter=FieldFilter('field_name', '==', 'value'))
            docs = list(query.stream())
            
            if docs:
                print(f"✅ DEBUG: Found by direct query")
                user_data = docs[0].to_dict()
                user_data['uid'] = docs[0].id
                print(f"🔍 DEBUG: Direct query - Doc ID: {docs[0].id}")
                print(f"🔍 DEBUG: Direct query - Email: '{user_data.get('email')}'")
                print(f"🔍 DEBUG: Direct query - Password: '{user_data.get('passwd')}'")
                return user_data
            
            # Manual search as fallback
            print(f"🔍 DEBUG: Direct query failed, trying manual search...")
            all_docs = list(self.users_collection.stream())
            print(f"🔍 DEBUG: Total documents to check: {len(all_docs)}")
            
            for i, doc in enumerate(all_docs):
                doc_data = doc.to_dict()
                doc_email = doc_data.get('email', '')
                doc_password = doc_data.get('passwd', 'NO_PASSWD')
                
                # Clean the document email
                clean_doc_email = doc_email.strip().strip('"').strip("'") if doc_email else ''
                
                print(f"🔍 DEBUG: Doc {i+1}/{len(all_docs)} - ID: {doc.id}")
                print(f"🔍 DEBUG: Raw doc email: '{doc_email}'")
                print(f"🔍 DEBUG: Clean doc email: '{clean_doc_email}'")  
                print(f"🔍 DEBUG: Doc password: '{doc_password}'")
                print(f"🔍 DEBUG: Email comparison: '{clean_search_email}' == '{clean_doc_email}' = {clean_search_email == clean_doc_email}")
                
                # Check for exact match
                if clean_search_email == clean_doc_email and clean_doc_email != '':
                    print(f"✅ DEBUG: EXACT MATCH FOUND - Doc ID: {doc.id}")
                    print(f"✅ DEBUG: Returning password: '{doc_password}'")
                    doc_data['uid'] = doc.id
                    return doc_data
                
                # Stop after checking first 5 docs for debugging (remove this later)
                if i >= 200:
                    print(f"🔍 DEBUG: Checked first 5 docs, stopping for debug...")
                    break
            
            print(f"❌ DEBUG: No match found for email: '{email}'")
            return None
            
        except Exception as e:
            print(f"❌ DEBUG: Exception in get_user_by_email: {e}")
            import traceback
            traceback.print_exc()
            return None

    async def update_last_login(self, uid: str) -> bool:
        """Update user's last login timestamp"""
        try:
            self.users_collection.document(uid).update({
                'last_login': datetime.utcnow()
            })
            return True
        except Exception as e:
            print(f"Error updating last login: {e}")
            return False
    
    async def update_user(self, uid: str, update_data: Dict[str, Any]) -> bool:
        """Update user document"""
        try:
            self.users_collection.document(uid).update(update_data)
            return True
        except Exception as e:
            print(f"Error updating user: {e}")
            return False
