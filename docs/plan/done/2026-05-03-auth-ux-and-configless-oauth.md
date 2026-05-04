# Auth UX And Configless OAuth Plan

## Goals

- Remove the requirement for `config.toml` in the common OAuth desktop flow.
- Add a guided `gmail-tool auth login` command for first-run setup.
- Print actionable setup instructions instead of raw config or auth exceptions.
- Use XDG defaults for OAuth client secret and token files when env vars are unset.
- Ensure the OAuth client secret file is private before use.

## Implementation

1. Add built-in default settings for OAuth mode, Gmail readonly scope, and `gmail_user_id=me`.
2. Keep `config.toml` optional and only override defaults when present.
3. Add default OAuth paths:
   - client secret: `${XDG_CONFIG_HOME:-~/.config}/gmail-tool/client_secret.json`
   - token: `${XDG_STATE_HOME:-~/.local/state}/gmail-tool/oauth-token.json`
4. Add `auth` subcommands:
   - `gmail-tool auth login`
   - `gmail-tool auth check`
5. Keep `auth-check` as a compatibility alias.
6. Fail with guided setup text when OAuth prerequisites are missing.
7. Enforce strict file permissions on the OAuth client secret file before reading it.

## Notes

- Google Cloud Console setup cannot be fully automated because users still need to create their own Desktop OAuth client.
- The CLI can automate the browser login and token persistence after the client secret file is present.
