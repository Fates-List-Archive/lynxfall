import secrets
import string
import time
import uuid
from loguru import Logger
from lynxfall.oauth.base import BaseOauth
from lynxfall.oauth.models import AccessToken
import aiohttp
from pydantic import BaseModel

class DiscordOauth(BaseOauth):
    """Discord oauth implementation, more in future for guilded etc."""
    
    IDENTIFIER = "discord"
    AUTH_URL = "https://discord.com/api/oauth2/authorize"
    TOKEN_URL = "https://discord.com/api/oauth2/token"
    API_URL = "https://discord.com/api"

    async def get_user_json(self, access_token: AccessToken):
        """Get the user json (https://discord.com/developers/docs/resources/user#user-object)"""
        url = f"{self.API_URL}/users/@me"

        headers = {
            "Authorization": f"Bearer {access_token.access_token}"
        }
        
        return await self._request(url, headers=headers)

    async def get_user_guilds(self, access_token: AccessToken, permissions: Optional[hex] = None):
        url = f"{self.API_URL}/users/@me/guilds"
        
        headers = {
            "Authorization": f"Bearer {access_token.access_token}"
        }
        
        guild_json = await self._request(url, headers=headers)
        
        try:
            guilds = []
            for guild in guild_json:
                
                if permissions is None:
                    guilds.append(str(guild["id"]))
                    continue
                    
                flag = False
                    
                for perm in permissions:
                    if (guild["permissions"] & perm) == perm:
                        guilds.append(str(guild["id"]))
                        
        except:
            guilds = []
            
        logger.debug(f"Got guilds {guilds}")
        return guilds

    async def add_user_to_guild(self, *, access_token: AccessToken, user_id: int, guild_id: int, bot_token: str):
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
