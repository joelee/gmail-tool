# Google Credentials

## Overview

This project supports two Google authentication modes:

- OAuth desktop flow for personal Gmail or Google Workspace users
- Service account with domain-wide delegation for Google Workspace administrators

Use OAuth unless you specifically manage a Workspace domain and need delegated access.

## OAuth Desktop Credentials

Use this flow for a normal Gmail account.

1. Open Google Cloud Console: `https://console.cloud.google.com/`
2. Create or select a project.
3. Enable the Gmail API:
   - Go to `APIs & Services` -> `Library`
   - Search for `Gmail API`
   - Click `Enable`
4. Configure the OAuth consent screen:
   - Go to `APIs & Services` -> `OAuth consent screen`
   - Choose `External` for personal Gmail, or `Internal` for Workspace if appropriate
   - Fill in the app name and required contact information
   - Add yourself as a test user if the app is in testing mode
5. Create OAuth client credentials:
   - Go to `APIs & Services` -> `Credentials`
   - Click `Create Credentials` -> `OAuth client ID`
   - Choose `Desktop app`
   - Download the JSON file
6. Save the downloaded JSON outside version control, for example `secrets/oauth-client-secret.json`
7. Update `.env`:

```dotenv
GOOGLE_OAUTH_CLIENT_SECRET_FILE=secrets/oauth-client-secret.json
GOOGLE_OAUTH_TOKEN_FILE=.secrets/oauth-token.json
GMAIL_USER_ID=me
```

8. Ensure `config.toml` contains:

```toml
[auth]
mode = "oauth"
scopes = ["https://www.googleapis.com/auth/gmail.readonly"]
```

9. Run the CLI once:

```bash
uv run gmail-tool labels
```

10. A browser window should open for consent. After approval, the refresh token will be stored at `GOOGLE_OAUTH_TOKEN_FILE`.

The live integration tests can also perform this first authorization if you run them with `ALLOW_GMAIL_OAUTH_BROWSER=true`.

## Service Account Credentials

Use this only for Google Workspace with domain-wide delegation.

1. Open Google Cloud Console: `https://console.cloud.google.com/`
2. Create or select a project.
3. Enable the Gmail API.
4. Create a service account:
   - Go to `IAM & Admin` -> `Service Accounts`
   - Click `Create Service Account`
   - Complete the creation flow
5. Enable domain-wide delegation for the service account if your Workspace setup requires it.
6. Create and download a JSON key for the service account.
7. In Google Workspace Admin, authorize the service account client ID for the Gmail scopes you need, such as `https://www.googleapis.com/auth/gmail.readonly`.
8. Save the downloaded JSON outside version control, for example `secrets/service-account.json`
9. Update `.env`:

```dotenv
GOOGLE_SERVICE_ACCOUNT_FILE=secrets/service-account.json
GOOGLE_SERVICE_ACCOUNT_SUBJECT=user@example.com
GMAIL_USER_ID=me
```

10. Update `config.toml`:

```toml
[auth]
mode = "service_account"
scopes = ["https://www.googleapis.com/auth/gmail.readonly"]
```

`GOOGLE_SERVICE_ACCOUNT_SUBJECT` should be the Workspace user mailbox to impersonate.

## Recommended Local Layout

- `.env`
- `config.toml`
- `secrets/oauth-client-secret.json`
- `secrets/service-account.json`
- `.secrets/oauth-token.json`

Credential JSON files and token files should remain untracked.

## Common Issues

- `access_denied` during OAuth: add your Google account as a test user on the OAuth consent screen.
- `invalid_grant` with stored OAuth token: delete the local token file and authenticate again.
- service account cannot access Gmail: verify Workspace domain-wide delegation is configured and the subject mailbox is valid.
- Gmail API not found: confirm the Gmail API is enabled in the selected Google Cloud project.

## Running Live Integration Tests

With an existing token file:

```bash
ENABLE_LIVE_GMAIL_TESTS=true uv run pytest -m live_gmail
```

To allow the first OAuth browser flow during tests:

```bash
ENABLE_LIVE_GMAIL_TESTS=true ALLOW_GMAIL_OAUTH_BROWSER=true uv run pytest -m live_gmail -s
```

These tests are intentionally skipped by default.
