from abc import ABC, abstractmethod
import google.generativeai as genai
from typing import Dict, Any, Optional, List
import os
from dotenv import load_dotenv
from .memory import AgentMemory

class BaseAgent(ABC):
    def __init__(self, name: str, description: str):
        self.name = name
        self.description = description
        self.llm = None
        self.current_token_index = 0
        self.llm_tokens = self._load_llm_tokens()
        self.initialize_llm()
        self.memories: Dict[str, AgentMemory] = {}

    def _load_llm_tokens(self) -> List[str]:
        """Load all available LLM tokens from environment variables"""
        load_dotenv()
        tokens = []
        # Look for tokens in the format GOOGLE_API_KEY_1, GOOGLE_API_KEY_2, etc.
        i = 1
        while True:
            token = os.getenv(f'GOOGLE_API_KEY_{i}')
            if not token:
                break
            tokens.append(token)
            i += 1
        
        # Also check for the default GOOGLE_API_KEY
        default_token = os.getenv('GOOGLE_API_KEY')
        if default_token and default_token not in tokens:
            tokens.append(default_token)
        
        if not tokens:
            raise ValueError("No LLM tokens found in environment variables")
        
        return tokens

    def _get_next_token(self) -> str:
        """Get the next available token in a round-robin fashion"""
        token = self.llm_tokens[self.current_token_index]
        self.current_token_index = (self.current_token_index + 1) % len(self.llm_tokens)
        return token

    def initialize_llm(self):
        """Initialize the Gemini model with the current token"""
        try:
            token = self._get_next_token()
            genai.configure(api_key=token)
            # Using Gemini 1.5 Flash model
            self.llm = genai.GenerativeModel('gemini-1.5-flash')
            
            # Test the model with a simple prompt to verify it works
            test_response = self.llm.generate_content("Hello")
            if not test_response:
                raise Exception("Failed to get response from model")
                
            print(f"Successfully initialized Gemini 1.5 Flash with token {token[:10]}...")
                
        except Exception as e:
            print(f"Error initializing LLM with token: {e}")
            if len(self.llm_tokens) > 1:
                print("Trying next available token...")
                self.initialize_llm()
            else:
                raise Exception("All tokens failed to initialize")

    def get_memory(self, user_id: str) -> AgentMemory:
        """Get or create memory for a user"""
        if user_id not in self.memories:
            self.memories[user_id] = AgentMemory(user_id)
        return self.memories[user_id]

    async def _generate_with_fallback(self, prompt: str, context: str = "", max_retries: int = 3) -> str:
        """Generate content with token fallback mechanism and context"""
        full_prompt = f"{context}\n\n{prompt}" if context else prompt
        
        for attempt in range(max_retries):
            try:
                print(f"Attempting to generate content (attempt {attempt + 1})")
                response = self.llm.generate_content(full_prompt)
                if response and hasattr(response, 'text'):
                    print("Successfully generated response")
                    return response.text
                else:
                    print(f"Error: Empty response from model (attempt {attempt + 1})")
                    self.initialize_llm()
            except Exception as e:
                print(f"Error generating content (attempt {attempt + 1}): {str(e)}")
                if attempt < max_retries - 1:
                    print("Trying with next token...")
                    self.initialize_llm()
                else:
                    return "I apologize, but I'm having trouble processing your request at the moment. Please try again later."

    @abstractmethod
    async def process_message(self, message: str, context: Dict[str, Any]) -> str:
        """Process incoming messages and return appropriate responses"""
        pass

    @abstractmethod
    async def handle_task(self, task: Dict[str, Any]) -> Dict[str, Any]:
        """Handle specific tasks assigned to this agent"""
        pass

    def get_capabilities(self) -> Dict[str, Any]:
        """Return the capabilities of this agent"""
        return {
            "name": self.name,
            "description": self.description,
            "capabilities": self._get_specific_capabilities()
        }

    @abstractmethod
    def _get_specific_capabilities(self) -> Dict[str, Any]:
        """Return specific capabilities of this agent"""
        pass 