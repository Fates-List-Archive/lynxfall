from typing import List

class BaseOauth():  
    def get_scopes(self, scopes_lst: List[str]) -> str:
        return "%20".join(scopes_lst)
