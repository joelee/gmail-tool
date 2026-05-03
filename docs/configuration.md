# Configuration

## Files

- `config.toml`: checked-in application defaults and non-secret settings
- `.env`: local secret values and machine-specific paths

## Discovery Order

If `--config` is not passed, the CLI discovers the configuration file in this order:

1. `GMAIL_TOOL_CONFIG`
2. `${XDG_CONFIG_HOME}/gmail-tool/config.toml`
3. `${HOME}/.config/gmail-tool/config.toml`
4. `/etc/gmail-tool.toml`
5. `./config.toml` in the current project directory

If `--config` is passed, it takes precedence over all discovery paths.

## Example

```toml
[app]
default_limit = 100

[search.saved_queries]
recent_attachments = "has:attachment newer_than:30d"
ring_recent = "from:no-reply@rs.ring.com newer_than:7d"

[auth]
mode = "oauth"
scopes = ["https://www.googleapis.com/auth/gmail.readonly"]

[auth.oauth]
client_secret_env = "GOOGLE_OAUTH_CLIENT_SECRET_FILE"
token_file_env = "GOOGLE_OAUTH_TOKEN_FILE"

[auth.service_account]
service_account_file_env = "GOOGLE_SERVICE_ACCOUNT_FILE"
subject_env = "GOOGLE_SERVICE_ACCOUNT_SUBJECT"

[backup]
path = "backup"

[gmail]
user_id_env = "GMAIL_USER_ID"
```

## Notes

- Auth mode can be `oauth` or `service_account`.
- Secret values are read indirectly from environment variables referenced by `config.toml`.
- Keep credential files outside version control.
- For setup instructions, see `docs/google-credentials.md`.
- `app.default_limit` is used when `--limit` is not provided. The default is `100`.
- `search.saved_queries` defines reusable raw Gmail queries for the `search --saved-query <name>` command path.
- `backup.path` sets the default root directory for the `backup` action. Relative paths resolve from the config file directory.
