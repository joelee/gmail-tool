# Configuration

## Files

- `config.toml`: checked-in application defaults and non-secret settings
- `.env`: local secret values and machine-specific paths

## Example

```toml
[app]
default_limit = 1000

[auth]
mode = "oauth"
scopes = ["https://www.googleapis.com/auth/gmail.readonly"]

[auth.oauth]
client_secret_env = "GOOGLE_OAUTH_CLIENT_SECRET_FILE"
token_file_env = "GOOGLE_OAUTH_TOKEN_FILE"

[auth.service_account]
service_account_file_env = "GOOGLE_SERVICE_ACCOUNT_FILE"
subject_env = "GOOGLE_SERVICE_ACCOUNT_SUBJECT"

[gmail]
user_id_env = "GMAIL_USER_ID"
```

## Notes

- Auth mode can be `oauth` or `service_account`.
- Secret values are read indirectly from environment variables referenced by `config.toml`.
- Keep credential files outside version control.
- For setup instructions, see `docs/google-credentials.md`.
- `app.default_limit` is used when `--limit` is not provided. The default is `1000`.
