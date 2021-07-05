from typing import List, Optional
from itsdangerous import URLSafeSerializer
from aioredis import Connection
from loguru import logger
from lynxfall.oauth.models import OauthConfig, OauthURL, AccessToken
from lynxfall.oauth.exceptions import OauthRequestError, OauthStateError
import aiohttp

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

    def get_auth_link(self, scopes: List[str], state_data: dict, redirect_uri: Optional[str] = None) -> OauthURL:
        """Creates a secure oauth. State data is any data you want to have about a user after auth like user settings/login stuff etc."""
        
        # Add in scopes to state data
        scopes = self.get_scopes(scopes)
        redirect_uri = self.redirect_uri if not redirect_uri else redirect_uri
        state_data["scopes"] = scopes
        state_data["redirect_uri"] = redirect_uri
        state_id = uuid.uuid4()
        state = self.create_state(state_id)
        
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
    
    async def get_access_token(
        self, 
        code: str, 
        state_jwt: str, 
        login_retry_url: str
    ) -> AccessToken: 
        """
        Creates a access token from the state (as JWT) that was created using get_auth_link. 
        Login retry URL is where users can go to login again if login fails   
        """
        
        try:
            state_id = self.auth_s.loads(state_jwt)
        
        except:
            raise OauthStateError(
                f"Invalid state provided. Please try logging in again using {login_retry_url}"
            )
        
        oauth = await redis_db.get(f"oauth-{state_id}")
        if not oauth:
            raise OauthStateError(
                f"Invalid state. There is no oauth data associated with this state. Please try logging in again using {login_retry_url}"
            )

        oauth = orjson.loads(oauth)
        
        redirect_uri = oauth["redirect_uri"]
        scopes = self.get_scopes(oauth["scopes"])

        return await 
    
    async def _generic_at(self, code, grant_type, redirect_uri, scopes):
        """Generic access token handling"""
        payload = {
            "client_id": self.client_id,
            "client_secret": self.client_secret,
            "grant_type": "authorization_code",
            "code": code,
            "redirect_uri": redirect_uri,
            "scope": scopes
        }
        
        headers = {
            'Content-Type': 'application/x-www-form-urlencoded'
        }
        
        json = await self._request(self.TOKEN_URL, payload, headers)
        return AccessToken(
            identifier = self.IDENTIFIER,
            redirect_uri = redirect_uri,
            access_token = json["access_token"],
            refresh_token = json["refresh_token"],
            expires_in = json["expires_in"],
            current_time = json["current_time"]
        )
        
    
    async def refresh_access_token(self, scope: str, access_token: AccessToken) -> str:
        """Refreshes a access token if expired. If it is not expired, this return the same access token again"""
        if not access_token.expired():
            logger.debug("Using old access token without making any changes")
            return access_token
        # Refresh
        payload = {
            "client_id": self.client_id,
            "client_secret": self.client_secret,
            "grant_type": "refresh_token",
            "refresh_token": access_token["refresh_token"],
            "redirect_uri": redirect_uri,
            "scope": scope
        }

        headers = {
            'Content-Type': 'application/x-www-form-urlencoded'
        }
        async with aiohttp.ClientSession() as sess:
            async with ss.post(self.discord_token_url, data=payload, headers=headers) as res:
                json = await res.json()
                return json | {"current_time": time.time()}
