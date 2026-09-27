from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path

import streamlit as st

from app.calendar_gate import CalendarApprovalGate, CalendarPolicyError, InMemoryCalendarStore
from app.extractor import extract
from app.label_review import (
    CALENDAR_ACTIONS, RELATIONS, TASK_TYPES, URGENCIES, load_jsonl, load_review_rows,
    review_progress, save_review_row, validate_review,
)
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

single_tab, chain_tab, safety_tab, evaluation_tab, review_tab = st.tabs(
    ["Single email", "Deadline update chain", "Safety and approval", "Evaluation", "Label review"]
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
        st.divider()
        st.subheader("Final-run readiness and cost")
        preflight_path = ROOT / "04_evaluation" / "outputs" / "final_evaluation_preflight.json"
        cost_path = ROOT / "04_evaluation" / "outputs" / "cost_analysis.json"
        if preflight_path.exists():
            preflight = json.loads(preflight_path.read_text(encoding="utf-8"))
            status_cols = st.columns(3)
            status_cols[0].metric("Frozen labels", "Ready" if preflight["frozen_labels_present"] else "Pending")
            status_cols[1].metric("Model configuration", "Ready" if preflight["live_model_configured"] else "Pending")
            status_cols[2].metric("Prompt version", preflight["prompt_version"])
        if cost_path.exists():
            cost = json.loads(cost_path.read_text(encoding="utf-8"))
            if cost["status"] == "PENDING":
                st.info("Cost result pending: " + ", ".join(cost["missing"]) + ".")
                st.caption(cost["architecture_decision"])
            else:
                st.metric("Measured cost per email", f"US${cost['cost_per_processed_email_usd']:.6f}")
                st.json({
                    "on_demand": cost["on_demand"],
                    "naive_hourly_llm_polling": cost["naive_hourly_llm_polling"],
                    "naive_15_minute_llm_polling": cost["naive_15_minute_llm_polling"],
                    "event_filtered_polling": cost["event_filtered_polling"],
                })

with review_tab:
    st.subheader("Human review before the final model run")
    st.caption("Review the source email and every label. Approval changes only the local review CSV.")
    review_path = ROOT / "02_data" / "gold_label_review.csv"
    email_path = ROOT / "02_data" / "evaluation_emails.jsonl"
    review_rows = load_review_rows(review_path)
    email_rows = {row["email_id"]: row for row in load_jsonl(email_path)}
    progress = review_progress(review_rows)
    st.progress(progress["approved"] / progress["total"], text=f"{progress['approved']} of {progress['total']} labels approved")

    selected_id = st.selectbox(
        "Case to review",
        [row["email_id"] for row in review_rows],
        format_func=lambda email_id: (
            f"{email_id} · {email_rows[email_id]['subject']} · "
            f"{next(row['review_status'] for row in review_rows if row['email_id'] == email_id)}"
        ),
    )
    review_row = next(row for row in review_rows if row["email_id"] == selected_id)
    source_email = email_rows[selected_id]
    st.markdown(f"**Subject:** {source_email['subject']}  \n**Sender:** {source_email['sender']}  \n**Split:** {source_email['split']}")
    st.code(source_email["body"], language=None)

    with st.form(f"review_{selected_id}"):
        left, right = st.columns(2)
        with left:
            course_gold = st.text_input("Course", value=review_row["course_gold"])
            task_type_gold = st.selectbox("Task type", TASK_TYPES, index=TASK_TYPES.index(review_row["task_type_gold"]))
            task_title_gold = st.text_input("Task title", value=review_row["task_title_gold"])
            deadline_gold = st.text_input("Deadline (ISO; blank if none)", value=review_row["deadline_gold"])
            timezone_gold = st.text_input("Timezone", value=review_row["timezone_gold"])
            urgency_gold = st.selectbox("Urgency", URGENCIES, index=URGENCIES.index(review_row["urgency_gold"]))
        with right:
            relation_gold = st.selectbox("Relation", RELATIONS, index=RELATIONS.index(review_row["relation_gold"]))
            calendar_action_gold = st.selectbox(
                "Calendar action", CALENDAR_ACTIONS,
                index=CALENDAR_ACTIONS.index(review_row["calendar_action_gold"]),
            )
            needs_clarification_gold = st.checkbox(
                "Needs clarification", value=review_row["needs_clarification_gold"].lower() == "true"
            )
            clarification_reason_gold = st.text_input(
                "Clarification reason", value=review_row["clarification_reason_gold"]
            )
            evidence_gold = st.text_area("Exact evidence quote", value=review_row["evidence_gold"], height=120)
            reviewer_notes = st.text_input("Reviewer notes", value=review_row["reviewer_notes"])
        save_draft = st.form_submit_button("Save as pending")
        approve_label = st.form_submit_button("Approve this label", type="primary")

    if save_draft or approve_label:
        updates = {
            "course_gold": course_gold,
            "task_type_gold": task_type_gold,
            "task_title_gold": task_title_gold,
            "deadline_gold": deadline_gold,
            "timezone_gold": timezone_gold,
            "urgency_gold": urgency_gold,
            "evidence_gold": evidence_gold,
            "relation_gold": relation_gold,
            "calendar_action_gold": calendar_action_gold,
            "needs_clarification_gold": needs_clarification_gold,
            "clarification_reason_gold": clarification_reason_gold,
            "reviewer_notes": reviewer_notes,
        }
        candidate = {**review_row, **{key: str(value) for key, value in updates.items()}}
        candidate["needs_clarification_gold"] = str(needs_clarification_gold)
        errors = validate_review(candidate, source_email)
        if errors:
            for error in errors:
                st.error(error)
        else:
            save_review_row(review_path, selected_id, updates, approve=approve_label)
            st.success("Label approved." if approve_label else "Draft saved and left pending.")
            st.rerun()

    if progress["pending"] == 0:
        st.success("All 50 labels are approved. The label set is ready to freeze.")
        st.code("python 02_data/freeze_labels.py", language="powershell")
    else:
        st.info(f"{progress['pending']} labels still need review before freezing.")
