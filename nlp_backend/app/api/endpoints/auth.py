from fastapi import APIRouter, HTTPException, Depends
from fastapi.security import OAuth2PasswordRequestForm
from datetime import timedelta
from ...core.config import ACCESS_TOKEN_EXPIRE_MINUTES
from ...core.security import verify_password, get_password_hash, create_access_token
from ...db.database import get_user, create_user
from ...schemas.user import UserRegister, Token

router = APIRouter()

@router.post("/register")
async def register(user: UserRegister):
    try:
        if len(user.password.encode("utf-8")) > 72:
            raise HTTPException(status_code=400, detail="Password too long (max 72 characters)")

        existing = get_user(user.username)
        if existing:
            raise HTTPException(status_code=400, detail="Account already exists")
        
        existing_email = get_user(user.email)
        if existing_email:
            raise HTTPException(status_code=400, detail="Account already exists")
        
        hashed_password = get_password_hash(user.password)
        success = create_user(user.username, user.email, hashed_password)
        if not success:
            raise HTTPException(status_code=500, detail="Could not create user in database")
        
        return {"message": "User registered successfully"}
    except HTTPException as he:
        raise he
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/login", response_model=Token)
async def login(form_data: OAuth2PasswordRequestForm = Depends()):
    user = get_user(form_data.username)
    if not user or not verify_password(form_data.password, user["password_hash"]):
        raise HTTPException(status_code=401, detail="Incorrect username or password")
    
    access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        data={"sub": user["username"]}, expires_delta=access_token_expires
    )
    return {"access_token": access_token, "token_type": "bearer", "username": user["username"]}
