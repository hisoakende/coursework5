from pydantic import BaseModel, EmailStr, Field
from typing import Optional


class UserCreate(BaseModel):
    email: EmailStr
    password: str


class UserLogin(BaseModel):
    email: EmailStr
    password: str


class User(BaseModel):
    id: int
    email: EmailStr


class UserOut(BaseModel):
    user_id: int


class SubscriptionCreate(BaseModel):
    journal_id: int


class Subscription(BaseModel):
    id: int
    user_id: int
    journal_id: int


class PostCreate(BaseModel):
    journal_id: int
    text: str


class Post(BaseModel):
    id: int
    journal_id: int
    text: str
    user_id: int


class JournalCreate(BaseModel):
    name: str


class JournalUpdate(BaseModel):
    name: Optional[str] = Field(None, min_length=3, max_length=50)


class Journal(BaseModel):
    id: int
    name: str
    user_id: int


class JournalSearch(BaseModel):
    name: str


class AccessToken(BaseModel):
    access_token: str
    token_type: str
