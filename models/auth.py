from pydantic import BaseModel
from typing import Optional, List, Dict
from datetime import datetime
from uuid import uuid4
from pymongo.results import UpdateResult
from db.index import mongoDBClient
import secrets

AccessTokens = mongoDBClient.get_collection("accessTokens")
Clients = mongoDBClient.get_collection("clients")

class OAuthClient(BaseModel):
    client_id: str
    client_secret: str
    redirect_uris: List[str]
    grant_types: List[str]
    response_types: List[str]
    scope: str
    token_endpoint_auth_method: str = "client_secret_post"
    default_redirect_uri: Optional[str] = None
    user_id: Optional[str] = None

    def get_client_id(self) -> str:
        return self.client_id

    def get_default_redirect_uri(self) -> Optional[str]:
        return self.default_redirect_uri or (self.redirect_uris[0] if self.redirect_uris else None)

    def check_redirect_uri(self, redirect_uri: str) -> bool:
        return redirect_uri in self.redirect_uris

    def check_client_secret(self, client_secret: str) -> bool:
        return secrets.compare_digest(self.client_secret, client_secret)

    def check_token_endpoint_auth_method(self, method: str) -> bool:
        return method == self.token_endpoint_auth_method

    def check_response_type(self, response_type: str) -> bool:
        return response_type in self.response_types

    def check_grant_type(self, grant_type: str) -> bool:
        return grant_type in self.grant_types

    def get_allowed_scope(self, scope: str) -> str:
        allowed = set(self.scope.split())
        requested = set(scope.split())
        return " ".join(allowed & requested)


class OAuthToken(BaseModel):
    access_token: str
    refresh_token: Optional[str] = None
    token_type: str
    expires_at: datetime
    scope: str
    client_id: str
    user_id: Optional[str] = None


class OAuthUser(BaseModel):
    user_id: str
    email: str
    hashed_password: str
    scopes: List[str] = []

def query_client(client_id: str) -> Optional[OAuthClient]:
    client_data = Clients.find_one({"client_id": client_id})
    if client_data:
        return OAuthClient(**client_data)
    return None