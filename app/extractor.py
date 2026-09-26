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
from app.models import EmailInput, ExtractedTask


PROMPT_VERSION = "v1.0"
COURSE_PATTERN = re.compile(r"\b[A-Z]{2,4}\d{4}[A-Z]?\b")
ACTION_PATTERN = re.compile(r"\b(due|deadline|submit|submitted|upload|complete|exam|quiz|class)\b", re.IGNORECASE)


def stable_id(prefix: str, value: str) -> str:
    digest = hashlib.sha256(value.encode("utf-8")).hexdigest()[:12]
    return f"{prefix}_{digest}"


def evidence_sentence(body: str) -> str:
    sentences = re.split(r"(?<=[.!?])\s+|\n+", body.strip())
    for sentence in sentences:
        if ACTION_PATTERN.search(sentence) and re.search(r"\d", sentence):
            return sentence.strip()
    return ""


def infer_task_type(subject: str, body: str) -> str:
    text = f"{subject} {body}".lower()
    if any(word in text for word in ("assignment", "project", "report", "submission")):
        return "assignment"
    if any(word in text for word in ("exam", "quiz", "test")):
        return "exam"
    if any(word in text for word in ("class moved", "class cancelled", "room changed")):
        return "class_change"
    if any(word in text for word in ("registration", "form", "administrative")):
        return "administrative"
    return "other"


def demo_extract(email: EmailInput, now=None) -> ExtractedTask:
    source_text = f"{email.subject}\n{email.body}"
    course_match = COURSE_PATTERN.search(source_text)
    course = course_match.group(0) if course_match else "Unknown course"
    evidence = evidence_sentence(email.body)
    deadline_iso, clarification = parse_deadline(evidence or email.body)
    email_id = stable_id("email", f"{email.subject}|{email.sender}|{email.body}")
    thread_id = stable_id("thread", f"{course}|{email.subject.lower()}")

    if clarification:
        urgency = "clarification"
        calendar_action = "ask_clarification"
    else:
        urgency = urgency_for(deadline_iso, source_text, now=now)
        calendar_action = "create"

    title = re.sub(COURSE_PATTERN, "", email.subject).strip(" -:|") or "Academic task"
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
        relation_to_previous="new",
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
        "date, time, task, or time zone is unsafe to infer. Return JSON only.\n\n"
        f"Schema:\n{json.dumps(schema, ensure_ascii=False)}\n\n"
        f"Subject: {email.subject}\nSender: {email.sender}\nBody:\n{email.body}"
    )


def live_extract(email: EmailInput) -> tuple[ExtractedTask, dict]:
    api_key = os.getenv("AI_SCROLL_API_KEY", "").strip()
    base_url = os.getenv("AI_SCROLL_BASE_URL", "").rstrip("/")
    model = os.getenv("AI_SCROLL_MODEL", "").strip()
    if not api_key or not base_url or not model:
        raise RuntimeError("Live mode requires AI_SCROLL_API_KEY, AI_SCROLL_BASE_URL and AI_SCROLL_MODEL.")

    payload = {
        "model": model,
        "temperature": 0,
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
    content = raw["choices"][0]["message"]["content"]
    task = ExtractedTask.model_validate_json(content)
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

