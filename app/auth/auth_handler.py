import os
from datetime import datetime, timedelta
from typing import Optional
from jose import JWTError, jwt
from passlib.context import CryptContext
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from firebase_admin import auth
from dotenv import load_dotenv

from .auth_models import User
from ..services.user_service import UserService

load_dotenv()

# Configuration
SECRET_KEY = os.getenv("SECRET_KEY", "your-secret-key-here")
ALGORITHM = os.getenv("ALGORITHM", "HS256")
ACCESS_TOKEN_EXPIRE_MINUTES = int(os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES", "30"))

# OAuth2 scheme
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="auth/login")

# Password hashing context (keeping for future use if needed)
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

class AuthHandler:
    def __init__(self):
        self.user_service = UserService()
    
    def verify_password(self, plain_password: str, hashed_password: str) -> bool:
        """Verify a password against its hash"""
        return pwd_context.verify(plain_password, hashed_password)
    
    def get_password_hash(self, password: str) -> str:
        """Hash a password"""
        return pwd_context.hash(password)
    
    async def create_firebase_user(self, email: str, password: str, full_name: str, role: str = "user"):
        """Create user in Firebase Auth and Firestore"""
        try:
            # Create user in Firebase Auth
            firebase_user = auth.create_user(
                email=email,
                password=password,
                display_name=full_name
            )
            
            # Create user document in Firestore with plain text password
            user_data = {
                "uid": firebase_user.uid,
                "email": email,
                "full_name": full_name,
                "role": role,
                "is_active": True,
                "created_at": datetime.utcnow(),
                "last_login": None,
                "passwd": password  # CHANGED: Store plain text password as 'passwd'
            }
            
            await self.user_service.create_user(firebase_user.uid, user_data)
            
            return firebase_user
            
        except Exception as e:
            print(f"Error creating Firebase user: {e}")
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Failed to create user: {str(e)}"
            )
    
    async def authenticate_user(self, email: str, password: str):
        """Authenticate user with plain text password comparison using 'passwd' field"""
        try:
            print(f"🔍 DEBUG: Attempting login for email: {email}")
            
            # Get user from Firestore first
            user_doc = await self.user_service.get_user_by_email(email)
            print(f"🔍 DEBUG: User found: {user_doc is not None}")
            
            if not user_doc:
                print("❌ DEBUG: No user document found")
                return False
            
            print(f"🔍 DEBUG: User doc keys: {list(user_doc.keys())}")
            
            # CRITICAL DEBUG: Check what email was actually found vs what was searched
            found_email = user_doc.get('email', 'NO_EMAIL')
            document_id = user_doc.get('uid', 'NO_UID')
            
            print(f"🔍 DEBUG: SEARCHED EMAIL: '{email}'")
            print(f"🔍 DEBUG: FOUND EMAIL: '{found_email}'")
            print(f"🔍 DEBUG: DOCUMENT ID: '{document_id}'")
            print(f"🔍 DEBUG: EMAIL MATCH: {email == found_email}")
            
            # Get the password for this specific document
            stored_password = user_doc.get('passwd')
            print(f"🔍 DEBUG: Password from document {document_id}: '{stored_password}'")
            
            if not stored_password:
                print("❌ DEBUG: No 'passwd' field found")
                print(f"🔍 DEBUG: Available fields: {list(user_doc.keys())}")
                return False
            
            print(f"🔍 DEBUG: Comparing passwords - Input length: {len(password)}, Stored length: {len(stored_password)}")
            print(f"🔍 DEBUG: Input password: '{password}'")
            print(f"🔍 DEBUG: Stored password: '{stored_password}'")
            
            # Simple string comparison for plain text passwords
            if password != stored_password:
                print("❌ DEBUG: Passwords do not match")
                return False
            
            print("✅ DEBUG: Passwords match, user authenticated successfully")
            
            # Prepare user data for User model
            user_data_for_model = {
                "uid": user_doc.get('uid', ''),
                "email": user_doc.get('email', '').strip('"'),  # Remove quotes from email
                "full_name": user_doc.get('name', ''),  # Using 'name' field from your document structure
                "role": user_doc.get('role', ['user'])[0] if isinstance(user_doc.get('role'), list) else user_doc.get('role', 'user'),
                "is_active": True,  # Assuming active if found
                "created_at": user_doc.get('createdOn') if user_doc.get('createdOn') and user_doc.get('createdOn') != '' else None,
                "last_login": user_doc.get('modifiedOn') if user_doc.get('modifiedOn') and user_doc.get('modifiedOn') != '' else None,
            }
            
            print(f"🔍 DEBUG: User data prepared: {user_data_for_model}")
            
            # Update last login
            await self.user_service.update_last_login(user_doc['uid'])
            
            return User(**user_data_for_model)
            
        except Exception as e:
            print(f"❌ DEBUG: Authentication error: {e}")
            import traceback
            traceback.print_exc()
            return False
    
    def create_access_token(self, data: dict, expires_delta: Optional[timedelta] = None):
        """Create JWT access token"""
        to_encode = data.copy()
        if expires_delta:
            expire = datetime.utcnow() + expires_delta
        else:
            expire = datetime.utcnow() + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
        
        to_encode.update({"exp": expire})
        encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
        return encoded_jwt
    
    async def get_current_user(self, token: str = Depends(oauth2_scheme)):
        """Get current user from JWT token"""
        credentials_exception = HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Could not validate credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )
        
        try:
            payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
            uid: str = payload.get("sub")
            if uid is None:
                raise credentials_exception
        except JWTError:
            raise credentials_exception
        
        user = await self.user_service.get_user_by_uid(uid)
        if user is None:
            raise credentials_exception
        
        # Prepare user data for User model
        user_data_for_model = {
            "uid": user.get('uid', ''),
            "email": user.get('email', '').strip('"'),  # Remove quotes from email
            "full_name": user.get('name', ''),  # Using 'name' field
            "role": user.get('role', ['user'])[0] if isinstance(user.get('role'), list) else user.get('role', 'user'),
            "is_active": True,
            "created_at": user.get('createdOn') if user.get('createdOn') and user.get('createdOn') != '' else None,
            "last_login": user.get('modifiedOn') if user.get('modifiedOn') and user.get('modifiedOn') != '' else None
        }
        
        return User(**user_data_for_model)
    
    async def get_current_active_user(self, current_user: User = Depends(get_current_user)):
        """Get current active user"""
        if not current_user.is_active:
            raise HTTPException(status_code=400, detail="Inactive user")
        return current_user

# Global instance
auth_handler = AuthHandler()

# Dependency functions
async def get_current_user(token: str = Depends(oauth2_scheme)):
    return await auth_handler.get_current_user(token)

async def get_current_active_user(current_user: User = Depends(get_current_user)):
    return await auth_handler.get_current_active_user(current_user)
