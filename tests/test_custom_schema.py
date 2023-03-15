from datetime import timedelta
from unittest.mock import patch

import pytest
from django.contrib.auth import get_user_model
from ninja import Schema

from ninja_jwt.schema import (
    TokenBlacklistInputSchema,
    TokenObtainPairInputSchema,
    TokenObtainSlidingInputSchema,
    TokenRefreshInputSchema,
    TokenRefreshSlidingInputSchema,
    TokenVerifyInputSchema,
)
from ninja_jwt.schema_control import SchemaControl
from ninja_jwt.settings import api_settings
from ninja_jwt.tokens import AccessToken, RefreshToken, SlidingToken
from ninja_jwt.utils import aware_utcnow, datetime_from_epoch, datetime_to_epoch

from .utils import APIViewTestCase

User = get_user_model()


class MyNewObtainPairTokenSchemaOutput(Schema):
    refresh: str
    access: str
    first_name: str
    last_name: str


class MyNewObtainTokenSlidingSchemaOutput(Schema):
    token: str
    first_name: str
    last_name: str


class MyNewObtainPairSchemaInput(TokenObtainPairInputSchema):
    @classmethod
    def get_response_schema(cls):
        return MyNewObtainPairTokenSchemaOutput

    def to_response_schema(self):
        return MyNewObtainPairTokenSchemaOutput(
            first_name=self._user.first_name,
            last_name=self._user.last_name,
            **self.dict(exclude={"password"})
        )


class MyNewObtainTokenSlidingSchemaInput(TokenObtainSlidingInputSchema):
    my_extra_field: str

    @classmethod
    def get_response_schema(cls):
        return MyNewObtainTokenSlidingSchemaOutput

    def to_response_schema(self):
        return MyNewObtainTokenSlidingSchemaOutput(
            first_name=self._user.first_name,
            last_name=self._user.last_name,
            **self.dict(exclude={"password"})
        )


class MyTokenRefreshInputSchema(TokenRefreshInputSchema):
    pass


class MyTokenRefreshSlidingInputSchema(TokenRefreshSlidingInputSchema):
    pass


class MyTokenVerifyInputSchema(TokenVerifyInputSchema):
    pass


class MyTokenBlacklistInputSchema(TokenBlacklistInputSchema):
    pass


class InvalidTokenSchema(Schema):
    whatever: str


@pytest.mark.django_db
class TestTokenObtainPairViewCustomSchema(APIViewTestCase):
    view_name = "jwt:token_obtain_pair"

    @pytest.fixture(autouse=True)
    def setUp(self):
        super().setUp()
        self.username = "test_user"
        self.password = "test_password"

        self.user = User.objects.create_user(
            username=self.username,
            password=self.password,
            first_name="John",
            last_name="Doe",
        )

    def test_success(self, monkeypatch):
        with monkeypatch.context() as m:
            m.setattr(
                api_settings,
                "TOKEN_OBTAIN_PAIR_INPUT_SCHEMA",
                "tests.test_custom_schema.MyNewObtainPairSchemaInput",
            )
            res = self.view_post(
                data={
                    User.USERNAME_FIELD: self.username,
                    "password": self.password,
                },
                content_type="application/json",
            )

        assert res.status_code == 200

        assert "access" in res.data
        assert "refresh" in res.data

        assert res.data["first_name"] == "John"
        assert res.data["last_name"] == "Doe"


@pytest.mark.django_db
class TestTokenRefreshViewCustomSchema(APIViewTestCase):
    view_name = "jwt:token_refresh"

    @pytest.fixture(autouse=True)
    def setUp(self):
        super().setUp()
        self.username = "test_user"
        self.password = "test_password"

        self.user = User.objects.create_user(
            username=self.username,
            password=self.password,
        )

    def test_refresh_works_fine(self, monkeypatch):
        refresh = RefreshToken()
        refresh["test_claim"] = "arst"

        # View returns 200
        now = aware_utcnow() - api_settings.ACCESS_TOKEN_LIFETIME / 2
        with monkeypatch.context() as m:
            m.setattr(
                api_settings,
                "TOKEN_OBTAIN_PAIR_REFRESH_INPUT_SCHEMA",
                "tests.test_custom_schema.MyTokenRefreshInputSchema",
            )
            with patch("ninja_jwt.tokens.aware_utcnow") as fake_aware_utcnow:
                fake_aware_utcnow.return_value = now

                res = self.view_post(
                    data={"refresh": str(refresh)}, content_type="application/json"
                )

        assert res.status_code == 200

        access = AccessToken(res.data["access"])

        assert refresh["test_claim"] == access["test_claim"]
        assert access["exp"] == datetime_to_epoch(
            now + api_settings.ACCESS_TOKEN_LIFETIME
        )


@pytest.mark.django_db
class TestTokenObtainSlidingViewCustomSchema(APIViewTestCase):
    view_name = "jwt:token_obtain_sliding"

    @pytest.fixture(autouse=True)
    def setUp(self):
        super().setUp()
        self.username = "test_user"
        self.password = "test_password"

        self.user = User.objects.create_user(
            username=self.username,
            password=self.password,
            first_name="John",
            last_name="Doe",
        )

    def test_incomplete_data(self, monkeypatch):
        with monkeypatch.context() as m:
            m.setattr(
                api_settings,
                "TOKEN_OBTAIN_SLIDING_INPUT_SCHEMA",
                "tests.test_custom_schema.MyNewObtainTokenSlidingSchemaInput",
            )
            res = self.view_post(
                data={
                    User.USERNAME_FIELD: self.username,
                    "password": "test_password",
                },
                content_type="application/json",
            )
        assert res.status_code == 422
        assert res.data == {
            "detail": [
                {
                    "loc": ["body", "user_token", "my_extra_field"],
                    "msg": "field required",
                    "type": "value_error.missing",
                }
            ]
        }

    def test_success(self, monkeypatch):
        with monkeypatch.context() as m:
            m.setattr(
                api_settings,
                "TOKEN_OBTAIN_SLIDING_INPUT_SCHEMA",
                "tests.test_custom_schema.MyNewObtainTokenSlidingSchemaInput",
            )
            res = self.view_post(
                data={
                    User.USERNAME_FIELD: self.username,
                    "password": self.password,
                    "my_extra_field": "some_data",
                },
                content_type="application/json",
            )
        assert res.status_code == 200
        assert "token" in res.data
        assert res.data["first_name"] == "John"
        assert res.data["last_name"] == "Doe"


@pytest.mark.django_db
class TestTokenRefreshSlidingViewCustomSchema(APIViewTestCase):
    view_name = "jwt:token_refresh_sliding"

    @pytest.fixture(autouse=True)
    def setUp(self):
        super().setUp()
        self.username = "test_user"
        self.password = "test_password"

        self.user = User.objects.create_user(
            username=self.username,
            password=self.password,
        )

    def test_it_should_update_token_exp_claim_if_everything_ok(self, monkeypatch):
        now = aware_utcnow()

        token = SlidingToken()
        exp = now + api_settings.SLIDING_TOKEN_LIFETIME - timedelta(seconds=1)
        token.set_exp(
            from_time=now,
            lifetime=api_settings.SLIDING_TOKEN_LIFETIME - timedelta(seconds=1),
        )
        with monkeypatch.context() as m:
            m.setattr(
                api_settings,
                "TOKEN_OBTAIN_SLIDING_REFRESH_INPUT_SCHEMA",
                "tests.test_custom_schema.MyTokenRefreshSlidingInputSchema",
            )
            # View returns 200
            res = self.view_post(
                data={"token": str(token)}, content_type="application/json"
            )
        assert res.status_code == 200

        # Expiration claim has moved into future
        new_token = SlidingToken(res.data["token"])
        new_exp = datetime_from_epoch(new_token["exp"])

        assert exp < new_exp


@pytest.mark.django_db
class TestTokenVerifyViewCustomSchema(APIViewTestCase):
    view_name = "jwt:token_verify"

    @pytest.fixture(autouse=True)
    def setUp(self):
        super().setUp()
        self.username = "test_user"
        self.password = "test_password"

        self.user = User.objects.create_user(
            username=self.username,
            password=self.password,
        )

    def test_it_should_return_200_if_everything_okay(self, monkeypatch):
        token = RefreshToken()
        with monkeypatch.context() as m:
            m.setattr(
                api_settings,
                "TOKEN_VERIFY_INPUT_SCHEMA",
                "tests.test_custom_schema.MyTokenVerifyInputSchema",
            )
            res = self.view_post(
                data={"token": str(token)}, content_type="application/json"
            )
        assert res.status_code == 200
        assert res.data == {}


@pytest.mark.django_db
class TestTokenBlacklistViewCustomSchema(APIViewTestCase):
    view_name = "jwt:token_blacklist"

    @pytest.fixture(autouse=True)
    def setUp(self):
        super().setUp()
        self.username = "test_user"
        self.password = "test_password"

        self.user = User.objects.create_user(
            username=self.username,
            password=self.password,
        )

    def test_it_should_return_if_everything_ok(self, monkeypatch):
        refresh = RefreshToken()
        refresh["test_claim"] = "arst"

        # View returns 200
        now = aware_utcnow() - api_settings.ACCESS_TOKEN_LIFETIME / 2
        with monkeypatch.context() as m:
            m.setattr(
                api_settings,
                "TOKEN_BLACKLIST_INPUT_SCHEMA",
                "tests.test_custom_schema.MyTokenBlacklistInputSchema",
            )
            with patch("ninja_jwt.tokens.aware_utcnow") as fake_aware_utcnow:
                fake_aware_utcnow.return_value = now

                res = self.view_post(
                    data={"refresh": str(refresh)}, content_type="application/json"
                )

        assert res.status_code == 200

        assert res.data == {}


class TestSchemaControlExceptions:
    def test_verify_schema_exception(self, monkeypatch):
        with monkeypatch.context() as m:
            m.setattr(
                api_settings,
                "TOKEN_VERIFY_INPUT_SCHEMA",
                "tests.test_custom_schema.InvalidTokenSchema",
            )
            with pytest.raises(Exception) as ex:
                SchemaControl(api_settings)
            assert (
                str(ex.value)
                == "TOKEN_VERIFY_INPUT_SCHEMA type must inherit from `<class 'ninja_jwt.schema.InputSchemaMixin'>`"
            )

    def test_blacklist_schema_exception(self, monkeypatch):
        with monkeypatch.context() as m:
            m.setattr(
                api_settings,
                "TOKEN_BLACKLIST_INPUT_SCHEMA",
                "tests.test_custom_schema.InvalidTokenSchema",
            )
            with pytest.raises(Exception) as ex:
                SchemaControl(api_settings)
            assert (
                str(ex.value)
                == "TOKEN_BLACKLIST_INPUT_SCHEMA type must inherit from `<class 'ninja_jwt.schema.InputSchemaMixin'>`"
            )

    def test_obtain_pair_schema_exception(self, monkeypatch):
        with monkeypatch.context() as m:
            m.setattr(
                api_settings,
                "TOKEN_OBTAIN_PAIR_INPUT_SCHEMA",
                "tests.test_custom_schema.InvalidTokenSchema",
            )
            with pytest.raises(Exception) as ex:
                SchemaControl(api_settings)
            assert (
                str(ex.value)
                == "TOKEN_OBTAIN_PAIR_INPUT_SCHEMA type must inherit from `<class 'ninja_jwt.schema.TokenInputSchemaMixin'>`"
            )

    def test_obtain_pair_refresh_schema_exception(self, monkeypatch):
        with monkeypatch.context() as m:
            m.setattr(
                api_settings,
                "TOKEN_OBTAIN_PAIR_REFRESH_INPUT_SCHEMA",
                "tests.test_custom_schema.InvalidTokenSchema",
            )
            with pytest.raises(Exception) as ex:
                SchemaControl(api_settings)
            assert (
                str(ex.value)
                == "TOKEN_OBTAIN_PAIR_REFRESH_INPUT_SCHEMA type must inherit from `<class 'ninja_jwt.schema.InputSchemaMixin'>`"
            )

    def test_sliding_schema_exception(self, monkeypatch):
        with monkeypatch.context() as m:
            m.setattr(
                api_settings,
                "TOKEN_OBTAIN_SLIDING_INPUT_SCHEMA",
                "tests.test_custom_schema.InvalidTokenSchema",
            )
            with pytest.raises(Exception) as ex:
                SchemaControl(api_settings)
            assert (
                str(ex.value)
                == "TOKEN_OBTAIN_SLIDING_INPUT_SCHEMA type must inherit from `<class 'ninja_jwt.schema.TokenInputSchemaMixin'>`"
            )

    def test_sliding_refresh_schema_exception(self, monkeypatch):
        with monkeypatch.context() as m:
            m.setattr(
                api_settings,
                "TOKEN_OBTAIN_SLIDING_REFRESH_INPUT_SCHEMA",
                "tests.test_custom_schema.InvalidTokenSchema",
            )
            with pytest.raises(Exception) as ex:
                SchemaControl(api_settings)
            assert (
                str(ex.value)
                == "TOKEN_OBTAIN_SLIDING_REFRESH_INPUT_SCHEMA type must inherit from `<class 'ninja_jwt.schema.InputSchemaMixin'>`"
            )
