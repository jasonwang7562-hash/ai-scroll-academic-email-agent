from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path

import streamlit as st

from app.extractor import extract
from app.merge_engine import build_timeline
from app.models import CalendarProposal, EmailInput, TimelineItem
from app.sample_data import SAMPLE_BODY, SAMPLE_SENDER, SAMPLE_SUBJECT


ROOT = Path(__file__).resolve().parents[1]
st.set_page_config(page_title="AI Scroll", page_icon="📬", layout="wide")
st.markdown(
    """
    <style>
    .block-container {max-width: 1160px; padding-top: 2rem;}
    .eyebrow {color:#256c5a; font-weight:700; letter-spacing:.08em; font-size:.78rem;}
    .result-card {border:1px solid #dce7e2; border-radius:14px; padding:18px; background:#f8fbfa; margin-bottom:12px;}
    .evidence {border-left:5px solid #287a64; background:#eef7f3; padding:14px 16px; border-radius:7px;}
    .before {color:#8b3a3a; text-decoration:line-through;}
    .after {color:#176b52; font-weight:700;}
    </style>
    """,
    unsafe_allow_html=True,
)


def show_single_result(task):
    if task.needs_clarification:
        st.warning(task.clarification_reason)
        st.json(task.model_dump())
        return
    c1, c2 = st.columns(2)
    c1.metric("Course", task.course)
    c2.metric("Urgency", task.urgency.title())
    st.markdown(f"**Task**  \n{task.task_title}")
    deadline = datetime.fromisoformat(task.deadline_iso)
    st.markdown(f"**Deadline**  \n{deadline.strftime('%d %B %Y, %I:%M %p')} ({task.timezone})")
    st.markdown("**Source evidence**")
    st.markdown(f'<div class="evidence">“{task.evidence_quote}”</div>', unsafe_allow_html=True)
    st.subheader("Calendar preview")
    proposal = CalendarProposal(
        title=f"{task.course} - {task.task_title}", start=task.deadline_iso,
        timezone=task.timezone,
        description=f"Source: {task.source_subject}\nEvidence: {task.evidence_quote}",
    )
    st.markdown(
        f'<div class="result-card"><b>{proposal.title}</b><br>{deadline.strftime("%d %B %Y, %I:%M %p")}<br><small>Preview only - not added to any calendar</small></div>',
        unsafe_allow_html=True,
    )
    with st.expander("View validated JSON"):
        st.json(task.model_dump())


def load_demo_chain(thread_id="c01"):
    rows = []
    path = ROOT / "02_data" / "evaluation_emails.jsonl"
    for line in path.read_text(encoding="utf-8").splitlines():
        row = json.loads(line)
        if row["thread_id"] == thread_id:
            rows.append(EmailInput(
                subject=row["subject"], sender=row["sender"], body=row["body"], sent_at=row["sent_at"]
            ))
    return rows


def show_timeline_item(item: TimelineItem):
    c1, c2, c3 = st.columns(3)
    c1.metric("Course", item.course)
    c2.metric("Sources merged", len(item.source_email_ids))
    c3.metric("Status", item.status.title())
    st.markdown(f"**Task:** {item.task_title}")
    if item.deadline_iso:
        deadline = datetime.fromisoformat(item.deadline_iso)
        st.markdown(f"**Final deadline:** {deadline.strftime('%d %B %Y, %I:%M %p')} ({item.timezone})")
    else:
        st.markdown("**Final deadline:** None")
    for change in item.change_history:
        if change.field == "deadline_iso":
            old = datetime.fromisoformat(change.previous_value).strftime("%d %B, %I:%M %p")
            new = datetime.fromisoformat(change.new_value).strftime("%d %B, %I:%M %p")
            st.markdown(
                f'<div class="result-card"><b>Deadline updated</b><br><span class="before">{old}</span> &nbsp;→&nbsp; <span class="after">{new}</span><br><small>{change.reason}</small></div>',
                unsafe_allow_html=True,
            )
        else:
            st.info(f"{change.field}: {change.previous_value} → {change.new_value}")
    st.markdown("**Evidence trail**")
    for index, evidence in enumerate(item.evidence_history, 1):
        st.markdown(f"{index}. **{evidence.source_subject}** — “{evidence.evidence_quote}”")
    st.caption(f"Calendar action: {item.calendar_action}. No external calendar was changed.")
    with st.expander("View merged JSON"):
        st.json(item.model_dump())


st.markdown('<div class="eyebrow">PE6201 INDIVIDUAL PROJECT</div>', unsafe_allow_html=True)
st.title("AI Scroll")
st.caption("Academic emails in. One evidence-backed course timeline and safe calendar proposal out.")

with st.sidebar:
    st.header("Run settings")
    mode = st.radio("Extraction mode", ["Demo", "Live model"], help="Demo requires no API key.")
    st.info("Calendar preview and calendar write are separate. This version cannot write to a real calendar.")
    st.markdown("**Urgency policy**")
    st.markdown("- High: within 72 hours\n- Medium: 4-7 days\n- Low: more than 7 days\n- Clarification: unsafe to infer")

single_tab, chain_tab = st.tabs(["Single email", "Deadline update chain"])

with single_tab:
    left, right = st.columns([1.08, 0.92], gap="large")
    with left:
        st.subheader("1. Selected academic email")
        subject = st.text_input("Subject", value=SAMPLE_SUBJECT)
        sender = st.text_input("Sender", value=SAMPLE_SENDER)
        body = st.text_area("Email body", value=SAMPLE_BODY, height=280)
        run = st.button("Extract task", type="primary", use_container_width=True)
    if run:
        try:
            st.session_state["task"] = extract(EmailInput(subject=subject, sender=sender, body=body), mode=mode)
        except Exception as exc:
            st.error(f"Extraction failed: {exc}")
    with right:
        st.subheader("2. Verified timeline item")
        task = st.session_state.get("task")
        if task is None:
            st.markdown('<div class="result-card">Run the sample email to produce the first timeline item.</div>', unsafe_allow_html=True)
        else:
            show_single_result(task)

with chain_tab:
    st.subheader("Two emails, one task")
    demo_chain = load_demo_chain("c01")
    cols = st.columns(2, gap="large")
    for index, (column, email) in enumerate(zip(cols, demo_chain), 1):
        with column:
            st.markdown(f"**Email {index}**")
            st.caption(email.sent_at)
            st.markdown(f'<div class="result-card"><b>{email.subject}</b><br><br>{email.body.replace(chr(10), "<br>")}</div>', unsafe_allow_html=True)
    if st.button("Merge update chain", type="primary", use_container_width=True):
        st.session_state["timeline"] = build_timeline(demo_chain)
    timeline = st.session_state.get("timeline")
    if timeline:
        st.divider()
        st.subheader("Merged timeline")
        for item in timeline:
            show_timeline_item(item)

