from typing import Dict, List, Any
import json
import os
from datetime import datetime

class AgentMemory:
    def __init__(self, user_id: str):
        self.user_id = user_id
        self.memory_file = f"memory_{user_id}.json"
        self.conversation_history: List[Dict[str, Any]] = []
        self.load_memory()

    def load_memory(self):
        """Load conversation history from file"""
        if os.path.exists(self.memory_file):
            try:
                with open(self.memory_file, 'r') as f:
                    self.conversation_history = json.load(f)
            except json.JSONDecodeError:
                self.conversation_history = []

    def save_memory(self):
        """Save conversation history to file"""
        with open(self.memory_file, 'w') as f:
            json.dump(self.conversation_history, f)

    def add_message(self, role: str, content: str):
        """Add a message to the conversation history"""
        message = {
            "role": role,
            "content": content,
            "timestamp": datetime.now().isoformat()
        }
        self.conversation_history.append(message)
        self.save_memory()

    def get_recent_history(self, limit: int = 5) -> List[Dict[str, Any]]:
        """Get recent conversation history"""
        return self.conversation_history[-limit:]

    def get_context(self) -> str:
        """Get conversation context for the LLM"""
        recent_history = self.get_recent_history()
        context = "Previous conversation:\n"
        for msg in recent_history:
            context += f"{msg['role']}: {msg['content']}\n"
        return context

    def clear_memory(self):
        """Clear conversation history"""
        self.conversation_history = []
        self.save_memory() 