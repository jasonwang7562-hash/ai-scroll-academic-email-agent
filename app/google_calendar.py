from __future__ import annotations

import os
from datetime import datetime, timedelta
from pathlib import Path

from app.gmail_connector import client_secrets_path
from app.models import CalendarProposal, CalendarWriteResult


GOOGLE_CALENDAR_SCOPE = "https://www.googleapis.com/auth/calendar.events"
ROOT = Path(__file__).resolve().parents[1]


def google_calendar_token_path() -> Path:
    raw = os.getenv("AI_SCROLL_GOOGLE_CALENDAR_TOKEN", "data/private/google_calendar_token.json")
    path = Path(raw).expanduser()
    return path if path.is_absolute() else ROOT / path


def google_calendar_is_authorized() -> bool:
    return client_secrets_path().is_file() and google_calendar_token_path().is_file()


class GoogleCalendarStore:
    """Google Calendar adapter used only after the approval gate confirms a proposal."""

    def __init__(self, service=None, calendar_id: str = "primary"):
        self.service = service
        self.calendar_id = calendar_id

    def _service(self):
        if self.service is not None:
            return self.service
        try:
            from google.auth.transport.requests import Request
            from google.oauth2.credentials import Credentials
            from googleapiclient.discovery import build
        except ImportError as exc:
            raise RuntimeError("Google Calendar dependencies are missing.") from exc
        token_path = google_calendar_token_path()
        if not token_path.is_file():
            raise RuntimeError("Google Calendar is not authorized yet.")
        credentials = Credentials.from_authorized_user_file(
            str(token_path), [GOOGLE_CALENDAR_SCOPE]
        )
        if credentials.expired and credentials.refresh_token:
            credentials.refresh(Request())
            token_path.write_text(credentials.to_json(), encoding="utf-8")
        if not credentials.valid:
            raise RuntimeError("Google Calendar authorization is invalid or expired.")
        self.service = build("calendar", "v3", credentials=credentials, cache_discovery=False)
        return self.service

    @staticmethod
    def _event_body(proposal: CalendarProposal) -> dict:
        start = datetime.fromisoformat(proposal.start)
        end = start + timedelta(minutes=30)
        return {
            "summary": proposal.title,
            "description": proposal.description,
            "start": {"dateTime": start.isoformat(), "timeZone": proposal.timezone},
            "end": {"dateTime": end.isoformat(), "timeZone": proposal.timezone},
            "extendedProperties": {
                "private": {"aiScrollProposalId": proposal.proposal_id}
            },
        }

    def create_or_update(self, proposal: CalendarProposal) -> CalendarWriteResult:
        service = self._service()
        existing = (
            service.events()
            .list(
                calendarId=self.calendar_id,
                privateExtendedProperty=f"aiScrollProposalId={proposal.proposal_id}",
                maxResults=1,
            )
            .execute()
            .get("items", [])
        )
        if existing and proposal.action == "create":
            return CalendarWriteResult(
                event_id=existing[0]["id"],
                proposal_id=proposal.proposal_id,
                status="deduplicated",
                external_write=False,
            )
        body = self._event_body(proposal)
        if existing:
            event = (
                service.events()
                .update(
                    calendarId=self.calendar_id,
                    eventId=existing[0]["id"],
                    body=body,
                )
                .execute()
            )
        else:
            event = (
                service.events()
                .insert(calendarId=self.calendar_id, body=body)
                .execute()
            )
        return CalendarWriteResult(
            event_id=event["id"],
            proposal_id=proposal.proposal_id,
            status="committed",
            external_write=True,
        )

