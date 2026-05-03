# Gmail Search Operators Cheat Sheet

## Core Operators

- `from:` sender address or name
  Example: `from:bob@example.com`
- `to:` recipient address or name
  Example: `to:alice@example.com`
- `subject:` match subject text
  Example: `subject:invoice`
- quoted text for exact phrase matching
  Example: `"monthly report"`

## Status And Flags

- `is:starred` starred messages
- `is:unread` unread messages
- `is:read` read messages
- `has:attachment` messages with attachments
- `is:important` important messages

## Date And Time

- `after:` messages after a date
  Example: `after:2026/05/01`
- `before:` messages before a date
  Example: `before:2026/06/01`
- `older_than:` relative age filter
  Example: `older_than:30d`
- `newer_than:` relative age filter
  Example: `newer_than:7d`

## Labels And Folders

- `label:` specific label
  Example: `label:INBOX`
- `in:` system location
  Example: `in:sent`

## Size

- `larger:` size in bytes
  Example: `larger:1000000`
- `smaller:` size in bytes
  Example: `smaller:500000`

## Boolean Operators

- space means AND
  Example: `from:bob@example.com has:attachment`
- `OR` matches either side
  Example: `from:bob@example.com OR from:alice@example.com`
- `-` negates a term
  Example: `-label:spam`
