# Message Read Command Plan

## Goals

- Include a message identifier in label list output.
- Add `gmail-tool read <message-identifier>` to print full message headers and decoded content.
- Keep the implementation compatible with the existing Gmail gateway abstraction.

## Design Plan

1. Extend the message-header model to include a stable message identifier.
2. Update the `list` action and CLI formatting to display the identifier.
3. Add a Gmail gateway method to fetch a single message in full format.
4. Decode message body data, preferring plain text and falling back when necessary.
5. Add an application method and CLI command for reading a message by identifier.
6. Update usage docs and examples.

## TDD Strategy

- Update existing list-related tests first to require the identifier.
- Add CLI and application tests for the new `read` command before implementation.

## Integration Test Coverage Plan

- Verify the application returns message identifiers in the list action path.
- Verify the application can fetch and return a single message with headers and content through the gateway abstraction.

## Risks

- Gmail message bodies can be multipart and nested.
- Some messages may have HTML-only bodies, so body extraction should use a clear fallback order.
