from gmail_tool.auth import (
    OAuthCredentialsProvider,
    ServiceAccountCredentialsProvider,
    build_credentials_provider,
)
from gmail_tool.config import (
    AppSettings,
    AuthMode,
    AuthSettings,
    GmailSettings,
    OAuthSettings,
    SearchSettings,
    ServiceAccountSettings,
    Settings,
)


def test_build_credentials_provider_for_oauth() -> None:
    settings = Settings(
        app=AppSettings(default_limit=100),
        search=SearchSettings(saved_queries={}),
        auth=AuthSettings(
            mode=AuthMode.OAUTH,
            scopes=["scope-a"],
            oauth=OAuthSettings(client_secret_file="secret.json", token_file="token.json"),
            service_account=ServiceAccountSettings(
                service_account_file="service.json",
                subject="user@example.com",
            ),
        ),
        gmail=GmailSettings(user_id="me"),
    )

    provider = build_credentials_provider(settings)

    assert isinstance(provider, OAuthCredentialsProvider)


def test_build_credentials_provider_for_service_account() -> None:
    settings = Settings(
        app=AppSettings(default_limit=100),
        search=SearchSettings(saved_queries={}),
        auth=AuthSettings(
            mode=AuthMode.SERVICE_ACCOUNT,
            scopes=["scope-a"],
            oauth=OAuthSettings(client_secret_file="secret.json", token_file="token.json"),
            service_account=ServiceAccountSettings(
                service_account_file="service.json",
                subject="user@example.com",
            ),
        ),
        gmail=GmailSettings(user_id="me"),
    )

    provider = build_credentials_provider(settings)

    assert isinstance(provider, ServiceAccountCredentialsProvider)
