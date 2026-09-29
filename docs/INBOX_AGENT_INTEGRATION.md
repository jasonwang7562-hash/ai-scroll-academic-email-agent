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

## Outlook / Microsoft 365 setup now implemented

1. Register a public client application in Microsoft Entra.
2. Add the Mobile and desktop application platform with `http://localhost` and allow public client flows.
3. Add the delegated Microsoft Graph `Mail.Read` permission.
4. Enter the Application (client) ID and Directory (tenant) ID in the Agent workspace.
5. Start Outlook authorization and sign in with the student Microsoft 365 account.

The client configuration and MSAL token cache are stored in ignored files under `data/private`. The connector reads up to 100 recent Inbox messages through Microsoft Graph and cannot send, modify or delete email.

### Personal Outlook fallback for restricted university tenants

When a university tenant blocks app registration and third-party Graph clients, AI Scroll can use a personal Outlook account as a restricted ingestion mailbox:

1. Add an Outlook rule that forwards only selected course messages to the personal account while retaining the original.
2. Authorize the personal account through Microsoft's official Graph Command Line Tools with delegated `Mail.Read`.
3. AI Scroll reuses the local Microsoft authentication cache and reads the personal Inbox through Microsoft Graph.

This avoids forwarding the entire student mailbox and avoids requiring the university to register an application. It should be documented as a provider-policy fallback, with the forwarded filter and privacy boundary stated explicitly.

## Scan policy and audit trail

The Agent workspace accepts a comma-separated course scope. Messages are classified before extraction:

- a matching course code is processed;
- a detected course outside the configured scope is ignored;
- a message without a course code is ignored.

The UI records the sender, subject, matched course code, decision and reason. It does not display or send the body of ignored messages to extraction. Each run also records elapsed time so the live demo can show operational behavior as well as model output.
