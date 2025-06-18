from fastapi import FastAPI, HTTPException, Depends, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from datetime import datetime, timedelta
from typing import List, Optional
import jwt
from passlib.context import CryptContext
from models import UserCreate, User, ChatMessage, DailyProgress
from mongodb import MongoDB
from chatbot import FitnessChatbot
import os
from dotenv import load_dotenv

load_dotenv()

app = FastAPI(title="Fitness AI Assistant")

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Security
SECRET_KEY = os.getenv("SECRET_KEY", "your-secret-key")
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 30

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")

# Initialize chatbot
chatbot = FitnessChatbot()

# Startup and shutdown events
@app.on_event("startup")
async def startup_db_client():
    await MongoDB.connect_to_database()

@app.on_event("shutdown")
async def shutdown_db_client():
    await MongoDB.close_database_connection()

# Helper functions
def create_access_token(data: dict):
    to_encode = data.copy()
    expire = datetime.utcnow() + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt

async def get_current_user(token: str = Depends(oauth2_scheme)):
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        user_id: str = payload.get("sub")
        if user_id is None:
            raise HTTPException(status_code=401, detail="Invalid authentication credentials")
    except jwt.JWTError:
        raise HTTPException(status_code=401, detail="Invalid authentication credentials")
    
    user = await MongoDB.get_user(user_id)
    if user is None:
        raise HTTPException(status_code=401, detail="User not found")
    return user

# Authentication endpoints
@app.post("/token")
async def login(form_data: OAuth2PasswordRequestForm = Depends()):
    user = await MongoDB.get_user_by_email(form_data.username)
    if not user or not pwd_context.verify(form_data.password, user["password"]):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    access_token = create_access_token(data={"sub": str(user["_id"])})
    return {"access_token": access_token, "token_type": "bearer"}

@app.post("/users/", response_model=User)
async def create_user(user: UserCreate):
    # Check if user already exists
    existing_user = await MongoDB.get_user_by_email(user.email)
    if existing_user:
        raise HTTPException(status_code=400, detail="Email already registered")
    
    # Hash password
    hashed_password = pwd_context.hash(user.password)
    user_data = user.dict()
    user_data["password"] = hashed_password
    user_data["created_at"] = datetime.utcnow()
    user_data["last_login"] = datetime.utcnow()
    
    user_id = await MongoDB.create_user(user_data)
    return await MongoDB.get_user(user_id)

# Chat endpoints
@app.post("/chat/{user_id}")
async def chat_with_ai(user_id: str, message: str, current_user: User = Depends(get_current_user)):
    if str(current_user["_id"]) != user_id:
        raise HTTPException(status_code=403, detail="Not authorized to chat as this user")
    
    response = await chatbot.generate_response(user_id, message)
    return {"response": response}

@app.get("/chat/history/{user_id}")
async def get_chat_history(user_id: str, limit: int = 50, current_user: User = Depends(get_current_user)):
    if str(current_user["_id"]) != user_id:
        raise HTTPException(status_code=403, detail="Not authorized to view this user's chat history")
    
    history = await MongoDB.get_user_chat_history(user_id, limit)
    return history

# Progress tracking endpoints
@app.post("/progress/{user_id}")
async def add_daily_progress(user_id: str, progress: DailyProgress, current_user: User = Depends(get_current_user)):
    if str(current_user["_id"]) != user_id:
        raise HTTPException(status_code=403, detail="Not authorized to add progress for this user")
    
    progress_id = await MongoDB.save_daily_progress(user_id, progress.dict())
    return {"id": progress_id}

@app.get("/progress/{user_id}")
async def get_progress(user_id: str, start_date: datetime, end_date: datetime, current_user: User = Depends(get_current_user)):
    if str(current_user["_id"]) != user_id:
        raise HTTPException(status_code=403, detail="Not authorized to view this user's progress")
    
    progress = await MongoDB.get_user_progress(user_id, start_date, end_date)
    return progress

# Plan generation endpoints
@app.post("/workout-plan/{user_id}")
async def generate_workout_plan(user_id: str, current_user: User = Depends(get_current_user)):
    if str(current_user["_id"]) != user_id:
        raise HTTPException(status_code=403, detail="Not authorized to generate plan for this user")
    
    plan = await chatbot.generate_workout_plan(user_id)
    if not plan:
        raise HTTPException(status_code=500, detail="Failed to generate workout plan")
    return plan

@app.post("/diet-plan/{user_id}")
async def generate_diet_plan(user_id: str, current_user: User = Depends(get_current_user)):
    if str(current_user["_id"]) != user_id:
        raise HTTPException(status_code=403, detail="Not authorized to generate plan for this user")
    
    plan = await chatbot.generate_diet_plan(user_id)
    if not plan:
        raise HTTPException(status_code=500, detail="Failed to generate diet plan")
    return plan

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
