from authlib.integrations.flask_oauth2 import AuthorizationServer
from authlib.oauth2.rfc6749 import ClientAuthentication
from authlib.oauth2.rfc6750 import BearerTokenValidator
from fastapi import Request, Depends
from models.index import OAuthClient, OAuthToken, OAuthUser, AccessTokens, Users
from typing import Optional, Dict, Any
from datetime import datetime
import secrets


class MCPClientAuthentication(ClientAuthentication):
    def authenticate(self, request: Request) -> Optional[OAuthClient]:
        client_id = request.form.get("client_id")
        client_secret = request.form.get("client_secret")

        # Query your database
        client_data = Users.find_one({"client_id": client_id})
        if not client_data or client_data["client_secret"] != client_secret:
            return None

        return OAuthClient(**client_data)


class MCPTokenValidator(BearerTokenValidator):
    def authenticate_token(self, token_string: str) -> Optional[OAuthToken]:
        token_data = AccessTokens.find_one({"access_token": token_string})
        if token_data and token_data["expires_at"] > datetime.utcnow():
            return OAuthToken(**token_data)
        return None


class MCPAuthorizationServer(AuthorizationServer):
    def __init__(self, query_client=None, save_token=None):
        super().__init__(
            token_generator=self.generate_token,
            token_validator=MCPTokenValidator(),
        )
        self.register_client_auth_method(MCPClientAuthentication())

    def generate_token(
        self,
        client: OAuthClient,
        grant_type: str,
        user: Optional[OAuthUser] = None,
        scope: Optional[str] = None,
        **kwargs,
    ) -> Dict[str, Any]:
        return {
            "access_token": secrets.token_urlsafe(32),
            "refresh_token": secrets.token_urlsafe(32),
            "token_type": "Bearer",
            "expires_in": 3600,
            "scope": scope or " ".join(client.scope),
        }
