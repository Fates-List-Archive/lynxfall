import secrets
import string
import time
import uuid
from lynxfall.oauth.base import BaseOauth
from typing import List, Optional, Union
from itsdangerous import URLSafeSerializer

import aiohttp
from pydantic import BaseModel

class DiscordOauth(BaseOauth):
    def __init__(self, oc: OauthConfig):
        self.client_id = oc.client_id
        self.client_secret = oc.client_secret
        self.redirect_uri = oc.redirect_uri
        self.login_url = f"https://discord.com/api/oauth2/authorize?client_id={self.client_id}&redirect_uri={self.redirect_uri}"
        self.token_url = "https://discord.com/api/oauth2/token"
        self.api_url = "https://discord.com/api"
    
    def get_scopes(self, scopes_lst: list) -> str:
        return "%20".join(scopes_lst)

    def get_oauth(self, id: uuid.UUID, scopes: list):
        return f"{self.discord_login_url}&state={id}&response_type=code&scope={self.get_scopes(scopes)}"

    async def get_access_token(self, code, scope) -> dict:
        payload = {
            "client_id": self.client_id,
            "client_secret": self.client_secret,
            "grant_type": "authorization_code",
            "code": code,
            "redirect_uri": self.redirect_uri,
            "scope": scope
        }

        headers = {
            'Content-Type': 'application/x-www-form-urlencoded'
        }
        async with aiohttp.ClientSession() as sess:
            async with sess.post(self.token_url, data=payload, headers=headers) as res:
                if res.status != 200:
                    return None
                json = await res.json()
                return json | {"current_time": time.time()}

    async def access_token_check(self, scope: str, access_token_dict: dict) -> str:
        if float(access_token_dict["current_time"]) + float(access_token_dict["expires_in"]) > time.time():
            logger.debug("Using old access token without making any changes")
            return access_token_dict
        # Refresh
        payload = {
            "client_id": self.client_id,
            "client_secret": self.client_secret,
            "grant_type": "refresh_token",
            "refresh_token": access_token_dict["refresh_token"],
            "redirect_uri": self.redirect_uri,
            "scope": scope
        }

        headers = {
            'Content-Type': 'application/x-www-form-urlencoded'
        }
        async with aiohttp.ClientSession() as sess:
            async with ss.post(self.discord_token_url, data=payload, headers=headers) as res:
                json = await res.json()
                return json | {"current_time": time.time()}

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
