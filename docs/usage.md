# Usage

## Command Summary

```bash
uv run gmail-tool --version
uv run gmail-tool --verbose labels
uv run gmail-tool labels
uv run gmail-tool labels -f json
uv run gmail-tool auth-check
uv run gmail-tool read <MESSAGE_ID>
uv run gmail-tool search <QUERY_PARTS...>
uv run gmail-tool search --list-actions
uv run gmail-tool search --list-query-examples
uv run gmail-tool search --cheat-sheet
uv run gmail-tool search --saved-query <NAME>
uv run gmail-tool label --list-actions
uv run gmail-tool label <LABEL> [OPTIONS]
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
uv run gmail-tool labels
```

Prints all Gmail labels visible to the configured account.

Structured formats are also available:

```bash
uv run gmail-tool labels -f json
uv run gmail-tool labels -f csv
```

### Auth Check

```bash
uv run gmail-tool auth-check
```

Performs a lightweight read-only auth and Gmail reachability check.

Example output:

```text
auth_mode=oauth
gmail_user_id=me
label_count=69
```

### Read A Message

```bash
uv run gmail-tool read <MESSAGE_ID>
```

Prints the full message headers and decoded message body for the given Gmail message identifier.

### Search Messages

```bash
uv run gmail-tool search <QUERY_PARTS...>
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
- `--backup-path <DIR>` for `backup`
- `--list-actions`
- `--list-query-examples`
- `--cheat-sheet`

Mutation actions:

- `backup`
- `label-add:<label_name>`
- `label-remove:<label_name>`

Examples:

```bash
uv run gmail-tool search from:bob@example.com has:attachment
uv run gmail-tool search newer_than:7d -f json
uv run gmail-tool search subject:invoice --starred true -l 20
uv run gmail-tool search --saved-query recent_attachments
uv run gmail-tool search --saved-query ring_recent has:drive
uv run gmail-tool search -a count from:bob@example.com
uv run gmail-tool search -a backup from:bob@example.com
uv run gmail-tool search -a backup --backup-path /tmp/gmail-backups from:bob@example.com
uv run gmail-tool search -a label-add:FollowUp from:bob@example.com
uv run gmail-tool search -a label-remove:Existing from:bob@example.com
```

Built-in query examples:

```bash
uv run gmail-tool search --list-query-examples
```

Operator cheat sheet:

```bash
uv run gmail-tool search --cheat-sheet
```

The same content is also available in `docs/search-cheat-sheet.md`.

### List Supported Actions

```bash
uv run gmail-tool label --list-actions
uv run gmail-tool search --list-actions
```

Current actions:

```text
backup                     Back up matching messages as .eml files.
count                      Print the number of matching messages.
label-add:<label_name>     Add a label to all matching messages.
label-remove:<label_name>  Remove a label from all matching messages.
list                       List matching message headers.
```

### Run A Label Action

```bash
uv run gmail-tool label <LABEL> [OPTIONS]
```

`<LABEL>` may be either an exact Gmail label name, such as `@Later`, or an exact Gmail label ID, such as `Label_66`.

Supported options:

- `--action <NAME>` or `-a <NAME>`. Defaults to `list`.
- `--backup-path <DIR>` for `backup`
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
uv run gmail-tool label INBOX -a count
```

Back up matching messages in `INBOX`:

```bash
uv run gmail-tool label INBOX -a backup
uv run gmail-tool label INBOX -a backup --backup-path /tmp/gmail-backups
```

Count starred messages in `IMPORTANT` since a date:

```bash
uv run gmail-tool label IMPORTANT -a count --from-date 2026-01-01 --starred true
```

Add a label to all matching messages in `INBOX`:

```bash
uv run gmail-tool label INBOX -a label-add:FollowUp
```

Remove a label from all matching messages in `INBOX`:

```bash
uv run gmail-tool label INBOX -a label-remove:Existing
```

List the latest five message headers in `INBOX`:

```bash
uv run gmail-tool label INBOX -l 5
```

The plain-text output includes `message_id=...` so you can read a specific message:

```bash
uv run gmail-tool read <MESSAGE_ID>
```

Search for recent attachment emails and export them as CSV:

```bash
uv run gmail-tool search has:attachment newer_than:30d -f csv
```

Run a saved query from `config.toml`:

```bash
uv run gmail-tool search --saved-query recent_attachments
```

Count search matches without listing them:

```bash
uv run gmail-tool search -a count from:bob@example.com
```

List the latest five message headers in JSON:

```bash
uv run gmail-tool label INBOX -l 5 -f json
```

Export label names as CSV:

```bash
uv run gmail-tool labels -f csv
```

List non-starred messages in a custom label within a date window:

```bash
uv run gmail-tool label JW/Receipts --from-date 2026-01-01 --to-date 2026-01-31 --starred false -l 10
```

## Notes

- Dates are interpreted as Gmail search date filters.
- `--to-date` is compiled as an exclusive upper bound on the next day.
- `--config <path>` or `-c <path>` overrides config discovery for any command.
- `--list-actions` works on both `label` and `search` and does not require Gmail authentication because it reads from the local action registry.
- `--format json|csv` is supported for `labels` and `label <LABEL> list`.
- `label <LABEL> list` includes a `message_id` field in text, JSON, and CSV output.
- `label <LABEL>` accepts an exact Gmail label name or an exact Gmail label ID.
- `backup` writes `.eml` files to `YYYY/MM-DD/YYYYMMDD-HHmmss-<message_id>.eml` under the configured backup root.
- `backup` skips already backed-up `message_id` values so interrupted runs can resume efficiently.
- `search` accepts raw Gmail query arguments and supports the same `--limit`, `--format`, and global filters as message listing.
- `search --list-query-examples` prints built-in Gmail query examples without accessing Gmail.
- `search --cheat-sheet` prints a quick Gmail operator reference without accessing Gmail.
- `search --saved-query <name>` loads reusable raw queries from `config.toml`.
- `search` defaults to the `list` action when `--action` is omitted.
- `label` defaults to the `list` action when `--action` is omitted.
