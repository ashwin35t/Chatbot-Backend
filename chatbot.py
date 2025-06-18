import openai
from datetime import datetime, timedelta
import os
from dotenv import load_dotenv
from typing import List, Dict
from models import ChatMessage, User, DailyProgress
from mongodb import MongoDB

load_dotenv()

openai.api_key = os.getenv("OPENAI_API_KEY")

class FitnessChatbot:
    def __init__(self):
        self.system_prompt = """You are an AI fitness and nutrition coach. Your role is to:
        1. Provide personalized workout and diet plans based on user goals and constraints
        2. Consider user's medical conditions, injuries, and dietary restrictions
        3. Track and analyze user progress
        4. Provide motivation and guidance
        5. Answer fitness and nutrition related questions
        Always prioritize user safety and health."""

    async def _get_user_context(self, user_id: str) -> str:
        """Get user's recent progress and chat history for context"""
        user = await MongoDB.get_user(user_id)
        if not user:
            return ""

        # Get last 7 days of progress
        end_date = datetime.utcnow()
        start_date = end_date - timedelta(days=7)
        progress = await MongoDB.get_user_progress(user_id, start_date, end_date)
        
        # Get recent chat history
        chat_history = await MongoDB.get_user_chat_history(user_id, limit=10)
        
        context = f"User Profile:\n"
        context += f"Name: {user['name']}\n"
        context += f"Age: {user['age']}\n"
        context += f"Goals: {', '.join(user['fitness_goals'])}\n"
        if user['medical_conditions']:
            context += f"Medical Conditions: {', '.join(user['medical_conditions'])}\n"
        if user['injuries']:
            context += f"Injuries: {', '.join(user['injuries'])}\n"
        if user['dietary_restrictions']:
            context += f"Dietary Restrictions: {', '.join(user['dietary_restrictions'])}\n"
        
        if progress:
            context += "\nRecent Progress:\n"
            for p in progress:
                context += f"Date: {p['date']}\n"
                if p.get('weight'): context += f"Weight: {p['weight']}kg\n"
                if p.get('workout_duration'): context += f"Workout: {p['workout_duration']} minutes\n"
                if p.get('calories_consumed'): context += f"Calories: {p['calories_consumed']}\n"
        
        return context

    async def generate_response(self, user_id: str, user_message: str) -> str:
        """Generate a response using OpenAI API with user context"""
        context = await self._get_user_context(user_id)
        
        messages = [
            {"role": "system", "content": self.system_prompt},
            {"role": "system", "content": f"User Context:\n{context}"},
            {"role": "user", "content": user_message}
        ]

        try:
            response = await openai.ChatCompletion.acreate(
                model="gpt-4",
                messages=messages,
                temperature=0.7,
                max_tokens=500
            )
            
            # Save the conversation
            await MongoDB.save_chat_message(user_id, {
                "role": "user",
                "content": user_message
            })
            
            assistant_message = response.choices[0].message.content
            await MongoDB.save_chat_message(user_id, {
                "role": "assistant",
                "content": assistant_message
            })
            
            return assistant_message
            
        except Exception as e:
            print(f"Error generating response: {str(e)}")
            return "I apologize, but I'm having trouble processing your request right now. Please try again later."

    async def generate_workout_plan(self, user_id: str) -> Dict:
        """Generate a personalized workout plan"""
        context = await self._get_user_context(user_id)
        
        messages = [
            {"role": "system", "content": self.system_prompt},
            {"role": "system", "content": f"User Context:\n{context}"},
            {"role": "user", "content": "Please generate a detailed workout plan for me."}
        ]

        try:
            response = await openai.ChatCompletion.acreate(
                model="gpt-4",
                messages=messages,
                temperature=0.7,
                max_tokens=1000
            )
            
            # Parse the response and structure it as a workout plan
            # This is a simplified version - you might want to add more structure
            workout_plan = {
                "user_id": user_id,
                "created_at": datetime.utcnow(),
                "plan": response.choices[0].message.content
            }
            
            return workout_plan
            
        except Exception as e:
            print(f"Error generating workout plan: {str(e)}")
            return None

    async def generate_diet_plan(self, user_id: str) -> Dict:
        """Generate a personalized diet plan"""
        context = await self._get_user_context(user_id)
        
        messages = [
            {"role": "system", "content": self.system_prompt},
            {"role": "system", "content": f"User Context:\n{context}"},
            {"role": "user", "content": "Please generate a detailed diet plan for me."}
        ]

        try:
            response = await openai.ChatCompletion.acreate(
                model="gpt-4",
                messages=messages,
                temperature=0.7,
                max_tokens=1000
            )
            
            # Parse the response and structure it as a diet plan
            diet_plan = {
                "user_id": user_id,
                "created_at": datetime.utcnow(),
                "plan": response.choices[0].message.content
            }
            
            return diet_plan
            
        except Exception as e:
            print(f"Error generating diet plan: {str(e)}")
            return None
