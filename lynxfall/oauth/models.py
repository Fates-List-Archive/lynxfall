from pydantic import BaseModel
from typing import Union
import time


class ResponseModel(BaseModel):
    identifier: str
    redirect_uri: str

# Core models
class OauthConfig(BaseModel):
    client_id: str
    client_secret: str
    redirect_uri: str
    lynxfall_jwt_key: str

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
        return float(self.current_time) + float(self.expires_in) > time.time()
