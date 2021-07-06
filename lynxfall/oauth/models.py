from pydantic import BaseModel
from typing import Union, Optional, List
import time


class ResponseModel(BaseModel):
    identifier: str
    redirect_uri: str

# Core models
class OauthConfig(BaseModel):
    """
    Get these from your oauth system/provider
    
    client_id - Client ID
    client_secret - Client Secret
    redirect_uri - A allowed redirect uri (some, like discord, need this to be added to your oauth application)
    
    lynxfall_key - A randomly generated key for lynxfall to use for state verification etc.
    """
    client_id: str
    client_secret: str
    redirect_uri: str
    lynxfall_key: str

class OauthURL(ResponseModel):
    url: str
    state_id: str

class AccessToken(ResponseModel):
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
    state_id: Optional[str] = None

    def expired(self):
        """Returns whether a access token has expired or not"""
        return float(self.current_time) + float(self.expires_in) < time.time()
