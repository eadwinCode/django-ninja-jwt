from typing import Any, Type

from django.contrib.auth import get_user_model
from django.contrib.auth.models import AbstractUser, AnonymousUser
from django.http import HttpRequest
from django.utils.translation import gettext_lazy as _
from ninja.security import HttpBearer

from .exceptions import AuthenticationFailed, InvalidToken, TokenError
from .settings import api_settings
from .tokens import Token


class JWTBaseAuthentication:
    def __init__(self) -> None:
        super().__init__()
        self.user_model = get_user_model()

    @classmethod
    def get_validated_token(cls, raw_token) -> Type[Token]:
        """
        Validates an encoded JSON web token and returns a validated token
        wrapper object.
        """
        messages = []
        for AuthToken in api_settings.AUTH_TOKEN_CLASSES:
            try:
                return AuthToken(raw_token)
            except TokenError as e:
                messages.append(
                    {
                        "token_class": AuthToken.__name__,
                        "token_type": AuthToken.token_type,
                        "message": e.args[0],
                    }
                )

        raise InvalidToken(
            {
                "detail": _("Given token not valid for any token type"),
                "messages": messages,
            }
        )

    def get_user(self, validated_token) -> Type[AbstractUser]:
        """
        Attempts to find and return a user using the given validated token.
        """
        try:
            user_id = validated_token[api_settings.USER_ID_CLAIM]
        except KeyError:
            raise InvalidToken(_("Token contained no recognizable user identification"))

        try:
            user = self.user_model.objects.get(**{api_settings.USER_ID_FIELD: user_id})
        except self.user_model.DoesNotExist:
            raise AuthenticationFailed(_("User not found"))

        if not user.is_active:
            raise AuthenticationFailed(_("User is inactive"))

        return user

    def jwt_authenticate(self, request: HttpRequest, token: str) -> Type[AbstractUser]:
        request.user = AnonymousUser()
        validated_token = self.get_validated_token(token)
        user = self.get_user(validated_token)
        request.user = user
        return user


class JWTAuth(JWTBaseAuthentication, HttpBearer):
    def authenticate(self, request: HttpRequest, token: str) -> Any:
        return self.jwt_authenticate(request, token)


class JWTTokenUserAuth(JWTBaseAuthentication, HttpBearer):
    """
    Experimental features
    JWTTokenUserAuth backend
    """

    def authenticate(self, request: HttpRequest, token: str) -> Any:
        return self.jwt_authenticate(request, token)

    def get_user(self, validated_token: Any) -> Type[AbstractUser]:
        """
        Returns a stateless user object which is backed by the given validated
        token.
        """
        if api_settings.USER_ID_CLAIM not in validated_token:
            # The TokenUser class assumes tokens will have a recognizable user
            # identifier claim.
            raise InvalidToken(_("Token contained no recognizable user identification"))

        return api_settings.TOKEN_USER_CLASS(validated_token)


def default_user_authentication_rule(user) -> bool:
    # Prior to Django 1.10, inactive users could be authenticated with the
    # default `ModelBackend`.  As of Django 1.10, the `ModelBackend`
    # prevents inactive users from authenticating.  App designers can still
    # allow inactive users to authenticate by opting for the new
    # `AllowAllUsersModelBackend`.  However, we explicitly prevent inactive
    # users from authenticating to enforce a reasonable policy and provide
    # sensible backwards compatibility with older Django versions.
    return user is not None and user.is_active