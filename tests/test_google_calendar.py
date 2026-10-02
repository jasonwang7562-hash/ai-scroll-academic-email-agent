from app.google_calendar import GoogleCalendarStore
from app.models import CalendarProposal


class _Request:
    def __init__(self, value):
        self.value = value

    def execute(self):
        return self.value


class _Events:
    def __init__(self, existing=None):
        self.existing = existing or []
        self.inserted = None
        self.updated = None

    def list(self, **kwargs):
        return _Request({"items": self.existing})

    def insert(self, **kwargs):
        self.inserted = kwargs
        return _Request({"id": "google-event-1"})

    def update(self, **kwargs):
        self.updated = kwargs
        return _Request({"id": kwargs["eventId"]})


class _Service:
    def __init__(self, events):
        self._events = events

    def events(self):
        return self._events


def proposal(action="create"):
    return CalendarProposal(
        proposal_id="proposal-123",
        source_thread_id="thread-1",
        title="PE6201 - Course project",
        start="2026-10-04T23:59:00+08:00",
        timezone="Asia/Singapore",
        description="Evidence retained",
        action=action,
    )


def test_google_calendar_store_creates_traceable_event():
    events = _Events()
    result = GoogleCalendarStore(service=_Service(events)).create_or_update(proposal())
    assert result.status == "committed"
    assert result.external_write is True
    assert events.inserted["body"]["extendedProperties"]["private"]["aiScrollProposalId"] == "proposal-123"
    assert events.inserted["body"]["end"]["dateTime"] == "2026-10-05T00:29:00+08:00"


def test_google_calendar_store_deduplicates_create_retry():
    events = _Events(existing=[{"id": "existing-event"}])
    result = GoogleCalendarStore(service=_Service(events)).create_or_update(proposal())
    assert result.status == "deduplicated"
    assert result.event_id == "existing-event"
    assert events.inserted is None


def test_google_calendar_store_updates_existing_event():
    events = _Events(existing=[{"id": "existing-event"}])
    result = GoogleCalendarStore(service=_Service(events)).create_or_update(proposal("update"))
    assert result.status == "committed"
    assert events.updated["eventId"] == "existing-event"
