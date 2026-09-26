from __future__ import annotations

from datetime import datetime

import streamlit as st

from app.extractor import extract
from app.models import CalendarProposal, EmailInput
from app.sample_data import SAMPLE_BODY, SAMPLE_SENDER, SAMPLE_SUBJECT


st.set_page_config(page_title="AI Scroll", page_icon="📬", layout="wide")

st.markdown(
    """
    <style>
    .block-container {max-width: 1100px; padding-top: 2rem;}
    .eyebrow {color:#256c5a; font-weight:700; letter-spacing:.08em; font-size:.78rem;}
    .result-card {border:1px solid #dce7e2; border-radius:14px; padding:18px; background:#f8fbfa; margin-bottom:12px;}
    .evidence {border-left:5px solid #287a64; background:#eef7f3; padding:14px 16px; border-radius:7px;}
    </style>
    """,
    unsafe_allow_html=True,
)

st.markdown('<div class="eyebrow">PE6201 INDIVIDUAL PROJECT</div>', unsafe_allow_html=True)
st.title("AI Scroll")
st.caption("Academic email in. Evidence-backed timeline item and safe calendar proposal out.")

with st.sidebar:
    st.header("Run settings")
    mode = st.radio("Extraction mode", ["Demo", "Live model"], help="Demo requires no API key.")
    st.info("Version 1 creates a preview only. It cannot write to a real calendar.")
    st.markdown("**Urgency policy**")
    st.markdown("- High: within 72 hours\n- Medium: 4-7 days\n- Low: more than 7 days\n- Clarification: unsafe to infer")

left, right = st.columns([1.08, 0.92], gap="large")

with left:
    st.subheader("1. Selected academic email")
    subject = st.text_input("Subject", value=SAMPLE_SUBJECT)
    sender = st.text_input("Sender", value=SAMPLE_SENDER)
    body = st.text_area("Email body", value=SAMPLE_BODY, height=280)
    run = st.button("Extract task", type="primary", use_container_width=True)

if run:
    try:
        task = extract(EmailInput(subject=subject, sender=sender, body=body), mode=mode)
        st.session_state["task"] = task
    except Exception as exc:
        st.error(f"Extraction failed: {exc}")

with right:
    st.subheader("2. Verified timeline item")
    task = st.session_state.get("task")
    if task is None:
        st.markdown('<div class="result-card">Run the sample email to produce the first timeline item.</div>', unsafe_allow_html=True)
    elif task.needs_clarification:
        st.warning(task.clarification_reason)
        st.json(task.model_dump())
    else:
        c1, c2 = st.columns(2)
        c1.metric("Course", task.course)
        c2.metric("Urgency", task.urgency.title())
        st.markdown(f"**Task**  \n{task.task_title}")
        deadline = datetime.fromisoformat(task.deadline_iso)
        st.markdown(f"**Deadline**  \n{deadline.strftime('%d %B %Y, %I:%M %p')} ({task.timezone})")
        st.markdown("**Source evidence**")
        st.markdown(f'<div class="evidence">“{task.evidence_quote}”</div>', unsafe_allow_html=True)

        st.subheader("3. Calendar preview")
        proposal = CalendarProposal(
            title=f"{task.course} - {task.task_title}",
            start=task.deadline_iso,
            timezone=task.timezone,
            description=f"Source: {task.source_subject}\nEvidence: {task.evidence_quote}",
        )
        st.markdown(
            f'<div class="result-card"><b>{proposal.title}</b><br>{deadline.strftime("%d %B %Y, %I:%M %p")}<br><small>Preview only - not added to any calendar</small></div>',
            unsafe_allow_html=True,
        )
        with st.expander("View validated JSON"):
            st.json(task.model_dump())

