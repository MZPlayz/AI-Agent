from typing import Dict, Any
from core.base_agent import BaseAgent
import datetime
import pytz

class PersonalAssistantAgent(BaseAgent):
    def __init__(self):
        super().__init__(
            name="personal_assistant",
            description="Manages schedules, reminders, emails, and basic queries"
        )
        self.schedule = {}
        self.reminders = {}

    async def process_message(self, message: str, context: Dict[str, Any]) -> str:
        """Process incoming messages and return appropriate responses"""
        try:
            user_id = str(context.get("user_id", "default"))
            memory = self.get_memory(user_id)
            
            # Add user message to memory
            memory.add_message("user", message)
            
            # Get conversation context
            conversation_context = memory.get_context()
            
            # Use the LLM to understand the intent and generate a response
            prompt = f"""You are a helpful AI assistant using Gemini 1.5 Flash. Please respond to the following message in a natural and helpful way.

Current message: {message}

Previous conversation context:
{conversation_context}

Consider the following aspects when responding:
1. If it's about scheduling, provide specific details about when and what is being scheduled
2. If it's about reminders, confirm what needs to be remembered and when
3. If it's a general query, provide a clear and concise answer
4. If it's about task management, explain how you'll help manage the task

Please provide a direct and helpful response that addresses the user's needs. Keep responses concise but informative."""
            
            print(f"Processing message for user {user_id}: {message}")
            response = await self._generate_with_fallback(prompt, conversation_context)
            
            # Only save successful responses to memory
            if not response.startswith("I apologize"):
                memory.add_message("assistant", response)
                print(f"Successfully processed message and saved to memory")
            
            return response
            
        except Exception as e:
            print(f"Error in personal assistant: {str(e)}")
            return "I'm having trouble understanding your request. Could you please rephrase it or try again?"

    async def handle_task(self, task: Dict[str, Any]) -> Dict[str, Any]:
        """Handle specific tasks assigned to this agent"""
        task_type = task.get("type")
        
        if task_type == "schedule":
            return await self._handle_scheduling(task)
        elif task_type == "reminder":
            return await self._handle_reminder(task)
        else:
            return {"status": "error", "message": f"Unknown task type: {task_type}"}

    async def _handle_scheduling(self, task: Dict[str, Any]) -> Dict[str, Any]:
        """Handle scheduling tasks"""
        event = task.get("event")
        time = task.get("time")
        
        if not event or not time:
            return {"status": "error", "message": "Missing event or time information"}
        
        self.schedule[time] = event
        return {"status": "success", "message": f"Scheduled: {event} at {time}"}

    async def _handle_reminder(self, task: Dict[str, Any]) -> Dict[str, Any]:
        """Handle reminder tasks"""
        reminder = task.get("reminder")
        time = task.get("time")
        
        if not reminder or not time:
            return {"status": "error", "message": "Missing reminder or time information"}
        
        self.reminders[time] = reminder
        return {"status": "success", "message": f"Set reminder: {reminder} for {time}"}

    def _get_specific_capabilities(self) -> Dict[str, Any]:
        """Return specific capabilities of this agent"""
        return {
            "keywords": ["schedule", "reminder", "calendar", "appointment", "meeting"],
            "capabilities": [
                "Schedule management",
                "Reminder setting",
                "Calendar integration",
                "Basic task management",
                "Conversation memory"
            ]
        } 