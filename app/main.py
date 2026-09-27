from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path

import streamlit as st

from app.calendar_gate import CalendarApprovalGate, CalendarPolicyError, InMemoryCalendarStore
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
    .result-card {border:1px solid #dce7e2; border-radius:14px; padding:18px; background:#f8fbfa; color:#15211d; margin-bottom:12px;}
    .result-card small {color:#52635d;}
    .evidence {border-left:5px solid #287a64; background:#eef7f3; color:#15211d; padding:14px 16px; border-radius:7px;}
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

single_tab, chain_tab, safety_tab, evaluation_tab = st.tabs(
    ["Single email", "Deadline update chain", "Safety and approval", "Evaluation"]
)

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

with safety_tab:
    st.subheader("Calendar safety gate")
    st.caption("Choose a case, inspect the decision, then explicitly confirm an eligible preview.")
    scenario = st.selectbox(
        "Safety scenario",
        ["Eligible deadline", "Ambiguous next Friday", "Cancelled workshop"],
    )
    if scenario == "Eligible deadline":
        safety_emails = [EmailInput(
            subject=SAMPLE_SUBJECT, sender=SAMPLE_SENDER, body=SAMPLE_BODY,
            sent_at="2026-09-26T09:00:00+08:00",
        )]
    elif scenario == "Ambiguous next Friday":
        safety_emails = [EmailInput(
            subject="PE6201 consultation",
            body="Please attend the PE6201 consultation next Friday.",
            sent_at="2026-09-26T09:00:00+08:00",
        )]
    else:
        safety_emails = [
            EmailInput(
                subject="PE6201 workshop",
                body="The PE6201 workshop is on 3 October 2026 at 10:00 AM SGT.",
                sent_at="2026-09-20T09:00:00+08:00",
            ),
            EmailInput(
                subject="PE6201 workshop cancelled",
                body="The PE6201 workshop on 3 October 2026 has been cancelled.",
                sent_at="2026-09-26T09:00:00+08:00",
            ),
        ]

    safety_item = build_timeline(safety_emails)[0]
    st.session_state.setdefault("calendar_events", {})
    st.session_state.setdefault("calendar_audit", [])
    store = InMemoryCalendarStore(st.session_state["calendar_events"])
    gate = CalendarApprovalGate(store=store, audit=st.session_state["calendar_audit"])

    try:
        proposal = gate.preview(safety_item)
        deadline = datetime.fromisoformat(proposal.start)
        st.success("Safety checks passed. A preview can be prepared.")
        st.markdown(
            f'<div class="result-card"><b>{proposal.title}</b><br>{deadline.strftime("%d %B %Y, %I:%M %p")} ({proposal.timezone})<br><small>Proposal ID: {proposal.proposal_id}</small></div>',
            unsafe_allow_html=True,
        )
        st.info("The next button is the explicit approval step. Review the course, task, deadline and evidence before selecting it.")
        if st.button(
            "Confirm reviewed event and add to simulated calendar",
            type="primary",
            use_container_width=True,
        ):
            result = gate.commit(proposal, user_confirmed=True)
            st.session_state["last_calendar_result"] = result.model_dump()
        last_result = st.session_state.get("last_calendar_result")
        if last_result and last_result["proposal_id"] == proposal.proposal_id:
            if last_result["status"] == "committed":
                st.success(f"Approved event recorded as {last_result['event_id']}.")
            else:
                st.info(f"Duplicate prevented. Existing event: {last_result['event_id']}.")
            st.caption("This demonstration uses a local in-memory adapter. No external calendar was changed.")
    except CalendarPolicyError as exc:
        st.warning(f"Calendar action blocked: {exc}")
        st.caption("The user must clarify or resolve the source email before a new preview can be created.")

    with st.expander("View safety audit"):
        st.json(st.session_state["calendar_audit"][-10:])

with evaluation_tab:
    st.subheader("Provisional offline evaluation")
    st.warning(
        "These are development diagnostics, not final assignment results. "
        "All labels still require human review, and no live language model was run."
    )
    metrics_path = ROOT / "04_evaluation" / "outputs" / "development_metrics.json"
    if not metrics_path.exists():
        st.info("Run `python 04_evaluation/score_development.py` to create the comparison.")
    else:
        evaluation = json.loads(metrics_path.read_text(encoding="utf-8"))
        systems = evaluation["systems"]
        baseline = systems["keyword_date_baseline_v1"]["metrics"]
        current = systems["deterministic_dev_pipeline_v1"]["metrics"]
        labels = [
            ("Course", "course_identification"),
            ("Task type", "task_type_classification"),
            ("Exact deadline", "deadline_exact_on_deadline_cases"),
            ("Urgency", "urgency_classification"),
            ("Calendar action", "calendar_action"),
            ("Cross-email merge", "cross_email_merging"),
        ]
        comparison = []
        for label, key in labels:
            comparison.append({
                "Capability": label,
                "Keyword/date baseline": f"{baseline[key]['correct']}/{baseline[key]['total']}",
                "Current pipeline": f"{current[key]['correct']}/{current[key]['total']}",
            })
        st.table(comparison)
        st.caption(
            f"Reference time: {evaluation['reference_time']} · "
            f"Population: {evaluation['population']['emails']} emails, "
            f"{evaluation['population']['multi_email_threads']} multi-email threads"
        )
        with st.expander("Why these results are not final"):
            for limitation in evaluation["limitations"]:
                st.markdown(f"- {limitation}")
