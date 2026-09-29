from __future__ import annotations

import json
import subprocess
import sys
from datetime import datetime
from pathlib import Path

import streamlit as st

from app.calendar_gate import CalendarApprovalGate, CalendarPolicyError, InMemoryCalendarStore
from app.evaluation_reporting import (
    comparison_rows, error_counts, filter_errors, load_errors, load_evaluation, primary_metrics,
)
from app.extractor import extract
from app.gmail_connector import (
    GmailMailboxConnector,
    client_secrets_path,
    gmail_is_authorized,
    gmail_token_path,
)
from app.inbox_agent import DemoMailboxConnector, InboxAgent
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
    :root {
        --ink:#14213d;
        --muted:#667085;
        --line:#e5e9f2;
        --panel:#ffffff;
        --canvas:#f5f7fb;
        --brand:#5267e8;
        --brand-soft:#eef1ff;
        --teal:#168a78;
        --teal-soft:#eaf8f4;
        --amber:#b56b09;
        --amber-soft:#fff6e5;
        --danger:#b54747;
        --danger-soft:#fff0f0;
    }
    .stApp {background:var(--canvas); color:var(--ink);}
    .block-container {max-width:1440px; padding-top:1.25rem; padding-bottom:4rem;}
    [data-testid="stSidebar"] {background:#111936; border-right:1px solid #263052;}
    [data-testid="stSidebar"] * {color:#f5f7ff;}
    [data-testid="stSidebar"] .stAlert {background:#1d284d; border:1px solid #34416c;}
    [data-testid="stTabs"] button {font-size:.95rem; font-weight:650; padding:.85rem 1rem;}
    [data-testid="stMetric"] {background:var(--panel); border:1px solid var(--line); border-radius:16px; padding:14px 16px; box-shadow:0 8px 24px rgba(20,33,61,.04);}
    [data-testid="stMetricValue"] {font-size:1.5rem; color:var(--ink);}
    [data-testid="stMetricLabel"] {color:#526078 !important; font-weight:700;}
    [data-testid="stAlert"] p {color:var(--ink); font-weight:600;}
    .eyebrow {color:var(--brand); font-weight:800; letter-spacing:.1em; font-size:.72rem; text-transform:uppercase;}
    .hero {background:linear-gradient(120deg,#101936 0%,#182451 58%,#26346f 100%); color:white; border-radius:24px; padding:28px 32px; margin:.4rem 0 1.25rem; box-shadow:0 18px 45px rgba(24,36,81,.18); overflow:hidden; position:relative;}
    .hero:after {content:""; position:absolute; width:260px; height:260px; border-radius:50%; right:-90px; top:-130px; background:radial-gradient(circle,rgba(96,193,255,.35),rgba(82,103,232,0));}
    .hero h1 {font-size:2.35rem; line-height:1.08; margin:.35rem 0 .55rem; color:white; letter-spacing:-.035em;}
    .hero p {font-size:1rem; color:#d6ddff; margin:0; max-width:760px;}
    .hero-kicker {display:inline-flex; gap:8px; align-items:center; padding:6px 10px; border-radius:999px; background:rgba(255,255,255,.1); color:#dfe5ff; font-size:.78rem; font-weight:700;}
    .status-strip {display:grid; grid-template-columns:repeat(4,1fr); gap:12px; margin-bottom:1.35rem;}
    .status-card {background:white; border:1px solid var(--line); border-radius:16px; padding:15px 17px; box-shadow:0 8px 22px rgba(20,33,61,.035);}
    .status-card .number {font-size:1.45rem; font-weight:780; color:var(--ink); line-height:1.1;}
    .status-card .label {font-size:.78rem; color:var(--muted); margin-top:5px;}
    .brief-banner {display:flex; align-items:center; justify-content:space-between; gap:22px; background:linear-gradient(100deg,#eef1ff,#f7f9ff 55%,#eaf8f4); border:1px solid #dce2fb; border-radius:18px; padding:16px 19px; margin:-.35rem 0 1.25rem;}
    .brief-banner .brief-copy {font-size:.9rem; color:#40506c; line-height:1.45;}
    .brief-banner .brief-copy b {display:block; color:var(--ink); font-size:1rem; margin-bottom:2px;}
    .brief-action {white-space:nowrap; border-radius:999px; padding:7px 12px; background:white; border:1px solid #ccd5f4; color:#4256c9; font-size:.76rem; font-weight:800;}
    .section-label {font-size:.7rem; color:#8790a5; font-weight:800; letter-spacing:.1em; text-transform:uppercase; margin:0 0 .6rem;}
    .view-pills {display:flex; flex-wrap:wrap; gap:6px; margin:0 0 13px;}
    .view-pill {border:1px solid var(--line); border-radius:999px; background:white; color:#58647a; padding:5px 9px; font-size:.7rem; font-weight:750;}
    .view-pill.active {background:var(--ink); color:white; border-color:var(--ink);}
    .rail-card {border:1px solid var(--line); border-radius:14px; padding:13px 14px; background:white; margin-bottom:9px;}
    .rail-card.active {border-color:#aeb9ff; background:var(--brand-soft); box-shadow:inset 3px 0 0 var(--brand);}
    .rail-card b {display:block; color:var(--ink); font-size:.93rem; margin-bottom:3px;}
    .rail-card span {font-size:.76rem; color:var(--muted);}
    .badge {display:inline-block; border-radius:999px; padding:4px 9px; font-size:.72rem; font-weight:750; margin-right:5px;}
    .badge-blue {background:var(--brand-soft); color:#4256c9;}
    .badge-green {background:var(--teal-soft); color:#087260;}
    .badge-amber {background:var(--amber-soft); color:#965909;}
    .badge-red {background:var(--danger-soft); color:#a23b3b;}
    .result-card {border:1px solid var(--line); border-radius:16px; padding:17px 18px; background:white; color:var(--ink); margin-bottom:12px; box-shadow:0 8px 24px rgba(20,33,61,.045);}
    .result-card small {color:var(--muted);}
    .result-title {font-size:1.08rem; font-weight:780; margin:.35rem 0 .2rem; color:var(--ink);}
    .result-meta {color:var(--muted); font-size:.84rem; line-height:1.55;}
    .source-context {display:grid; grid-template-columns:36px 1fr auto; gap:10px; align-items:center; border:1px solid var(--line); border-radius:13px; padding:11px 12px; background:white; margin-bottom:12px;}
    .source-avatar {width:36px; height:36px; display:flex; align-items:center; justify-content:center; border-radius:10px; background:var(--brand-soft); color:#4256c9; font-weight:850;}
    .source-main {font-size:.8rem; color:var(--muted); line-height:1.35;}
    .source-main b {display:block; color:var(--ink); font-size:.86rem;}
    .route {display:grid; grid-template-columns:repeat(4,1fr); gap:7px; margin:.7rem 0 1rem;}
    .route-step {position:relative; border:1px solid var(--line); border-radius:11px; background:white; padding:10px 8px; color:#68748a; font-size:.68rem; line-height:1.25;}
    .route-step b {display:block; color:var(--ink); font-size:.74rem; margin-top:4px;}
    .route-step.done {border-color:#bfe2d9; background:var(--teal-soft);}
    .route-step.active {border-color:#aeb9ff; background:var(--brand-soft); box-shadow:inset 0 -3px 0 var(--brand);}
    .route-step.warn {border-color:#f0cf94; background:var(--amber-soft); box-shadow:inset 0 -3px 0 #d58a1f;}
    .route-dot {width:18px; height:18px; border-radius:50%; display:flex; align-items:center; justify-content:center; background:#dfe4ef; color:#68748a; font-size:.62rem; font-weight:900;}
    .route-step.done .route-dot {background:var(--teal); color:white;}
    .route-step.active .route-dot {background:var(--brand); color:white;}
    .route-step.warn .route-dot {background:#d58a1f; color:white;}
    .trust-panel {border:1px solid #dce2ef; border-radius:14px; overflow:hidden; background:white; margin:12px 0;}
    .trust-head {display:flex; align-items:center; justify-content:space-between; gap:10px; padding:12px 14px; background:#f8f9fc; border-bottom:1px solid var(--line);}
    .trust-head b {font-size:.84rem; color:var(--ink);}
    .trust-head span {font-size:.7rem; color:#4256c9; font-weight:800;}
    .trust-row {display:grid; grid-template-columns:20px 1fr auto; align-items:center; gap:8px; padding:9px 14px; border-bottom:1px solid #eef1f6; font-size:.76rem; color:#536078;}
    .trust-row:last-child {border-bottom:0;}
    .trust-check {width:18px; height:18px; display:flex; align-items:center; justify-content:center; border-radius:50%; background:var(--teal-soft); color:var(--teal); font-size:.68rem; font-weight:900;}
    .trust-lock {font-size:.68rem; color:#7b879c; font-weight:750;}
    .decision-banner {border-left:4px solid var(--brand); border-radius:10px; background:var(--brand-soft); padding:11px 13px; color:#35447a; font-size:.78rem; line-height:1.45; margin:10px 0 12px;}
    .policy-grid {display:grid; grid-template-columns:repeat(3,1fr); gap:10px; margin:12px 0 16px;}
    .policy-card {border:1px solid var(--line); border-radius:14px; background:white; padding:13px 14px; min-height:88px;}
    .policy-card span {display:block; color:#8993a7; font-size:.66rem; font-weight:800; letter-spacing:.08em; text-transform:uppercase; margin-bottom:7px;}
    .policy-card b {display:block; color:var(--ink); font-size:.88rem; margin-bottom:4px;}
    .policy-card small {display:block; color:var(--muted); font-size:.72rem; line-height:1.35;}
    .policy-card.pass {border-top:4px solid var(--teal);}
    .policy-card.review {border-top:4px solid var(--brand);}
    .policy-card.block {border-top:4px solid #d58a1f;}
    .audit-line {display:grid; grid-template-columns:78px 110px 1fr; gap:10px; padding:9px 11px; border-bottom:1px solid #edf0f5; font-size:.73rem; align-items:center;}
    .audit-line:last-child {border-bottom:0;}
    .audit-action {font-weight:800; color:var(--ink); text-transform:capitalize;}
    .audit-status {color:#5267e8; font-weight:750;}
    .approval-summary {display:grid; grid-template-columns:1fr 1fr; gap:9px; margin:11px 0 13px;}
    .approval-item {border:1px solid #dfe4ee; border-radius:12px; padding:11px 12px; background:#fbfcfe;}
    .approval-item span {display:block; color:#8790a5; font-size:.64rem; font-weight:800; letter-spacing:.08em; text-transform:uppercase; margin-bottom:5px;}
    .approval-item b {display:block; color:var(--ink); font-size:.8rem; margin-bottom:3px;}
    .approval-item small {display:block; color:var(--muted); font-size:.7rem; line-height:1.35;}
    .agent-grid {display:grid; grid-template-columns:repeat(3,1fr); gap:10px; margin:12px 0 18px;}
    .agent-card {background:white; border:1px solid var(--line); border-radius:15px; padding:14px 15px;}
    .agent-card span {display:block; color:#8790a5; font-size:.65rem; font-weight:800; letter-spacing:.08em; text-transform:uppercase; margin-bottom:5px;}
    .agent-card b {display:block; color:var(--ink); font-size:.9rem; margin-bottom:3px;}
    .agent-card small {color:var(--muted); font-size:.72rem; line-height:1.4;}
    .agent-run {border:1px solid #cfd7fb; background:linear-gradient(120deg,#f2f4ff,#eefaf7); border-radius:18px; padding:18px; margin-bottom:14px;}
    .chain-flow {display:grid; grid-template-columns:1fr 24px 1fr 24px 1fr; align-items:center; gap:7px; margin:12px 0 19px;}
    .flow-card {border:1px solid var(--line); border-radius:13px; background:white; padding:12px; min-height:72px;}
    .flow-card b {display:block; color:var(--ink); font-size:.82rem; margin-bottom:4px;}
    .flow-card span {color:var(--muted); font-size:.72rem; line-height:1.35;}
    .flow-arrow {text-align:center; color:#8994aa; font-weight:900;}
    .evidence {border:1px solid #ccebe2; border-left:5px solid var(--teal); background:var(--teal-soft); color:#173b34; padding:14px 16px; border-radius:10px; line-height:1.5;}
    .before {color:var(--danger); text-decoration:line-through;}
    .after {color:var(--teal); font-weight:750;}
    .empty-state {border:1px dashed #cbd2e3; border-radius:18px; padding:34px 22px; text-align:center; background:rgba(255,255,255,.68); color:var(--muted);}
    .empty-state b {display:block; color:var(--ink); font-size:1rem; margin-bottom:6px;}
    .stButton > button[kind="primary"] {background:var(--brand); border-color:var(--brand); border-radius:11px; min-height:46px; font-weight:750;}
    .stButton > button[kind="secondary"] {border-radius:11px; min-height:43px; background:white !important; color:var(--ink) !important; border:1px solid #cfd6e5 !important;}
    .stButton > button[kind="secondary"]:disabled {background:#eef1f6 !important; color:#7a8498 !important;}
    .stTextInput input, .stTextArea textarea, .stSelectbox > div > div {border-radius:11px !important; border-color:#d9deea !important; background:white !important;}
    .before {color:#8b3a3a; text-decoration:line-through;}
    .after {color:#176b52; font-weight:700;}
    @media (max-width:900px) {
      .status-strip{grid-template-columns:repeat(2,1fr)}
      .hero h1{font-size:1.85rem}
      .brief-banner{align-items:flex-start;flex-direction:column}
      .route{grid-template-columns:repeat(2,1fr)}
      .policy-grid{grid-template-columns:1fr}
      .approval-summary{grid-template-columns:1fr}
      .agent-grid{grid-template-columns:1fr}
      .chain-flow{grid-template-columns:1fr}
      .flow-arrow{transform:rotate(90deg)}
      [data-testid="stHorizontalBlock"]{flex-wrap:wrap !important;}
      [data-testid="stColumn"]{min-width:280px !important; flex:1 1 100% !important;}
    }
    </style>
    """,
    unsafe_allow_html=True,
)


def show_single_result(task):
    if task.needs_clarification:
        st.warning(task.clarification_reason)
        st.json(task.model_dump())
        return
    deadline = datetime.fromisoformat(task.deadline_iso)
    urgency_class = {"high": "badge-red", "medium": "badge-amber", "low": "badge-green"}.get(task.urgency, "badge-blue")
    st.markdown(
        f'<span class="badge badge-blue">{task.course}</span>'
        f'<span class="badge {urgency_class}">{task.urgency.title()} priority</span>'
        f'<div class="result-title">{task.task_title}</div>'
        f'<div class="result-meta">Due {deadline.strftime("%d %B %Y, %I:%M %p")} · {task.timezone}</div>',
        unsafe_allow_html=True,
    )
    st.markdown(
        '<div class="decision-banner"><b>Decision:</b> create a calendar preview, keep it locked, and ask the student to review the source evidence before approval.</div>',
        unsafe_allow_html=True,
    )
    st.markdown('<div class="section-label" style="margin-top:1rem">Evidence from source</div>', unsafe_allow_html=True)
    st.markdown(f'<div class="evidence">“{task.evidence_quote}”</div>', unsafe_allow_html=True)
    st.markdown('<div class="section-label" style="margin-top:1rem">Calendar preview</div>', unsafe_allow_html=True)
    proposal = CalendarProposal(
        title=f"{task.course} - {task.task_title}", start=task.deadline_iso,
        timezone=task.timezone,
        description=f"Source: {task.source_subject}\nEvidence: {task.evidence_quote}",
    )
    st.markdown(
        f'<div class="result-card"><span class="badge badge-green">Ready for review</span><div class="result-title">{proposal.title}</div><div class="result-meta">{deadline.strftime("%d %B %Y, %I:%M %p")} · {proposal.timezone}<br>Preview only — no calendar change has been made.</div></div>',
        unsafe_allow_html=True,
    )
    st.markdown(
        '<div class="trust-panel"><div class="trust-head"><b>Validation checklist</b><span>4 checks passed</span></div>'
        '<div class="trust-row"><span class="trust-check">✓</span><span>Course and task identified</span><span class="trust-lock">STRUCTURED</span></div>'
        '<div class="trust-row"><span class="trust-check">✓</span><span>Exact source sentence retained</span><span class="trust-lock">TRACEABLE</span></div>'
        '<div class="trust-row"><span class="trust-check">✓</span><span>Deadline and timezone normalized</span><span class="trust-lock">VALIDATED</span></div>'
        '<div class="trust-row"><span class="trust-check">✓</span><span>External calendar write remains locked</span><span class="trust-lock">SAFE</span></div></div>',
        unsafe_allow_html=True,
    )
    with st.expander("View validated JSON"):
        st.json(task.model_dump())


def show_processing_route(task=None):
    if task is None:
        classes = ["active", "", "", ""]
        dots = ["1", "2", "3", "4"]
        notes = ["Await source", "Extract task", "Check evidence", "Ask approval"]
    elif task.needs_clarification:
        classes = ["done", "done", "warn", ""]
        dots = ["✓", "✓", "!", "4"]
        notes = ["Source read", "Task found", "Needs clarification", "Locked"]
    else:
        classes = ["done", "done", "done", "active"]
        dots = ["✓", "✓", "✓", "4"]
        notes = ["Source read", "Task extracted", "Evidence checked", "Review required"]
    labels = ["Capture", "Understand", "Verify", "Schedule"]
    cards = "".join(
        f'<div class="route-step {css_class}"><span class="route-dot">{dot}</span><b>{label}</b>{note}</div>'
        for css_class, dot, label, note in zip(classes, dots, labels, notes)
    )
    st.markdown(f'<div class="route">{cards}</div>', unsafe_allow_html=True)


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


st.session_state.setdefault("demo_mailbox_connected", False)
st.session_state.setdefault("mailbox_provider", "demo")
st.session_state.setdefault("agent_run", None)
agent_snapshot = st.session_state["agent_run"]
gmail_authorized = gmail_is_authorized()
active_provider = st.session_state["mailbox_provider"]
connected = gmail_authorized if active_provider == "gmail" else st.session_state["demo_mailbox_connected"]
mailbox_status = (
    "Gmail connected" if active_provider == "gmail" and gmail_authorized
    else "Demo connected" if connected
    else "Not connected"
)
scanned_count = agent_snapshot.scanned if agent_snapshot else 0
prepared_count = len(agent_snapshot.timeline) if agent_snapshot else 0
attention_count = agent_snapshot.review_required if agent_snapshot else 0
agent_focus = (
    "The latest mailbox run is complete. Review the prepared course timeline and approve only verified calendar proposals."
    if agent_snapshot else
    "Connect a mailbox once, then let AI Scroll fetch, filter and consolidate new academic mail for you."
)

st.markdown(
    f"""
    <div class="hero">
      <div class="hero-kicker">✦ AI SCROLL · AUTONOMOUS INBOX AGENT</div>
      <h1>Connect once. Let the agent follow every deadline.</h1>
      <p>AI Scroll watches new academic mail, merges changing instructions and prepares evidence-backed actions for your approval.</p>
    </div>
    <div class="status-strip">
      <div class="status-card"><div class="number">{mailbox_status}</div><div class="label">Mailbox agent</div></div>
      <div class="status-card"><div class="number">{scanned_count}</div><div class="label">Messages scanned</div></div>
      <div class="status-card"><div class="number">{prepared_count}</div><div class="label">Course tasks prepared</div></div>
      <div class="status-card"><div class="number">0</div><div class="label">Unauthorized writes</div></div>
    </div>
    <div class="brief-banner">
      <div class="brief-copy"><b>Agent status</b>{agent_focus}</div>
      <div class="brief-action">{attention_count} item(s) need review</div>
    </div>
    """,
    unsafe_allow_html=True,
)

with st.sidebar:
    st.markdown("## AI Scroll")
    st.caption("Evidence-backed academic planning")
    st.divider()
    st.markdown("### Workspace")
    mode = st.radio("Extraction mode", ["Demo", "Live model"], help="Demo requires no API key.")
    st.info("Calendar proposals remain local until you explicitly confirm them.")
    with st.expander("Urgency policy"):
        st.markdown("- **High:** within 72 hours\n- **Medium:** 4–7 days\n- **Low:** more than 7 days\n- **Clarification:** unsafe to infer")

agent_tab, single_tab, chain_tab, safety_tab, evaluation_tab, review_tab = st.tabs(
    ["Agent workspace", "Academic inbox", "Course timeline", "Calendar review", "Evaluation", "Label review"]
)

with agent_tab:
    st.markdown('<div class="eyebrow">Autonomous inbox agent</div>', unsafe_allow_html=True)
    st.subheader("Connect once. Let the agent watch the inbox.")
    st.caption("The agent fetches new messages, ignores unrelated mail, merges course updates and asks for approval before any calendar write.")

    connector_name = "Gmail · read only" if active_provider == "gmail" and gmail_authorized else "Local demo mailbox"
    st.markdown(
        '<div class="agent-grid">'
        f'<div class="agent-card"><span>Mailbox</span><b>{"Connected" if connected else "Not connected"}</b><small>{connector_name if connected else "Choose a connector to begin"}</small></div>'
        '<div class="agent-card"><span>Scan policy</span><b>New mail only</b><small>A real deployment would use a provider webhook or scheduled delta sync.</small></div>'
        '<div class="agent-card"><span>Safety policy</span><b>Human approval</b><small>The agent can prepare proposals but cannot write to a calendar by itself.</small></div>'
        '</div>',
        unsafe_allow_html=True,
    )
    connect_col, gmail_col, run_col, real_col = st.columns(4)
    if connect_col.button(
        "Using demo mailbox" if connected and active_provider == "demo" else "Use demo mailbox",
        type="secondary",
        use_container_width=True,
        disabled=connected and active_provider == "demo",
    ):
        st.session_state["demo_mailbox_connected"] = True
        st.session_state["mailbox_provider"] = "demo"
        st.session_state["agent_run"] = None
        st.rerun()
    if gmail_col.button(
        "Using Gmail" if connected and active_provider == "gmail" else "Use Gmail",
        type="secondary",
        use_container_width=True,
        disabled=not gmail_authorized or (connected and active_provider == "gmail"),
        help="Gmail access is read only.",
    ):
        st.session_state["mailbox_provider"] = "gmail"
        st.session_state["agent_run"] = None
        st.rerun()
    if run_col.button("Run inbox agent now", type="primary", use_container_width=True, disabled=not connected):
        try:
            connector = GmailMailboxConnector() if active_provider == "gmail" else DemoMailboxConnector()
            st.session_state["agent_run"] = InboxAgent(connector).run(
                now=datetime.now().astimezone()
            )
            st.rerun()
        except Exception as exc:
            st.error(f"Mailbox run failed: {exc}")
    if real_col.button("Set up Gmail", type="secondary", use_container_width=True):
        st.session_state["show_mailbox_setup"] = not st.session_state.get("show_mailbox_setup", False)

    if st.session_state.get("show_mailbox_setup"):
        st.markdown("#### Gmail read-only setup")
        st.caption("AI Scroll requests only `gmail.readonly`. It cannot send, delete or modify email.")
        setup_left, setup_right = st.columns([1.45, 1])
        with setup_left:
            st.markdown(
                "1. In Google Cloud, enable **Gmail API**.\n"
                "2. Configure the OAuth consent screen and add your Google account as a test user.\n"
                "3. Create an **OAuth client ID → Desktop app** and download the JSON.\n"
                "4. Save it at the private path shown here, then start authorization."
            )
            st.code(str(client_secrets_path()), language=None)
            st.link_button(
                "Open Google Cloud credentials",
                "https://console.cloud.google.com/apis/credentials",
                use_container_width=True,
            )
        with setup_right:
            secret_ready = client_secrets_path().is_file()
            st.metric("OAuth client file", "Ready" if secret_ready else "Missing")
            st.metric("Gmail token", "Authorized" if gmail_authorized else "Not authorized")
            if st.button(
                "Start Gmail authorization",
                type="primary",
                use_container_width=True,
                disabled=not secret_ready or gmail_authorized,
            ):
                creation_flags = getattr(subprocess, "CREATE_NO_WINDOW", 0)
                subprocess.Popen(
                    [sys.executable, str(ROOT / "scripts" / "authorize_gmail.py")],
                    cwd=str(ROOT),
                    creationflags=creation_flags,
                )
                st.info("Google authorization opened in your browser. After allowing read-only access, select Refresh status.")
            if st.button("Refresh authorization status", use_container_width=True):
                st.rerun()
            st.caption(f"Token location: {gmail_token_path()}")

    agent_run = st.session_state.get("agent_run")
    if agent_run is None:
        st.markdown(
            '<div class="agent-run"><b>Ready for an autonomous run</b><br><span>Connect the demo mailbox, then select “Run inbox agent now”. You will not paste any individual email.</span></div>',
            unsafe_allow_html=True,
        )
    else:
        st.success(f"Agent completed a mailbox run through {agent_run.connector}.")
        metric_cols = st.columns(4)
        metric_cols[0].metric("Messages scanned", agent_run.scanned)
        metric_cols[1].metric("Academic mail", agent_run.academic)
        metric_cols[2].metric("Noise ignored", agent_run.ignored)
        metric_cols[3].metric("Needs review", agent_run.review_required)
        st.markdown("#### Agent-created course timeline")
        for item in agent_run.timeline:
            deadline = datetime.fromisoformat(item.deadline_iso).strftime("%d %b %Y, %I:%M %p") if item.deadline_iso else "No active deadline"
            status_class = "badge-green" if item.status == "active" else "badge-red" if item.status == "cancelled" else "badge-amber"
            st.markdown(
                f'<div class="result-card"><span class="badge {status_class}">{item.status.title()}</span>'
                f'<span class="badge badge-blue">{item.course}</span>'
                f'<div class="result-title">{item.task_title}</div>'
                f'<div class="result-meta">{deadline} · {len(item.source_email_ids)} source email(s) merged · Action: {item.calendar_action}</div></div>',
                unsafe_allow_html=True,
            )
        st.info("The agent stopped at review. Open Calendar review to inspect evidence and approve an eligible proposal.")

with single_tab:
    rail, email_panel, assistant_panel = st.columns([0.62, 1.25, 1.05], gap="large")
    with rail:
        st.markdown('<div class="section-label">Academic inbox</div>', unsafe_allow_html=True)
        st.markdown('<div class="view-pills"><span class="view-pill active">All · 3</span><span class="view-pill">Deadlines · 1</span><span class="view-pill">Review · 1</span></div>', unsafe_allow_html=True)
        st.markdown('<div class="rail-card active"><b>PE6201</b><span>Individual Project · due soon</span></div>', unsafe_allow_html=True)
        st.markdown('<div class="rail-card"><b>Course updates</b><span>1 deadline change detected</span></div>', unsafe_allow_html=True)
        st.markdown('<div class="rail-card"><b>Needs review</b><span>Calendar proposals waiting</span></div>', unsafe_allow_html=True)
        st.markdown('<div class="section-label" style="margin-top:1.25rem">Status</div>', unsafe_allow_html=True)
        st.markdown('<span class="badge badge-amber">Deadline detected</span><br><br><span class="badge badge-green">Evidence found</span>', unsafe_allow_html=True)
    with email_panel:
        st.markdown('<div class="section-label">Selected academic email</div>', unsafe_allow_html=True)
        st.markdown('<div class="source-context"><div class="source-avatar">PE</div><div class="source-main"><b>Course announcement</b>Primary source · selected for extraction</div><span class="badge badge-green">Ready</span></div>', unsafe_allow_html=True)
        subject = st.text_input("Subject", value=SAMPLE_SUBJECT)
        sender = st.text_input("Sender", value=SAMPLE_SENDER)
        body = st.text_area("Email body", value=SAMPLE_BODY, height=280)
        run = st.button("Analyze email", type="primary", use_container_width=True)
    if run:
        try:
            st.session_state["task"] = extract(EmailInput(subject=subject, sender=sender, body=body), mode=mode)
        except Exception as exc:
            st.error(f"Extraction failed: {exc}")
    with assistant_panel:
        st.markdown('<div class="section-label">AI extracted details</div>', unsafe_allow_html=True)
        task = st.session_state.get("task")
        show_processing_route(task)
        if task is None:
            st.markdown('<div class="empty-state"><b>Ready to analyze</b>Select “Analyze email” to extract the course, task, deadline, priority and exact source evidence.</div>', unsafe_allow_html=True)
        else:
            show_single_result(task)

with chain_tab:
    st.markdown('<div class="section-label">Update detector</div>', unsafe_allow_html=True)
    st.subheader("One task, two emails, one final deadline")
    st.caption("AI Scroll keeps the original evidence, applies the later correction and records exactly what changed.")
    st.markdown('<div class="chain-flow"><div class="flow-card"><b>1 · Original message</b><span>Create the first evidence-backed task.</span></div><div class="flow-arrow">→</div><div class="flow-card"><b>2 · Later correction</b><span>Detect that both emails refer to the same task.</span></div><div class="flow-arrow">→</div><div class="flow-card"><b>3 · Final timeline</b><span>Keep the latest deadline and the complete source trail.</span></div></div>', unsafe_allow_html=True)
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
    st.markdown('<div class="section-label">Human approval gate</div>', unsafe_allow_html=True)
    st.subheader("Review before any calendar action")
    st.caption("Choose a case, inspect the proposed change and confirm only when its evidence is complete.")
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
    if scenario == "Eligible deadline":
        safety_cards = (
            '<div class="policy-card pass"><span>Source</span><b>Evidence complete</b><small>An exact deadline and timezone were found.</small></div>'
            '<div class="policy-card review"><span>Policy</span><b>Preview allowed</b><small>The proposal still requires explicit approval.</small></div>'
            '<div class="policy-card pass"><span>External effect</span><b>0 writes</b><small>No real calendar has been changed.</small></div>'
        )
    elif scenario == "Ambiguous next Friday":
        safety_cards = (
            '<div class="policy-card block"><span>Source</span><b>Date is ambiguous</b><small>“Next Friday” is unsafe to normalize here.</small></div>'
            '<div class="policy-card block"><span>Policy</span><b>Preview blocked</b><small>The user must clarify the date first.</small></div>'
            '<div class="policy-card pass"><span>External effect</span><b>0 writes</b><small>The calendar remains unchanged.</small></div>'
        )
    else:
        safety_cards = (
            '<div class="policy-card pass"><span>Source</span><b>Cancellation detected</b><small>The later email overrides the original event.</small></div>'
            '<div class="policy-card block"><span>Policy</span><b>New event blocked</b><small>A cancelled task cannot create a calendar item.</small></div>'
            '<div class="policy-card pass"><span>External effect</span><b>0 writes</b><small>The calendar remains unchanged.</small></div>'
        )
    st.markdown(f'<div class="policy-grid">{safety_cards}</div>', unsafe_allow_html=True)
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
        approval_evidence = safety_item.evidence_history[-1]
        st.markdown('<div class="section-label">Evidence to approve</div>', unsafe_allow_html=True)
        st.markdown(
            f'<div class="evidence">“{approval_evidence.evidence_quote}”<br><small>Source: {approval_evidence.source_subject}</small></div>',
            unsafe_allow_html=True,
        )
        st.markdown(
            '<div class="approval-summary">'
            '<div class="approval-item"><span>On confirmation</span><b>Record one simulated event</b><small>The local demo adapter receives this reviewed proposal.</small></div>'
            '<div class="approval-item"><span>Retry protection</span><b>Duplicate writes are prevented</b><small>The proposal fingerprint maps repeated approval to the existing event.</small></div>'
            '</div>',
            unsafe_allow_html=True,
        )
        st.info("The next button is the explicit approval step. No external calendar is connected in this demonstration.")
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
        if safety_item.evidence_history:
            blocking_evidence = safety_item.evidence_history[-1]
            st.markdown('<div class="section-label">Evidence that triggered the block</div>', unsafe_allow_html=True)
            st.markdown(
                f'<div class="evidence">“{blocking_evidence.evidence_quote}”<br><small>Source: {blocking_evidence.source_subject}</small></div>',
                unsafe_allow_html=True,
            )
        st.caption("The user must clarify or resolve the source email before a new preview can be created.")

    with st.expander("View safety audit"):
        recent_audit = st.session_state["calendar_audit"][-8:]
        if not recent_audit:
            st.caption("No policy decisions recorded in this session.")
        else:
            audit_rows = "".join(
                '<div class="audit-line">'
                f'<span class="audit-action">{entry.get("action", "check")}</span>'
                f'<span class="audit-status">{entry.get("status", "unknown").replace("_", " ")}</span>'
                f'<span>{entry.get("reason") or entry.get("event_id") or entry.get("proposal_id") or "Policy evaluated"}</span>'
                '</div>'
                for entry in reversed(recent_audit)
            )
            st.markdown(f'<div class="trust-panel">{audit_rows}</div>', unsafe_allow_html=True)
        with st.expander("Raw audit JSON"):
            st.json(recent_audit)

with evaluation_tab:
    st.markdown('<div class="eyebrow">Evaluation evidence</div>', unsafe_allow_html=True)
    st.subheader("Provisional offline evaluation")
    st.warning(
        "These are development diagnostics, not final assignment results. "
        "All labels still require human review, and no live language model was run."
    )
    metrics_path = ROOT / "04_evaluation" / "outputs" / "development_metrics.json"
    if not metrics_path.exists():
        st.info("Run `python 04_evaluation/score_development.py` to create the comparison.")
    else:
        evaluation = load_evaluation(metrics_path)
        summary_cols = st.columns(4)
        for column, metric in zip(summary_cols, primary_metrics(evaluation)):
            column.metric(metric["label"], metric["value"], help=metric["detail"])

        st.markdown("#### Baseline comparison")
        split = st.selectbox(
            "Evaluation split",
            ["all", "development", "test", "synthetic_holdout"],
            format_func=lambda value: {
                "all": "All 50 emails",
                "development": "Development · 20 emails",
                "test": "Test · 18 emails",
                "synthetic_holdout": "Synthetic holdout · 12 emails",
            }[value],
            key="evaluation_split",
        )
        st.table(comparison_rows(evaluation, split=split))
        st.caption(
            f"Reference time: {evaluation['reference_time']} · "
            f"Population: {evaluation['population']['emails']} emails, "
            f"{evaluation['population']['multi_email_threads']} multi-email threads"
        )

        errors_path = ROOT / "04_evaluation" / "outputs" / "development_errors.csv"
        if errors_path.exists():
            current_errors = load_errors(errors_path)
            st.markdown("#### Current-pipeline error analysis")
            error_summary, error_detail = st.columns([1, 2])
            with error_summary:
                st.caption(f"{len(current_errors)} field-level errors across the 50 provisional cases")
                st.table(error_counts(current_errors))
            with error_detail:
                field_options = ["all", *sorted({row["field"] for row in current_errors})]
                selected_field = st.selectbox(
                    "Error field",
                    field_options,
                    format_func=lambda value: "All fields" if value == "all" else value.replace("_", " ").title(),
                    key="evaluation_error_field",
                )
                selected_errors = filter_errors(current_errors, split=split, field=selected_field)
                st.caption(f"Showing {len(selected_errors)} errors for the selected filters")
                st.dataframe(
                    [{
                        "Case": row["email_id"],
                        "Split": row["split"],
                        "Field": row["field"],
                        "Predicted": row["predicted"] or "—",
                        "Draft expected": row["gold_draft"] or "—",
                    } for row in selected_errors],
                    use_container_width=True,
                    hide_index=True,
                )

        st.markdown("#### Multi-email chain verification")
        st.dataframe(
            [{
                "Thread": row["thread_id"],
                "Split": row["split"],
                "Final state": "Pass" if row["merged_final_state_correct"] else "Fail",
                "Full record": "Pass" if row["full_record_correct"] else "Fail",
                "Timeline items": row["timeline_items_returned"],
            } for row in evaluation["merge_details"]],
            use_container_width=True,
            hide_index=True,
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
