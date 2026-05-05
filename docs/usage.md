# Usage

## Command Summary

```bash
gmail-tool --version
gmail-tool --verbose labels
gmail-tool labels
gmail-tool labels -f json
gmail-tool auth login
gmail-tool auth check
gmail-tool auth paths
gmail-tool auth logout
gmail-tool message read <MESSAGE_ID>
gmail-tool message delete <MESSAGE_ID>
gmail-tool search <QUERY_PARTS...>
gmail-tool search --list-actions
gmail-tool search --list-query-examples
gmail-tool search --cheat-sheet
gmail-tool search --saved-query <NAME>
gmail-tool label --list-actions
gmail-tool label <LABEL> [OPTIONS]
```

## Commands

### Global Options

- `--version` or `-V`: print the CLI version and exit.
- `--verbose` or `-v`: print debug information such as the resolved config path to stderr.
- `--help` or `-h`: show help.

Most command options also support short aliases:

- `-c` for `--config`
- `-f` for `--format`
- `-l` for `--limit`
- `-a` for `--action`

### List Labels

```bash
gmail-tool labels
```

Prints all Gmail labels visible to the configured account.

Structured formats are also available:

```bash
gmail-tool labels -f json
gmail-tool labels -f csv
```

### Auth Check

```bash
gmail-tool auth check
```

Performs a lightweight read-only auth and Gmail reachability check.

### Auth Login

```bash
gmail-tool auth login
```

Starts the OAuth desktop browser flow and stores the refresh token locally.

Force a fresh browser login even if a token already exists:

```bash
gmail-tool auth login --force
```

Use a copy-paste console flow instead of opening a browser:

```bash
gmail-tool auth login --no-browser
```

Default OAuth file locations when no overrides are set:

- client secret: `${XDG_CONFIG_HOME:-~/.config}/gmail-tool/client_secret.json`
- token: `${XDG_STATE_HOME:-~/.local/state}/gmail-tool/oauth-token.json`

### Auth Paths

```bash
gmail-tool auth paths
```

Prints the resolved auth mode, OAuth file locations, service account file path, and Gmail user ID.

### Auth Logout

```bash
gmail-tool auth logout
```

Deletes the locally stored OAuth token file without touching the client secret file.

Example output:

```text
auth_mode=oauth
gmail_user_id=me
label_count=69
```

### Message Read

```bash
gmail-tool message read <MESSAGE_ID>
```

Prints the full message headers and decoded message body for the given Gmail message identifier.

### Message Delete

```bash
gmail-tool message delete <MESSAGE_ID>
```

Moves the given Gmail message to Bin after prompting for confirmation.

Skip the confirmation prompt:

```bash
gmail-tool message delete <MESSAGE_ID> --force
```

### Search Messages

```bash
gmail-tool search <QUERY_PARTS...>
```

Runs a raw Gmail search query and lists matching messages with the same output structure as `label <LABEL> list`.

Supported options:

- `--action <NAME>` or `-a <NAME>`. Defaults to `list`.
- `--limit <N>` or `-l <N>`
- `--format json|csv` or `-f json|csv` for `list`
- `--from-date YYYY-MM-DD`
- `--to-date YYYY-MM-DD`
- `--starred true|false`
- `--saved-query <NAME>`
- `--force` with `delete` to skip the confirmation prompt
- `--backup-path <DIR>` for `backup`
- `--delete` for `backup` to move successfully written messages to Bin
- `--force` with `--delete` for `backup` to skip the confirmation prompt
- `--list-actions`
- `--help-action <NAME>`
- `--list-query-examples`
- `--cheat-sheet`

Mutation actions:

- `backup`
- `delete`
- `label-add` with `--name <label_name>`
- `label-remove` with `--name <label_name>`

Examples:

```bash
gmail-tool search from:bob@example.com has:attachment
gmail-tool search newer_than:7d -f json
gmail-tool search subject:invoice --starred true -l 20
gmail-tool search --saved-query recent_attachments
gmail-tool search --saved-query ring_recent has:drive
gmail-tool search -a count from:bob@example.com
gmail-tool search -a delete from:bob@example.com
gmail-tool search -a delete --force from:bob@example.com
gmail-tool search -a backup from:bob@example.com
gmail-tool search -a backup --backup-path /tmp/gmail-backups from:bob@example.com
gmail-tool search -a backup --backup-path /tmp/gmail-backups --delete from:bob@example.com
gmail-tool search -a backup --backup-path /tmp/gmail-backups --delete --force from:bob@example.com
gmail-tool search --help-action backup
gmail-tool search --help-action delete
gmail-tool search -a label-add --name FollowUp from:bob@example.com
gmail-tool search -a label-remove --name Existing from:bob@example.com
```

Built-in query examples:

```bash
gmail-tool search --list-query-examples
```

Operator cheat sheet:

```bash
gmail-tool search --cheat-sheet
```

The same content is also available in `docs/search-cheat-sheet.md`.

### List Supported Actions

```bash
gmail-tool label --list-actions
gmail-tool search --list-actions
gmail-tool search --help-action backup
gmail-tool label --help-action label-add
```

Current actions:

```text
backup                     Back up matching messages as .eml files.
count                      Print the number of matching messages.
delete                     Move all matching messages to Bin.
label-add                  Add a label to all matching messages.
label-remove               Remove a label from all matching messages.
list                       List matching message headers.
```

### Run A Label Action

```bash
gmail-tool label <LABEL> [OPTIONS]
```

`<LABEL>` may be either an exact Gmail label name, such as `@Later`, or an exact Gmail label ID, such as `Label_66`.

Supported options:

- `--action <NAME>` or `-a <NAME>`. Defaults to `list`.
- `--name <LABEL_NAME>` for `label-add` and `label-remove`
- `--help-action <NAME>`
- `--force` with `delete` to skip the confirmation prompt
- `--backup-path <DIR>` for `backup`
- `--delete` for `backup` to move successfully written messages to Bin
- `--force` with `--delete` for `backup` to skip the confirmation prompt
- `--limit <N>` or `-l <N>` for actions that return message rows. If omitted, the default is `100`.
- `--from-date YYYY-MM-DD`
- `--to-date YYYY-MM-DD`
- `--starred true|false`

For `label <LABEL> list`, you can also use:

- `--format json`
- `--format csv`

Short forms:

- `-f json`
- `-f csv`

## Examples

Count all messages in `INBOX`:

```bash
gmail-tool label INBOX -a count
gmail-tool label INBOX -a delete
gmail-tool label INBOX -a delete --force
```

Back up matching messages in `INBOX`:

```bash
gmail-tool label INBOX -a backup
gmail-tool label INBOX -a backup --backup-path /tmp/gmail-backups
gmail-tool label INBOX -a backup --backup-path /tmp/gmail-backups --delete
gmail-tool label INBOX -a backup --backup-path /tmp/gmail-backups --delete --force
```

Count starred messages in `IMPORTANT` since a date:

```bash
gmail-tool label IMPORTANT -a count --from-date 2026-01-01 --starred true
```

Add a label to all matching messages in `INBOX`:

```bash
gmail-tool label INBOX -a label-add --name FollowUp
```

Remove a label from all matching messages in `INBOX`:

```bash
gmail-tool label INBOX -a label-remove --name Existing
```

List the latest five message headers in `INBOX`:

```bash
gmail-tool label INBOX -l 5
```

The plain-text output includes `message_id=...` so you can read a specific message:

```bash
gmail-tool message read <MESSAGE_ID>
```

Search for recent attachment emails and export them as CSV:

```bash
gmail-tool search has:attachment newer_than:30d -f csv
```

Run a saved query from `config.toml`:

```bash
gmail-tool search --saved-query recent_attachments
```

Count search matches without listing them:

```bash
gmail-tool search -a count from:bob@example.com
```

List the latest five message headers in JSON:

```bash
gmail-tool label INBOX -l 5 -f json
```

Export label names as CSV:

```bash
gmail-tool labels -f csv
```

List non-starred messages in a custom label within a date window:

```bash
gmail-tool label JW/Receipts --from-date 2026-01-01 --to-date 2026-01-31 --starred false -l 10
```

## Notes

- Dates are interpreted as Gmail search date filters.
- `--to-date` is compiled as an exclusive upper bound on the next day.
- `--config <path>` or `-c <path>` overrides config discovery for any command.
- `config.toml` is optional for the normal OAuth flow.
- `--list-actions` works on both `label` and `search` and does not require Gmail authentication because it reads from the local action registry.
- `--help-action <name>` works on both `label` and `search` and does not require Gmail authentication because it reads from the local action registry.
- `--format json|csv` is supported for `labels` and `label <LABEL> list`.
- `label <LABEL> list` includes a `message_id` field in text, JSON, and CSV output.
- `message delete` moves the selected message to Gmail Bin and prompts unless `--force` is used.
- `label <LABEL>` accepts an exact Gmail label name or an exact Gmail label ID.
- `delete` moves each matching message to the Gmail Bin.
- `delete` prompts before deleting, and `--force` bypasses that confirmation.
- `backup` writes `.eml` files to `YYYY/MM-DD/YYYYMMDD-HHmmss-<message_id>.eml` under the configured backup root.
- `backup` skips already backed-up `message_id` values so interrupted runs can resume efficiently.
- `backup --delete` moves each successfully written message to the Gmail Bin after the file is created.
- `backup --delete` prompts before deleting, and `--force` bypasses that confirmation.
- Long-running batch actions such as `backup`, `delete`, `label-add`, and `label-remove` print a single-line progress update per message to stderr.
- `search` accepts raw Gmail query arguments and supports the same `--limit`, `--format`, and global filters as message listing.
- `search --list-query-examples` prints built-in Gmail query examples without accessing Gmail.
- `search --cheat-sheet` prints a quick Gmail operator reference without accessing Gmail.
- `search --saved-query <name>` loads reusable raw queries from `config.toml`.
- `search` defaults to the `list` action when `--action` is omitted.
- `label` defaults to the `list` action when `--action` is omitted.
