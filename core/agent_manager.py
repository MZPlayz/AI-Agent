from typing import Dict, Any, List
import asyncio
from .base_agent import BaseAgent

class AgentManager:
    def __init__(self):
        self.agents: Dict[str, BaseAgent] = {}
        self.task_queue = asyncio.Queue()

    def register_agent(self, agent: BaseAgent):
        """Register a new agent with the manager"""
        self.agents[agent.name] = agent

    def get_agent(self, agent_name: str) -> BaseAgent:
        """Get a specific agent by name"""
        return self.agents.get(agent_name)

    def get_all_agents(self) -> List[Dict[str, Any]]:
        """Get information about all registered agents"""
        return [agent.get_capabilities() for agent in self.agents.values()]

    async def route_message(self, message: str, context: Dict[str, Any]) -> str:
        """Route a message to the appropriate agent"""
        # First, try to identify which agent should handle this message
        for agent in self.agents.values():
            if self._should_handle_message(agent, message):
                return await agent.process_message(message, context)
        
        # If no specific agent is identified, use the personal assistant as default
        default_agent = self.agents.get("personal_assistant")
        if default_agent:
            return await default_agent.process_message(message, context)
        
        return "I'm sorry, I couldn't find an appropriate agent to handle your request."

    def _should_handle_message(self, agent: BaseAgent, message: str) -> bool:
        """Determine if an agent should handle a given message"""
        # This is a simple implementation - you might want to use more sophisticated
        # NLP techniques to determine the appropriate agent
        capabilities = agent.get_capabilities()
        keywords = capabilities.get("keywords", [])
        return any(keyword.lower() in message.lower() for keyword in keywords)

    async def assign_task(self, task: Dict[str, Any]):
        """Assign a task to the appropriate agent"""
        agent_name = task.get("agent")
        if agent_name in self.agents:
            agent = self.agents[agent_name]
            return await agent.handle_task(task)
        return {"status": "error", "message": f"No agent found with name {agent_name}"}

    async def process_task_queue(self):
        """Process tasks in the queue"""
        while True:
            task = await self.task_queue.get()
            try:
                result = await self.assign_task(task)
                print(f"Task completed: {result}")
            except Exception as e:
                print(f"Error processing task: {e}")
            finally:
                self.task_queue.task_done() 