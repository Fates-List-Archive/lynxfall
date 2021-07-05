from typing import List, Optional
from itsdangerous import URLSafeSerializer
from aioredis import Connection
from lynxfall.oauth.models import OauthConfig, OauthURL
from lynxfall.oauth.exceptions import OauthRequestError

class BaseOauth():
    IDENTIFIER = "base"
    AUTH_ENDPOINT = "https://example.com/api/oauth2/authorize"
    TOKEN_ENDPOINT = "https://example.com/api/oauth2/token"
    API_URL = "https://example.com/api"
    
    def __init__(self, auth_jwt_key: str, oc: OauthConfig, redis: Connection):
        self.auth_s = URLSafeSerializer(auth_jwt_key, "auth")
        self.client_id = oc.client_id
        self.client_secret = oc.client_secret
        self.redirect_uri = oc.redirect_uri
        self.redis = redis
        
    def get_scopes(self, scopes_lst: List[str]) -> str:
        return "%20".join(scopes_lst)

    def create_state(self, id):
        return self.auth_s.dumps(str(id))

    def get_oauth(self, scopes: List[str], state_data: dict, redirect_uri: Optional[str] = None) -> OauthURL:
        """Creates a secure oauth. State data is any data you want to have about a user after auth like user settings/login stuff etc."""
        
        state_id = uuid.uuid4()
        state = self.create_state(state_id)
        redirect_uri = self.redirect_uri if not redirect_uri else redirect_uri
        scopes = self.get_scopes(scopes)
        await self.redis.set(f"oauth.{self.IDENTIFIER}-{state_id}", orjson.dumps(state_data))
        
        return OauthURL(
            identifier = self.IDENTIFIER,
            url = f"{self.AUTH_ENDPOINT}?client_id={self.client_id}&redirect_uri={redirect_uri}&state={state}&response_type=code&scope={scopes}",
            state_id = state_id,
            redirect_uri = redirect_uri
        )

    async def _request(self, url, data, headers):
        """Makes a API request using aiohttp"""
        async with aiohttp.ClientSession() as sess:
            async with sess.post(url, data=data, headers=headers) as res:
                if str(res.status) != "2":
                    raise OauthRequestError("Could not make oauth request, recheck your client_secret")
                json = await res.json()
                return json | {"current_time": time.time()}
    
    async def get_access_token(self, code: str, scope: str, redirect_uri: Optional[str] = None) -> dict: 
        
        payload = {
            "client_id": self.client_id,
            "client_secret": self.client_secret,
            "grant_type": "authorization_code",
            "code": code,
            "redirect_uri": redirect_uri,
            "scope": scope
        }
        
        headers = {
            'Content-Type': 'application/x-www-form-urlencoded'
        }
        
        redirect_uri = self.redirect_uri if not redirect_uri else redirect_uri
        
        return await self._request(self.TOKEN_URL, payload, headers)
