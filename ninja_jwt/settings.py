from datetime import timedelta
from typing import Any, List, Optional, Union

from django.conf import settings
from django.test.signals import setting_changed
from ninja_extra.lazy import LazyStrImport
from pydantic import AnyUrl, Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class NinjaJWTUserDefinedSettingsMapper:
    def __init__(self, data: dict) -> None:
        self.__dict__ = data


NinjaJWT_SETTINGS_DEFAULTS = {
    "USER_AUTHENTICATION_RULE": "ninja_jwt.authentication.default_user_authentication_rule",
    "AUTH_TOKEN_CLASSES": ["ninja_jwt.tokens.AccessToken"],
    "TOKEN_USER_CLASS": "ninja_jwt.models.TokenUser",
}

USER_SETTINGS = NinjaJWTUserDefinedSettingsMapper(
    getattr(
        settings,
        "SIMPLE_JWT",
        getattr(settings, "NINJA_JWT", NinjaJWT_SETTINGS_DEFAULTS),
    )
)


class NinjaJWTSettings(BaseSettings):
    model_config = SettingsConfigDict(
        validate_assignment=True,
        extra="ignore",
    )

    ACCESS_TOKEN_LIFETIME: timedelta = Field(timedelta(minutes=5))
    REFRESH_TOKEN_LIFETIME: timedelta = Field(timedelta(days=1))
    ROTATE_REFRESH_TOKENS: bool = Field(False)
    BLACKLIST_AFTER_ROTATION: bool = Field(False)
    UPDATE_LAST_LOGIN: bool = Field(False)
    ALGORITHM: str = Field("HS256")
    SIGNING_KEY: str = Field(settings.SECRET_KEY)
    VERIFYING_KEY: Optional[str] = Field("")
    AUDIENCE: Optional[str] = Field(None)
    ISSUER: Optional[str] = Field(None)
    JWK_URL: Optional[AnyUrl] = Field(None)
    LEEWAY: Union[int, timedelta] = Field(0)

    # AUTH_HEADER_TYPES: Tuple[str] = Field(('Bearer',))
    # AUTH_HEADER_NAME: str = Field('HTTP_AUTHORIZATION')

    USER_ID_FIELD: str = Field("id")
    USER_ID_CLAIM: str = Field("user_id")

    USER_AUTHENTICATION_RULE: Any = Field(
        "ninja_jwt.authentication.default_user_authentication_rule"
    )
    TOKEN_USER_CLASS: Any = Field("ninja_jwt.models.TokenUser")
    AUTH_TOKEN_CLASSES: List[Any] = Field(["ninja_jwt.tokens.AccessToken"])
    JSON_ENCODER: Optional[Any] = Field(None)
    TOKEN_TYPE_CLAIM: Optional[str] = Field("token_type")
    JTI_CLAIM: Optional[str] = Field("jti")
    SLIDING_TOKEN_REFRESH_EXP_CLAIM: str = Field("refresh_exp")
    SLIDING_TOKEN_LIFETIME: timedelta = Field(timedelta(minutes=5))
    SLIDING_TOKEN_REFRESH_LIFETIME: timedelta = Field(timedelta(days=1))

    TOKEN_OBTAIN_PAIR_INPUT_SCHEMA: Any = Field(
        "ninja_jwt.schema.TokenObtainPairInputSchema"
    )
    TOKEN_OBTAIN_PAIR_REFRESH_INPUT_SCHEMA: Any = Field(
        "ninja_jwt.schema.TokenRefreshInputSchema"
    )

    TOKEN_OBTAIN_SLIDING_INPUT_SCHEMA: Any = Field(
        "ninja_jwt.schema.TokenObtainSlidingInputSchema"
    )
    TOKEN_OBTAIN_SLIDING_REFRESH_INPUT_SCHEMA: Any = Field(
        "ninja_jwt.schema.TokenRefreshSlidingInputSchema"
    )

    TOKEN_BLACKLIST_INPUT_SCHEMA: Any = Field(
        "ninja_jwt.schema.TokenBlacklistInputSchema"
    )
    TOKEN_VERIFY_INPUT_SCHEMA: Any = Field("ninja_jwt.schema.TokenVerifyInputSchema")

    def __getattribute__(self, item):
        # Get the actual value using object.__getattribute__ to avoid recursion
        value = object.__getattribute__(self, item)

        if item in NinjaJWT_SETTINGS_DEFAULTS:
            if isinstance(value, (list, tuple)) and value and isinstance(value[0], str):
                return [LazyStrImport(str(klass)) for klass in value]
            elif isinstance(value, str):
                return LazyStrImport(value)

        return value


# convert to lazy object
api_settings = NinjaJWTSettings.model_validate(USER_SETTINGS.__dict__)


def reload_api_settings(*args: Any, **kwargs: Any) -> None:
    global api_settings

    setting, value = kwargs["setting"], kwargs["value"]

    if setting in ["SIMPLE_JWT", "NINJA_JWT"]:
        api_settings = NinjaJWTSettings.model_validate(value)


setting_changed.connect(reload_api_settings)
