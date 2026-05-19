from fastapi import Depends, HTTPException
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from jose import jwt, JWTError
import httpx
from app.config import settings

security = HTTPBearer(auto_error=False)

def verify_token(credentials: HTTPAuthorizationCredentials = Depends(security)):
    """
    Validates the JWT token coming from the frontend (which signed in via Supabase).
    """
    if not credentials:
        return None
    token = credentials.credentials
    try:
        # Prefer asymmetric verification only when a real PEM public key is configured.
        # Otherwise, fall back to shared-secret verification.
        has_pem_public_key = "BEGIN" in (settings.supabase_jwt_public_key or "")
        if has_pem_public_key:
            key = settings.supabase_jwt_public_key
            algorithm = "ES256"
        else:
            key = settings.supabase_jwt_secret
            algorithm = "HS256"
        if not key:
            return None
        
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
    if user_id:
        return user_id
    if settings.dev_bypass_auth and settings.dev_user_id:
        return settings.dev_user_id
    return user_id
