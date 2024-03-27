from fastapi import FastAPI, HTTPException, Depends, status
from pydantic import BaseModel, EmailStr
from typing import List, Optional
from uuid import uuid4
from cachetools import TTLCache
from datetime import datetime, timedelta
from views import user_views


fake_db = {
    "users": {},
    "posts": [],
    "cache": TTLCache(maxsize=100, ttl=300)  # Cache for storing user posts
}

app = FastAPI()


# Authentication dependency
def authenticate_user(token: str):
    if token not in fake_db["users"]:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token")
    return token


# Dependency to get the current user's token
def get_current_user(token: str = Depends(authenticate_user)):
    return token


# Endpoint to signup a new user
@app.post("/signup", response_model=Token)
def signup(user: User):
    if user.email in fake_db["users"]:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Email already registered")
    fake_db["users"][user.email] = user.password
    return {"token": user.email}  # Using email as token


# Endpoint to login an existing user and get a token
@app.post("/login", response_model=Token)
def login(user: User):
    stored_password = fake_db["users"].get(user.email)
    if not stored_password or stored_password != user.password:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid email or password")
    return {"token": user.email}  # Using email as token


# Endpoint to add a new post, authenticated with token and request validation
@app.post("/addPost", response_model=str)
def add_post(post_data: AddPostInput, token: str = Depends(get_current_user)):
    if len(post_data.text.encode('utf-8')) > 1024*1024:
        raise HTTPException(status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE, detail="Payload too large")

    post_id = str(uuid4())
    post = Post(post_id=post_id, email=token, text=post_data.text, created_at=datetime.now())
    fake_db["posts"].append(post)
    return post_id


# Endpoint to get all posts, authenticated with token and response caching
@app.get("/getPosts", response_model=GetPostsOutput)
def get_posts(token: str = Depends(get_current_user)):
    if token not in fake_db["cache"]:
        user_posts = [post for post in fake_db["posts"] if post.email == token]
        fake_db["cache"][token] = GetPostsOutput(posts=user_posts)
    return fake_db["cache"][token]


# Endpoint to delete a post, authenticated with token
@app.delete("/deletePost", response_model=None)
def delete_post(post_id: str, token: str = Depends(get_current_user)):
    post = next((p for p in fake_db["posts"] if p.post_id == post_id and p.email == token), None)
    if not post:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Post not found")
    fake_db["posts"].remove(post)
    return None


# Include routers from different views
app.include_router(user_views.router, prefix="/users", tags=["users"])
