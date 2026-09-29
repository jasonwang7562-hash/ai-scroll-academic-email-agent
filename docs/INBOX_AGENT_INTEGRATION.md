# Inbox agent integration

AI Scroll now has a connector boundary and an autonomous run loop. The local demo connector proves the product flow without claiming access to a real mailbox: fetch new messages, filter unrelated mail, consolidate course threads and stop at human review.

## Real mailbox implementation

1. Add a Gmail connector using OAuth with `gmail.readonly`, or a Microsoft Graph connector using delegated `Mail.Read`.
2. Store refresh tokens outside the repository in an OS or deployment secret store.
3. Fetch only messages newer than the last provider cursor or delta token.
4. Send only selected academic messages to extraction; ordinary personal mail remains outside the model path.
5. Keep calendar permission separate. A proposal must pass the existing evidence and approval gate before any write.
6. Log provider message IDs, processing decisions and model usage without storing unnecessary message bodies.

OAuth client credentials and one user authorization are required before the real connector can be enabled. The UI therefore labels the current connector as a local demo mailbox rather than pretending that Gmail or Outlook is connected.

## Gmail setup now implemented

1. Enable Gmail API in a Google Cloud project.
2. Configure the OAuth consent screen, keep the app in testing, and add the mailbox owner as a test user.
3. Create an OAuth client ID for a Desktop app.
4. Save the downloaded JSON as `data/private/google_client_secret.json`.
5. Run `python scripts/authorize_gmail.py`, or select **Start Gmail authorization** in the Agent workspace.
6. Approve the read-only Gmail scope. The refresh token is stored at `data/private/gmail_token.json` and both files remain outside Git.

The real connector currently reads at most 100 messages from the last 60 days. It does not send, modify or delete email. The agent still filters for academic course codes before building the timeline.
