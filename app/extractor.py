from __future__ import annotations

import csv
import hashlib
import json
import os
import re
import time
import urllib.error
import urllib.request
from pathlib import Path

from app.date_validation import parse_deadline, urgency_for
from app.live_config import load_local_env
from app.models import EmailInput, ExtractedTask


load_local_env()


PROMPT_VERSION = "v1.1"
COURSE_PATTERN = re.compile(r"\b[A-Z]{2,4}\d{4}[A-Z]?\b")
ACTION_PATTERN = re.compile(
    r"\b(due|deadline|submit|submitted|upload|complete|post|send|bring|exam|quiz|"
    r"meeting|class|cancelled|canceled|extended|moved|reminder|workshop|briefing|"
    r"presentation|consultation|registration|survey)\b",
    re.IGNORECASE,
)


def stable_id(prefix: str, value: str) -> str:
    digest = hashlib.sha256(value.encode("utf-8")).hexdigest()[:12]
    return f"{prefix}_{digest}"


def evidence_sentence(body: str) -> str:
    sentences = re.split(r"(?<=[.!?])\s+|\n+", body.strip())
    for sentence in sentences:
        if ACTION_PATTERN.search(sentence) and re.search(r"\d", sentence):
            return sentence.strip()
    for sentence in sentences:
        if re.search(r"\d", sentence) and re.search(
            r"\b(January|February|March|April|May|June|July|August|September|October|November|December)\b",
            sentence,
            re.IGNORECASE,
        ):
            return sentence.strip()
    for sentence in sentences:
        cleaned = sentence.strip()
        if cleaned and cleaned.lower() not in {"dear student,", "regards,", "course team"}:
            return cleaned
    return ""


def infer_task_type(subject: str, body: str) -> str:
    text = f"{subject} {body}".lower()
    if any(word in text for word in ("workshop", "seminar", "class moved", "class cancelled", "room change", "has moved", "cancelled")):
        return "class_change"
    if any(word in text for word in ("registration", "form", "administrative", "survey", "declaration")):
        return "administrative"
    if any(word in text for word in ("exam", "quiz", "test")):
        return "exam"
    if any(word in text for word in ("consultation", "briefing", "meeting")):
        return "other"
    if any(word in text for word in (
        "assignment", "project", "report", "submission", "reflection", "presentation",
        "case response", "reading response", "draft", "case analysis",
    )):
        return "assignment"
    return "other"


def demo_extract(email: EmailInput, now=None) -> ExtractedTask:
    source_text = f"{email.subject}\n{email.body}"
    course_match = COURSE_PATTERN.search(source_text)
    course = course_match.group(0) if course_match else "Unknown course"
    evidence = evidence_sentence(email.body)
    deadline_iso, clarification = parse_deadline(evidence or email.body, reference=now)
    email_id = stable_id("email", f"{email.subject}|{email.sender}|{email.body}")
    thread_id = stable_id("thread", f"{course}|{email.subject.lower()}")

    lowered = source_text.lower()
    is_cancel = any(term in lowered for term in ("cancelled", "canceled"))
    informational = any(
        term in lowered for term in ("no submission requirement", "resources are now available")
    )
    # "Optional" can describe one small report section inside an otherwise
    # mandatory assignment email. Only treat it as an informational signal
    # when the message has no verified deadline.
    informational = informational or ("optional" in lowered and deadline_iso is None)
    platform_metadata_only = (
        "scheduled to post" in lowered
        or "not available until" in lowered
        or ("available until" in lowered and " due " not in f" {lowered} ")
    )
    informational = informational or platform_metadata_only
    has_action = (deadline_iso is not None or bool(ACTION_PATTERN.search(source_text))) and not informational
    update_context = f"{email.subject}\n{evidence}".lower()
    is_update = any(
        term in update_context
        for term in (
            "extended", "moved", "instead of", "corrected", "remains",
            "reminder:", "no longer applies", "must now include",
        )
    )
    relation = "cancel" if is_cancel else "update" if is_update else "new"

    if is_cancel:
        deadline_iso = None
        clarification = None
        urgency = "low"
        calendar_action = "do_not_create"
    elif not has_action:
        deadline_iso = None
        clarification = None
        urgency = "low"
        calendar_action = "do_not_create"
    elif clarification:
        urgency = "clarification"
        calendar_action = "ask_clarification"
    else:
        urgency = urgency_for(deadline_iso, source_text, now=now)
        calendar_action = "update" if is_update else "create"

    clean_subject = re.sub(r"^(?:re|fw|fwd|转发|答复)\s*:\s*", "", email.subject, flags=re.IGNORECASE)
    clean_subject = re.sub(COURSE_PATTERN, "", clean_subject).strip(" -:|")
    clean_subject = re.sub(
        r"^EMERGING\s+AI\s+TECHNOLOGIES-GROUP\s+[A-Z]\s*:\s*",
        "",
        clean_subject,
        flags=re.IGNORECASE,
    )
    title = clean_subject or "Academic task"
    return ExtractedTask(
        email_id=email_id,
        thread_id=thread_id,
        course=course,
        task_type=infer_task_type(email.subject, email.body),
        task_title=title,
        deadline_iso=deadline_iso,
        timezone="Asia/Singapore",
        urgency=urgency,
        evidence_quote=evidence,
        relation_to_previous=relation,
        calendar_action=calendar_action,
        needs_clarification=bool(clarification),
        clarification_reason=clarification,
        source_subject=email.subject,
    )


def _live_prompt(email: EmailInput) -> str:
    schema = ExtractedTask.model_json_schema()
    return (
        "Extract one academic task from the email. Copy evidence_quote verbatim. "
        "Use null when a deadline is missing. Set needs_clarification=true when the "
        "date, time, task, or time zone is unsafe to infer. A platform availability window "
        "(available until / not available until) is not an assessed due date. A scheduled "
        "publication or post time is not an assignment due date. For those platform metadata "
        "cases use deadline_iso=null, urgency=low, calendar_action=do_not_create and "
        "needs_clarification=false unless a separate explicit due date is present. When "
        "needs_clarification=true, deadline_iso must be null. Return JSON only.\n\n"
        f"Schema:\n{json.dumps(schema, ensure_ascii=False)}\n\n"
        f"Subject: {email.subject}\nSender: {email.sender}\nBody:\n{email.body}"
    )


def enforce_live_safety(task: ExtractedTask, email: EmailInput) -> ExtractedTask:
    """Apply deterministic calendar safety rules after model extraction."""
    source_text = f"{email.subject}\n{email.body}"
    lowered = f" {source_text} ".lower()
    course_match = COURSE_PATTERN.search(source_text)
    trusted_fields = {
        "email_id": stable_id("email", f"{email.subject}|{email.sender}|{email.body}"),
        "source_subject": email.subject,
    }
    if course_match:
        trusted_fields["course"] = course_match.group(0)
    task = task.model_copy(update=trusted_fields)
    platform_metadata_only = (
        "scheduled to post" in lowered
        or "not available until" in lowered
        or ("available until" in lowered and " due " not in lowered)
    )
    if platform_metadata_only:
        return task.model_copy(update={
            "deadline_iso": None,
            "urgency": "low",
            "calendar_action": "do_not_create",
            "needs_clarification": False,
            "clarification_reason": None,
        })
    if task.needs_clarification and task.deadline_iso is not None:
        return task.model_copy(update={"deadline_iso": None})
    return task


def live_extract(email: EmailInput) -> tuple[ExtractedTask, dict]:
    api_key = os.getenv("AI_SCROLL_API_KEY", "").strip()
    base_url = os.getenv("AI_SCROLL_BASE_URL", "").rstrip("/")
    model = os.getenv("AI_SCROLL_MODEL", "").strip()
    if not api_key or not base_url or not model:
        raise RuntimeError("Live mode requires AI_SCROLL_API_KEY, AI_SCROLL_BASE_URL and AI_SCROLL_MODEL.")

    payload = {
        "model": model,
        "temperature": 0,
        "max_tokens": 1600,
        "reasoning": {"effort": "minimal"},
        "messages": [
            {"role": "system", "content": "You are a precise academic email extraction service."},
            {"role": "user", "content": _live_prompt(email)},
        ],
        "response_format": {"type": "json_object"},
    }
    request = urllib.request.Request(
        f"{base_url}/chat/completions",
        data=json.dumps(payload).encode("utf-8"),
        headers={"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"},
        method="POST",
    )
    started = time.perf_counter()
    try:
        with urllib.request.urlopen(request, timeout=60) as response:
            raw = json.loads(response.read().decode("utf-8"))
    except urllib.error.HTTPError as exc:
        detail = exc.read().decode("utf-8", errors="replace")
        raise RuntimeError(f"Model request failed ({exc.code}): {detail[:400]}") from exc

    latency_ms = round((time.perf_counter() - started) * 1000)
    content = raw["choices"][0]["message"].get("content")
    if not content:
        finish_reason = raw["choices"][0].get("finish_reason", "unknown")
        raise RuntimeError(
            "The model returned no JSON content "
            f"(finish_reason={finish_reason}). Please retry the scan."
        )
    task = ExtractedTask.model_validate_json(content)
    task = enforce_live_safety(task, email)
    if task.evidence_quote and task.evidence_quote not in email.body:
        raise ValueError("The model evidence quote does not appear verbatim in the source email.")
    usage = raw.get("usage", {})
    usage.update({"latency_ms": latency_ms, "model": model})
    return task, usage


def estimate_cost(usage: dict) -> float:
    input_price = float(os.getenv("AI_SCROLL_INPUT_PRICE_PER_MILLION", "0") or 0)
    output_price = float(os.getenv("AI_SCROLL_OUTPUT_PRICE_PER_MILLION", "0") or 0)
    return (
        usage.get("prompt_tokens", 0) * input_price
        + usage.get("completion_tokens", 0) * output_price
    ) / 1_000_000


def log_call(mode: str, task: ExtractedTask, usage: dict, log_path: Path) -> None:
    log_path.parent.mkdir(parents=True, exist_ok=True)
    row = {
        "timestamp": time.strftime("%Y-%m-%dT%H:%M:%S%z"),
        "mode": mode,
        "model": usage.get("model", "deterministic-demo-v1"),
        "prompt_version": PROMPT_VERSION,
        "email_id": task.email_id,
        "prompt_tokens": usage.get("prompt_tokens", 0),
        "completion_tokens": usage.get("completion_tokens", 0),
        "latency_ms": usage.get("latency_ms", 0),
        "estimated_cost_usd": f"{estimate_cost(usage):.8f}",
    }
    exists = log_path.exists()
    with log_path.open("a", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(row))
        if not exists:
            writer.writeheader()
        writer.writerow(row)


def extract(email: EmailInput, mode: str = "Demo", now=None) -> ExtractedTask:
    started = time.perf_counter()
    if mode == "Live model":
        task, usage = live_extract(email)
    else:
        task = demo_extract(email, now=now)
        usage = {"latency_ms": round((time.perf_counter() - started) * 1000)}
    root = Path(__file__).resolve().parents[1]
    log_call(mode, task, usage, root / "logs" / "model_calls.csv")
    return task
