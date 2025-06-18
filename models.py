from pydantic import BaseModel, Field
from typing import List, Optional
from datetime import datetime
from enum import Enum

class FitnessGoal(str, Enum):
    WEIGHT_LOSS = "weight_loss"
    MUSCLE_GAIN = "muscle_gain"
    ENDURANCE = "endurance"
    FLEXIBILITY = "flexibility"
    GENERAL_FITNESS = "general_fitness"

class UserBase(BaseModel):
    email: str
    name: str
    age: int
    weight: float
    height: float
    fitness_goals: List[FitnessGoal]
    medical_conditions: Optional[List[str]] = []
    injuries: Optional[List[str]] = []
    dietary_restrictions: Optional[List[str]] = []

class UserCreate(UserBase):
    password: str

class User(UserBase):
    id: str
    created_at: datetime
    last_login: datetime

class ChatMessage(BaseModel):
    role: str
    content: str
    timestamp: datetime = Field(default_factory=datetime.utcnow)

class DailyProgress(BaseModel):
    user_id: str
    date: datetime
    weight: Optional[float]
    calories_consumed: Optional[int]
    calories_burned: Optional[int]
    workout_duration: Optional[int]  # in minutes
    steps: Optional[int]
    water_intake: Optional[float]  # in liters
    sleep_hours: Optional[float]
    mood: Optional[str]
    notes: Optional[str]

class WorkoutPlan(BaseModel):
    user_id: str
    created_at: datetime
    exercises: List[dict]
    duration: int  # in minutes
    difficulty: str
    target_muscle_groups: List[str]
    equipment_needed: List[str]

class DietPlan(BaseModel):
    user_id: str
    created_at: datetime
    meals: List[dict]
    total_calories: int
    macros: dict  # protein, carbs, fats
    dietary_restrictions: List[str]
