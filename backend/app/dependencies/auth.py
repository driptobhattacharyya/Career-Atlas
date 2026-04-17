from fastapi import Depends, HTTPException
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from jose import jwt, JWTError
import httpx
from app.config import settings

security = HTTPBearer()

def verify_token(credentials: HTTPAuthorizationCredentials = Depends(security)):
    """
    Validates the JWT token coming from the frontend (which signed in via InsForge).
    """
    token = credentials.credentials
    try:
        # Use Insforge JWT secret to verify
        payload = jwt.decode(
            token, 
            settings.insforge_jwt_secret, 
            algorithms=["HS256"], 
            audience="authenticated"
        )
        # return user identifier (UUID)
        return payload.get("sub")
    except JWTError:
        raise HTTPException(status_code=401, detail="Invalid or expired token")

def get_current_user_id(user_id: str = Depends(verify_token)) -> str:
    return user_id
