"""
Firebase Authentication Service

Handles Firebase token verification and user management for Google Sign-In.
"""

try:
    import firebase_admin
    from firebase_admin import credentials, auth
    FIREBASE_AVAILABLE = True
except ImportError:
    FIREBASE_AVAILABLE = False
    firebase_admin = None
    credentials = None
    auth = None

from typing import Optional, Dict, Any
from fastapi import HTTPException
from datetime import datetime
from app.models.user import User
from app.config import settings
import json
import os

class FirebaseService:
    """Service for Firebase authentication operations."""
    
    def __init__(self):
        self._app = None
        self._initialize_firebase()
    
    def _initialize_firebase(self):
        """Initialize Firebase Admin SDK."""
        if not FIREBASE_AVAILABLE:
            print("Firebase Admin SDK not installed - Google auth disabled")
            return
            
        try:
            # Check if already initialized
            if not firebase_admin._apps:
                # Try to get Firebase config from environment variables
                firebase_config = self._get_firebase_config()
                
                if firebase_config:
                    # Initialize with service account or config
                    cred = credentials.Certificate(firebase_config)
                    self._app = firebase_admin.initialize_app(cred)
                    print("Firebase Admin SDK initialized successfully")
                else:
                    print("Firebase config not found - Google auth disabled")
            else:
                self._app = firebase_admin.get_app()
                print("Firebase Admin SDK already initialized")
                
        except Exception as e:
            print(f"Firebase initialization failed: {e}")
            self._app = None
    
    def _get_firebase_config(self) -> Optional[str]:
        """Get Firebase configuration from environment or file."""
        
        # Method 1: Environment variable with JSON content
        firebase_json = os.getenv('FIREBASE_SERVICE_ACCOUNT_JSON')
        if firebase_json:
            try:
                # Save to temp file and return path
                import tempfile
                with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
                    json.dump(json.loads(firebase_json), f)
                    return f.name
            except Exception as e:
                print(f"Failed to parse FIREBASE_SERVICE_ACCOUNT_JSON: {e}")
        
        # Method 2: File path from environment
        firebase_path = os.getenv('FIREBASE_SERVICE_ACCOUNT_PATH')
        if firebase_path and os.path.exists(firebase_path):
            return firebase_path
        
        # Method 3: Default file location
        default_path = os.path.join(os.path.dirname(__file__), '..', '..', 'firebase-service-account.json')
        if os.path.exists(default_path):
            return default_path
        
        return None
    
    async def verify_id_token(self, id_token: str) -> Optional[Dict[str, Any]]:
        """Verify Firebase ID token and return decoded user info."""
        if not FIREBASE_AVAILABLE:
            raise HTTPException(
                status_code=503,
                detail="Firebase authentication not available - install firebase-admin"
            )
        
        if not self._app:
            raise HTTPException(
                status_code=503,
                detail="Firebase authentication not available - check configuration"
            )
        
        try:
            # Verify the ID token
            decoded_token = auth.verify_id_token(id_token)
            return decoded_token
        except auth.ExpiredIdTokenError:
            raise HTTPException(
                status_code=401,
                detail="ID token has expired"
            )
        except auth.InvalidIdTokenError:
            raise HTTPException(
                status_code=401,
                detail="Invalid ID token"
            )
        except Exception as e:
            print(f"Token verification error: {e}")
            raise HTTPException(
                status_code=401,
                detail="Token verification failed"
            )
    
    async def create_or_update_user(self, firebase_user: Dict[str, Any], user_info: Dict[str, Any]) -> User:
        """Create or update user from Firebase authentication."""
        
        if not FIREBASE_AVAILABLE:
            raise HTTPException(
                status_code=503,
                detail="Firebase authentication not available - install firebase-admin"
            )
        
        email = firebase_user.get('email')
        firebase_uid = firebase_user.get('uid')
        
        if not email:
            raise HTTPException(
                status_code=400,
                detail="Email is required from Firebase user"
            )
        
        # Check if user exists by Firebase UID
        existing_user = await User.find_one(User.firebase_uid == firebase_uid)
        
        if existing_user:
            # Update existing user
            existing_user.email = email
            existing_user.firebase_uid = firebase_uid
            existing_user.auth_provider = 'google'
            existing_user.last_login = datetime.utcnow()
            
            # Update profile if provided
            if user_info.get('displayName'):
                existing_user.username = user_info['displayName']
            if user_info.get('photoURL'):
                existing_user.avatar_url = user_info['photoURL']
            
            existing_user.email_verified = firebase_user.get('email_verified', False)
            await existing_user.save()
            
            print(f"Updated existing user: {email}")
            return existing_user
        
        # Check if user exists by email (merge accounts)
        existing_email_user = await User.find_one(User.email == email)
        
        if existing_email_user:
            # Link Firebase to existing email account
            existing_email_user.firebase_uid = firebase_uid
            existing_email_user.auth_provider = 'google'
            existing_email_user.last_login = datetime.utcnow()
            
            # Update profile if provided
            if user_info.get('displayName'):
                existing_email_user.username = user_info['displayName']
            if user_info.get('photoURL'):
                existing_email_user.avatar_url = user_info['photoURL']
            
            existing_email_user.email_verified = firebase_user.get('email_verified', False)
            await existing_email_user.save()
            
            print(f"Linked Firebase to existing user: {email}")
            return existing_email_user
        
        # Create new user
        new_user = User(
            email=email,
            username=user_info.get('displayName', email.split('@')[0]),
            firebase_uid=firebase_uid,
            auth_provider='google',
            avatar_url=user_info.get('photoURL'),
            email_verified=firebase_user.get('email_verified', False),
            is_active=True,
            last_login=datetime.utcnow()
        )
        
        await new_user.insert()
        print(f"Created new user from Firebase: {email}")
        return new_user

# Global Firebase service instance
firebase_service = FirebaseService()