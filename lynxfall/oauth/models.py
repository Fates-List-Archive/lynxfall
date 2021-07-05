from pydantic import BaseModel
from typing import Union
import aiohttp


# Core models
class OauthConfig(BaseModel):
    client_id: str
    client_secret: str
    redirect_uri: str

class OauthURL(BaseModel):
    identifier: str
    url: str
    state_id: str
    redirect_uri: str

class AccessToken(BaseModel):
    """
    Represents a access token
    
    token_type should always be Bearer and is hence not included
    """
    access_token: str
    refresh_token: str
    expires_in: Union[int, float]
    scope: str
    current_time: Union[int, float]    
    
