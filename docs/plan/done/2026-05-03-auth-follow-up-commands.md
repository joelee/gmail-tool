# Auth Follow-Up Commands Plan

## Goals

- Add `gmail-tool auth logout` to remove the stored OAuth token.
- Add `gmail-tool auth paths` to print resolved auth-related file paths.
- Add `gmail-tool auth login --no-browser` for copy-paste style OAuth flows.

## Notes

- `auth logout` should only remove the local OAuth token and should not touch the client secret file.
- `auth paths` should work without Gmail access.
- `--no-browser` should still rely on the Google Desktop OAuth client and should fall back to console flow support from `google-auth-oauthlib`.
