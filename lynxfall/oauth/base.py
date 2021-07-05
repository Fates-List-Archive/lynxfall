from typing import List

class BaseOauth():
    def __init__(self, auth_jwt_key: str, oc: OauthConfig):
        self.auth_s = URLSafeSerializer(auth_jwt_key, "auth")
        
    def get_scopes(self, scopes_lst: List[str]) -> str:
        return "%20".join(scopes_lst)
