from typing import Dict, Any, List
from core.base_agent import BaseAgent
import tweepy
import facebook
import instagram_private_api
from datetime import datetime
import os
from dotenv import load_dotenv

class SocialMediaAgent(BaseAgent):
    def __init__(self):
        super().__init__(
            name="social_media_manager",
            description="Manages social media accounts, creates and schedules posts"
        )
        self.accounts = {}
        self.scheduled_posts = {}
        self.initialize_social_media_clients()

    def initialize_social_media_clients(self):
        """Initialize social media API clients"""
        load_dotenv()
        
        # Twitter (X) Configuration
        twitter_api_key = os.getenv('TWITTER_API_KEY')
        twitter_api_secret = os.getenv('TWITTER_API_SECRET')
        twitter_access_token = os.getenv('TWITTER_ACCESS_TOKEN')
        twitter_access_secret = os.getenv('TWITTER_ACCESS_SECRET')
        
        if all([twitter_api_key, twitter_api_secret, twitter_access_token, twitter_access_secret]):
            auth = tweepy.OAuthHandler(twitter_api_key, twitter_api_secret)
            auth.set_access_token(twitter_access_token, twitter_access_secret)
            self.accounts['twitter'] = tweepy.API(auth)
        
        # Facebook Configuration
        facebook_access_token = os.getenv('FACEBOOK_ACCESS_TOKEN')
        if facebook_access_token:
            self.accounts['facebook'] = facebook.GraphAPI(access_token=facebook_access_token)
        
        # Instagram Configuration
        instagram_username = os.getenv('INSTAGRAM_USERNAME')
        instagram_password = os.getenv('INSTAGRAM_PASSWORD')
        if instagram_username and instagram_password:
            self.accounts['instagram'] = instagram_private_api.Client(
                username=instagram_username,
                password=instagram_password
            )

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
            prompt = f"""You are a social media management AI assistant. Please help with the following request:

Current message: {message}

Previous conversation context:
{conversation_context}

Available platforms: {', '.join(self.accounts.keys())}

Consider the following aspects when responding:
1. If it's about posting content, specify which platform and what type of content
2. If it's about scheduling posts, provide specific timing details
3. If it's about account management, explain what needs to be done
4. If it's about analytics or performance, provide relevant metrics

Please provide a clear and actionable response."""
            
            print(f"Processing social media request for user {user_id}: {message}")
            response = await self._generate_with_fallback(prompt, conversation_context)
            
            # Only save successful responses to memory
            if not response.startswith("I apologize"):
                memory.add_message("assistant", response)
                print(f"Successfully processed social media request and saved to memory")
            
            return response
            
        except Exception as e:
            print(f"Error in social media agent: {str(e)}")
            return "I'm having trouble with your social media request. Could you please rephrase it or try again?"

    async def handle_task(self, task: Dict[str, Any]) -> Dict[str, Any]:
        """Handle specific social media tasks"""
        task_type = task.get("type")
        
        if task_type == "post":
            return await self._handle_posting(task)
        elif task_type == "schedule":
            return await self._handle_scheduling(task)
        elif task_type == "analyze":
            return await self._handle_analysis(task)
        else:
            return {"status": "error", "message": f"Unknown task type: {task_type}"}

    async def _handle_posting(self, task: Dict[str, Any]) -> Dict[str, Any]:
        """Handle posting content to social media"""
        platform = task.get("platform")
        content = task.get("content")
        media = task.get("media", None)
        
        if not platform or not content:
            return {"status": "error", "message": "Missing platform or content information"}
        
        try:
            if platform == "twitter":
                if media:
                    self.accounts['twitter'].update_status_with_media(content, media)
                else:
                    self.accounts['twitter'].update_status(content)
            elif platform == "facebook":
                if media:
                    self.accounts['facebook'].put_photo(image=media, message=content)
                else:
                    self.accounts['facebook'].put_object(parent_object='me', connection_name='feed', message=content)
            elif platform == "instagram":
                if media:
                    self.accounts['instagram'].post_photo(media, caption=content)
                else:
                    self.accounts['instagram'].post_photo(media=None, caption=content)
            
            return {"status": "success", "message": f"Successfully posted to {platform}"}
        except Exception as e:
            return {"status": "error", "message": f"Error posting to {platform}: {str(e)}"}

    async def _handle_scheduling(self, task: Dict[str, Any]) -> Dict[str, Any]:
        """Handle scheduling posts"""
        platform = task.get("platform")
        content = task.get("content")
        schedule_time = task.get("time")
        media = task.get("media", None)
        
        if not all([platform, content, schedule_time]):
            return {"status": "error", "message": "Missing required information for scheduling"}
        
        try:
            post_id = f"{platform}_{datetime.now().timestamp()}"
            self.scheduled_posts[post_id] = {
                "platform": platform,
                "content": content,
                "time": schedule_time,
                "media": media
            }
            return {"status": "success", "message": f"Post scheduled for {schedule_time}"}
        except Exception as e:
            return {"status": "error", "message": f"Error scheduling post: {str(e)}"}

    async def _handle_analysis(self, task: Dict[str, Any]) -> Dict[str, Any]:
        """Handle social media analytics"""
        platform = task.get("platform")
        metric = task.get("metric")
        
        if not platform or not metric:
            return {"status": "error", "message": "Missing platform or metric information"}
        
        try:
            if platform == "twitter":
                # Implement Twitter analytics
                pass
            elif platform == "facebook":
                # Implement Facebook analytics
                pass
            elif platform == "instagram":
                # Implement Instagram analytics
                pass
            
            return {"status": "success", "message": f"Analysis completed for {platform}"}
        except Exception as e:
            return {"status": "error", "message": f"Error analyzing {platform}: {str(e)}"}

    def _get_specific_capabilities(self) -> Dict[str, Any]:
        """Return specific capabilities of this agent"""
        return {
            "keywords": ["post", "schedule", "social media", "tweet", "facebook", "instagram"],
            "capabilities": [
                "Social media posting",
                "Content scheduling",
                "Account management",
                "Analytics and insights",
                "Multi-platform support"
            ],
            "supported_platforms": list(self.accounts.keys())
        } 