from fastapi import Depends, HTTPException
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from jose import jwt, JWTError
import httpx
from app.config import settings

security = HTTPBearer(auto_error=False)

def verify_token(credentials: HTTPAuthorizationCredentials = Depends(security)):
    """
    Validates the JWT token coming from the frontend (which signed in via InsForge).
    """
    if not credentials:
        return None
    token = credentials.credentials
    try:
        # Determine algorithm and key
        # If the key looks like a public key, use ES256, otherwise HS256
        key = settings.supabase_jwt_public_key or settings.supabase_jwt_secret
        algorithm = "ES256" if "PUBLIC KEY" in key or "BEGIN" in key else "HS256"
        
        payload = jwt.decode(
            token, 
            key, 
            algorithms=[algorithm], 
            audience="authenticated"
        )
        # return user identifier (UUID)
        return payload.get("sub")
    except JWTError:
        return None

def get_current_user_id(user_id: str = Depends(verify_token)) -> str:
    return user_id
