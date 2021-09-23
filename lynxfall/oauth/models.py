from pydantic import BaseModel
from typing import Union, Optional, List
import time

# Core models
class OauthConfig(BaseModel):
    """
    Get these from your oauth system/provider
    
    client_id - Client ID
    client_secret - Client Secret
    redirect_uri - A allowed redirect uri (some, like discord, need this to be added to your oauth application)
    """
    client_id: str
    client_secret: str
    redirect_uri: str

class OauthURL(BaseModel):
    url: str
    state: str

class AccessToken(BaseModel):
    """
    Represents a access token
    
    token_type should always be Bearer and is hence not included
    
    state_id is None on a refresh request, but is present otherwise
    """
    
    access_token: str
    refresh_token: str
    expires_in: Union[int, float]
    scopes: str
    current_time: Union[int, float]

    def expired(self):
        """Returns whether a access token has expired or not"""
        return float(self.current_time) + float(self.expires_in) < time.time()
