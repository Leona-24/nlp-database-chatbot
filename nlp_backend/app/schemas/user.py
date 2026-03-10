from pydantic import BaseModel

class UserBase(BaseModel):
    username: str
    email: str

class UserRegister(UserBase):
    password: str

class User(UserBase):
    id: int
    password_hash: str

    class Config:
        from_attributes = True

class Token(BaseModel):
    access_token: str
    token_type: str
    username: str
