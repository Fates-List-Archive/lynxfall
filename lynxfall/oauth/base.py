from typing import List
from itsdangerous import URLSafeSerializer

class BaseOauth():
    def __init__(self, auth_jwt_key: str, oc: OauthConfig):
        self.auth_s = URLSafeSerializer(auth_jwt_key, "auth")
        
    def get_scopes(self, scopes_lst: List[str]) -> str:
        return "%20".join(scopes_lst)

    def create_state(self, id):
        return self.auth_s.dumps(str(id))

    def get_oauth(self, scopes: list, state_data: dict, redirect_uri: Optional[str] = None):
        """Creates a secure oauth. State data is any data you want to have about a user after auth like user settings/login stuff etc."""
        
        state_id = uuid.uuid4()
        state = self.create_state(state_id)
        await self.redis.set(f"oauth.{self.IDENTIFIER}-{state_id}", orjson.dumps(state_data))
        return f"{self.login_url}?client_id={self.client_id}&redirect_uri={self.redirect_uri}&state={state}&response_type=code&scope={self.get_scopes(scopes)}"
