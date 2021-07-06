from typing import List, Optional
from itsdangerous import URLSafeSerializer
from aioredis import Connection
from loguru import logger
from lynxfall.oauth.models import OauthConfig, OauthURL, AccessToken
from lynxfall.oauth.exceptions import OauthRequestError, OauthStateError
from lynxfall.utils.string import secure_strcmp
import aiohttp
import uuid
import orjson
import time

class BaseOauth():
    IDENTIFIER = "base"
    AUTH_URL = "https://example.com/api/oauth2/authorize"
    TOKEN_URL = "https://example.com/api/oauth2/token"
    API_URL = "https://example.com/api"
    
    def __init__(self, oc: OauthConfig, redis: Connection):
        self.auth_s = URLSafeSerializer(oc.lynxfall_key, "auth")
        self.client_id = oc.client_id
        self.client_secret = oc.client_secret
        self.redirect_uri = oc.redirect_uri
        self.redis = redis
        
    def get_scopes(self, scopes_lst: List[str]) -> str:
        """Helper function to turn a list of scopes into a space seperated string"""
        return "%20".join(scopes_lst)

    def create_state(self, id):
        """
        Creates a state as JWT from a state id
        
        Lynxfall internally uses UUID for state ID which
        is subject to change and should not be relied on.
        """
        return self.auth_s.dumps(str(id))

    def get_state_id(self, state_jwt):
        """Get the state given the state jwt. Returns None if jwt is invalid"""
        try:
            state_jwt_id = self.auth_s.loads(state_jwt)
            return state_jwt_id
        except Exception:
            return None
        
    async def get_state(self, state_id):
        """Get a state from redis"""
        data = await self.redis.get(f"oauth.{self.IDENTIFIER}-{state_id}")
        if not data:
            return None
        
        try:
            return orjson.loads(data)
        except:
            return None
        
    def verify_state(self, state_id, state_jwt):
        """Verifies a state id based on state jwt"""
        state_jwt_id = self.get_state(state_jwt)
        if not state_jwt_id:
            return False
        
        if secure_strcmp(state_id, state_jwt_id):
            return True
        return False
    
    async def clear_state(self, state_id):
        """Clears a state ID from redis"""
        await self.redis.delete(f"oauth.{self.IDENTIFIER}-{state_id}")
        
    async def get_auth_url(
        self, 
        scopes: List[str],
        state_data: dict, 
        redirect_uri: Optional[str] = None,
        state_expiry = 150
    ) -> OauthURL:
        """
        Gets a one time auth url for a user and saves state ID to redis. 
        State data is any data you want to have about a user after auth like user settings/login stuff etc.
        """
        
        # Add in scopes to state data
        scopes = self.get_scopes(scopes)
        redirect_uri = self.redirect_uri if not redirect_uri else redirect_uri
        state_data["scopes"] = scopes
        state_data["redirect_uri"] = redirect_uri
        state_id = str(uuid.uuid4())
        state = self.create_state(state_id)
        
        await self.redis.set(f"oauth.{self.IDENTIFIER}-{state_id}", orjson.dumps(state_data), ex = state_expiry)
      
        return OauthURL(
            identifier = self.IDENTIFIER,
            url = f"{self.AUTH_URL}?client_id={self.client_id}&redirect_uri={redirect_uri}&state={state}&response_type=code&scope={scopes}",  # noqa
            state_id = state_id,
            redirect_uri = redirect_uri
        )
    
    async def _request(self, url, method, **urlargs):
        """Makes a API request using aiohttp"""
        
        async with aiohttp.ClientSession() as sess:
            f = getattr(sess, method.lower())
            async with f(url, **urlargs) as res:
                if str(res.status)[0] != "2":
                    try:
                        json = await res.json()
                    except Exception:
                        json = {}
                    raise OauthRequestError(f"Could not make oauth request, recheck your client_secret. Got status code {res.status} and json of {json}")
                    
                elif res.status == 401:
                    return OauthRequestError("Oauth endpoint returned 401")
                
                json = await res.json()
                return json | {"current_time": time.time()}
            
    async def _generic_at(
        self, 
        code: str, 
        grant_type: str, 
        redirect_uri: str, 
        scopes: str,
        *, 
        state_id: Optional[str] = None
    ) -> AccessToken:
        """Generic access token handling"""
        payload = {
            "client_id": self.client_id,
            "client_secret": self.client_secret,
            "grant_type": grant_type,
            "code": code,
            "redirect_uri": redirect_uri,
            "scope": scopes
        }
        
        headers = {
            'Content-Type': 'application/x-www-form-urlencoded'
        }
        
        json = await self._request(self.TOKEN_URL, "POST", data=payload, headers=headers)
        
        return AccessToken(
            identifier = self.IDENTIFIER,
            redirect_uri = redirect_uri,
            access_token = json["access_token"],
            refresh_token = json["refresh_token"],
            expires_in = json["expires_in"],
            current_time = json["current_time"],
            scopes = scopes,
            state_id = state_id
        )
    
    async def get_access_token(
        self, 
        code: str, 
        state_jwt: str, 
        login_retry_url: str,
        clear_state: bool = True
    ) -> AccessToken: 
        """
        Creates a access token from the state (as JWT) that was created using get_auth_link. 
        Login retry URL is where users can go to login again if login fails.
        
        For security, use clear_state as True unless you have a reason not to. 
        If you do need clear_state as False, be sure to call clear_state(state_id) to clear the state from the DB.
        """
        state_id = self.get_state_id(state_jwt)
        if not state_id:
            raise OauthStateError(
                f"Invalid state provided. Please try logging in again using {login_retry_url}"
            )
        
        oauth = await self.get_state(state_id)
        if not oauth:
            raise OauthStateError(
                f"Invalid state. There is no oauth data associated with this state. Please try logging in again using {login_retry_url}"
            )
        
        if clear_state:
            await self.clear_state(state_id)
            
        scopes = self.get_scopes(oauth["scopes"])
        
        logger.debug(f"{code}, {self.get_scopes(oauth['scopes'])}")
        return await self._generic_at(
            code, 
            "authorization_code",
            oauth["redirect_uri"], 
            self.get_scopes(oauth["scopes"]),
            state_id = state_id
        )
           
    async def refresh_access_token(self, access_token: AccessToken) -> str:
        """
        Refreshes a access token if expired. 
        
        If it is not expired, this returns the 
        same access token passed to the function
        """
        if not access_token.expired():
            logger.warning("Using old access token previously passed to the function")
            return access_token
        
        return await self._generic_at(
            access_token.refresh_token, 
            "refresh_token",
            access_token.redirect_uri, 
            access_token.scopes
        )
