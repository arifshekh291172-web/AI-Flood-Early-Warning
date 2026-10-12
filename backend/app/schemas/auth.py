from typing import Optional
from pydantic import BaseModel, EmailStr

class LoginRequest(BaseModel):
    email: EmailStr
    password: str

class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    expires_in: int
    user_id: str
    email: str
    full_name: str
    role: str
    department: Optional[str] = None
    state_jurisdiction: Optional[str] = None

class UserProfile(BaseModel):
    id: str
    email: str
    full_name: str
    role: str
    phone: Optional[str] = None
    department: Optional[str] = None
    state_jurisdiction: Optional[str] = None
    is_active: bool
