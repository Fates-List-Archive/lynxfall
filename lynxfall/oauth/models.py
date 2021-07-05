from pydantic import BaseModel

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
