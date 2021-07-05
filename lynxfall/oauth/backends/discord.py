import secrets
import string
import time
import uuid
from lynxfall.oauth.base import BaseOauth, OauthConfig
from aioredis import Connection
from typing import List, Optional, Union

import aiohttp
from pydantic import BaseModel

class DiscordOauth(BaseOauth):
    """Discord oauth implementation, more in future for guilded etc."""
    
    IDENTIFIER = "discord"
    AUTHORIZE_URL = "https://discord.com/api/oauth2/authorize"
    TOKEN_URL = "https://discord.com/api/oauth2/token"
    API_URL = "https://discord.com/api"

    async def get_user_json(self, access_token):
        url = self.discord_api_url + "/users/@me"

        headers = {
            "Authorization": f"Bearer {access_token}"
        }
        async with aiohttp.ClientSession() as sess:
            async with sess.get(url, headers=headers) as res:
                if res.status == 401:
                    return None
                return await res.json()

    async def get_guilds(self, access_token: str, permissions: Optional[hex] = None):
        url = self.discord_api_url + "/users/@me/guilds"
        headers = {
            "Authorization": f"Bearer {access_token}"
        }
        async with aiohttp.ClientSession() as sess:
            async with sess.get(url, headers = headers) as res:
                if res.status != 200:
                    return []
                guild_json = await res.json()
        try:
            guilds = []
            for guild in guild_json:
                if permissions is None:
                    guilds.append(str(guild["id"]))
                else:
                    flag = False
                    for perm in permissions:
                        if flag:
                            continue
                        elif (guild["permissions"] & perm) == perm:
                            flag = True
                        else:
                            pass
                    if flag:
                        guilds.append(str(guild["id"]))
        except:
            guilds = []
        logger.debug(f"Got guilds {guilds}")
        return guilds

    async def join_user(self, access_token, user_id):
        url = self.discord_api_url+f"/guilds/{main_server}/members/{user_id}"

        headers = {
            "Authorization": f"Bot {TOKEN_MAIN}"
        }
        async with aiohttp.ClientSession() as sess:
            async with sess.put(url, headers = headers, json = {"access_token": access_token}) as res:
                if res.status not in (201, 204):
                    return False
                return True
