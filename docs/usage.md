# Usage

## Command Summary

```bash
uv run gmail-tool labels
uv run gmail-tool labels --format json
uv run gmail-tool auth-check
uv run gmail-tool read <MESSAGE_ID>
uv run gmail-tool label --list-actions
uv run gmail-tool label <LABEL> <ACTION> [OPTIONS]
```

## Commands

### List Labels

```bash
uv run gmail-tool labels
```

Prints all Gmail labels visible to the configured account.

Structured formats are also available:

```bash
uv run gmail-tool labels --format json
uv run gmail-tool labels --format csv
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

### List Supported Actions

```bash
uv run gmail-tool label --list-actions
```

Current actions:

```text
count
list
```

### Run A Label Action

```bash
uv run gmail-tool label <LABEL> <ACTION> [OPTIONS]
```

Supported options:

- `--limit <N>` for actions that return message rows. If omitted, the default is `1000`.
- `--from-date YYYY-MM-DD`
- `--to-date YYYY-MM-DD`
- `--starred true|false`

For `label <LABEL> list`, you can also use:

- `--format json`
- `--format csv`

## Examples

Count all messages in `INBOX`:

```bash
uv run gmail-tool label INBOX count
```

Count starred messages in `IMPORTANT` since a date:

```bash
uv run gmail-tool label IMPORTANT count --from-date 2026-01-01 --starred true
```

List the latest five message headers in `INBOX`:

```bash
uv run gmail-tool label INBOX list --limit 5
```

The plain-text output includes `message_id=...` so you can read a specific message:

```bash
uv run gmail-tool read <MESSAGE_ID>
```

List the latest five message headers in JSON:

```bash
uv run gmail-tool label INBOX list --limit 5 --format json
```

Export label names as CSV:

```bash
uv run gmail-tool labels --format csv
```

List non-starred messages in a custom label within a date window:

```bash
uv run gmail-tool label JW/Receipts list --from-date 2026-01-01 --to-date 2026-01-31 --starred false --limit 10
```

## Notes

- Dates are interpreted as Gmail search date filters.
- `--to-date` is compiled as an exclusive upper bound on the next day.
- `--list-actions` does not require Gmail authentication because it reads from the local action registry.
- `--format json|csv` is supported for `labels` and `label <LABEL> list`.
- `label <LABEL> list` includes a `message_id` field in text, JSON, and CSV output.
