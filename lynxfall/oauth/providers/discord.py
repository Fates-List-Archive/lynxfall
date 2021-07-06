import secrets
import string
import time
import uuid
from loguru import logger
from lynxfall.oauth.base import BaseOauth
from lynxfall.oauth.models import AccessToken
import aiohttp
from typing import Optional, List, Union
from pydantic import BaseModel

class DiscordOauth(BaseOauth):
    """Discord oauth implementation, more in future for guilded etc."""
    
    IDENTIFIER = "discord"
    AUTH_URL = "https://discord.com/api/oauth2/authorize"
    TOKEN_URL = "https://discord.com/api/oauth2/token"
    API_URL = "https://discord.com/api"

    async def get_user_json(self, access_token: AccessToken) -> dict:
        """Get the user json (https://discord.com/developers/docs/resources/user#user-object)"""
        url = f"{self.API_URL}/users/@me"

        headers = {
            "Authorization": f"Bearer {access_token.access_token}"
        }
        
        return await self._request(url, "GET", headers=headers)

    async def get_user_guilds(
        self, 
        access_token: AccessToken, 
        permissions: Optional[List[hex]] = None
    ) -> List[dict]:
        """
        Gets a list of guilds. 
        If permissions is provided, only guilds in which user has said permission will be returned
        """
        url = f"{self.API_URL}/users/@me/guilds"
        
        headers = {
            "Authorization": f"Bearer {access_token.access_token}"
        }
        
        guild_json = await self._request(url, "GET", headers=headers)
        
        try:
            guilds = []
            for guild in guild_json:
                
                if permissions is None:
                    guilds.append(guild)
                    continue
                    
                for perm in permissions:
                    if (guild["permissions"] & perm) == perm:
                        guilds.append(guild)
                        continue
                        
        except Exception:
            guilds = []
            
        return guilds

    async def add_user_to_guild(
        self,
        access_token: AccessToken,
        user_id: Union[int, str],
        guild_id: int, 
        bot_token: str
    ) -> bool:
        """
        Adds/joins a user to a discord server/guild
        
        This needs a bot and a bot token to be provided
        
        Get the user_id from the get_user_json method. Should be integer, but string is also supported
        
        Returns a boolean on whether the user has been added to the guild or not.
        """
        url = f"{self.API_URL}/guilds/{guild_id}/members/{user_id}"

        headers = {
            "Authorization": f"Bot {bot_token}"
        }
        
        payload = {"access_token": access_token.access_token}
        
        async with aiohttp.ClientSession() as sess:
            async with sess.put(url, headers = headers, json = payload) as res:
                if res.status not in (201, 204):
                    return False
                return True
