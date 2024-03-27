from fastapi import FastAPI, HTTPException, Depends
from sqlalchemy.orm import Session
from . import models

app = FastAPI()


# Dependency to get the database session
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


# Endpoint to create a new user
@app.post("/users/", response_model=models.User)
def create_user(user: models.UserCreate, db: Session = Depends(get_db)):
    db_user = models.User(email=user.email, password=user.password)
    db.add(db_user)
    db.commit()
    db.refresh(db_user)
    return db_user
