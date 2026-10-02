from __future__ import annotations

import html
import json
import subprocess
import sys
from datetime import datetime
from pathlib import Path

import streamlit as st

from app.calendar_gate import CalendarApprovalGate, CalendarPolicyError, InMemoryCalendarStore
from app.backward_planner import (
    PlanningError, build_backward_plan, milestone_proposal, suggested_effort_hours,
)
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
from app.google_calendar import (
    GoogleCalendarStore,
    google_calendar_is_authorized,
    google_calendar_token_path,
)
from app.inbox_agent import DemoMailboxConnector, InboxAgent
from app.label_review import (
    CALENDAR_ACTIONS, RELATIONS, TASK_TYPES, URGENCIES, load_jsonl, load_review_rows,
    review_progress, save_review_row, validate_review,
)
from app.merge_engine import build_timeline
from app.models import CalendarProposal, EmailInput, TimelineItem
from app.outlook_connector import (
    OutlookMailboxConnector,
    microsoft_client_id,
    microsoft_config_path,
    microsoft_tenant_id,
    outlook_device_flow_path,
    outlook_graph_marker_path,
    outlook_is_authorized,
    save_microsoft_config,
)
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
    .block-container {max-width:1440px; padding-top:3.6rem; padding-bottom:4rem;}
    [data-testid="stSidebar"] {background:#111936; border-right:1px solid #263052;}
    [data-testid="stSidebar"] * {color:#f5f7ff;}
    [data-testid="stSidebar"] .stAlert {background:#1d284d; border:1px solid #34416c;}
    [data-testid="stSidebar"] [data-testid="stAlert"] p {color:#f5f7ff !important;}
    [data-testid="stTabs"] button {font-size:.95rem; font-weight:650; padding:.85rem 1rem;}
    [data-testid="stMetric"] {background:var(--panel); border:1px solid var(--line); border-radius:16px; padding:14px 16px; box-shadow:0 8px 24px rgba(20,33,61,.04);}
    [data-testid="stMetricValue"] {font-size:1.5rem; color:var(--ink);}
    [data-testid="stMetricLabel"] {color:#526078 !important; font-weight:700;}
    [data-testid="stAlert"] p {color:var(--ink); font-weight:600;}
    .eyebrow {color:var(--brand); font-weight:800; letter-spacing:.1em; font-size:.72rem; text-transform:uppercase;}
    .workspace-head {display:flex; align-items:center; justify-content:space-between; gap:18px; margin:.1rem 0 .9rem;}
    .workspace-brand {font-size:1.35rem; font-weight:850; color:var(--ink); letter-spacing:-.025em;}
    .workspace-brand span {color:var(--brand);}
    .workspace-sub {font-size:.76rem; color:var(--muted); margin-top:1px;}
    .info-dot {display:inline-flex !important; align-items:center; justify-content:center; width:17px; height:17px; margin-left:4px; border-radius:50%; border:1px solid #c7cfdf; background:#f8f9fc; color:#59667d !important; font-size:.65rem !important; font-weight:850; line-height:1; cursor:help; vertical-align:1px; text-transform:none !important; letter-spacing:0 !important;}
    .sync-pill {display:inline-flex; align-items:center; gap:7px; background:white; border:1px solid var(--line); border-radius:999px; padding:7px 11px; color:#46536a; font-size:.74rem; font-weight:750;}
    .sync-dot {width:8px; height:8px; border-radius:50%; background:var(--teal); box-shadow:0 0 0 4px rgba(22,138,120,.1);}
    .sync-dot.off {background:#98a2b3; box-shadow:0 0 0 4px rgba(152,162,179,.12);}
    .today-grid {display:grid; grid-template-columns:minmax(0,1.65fr) minmax(280px,.85fr); gap:14px; margin-bottom:14px;}
    .today-focus {position:relative; overflow:hidden; min-height:188px; border-radius:22px; padding:24px 26px; background:linear-gradient(125deg,#111a38 0%,#1d2c62 70%,#304691 100%); color:white; box-shadow:0 16px 38px rgba(24,36,81,.16);}
    .today-focus:after {content:""; position:absolute; width:220px; height:220px; border-radius:50%; right:-75px; top:-110px; background:radial-gradient(circle,rgba(83,210,185,.32),rgba(82,103,232,0));}
    .today-kicker {font-size:.68rem; color:#b8c5f3; font-weight:850; letter-spacing:.11em; text-transform:uppercase;}
    .today-focus h1 {max-width:720px; color:white; font-size:1.85rem; line-height:1.12; letter-spacing:-.035em; margin:.55rem 0 .55rem;}
    .today-focus p {max-width:760px; color:#d7def8; font-size:.88rem; line-height:1.5; margin:0;}
    .focus-tags {display:flex; flex-wrap:wrap; gap:7px; margin-top:16px;}
    .focus-tag {background:rgba(255,255,255,.1); border:1px solid rgba(255,255,255,.13); border-radius:999px; padding:5px 9px; color:#edf1ff; font-size:.68rem; font-weight:700;}
    .activity-card {border:1px solid var(--line); border-radius:22px; background:white; padding:18px 19px; box-shadow:0 10px 28px rgba(20,33,61,.05);}
    .activity-head {display:flex; justify-content:space-between; align-items:center; gap:10px; color:var(--ink); font-size:.86rem; font-weight:800; margin-bottom:14px;}
    .activity-head > .state-pill {font-size:.63rem; color:var(--teal); background:var(--teal-soft); border-radius:999px; padding:4px 8px; text-transform:uppercase; letter-spacing:.06em;}
    .activity-stat {display:grid; grid-template-columns:40px 1fr; gap:10px; align-items:center; padding:8px 0; border-bottom:1px solid #eef1f6;}
    .activity-stat:last-of-type {border-bottom:0;}
    .activity-stat b {font-size:1.18rem; color:var(--ink);}
    .activity-stat span {font-size:.73rem; color:var(--muted); line-height:1.3;}
    .safety-lock {margin-top:10px; border-radius:10px; padding:8px 10px; background:#f7f9fc; color:#43506a; font-size:.7rem; font-weight:750;}
    .quick-strip {display:grid; grid-template-columns:1.35fr 1fr 1fr; gap:10px; margin-bottom:1.2rem;}
    .quick-card {display:flex; align-items:center; justify-content:space-between; gap:12px; min-height:68px; background:white; border:1px solid var(--line); border-radius:14px; padding:11px 14px;}
    .quick-card span {display:block; color:#8a94a6; font-size:.63rem; font-weight:850; letter-spacing:.08em; text-transform:uppercase; margin-bottom:4px;}
    .quick-card b {display:block; color:var(--ink); font-size:.82rem; line-height:1.25;}
    .quick-value {flex:0 0 auto; color:var(--brand); font-weight:850; font-size:1.08rem;}
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
    [data-testid="stExpander"] {
      color-scheme:light;
      background:#ffffff !important;
      border:1px solid #d9deea !important;
      border-radius:12px !important;
      overflow:hidden;
    }
    [data-testid="stExpander"] details,
    [data-testid="stExpander"] [data-testid="stExpanderDetails"] {
      background:#ffffff !important;
      color:var(--ink) !important;
    }
    [data-testid="stExpander"] summary {
      background:#f8fafc !important;
      color:var(--ink) !important;
    }
    [data-testid="stExpander"] summary:hover {background:#f1f4f9 !important;}
    [data-testid="stExpander"] summary *,
    [data-testid="stExpander"] summary svg {
      color:var(--ink) !important;
      fill:var(--ink) !important;
    }
    [data-testid="stWidgetLabel"] p,
    .stTextInput label,
    .stTextInput label p {
      color:#344054 !important;
      font-weight:700 !important;
    }
    .stTextInput input,
    .stTextArea textarea,
    .stSelectbox > div > div {
      color-scheme:light;
      border-radius:11px !important;
      border-color:#cbd2df !important;
      background:#ffffff !important;
      color:#14213d !important;
      caret-color:#14213d !important;
      -webkit-text-fill-color:#14213d !important;
    }
    .stTextInput input::placeholder,
    .stTextArea textarea::placeholder {
      color:#8a94a6 !important;
      -webkit-text-fill-color:#8a94a6 !important;
      opacity:1 !important;
    }
    [data-testid="stPopover"] > button {border-radius:11px !important; border:1px solid #3b4b79 !important; background:#1a2449 !important; color:#f5f7ff !important; font-weight:750 !important;}
    [data-testid="stPopover"] > button:hover {background:#26335f !important; border-color:#53649b !important;}
    .help-fab {position:fixed; right:24px; bottom:24px; z-index:9999;}
    .help-fab details {position:relative;}
    .help-fab summary {display:flex; align-items:center; justify-content:center; width:46px; height:46px; border-radius:50%; list-style:none; cursor:pointer; background:var(--brand); color:white; border:3px solid white; box-shadow:0 10px 28px rgba(20,33,61,.28); font-size:1.15rem; font-weight:900;}
    .help-fab summary::-webkit-details-marker {display:none;}
    .help-fab details[open] summary {background:#3448bd;}
    .help-fab-panel {position:absolute; right:0; bottom:58px; width:292px; border:1px solid #dce2ef; border-radius:16px; background:white; color:var(--ink); padding:15px 16px; box-shadow:0 18px 48px rgba(20,33,61,.22);}
    .help-fab-panel b {display:block; font-size:.92rem; margin-bottom:8px;}
    .help-fab-step {display:grid; grid-template-columns:22px 1fr; gap:8px; align-items:start; padding:6px 0; color:#536078; font-size:.73rem; line-height:1.35;}
    .help-fab-step span {display:flex; align-items:center; justify-content:center; width:20px; height:20px; border-radius:6px; background:var(--brand-soft); color:#4256c9; font-size:.65rem; font-weight:850;}
    .help-fab-note {border-top:1px solid #edf0f5; margin-top:7px; padding-top:9px; color:#748096; font-size:.68rem; line-height:1.4;}
    .before {color:#8b3a3a; text-decoration:line-through;}
    .after {color:#176b52; font-weight:700;}

    /* 2026-10-02 workspace redesign: quiet, compact and task-first. */
    :root {
      --ink:#202522;
      --muted:#707771;
      --line:#e2e5e0;
      --panel:#ffffff;
      --canvas:#f7f7f4;
      --brand:#217a55;
      --brand-soft:#eaf4ee;
      --teal:#217a55;
      --teal-soft:#eaf4ee;
      --amber:#9a6718;
      --amber-soft:#fbf1df;
    }
    .stApp {background:var(--canvas);}
    .block-container {max-width:1280px; padding-top:2rem;}
    [data-testid="stHeader"] {background:rgba(247,247,244,.88);}
    [data-testid="stSidebar"] {background:#fff; border-right:1px solid var(--line);}
    [data-testid="stSidebar"] * {color:var(--ink);}
    [data-testid="stSidebar"] [data-testid="stMarkdownContainer"] p,
    [data-testid="stSidebar"] .stCaption {color:#707771 !important;}
    [data-testid="stSidebar"] .stAlert {background:#f4f7f4; border:1px solid #dce7df;}
    [data-testid="stSidebar"] [data-testid="stAlert"] p {color:#425048 !important;}
    [data-testid="stSidebar"] hr {border-color:#eceeea;}
    [data-testid="stSidebar"] [role="radiogroup"] label {padding:.32rem .1rem;}
    [data-testid="stSidebar"] [data-testid="stPopover"] > button {
      background:#f7f8f6 !important; border:1px solid #dfe3dd !important;
      color:var(--ink) !important; box-shadow:none !important;
    }
    [data-testid="stSidebar"] [data-testid="stPopover"] > button:hover {background:#eff3ef !important;}
    .workspace-head {margin:0 0 1.15rem; padding-bottom:1rem; border-bottom:1px solid var(--line);}
    .workspace-brand {font-size:1.28rem; letter-spacing:-.04em;}
    .workspace-brand span {color:var(--brand);}
    .workspace-sub {font-size:.72rem; color:#838982;}
    .sync-pill {background:transparent; border:0; padding:6px 0; color:#59615b;}
    .sync-dot {width:7px; height:7px; box-shadow:none;}
    .today-grid {display:grid; grid-template-columns:minmax(0,1fr) 310px; gap:0; margin:0 0 12px; border:1px solid var(--line); border-radius:12px; overflow:hidden; background:#fff;}
    .today-focus {min-height:0; border-radius:0; padding:24px 26px; background:#fff; color:var(--ink); box-shadow:none;}
    .today-focus:after {display:none;}
    .today-kicker {font-size:.68rem; color:var(--brand); letter-spacing:.08em;}
    .today-focus h1 {max-width:760px; color:var(--ink); font-size:1.7rem; line-height:1.15; letter-spacing:-.04em; margin:.5rem 0 .5rem;}
    .today-focus p {max-width:760px; color:var(--muted); font-size:.84rem; line-height:1.5;}
    .focus-tags {gap:14px; margin-top:17px;}
    .focus-tag {position:relative; background:transparent; border:0; border-radius:0; padding:0 0 0 11px; color:#59615b; font-size:.69rem; font-weight:650;}
    .focus-tag:before {content:""; position:absolute; left:0; top:50%; width:5px; height:5px; margin-top:-2px; border-radius:50%; background:#9aa19b;}
    .activity-card {border:0; border-left:1px solid var(--line); border-radius:0; padding:20px 22px; box-shadow:none; background:#fbfcfa;}
    .activity-head {font-size:.77rem; margin-bottom:9px;}
    .activity-head > .state-pill {font-size:.59rem; background:var(--brand-soft); color:var(--brand);}
    .activity-stat {grid-template-columns:34px 1fr; gap:8px; padding:7px 0; border-bottom:0;}
    .activity-stat b {font-size:1rem; font-variant-numeric:tabular-nums;}
    .activity-stat span {font-size:.69rem;}
    .safety-lock {margin-top:8px; border:1px solid #e1e5e0; border-radius:7px; padding:7px 9px; background:white; font-size:.65rem; color:#5e665f;}
    .quick-strip {display:grid; grid-template-columns:1.5fr 1fr 1fr; gap:0; margin:0 0 1.05rem; border:1px solid var(--line); border-radius:10px; overflow:hidden; background:#fff;}
    .quick-card {min-height:57px; border:0; border-right:1px solid var(--line); border-radius:0; padding:10px 15px; background:#fff;}
    .quick-card:last-child {border-right:0;}
    .quick-card span {font-size:.58rem; color:#929891; letter-spacing:.07em;}
    .quick-card b {font-size:.76rem;}
    .quick-value {font-size:.88rem; color:var(--brand);}
    [data-testid="stTabs"] {background:transparent;}
    [data-testid="stTabs"] [data-baseweb="tab-list"] {gap:22px; border-bottom:1px solid var(--line);}
    [data-testid="stTabs"] button {font-size:.79rem; font-weight:650; padding:.7rem 0; color:#747b75;}
    [data-testid="stTabs"] button[aria-selected="true"] {color:var(--ink);}
    [data-testid="stTabs"] [data-baseweb="tab-highlight"] {background:var(--brand); height:2px;}
    [data-testid="stMetric"] {border:0; border-radius:8px; padding:11px 12px; box-shadow:none; background:#fff; border-left:2px solid #dfe5df;}
    [data-testid="stMetricValue"] {font-size:1.25rem;}
    .agent-grid {gap:0; border:1px solid var(--line); border-radius:10px; overflow:hidden; background:#fff;}
    .agent-card {border:0; border-right:1px solid var(--line); border-radius:0; padding:13px 15px;}
    .agent-card:last-child {border-right:0;}
    .result-card,.rail-card,.source-context,.flow-card,.policy-card {border-radius:9px; box-shadow:none;}
    .agent-run {border:1px solid #dbe5de; background:#f3f7f4; border-radius:10px;}
    .empty-state {border-radius:10px; background:#fbfcfa;}
    .stButton > button[kind="primary"] {background:var(--brand); border-color:var(--brand); border-radius:8px; color:#fff !important;}
    .stButton > button[kind="primary"] * {color:#fff !important;}
    .stButton > button[kind="primary"]:hover {background:#196746; border-color:#196746;}
    .stButton > button[kind="secondary"] {border-radius:8px;}
    .stTextInput input,.stTextArea textarea,.stSelectbox > div > div {border-radius:8px !important; color:#202522 !important; -webkit-text-fill-color:#202522 !important;}
    [data-testid="stExpander"] {border-radius:8px !important;}
    .help-fab summary {width:42px; height:42px; background:var(--brand); border:2px solid white; box-shadow:0 7px 20px rgba(32,70,52,.2); font-size:1rem;}
    .help-fab details[open] summary {background:#196747;}
    .help-fab-panel {border-radius:10px; box-shadow:0 15px 38px rgba(34,43,37,.15);}
    .help-fab-step span {background:var(--brand-soft); color:var(--brand);}
    .info-dot {border-color:#cbd2cc; background:#fff; color:#69716b !important;}
    .connect-guide {border:1px solid #d9e5dc; border-radius:11px; background:#f3f8f4; padding:18px 19px; margin:.8rem 0 1rem;}
    .connect-guide-head {display:flex; justify-content:space-between; gap:14px; align-items:flex-start; margin-bottom:14px;}
    .connect-guide-head b {display:block; color:var(--ink); font-size:1rem; margin-bottom:3px;}
    .connect-guide-head span {display:block; color:#68716a; font-size:.75rem; line-height:1.4;}
    .connect-badge {flex:0 0 auto; border:1px solid #cdded2; border-radius:999px; background:#fff; color:var(--brand) !important; padding:5px 9px; font-size:.63rem !important; font-weight:800; text-transform:uppercase; letter-spacing:.06em;}
    .connect-steps {display:grid; grid-template-columns:repeat(4,1fr); border:1px solid #dfe8e1; border-radius:9px; overflow:hidden; background:#fff;}
    .connect-step {position:relative; min-height:67px; padding:11px 11px 10px 36px; border-right:1px solid #e7ebe7;}
    .connect-step:last-child {border-right:0;}
    .connect-step i {position:absolute; left:11px; top:11px; display:flex; align-items:center; justify-content:center; width:18px; height:18px; border-radius:50%; background:var(--brand-soft); color:var(--brand); font-size:.62rem; font-style:normal; font-weight:850;}
    .connect-step b {display:block; font-size:.72rem; margin-bottom:3px;}
    .connect-step span {display:block; color:#7a827c; font-size:.64rem; line-height:1.35;}
    .setup-status {border:1px solid var(--line); border-radius:9px; background:#fff; padding:13px 14px; margin:.4rem 0 .8rem;}
    .setup-status span {display:block; color:#888f89; font-size:.61rem; font-weight:800; letter-spacing:.08em; text-transform:uppercase;}
    .setup-status b {display:block; color:var(--ink); font-size:.9rem; margin-top:4px;}

    /* Submission polish: restore one memorable focus card without the old heavy dashboard. */
    :root {
      --canvas:#eef3f7;
      --ink:#17243b;
      --muted:#66758a;
      --line:#dce4ec;
      --brand:#236b67;
      --brand-soft:#e7f3f1;
    }
    .stApp {
      background:
        radial-gradient(circle at 80% 0%, rgba(113,190,177,.12), transparent 28rem),
        linear-gradient(180deg,#f7fafc 0,#edf2f6 100%);
    }
    [data-testid="stHeader"] {background:rgba(247,250,252,.78); backdrop-filter:blur(12px);}
    [data-testid="stSidebar"] {background:#f8fafb; border-right:1px solid #dce4ea;}
    .block-container {max-width:1320px; padding-top:2.25rem;}
    .workspace-head {border-bottom:0; padding:0 2px; margin-bottom:1.1rem;}
    .workspace-brand {font-size:1.38rem;}
    .workspace-sub {color:#778599;}
    .sync-pill {background:#fff; border:1px solid #dce4ea; border-radius:999px; padding:7px 11px; box-shadow:0 4px 16px rgba(34,58,80,.05);}
    .today-grid {grid-template-columns:minmax(0,1.65fr) minmax(285px,.75fr); gap:14px; border:0; border-radius:0; overflow:visible; background:transparent; margin-bottom:14px;}
    .today-focus {
      position:relative; overflow:hidden; min-height:210px; border:0; border-radius:24px;
      padding:27px 29px; color:white;
      background:linear-gradient(130deg,#102b4a 0%,#174768 52%,#197a71 100%);
      box-shadow:0 18px 42px rgba(22,55,78,.18);
    }
    .today-focus:before {content:""; position:absolute; width:260px; height:260px; border-radius:50%; right:-90px; top:-130px; background:rgba(255,255,255,.08);}
    .today-focus:after {display:block; content:""; position:absolute; width:170px; height:170px; border-radius:50%; right:70px; bottom:-125px; border:1px solid rgba(255,255,255,.12);}
    .today-kicker {position:relative; z-index:1; color:#aee6d9; font-size:.67rem;}
    .today-focus h1 {position:relative; z-index:1; color:#fff; font-size:2rem; max-width:720px; margin:.65rem 0 .55rem;}
    .today-focus p {position:relative; z-index:1; color:#dcebf2; font-size:.88rem; max-width:720px;}
    .focus-tags {position:relative; z-index:1; gap:7px; margin-top:20px;}
    .focus-tag {border:1px solid rgba(255,255,255,.15); background:rgba(255,255,255,.09); color:#f5fbff; border-radius:999px; padding:6px 10px; font-size:.67rem;}
    .focus-tag:before {display:none;}
    .activity-card {border:1px solid rgba(218,228,236,.95); border-radius:24px; background:rgba(255,255,255,.92); padding:20px 21px; box-shadow:0 14px 34px rgba(34,58,80,.09);}
    .activity-head {font-size:.82rem; margin-bottom:11px;}
    .activity-stat {grid-template-columns:40px 1fr; padding:8px 0; border-bottom:1px solid #edf1f4;}
    .activity-stat:last-of-type {border-bottom:0;}
    .activity-stat b {font-size:1.15rem; color:#17344e;}
    .activity-stat span {font-size:.7rem;}
    .safety-lock {border:0; background:#edf7f4; color:#27655d; border-radius:10px; padding:9px 10px;}
    .quick-strip {gap:10px; border:0; border-radius:0; overflow:visible; background:transparent; margin-bottom:1.2rem;}
    .quick-card {min-height:72px; border:1px solid #dce4eb; border-radius:16px; padding:12px 15px; background:rgba(255,255,255,.94); box-shadow:0 8px 22px rgba(34,58,80,.055);}
    .quick-card:last-child {border-right:1px solid #dce4eb;}
    .quick-card span {color:#8290a2;}
    .quick-card b {font-size:.8rem;}
    .quick-value {color:#19756b; font-size:1rem;}
    [data-testid="stTabs"] > div > [data-baseweb="tab-list"] {gap:5px; border:1px solid #dce4eb; border-radius:14px; background:rgba(255,255,255,.9); padding:5px; box-shadow:0 8px 22px rgba(34,58,80,.045);}
    [data-testid="stTabs"] button {padding:.58rem .85rem; border-radius:9px; color:#657487 !important;}
    [data-testid="stTabs"] button:hover {background:#edf3f6; color:#17344e !important;}
    [data-testid="stTabs"] button[aria-selected="true"] {background:#17344e; color:#fff !important;}
    [data-testid="stTabs"] [data-baseweb="tab-highlight"] {display:none;}
    .agent-grid {gap:10px; border:0; border-radius:0; overflow:visible; background:transparent;}
    .agent-card {border:1px solid #dce4eb; border-radius:14px; padding:14px 15px; box-shadow:0 7px 20px rgba(34,58,80,.04);}
    .agent-card:last-child {border-right:1px solid #dce4eb;}
    .result-card,.rail-card,.source-context,.flow-card,.policy-card {border-radius:13px; box-shadow:0 6px 18px rgba(34,58,80,.04);}
    .connect-guide {background:linear-gradient(135deg,#f2f8f7,#f7fafc); border-color:#cfe1df; border-radius:16px;}
    .guided-shell {border:1px solid #cfe0e7; border-radius:18px; background:linear-gradient(135deg,#fff,#f2f8f8); padding:18px; margin:.5rem 0 1.25rem; box-shadow:0 8px 24px rgba(34,58,80,.05);}
    .guided-head {display:flex; align-items:flex-start; justify-content:space-between; gap:16px; margin-bottom:14px;}
    .guided-head b {display:block; color:#17344e; font-size:1rem;}
    .guided-head span {display:block; color:#748397; font-size:.72rem; margin-top:3px;}
    .guided-progress {white-space:nowrap; border-radius:999px; background:#e5f3ef; color:#17695f; padding:6px 10px; font-size:.68rem; font-weight:800;}
    .guided-steps {display:grid; grid-template-columns:repeat(4,1fr); gap:9px;}
    .guided-step {position:relative; min-height:92px; border:1px solid #dde6ec; border-radius:13px; background:#fff; padding:12px;}
    .guided-step i {display:flex; align-items:center; justify-content:center; width:24px; height:24px; border-radius:50%; background:#eaf0f4; color:#607286; font-size:.68rem; font-style:normal; font-weight:850; margin-bottom:8px;}
    .guided-step b {display:block; color:#26364c; font-size:.75rem; line-height:1.3;}
    .guided-step span {display:block; color:#8290a1; font-size:.65rem; line-height:1.35; margin-top:4px;}
    .guided-step.done {border-color:#c9e2dc; background:#f4faf8;}
    .guided-step.done i {background:#21786d; color:#fff;}
    .guided-step.active {border-color:#2c667f; box-shadow:0 0 0 2px rgba(44,102,127,.09);}
    .guided-step.active i {background:#173f5a; color:#fff;}
    @media (max-width:900px) {
      .workspace-head{align-items:flex-start}
      .today-grid{grid-template-columns:1fr}
      .quick-strip{grid-template-columns:1fr}
      .today-focus h1{font-size:1.45rem}
      .activity-card{border:1px solid var(--line)}
      .quick-card{border:1px solid var(--line)}
      .quick-card:last-child{border:1px solid var(--line)}
      .route{grid-template-columns:repeat(2,1fr)}
      .policy-grid{grid-template-columns:1fr}
      .approval-summary{grid-template-columns:1fr}
      .guided-steps{grid-template-columns:1fr 1fr}
      .agent-grid{grid-template-columns:1fr}
      .chain-flow{grid-template-columns:1fr}
      .flow-arrow{transform:rotate(90deg)}
      [data-testid="stHorizontalBlock"]{flex-wrap:wrap !important;}
      [data-testid="stColumn"]{min-width:280px !important; flex:1 1 100% !important;}
      .help-fab{right:14px;bottom:14px}
      .help-fab-panel{width:270px}
      .connect-steps{grid-template-columns:1fr 1fr}
      .connect-step:nth-child(2){border-right:0}
      .connect-step:nth-child(-n+2){border-bottom:1px solid #e7ebe7}
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


st.session_state.setdefault("demo_mailbox_connected", True)
st.session_state.setdefault("mailbox_provider", "demo")
st.session_state.setdefault("agent_run", None)
st.session_state.setdefault("course_scope", "PE6201, HR6102")
st.session_state.setdefault("calendar_provider", "demo")
agent_snapshot = st.session_state["agent_run"]
gmail_authorized = gmail_is_authorized()
outlook_authorized = outlook_is_authorized()
calendar_authorized = google_calendar_is_authorized()
active_provider = st.session_state["mailbox_provider"]
if (active_provider == "outlook" and not outlook_authorized) or (
    active_provider == "gmail" and not gmail_authorized
):
    st.session_state["mailbox_provider"] = "demo"
    st.session_state["demo_mailbox_connected"] = True
    st.session_state["agent_run"] = None
    active_provider = "demo"
if active_provider == "demo":
    st.session_state["demo_mailbox_connected"] = True
connected = (
    gmail_authorized if active_provider == "gmail"
    else outlook_authorized if active_provider == "outlook"
    else st.session_state["demo_mailbox_connected"]
)
mailbox_status = (
    "Gmail connected" if active_provider == "gmail" and gmail_authorized
    else "Outlook connected" if active_provider == "outlook" and outlook_authorized
    else "Demo connected" if connected
    else "Not connected"
)
scanned_count = agent_snapshot.scanned if agent_snapshot else 0
prepared_count = len(agent_snapshot.timeline) if agent_snapshot else 0
attention_count = agent_snapshot.review_required if agent_snapshot else 0
active_deadlines: list[tuple[datetime, TimelineItem]] = []
if agent_snapshot:
    for timeline_item in agent_snapshot.timeline:
        if timeline_item.status != "active" or not timeline_item.deadline_iso:
            continue
        try:
            active_deadlines.append((datetime.fromisoformat(timeline_item.deadline_iso), timeline_item))
        except ValueError:
            continue
next_deadline = min(active_deadlines, key=lambda pair: pair[0]) if active_deadlines else None
today_label = datetime.now().astimezone().strftime("%A · %d %B")
if agent_snapshot and attention_count:
    focus_title = f"Review {attention_count} calendar proposal{'s' if attention_count != 1 else ''}"
    focus_copy = "The agent has finished triage. Check the source evidence before approving any calendar change."
elif agent_snapshot:
    focus_title = "Your academic inbox is up to date"
    focus_copy = "The latest scan is complete and no calendar proposal currently needs your attention."
else:
    focus_title = "Turn course emails into one reliable timeline"
    focus_copy = "Connect a mailbox once. AI Scroll filters course mail, merges updates and stops before every external action."
if next_deadline:
    next_dt, next_item = next_deadline
    next_deadline_title = html.escape(f"{next_item.course} · {next_item.task_title}")
    next_deadline_value = html.escape(next_dt.strftime("%d %b · %H:%M"))
else:
    next_deadline_title = "No active deadline yet"
    next_deadline_value = "—"
scope_display = html.escape(st.session_state["course_scope"] or "All courses")
connection_class = "" if connected else " off"
agent_state_label = "Ready" if connected else "Setup"

st.markdown(
    f"""
    <div class="workspace-head">
      <div>
        <div class="workspace-brand">AI <span>Scroll</span></div>
        <div class="workspace-sub">Academic command center · evidence before action <span class="info-dot" title="AI Scroll keeps the original email evidence visible before it proposes an external action.">?</span></div>
      </div>
      <div class="sync-pill"><span class="sync-dot{connection_class}"></span>{html.escape(mailbox_status)}</div>
    </div>
    <div class="today-grid">
      <section class="today-focus">
        <div class="today-kicker">Today · {html.escape(today_label)}</div>
        <h1>{html.escape(focus_title)}</h1>
        <p>{html.escape(focus_copy)}</p>
        <div class="focus-tags">
          <span class="focus-tag">{prepared_count} timeline items</span>
          <span class="focus-tag">{attention_count} awaiting review</span>
          <span class="focus-tag">Human approval required</span>
        </div>
      </section>
      <aside class="activity-card">
        <div class="activity-head"><div>Agent activity <span class="info-dot" title="Shows what the latest mailbox scan inspected, consolidated and left for review.">?</span></div><span class="state-pill">{agent_state_label}</span></div>
        <div class="activity-stat"><b>{scanned_count}</b><span>messages inspected in the latest run</span></div>
        <div class="activity-stat"><b>{prepared_count}</b><span>course items consolidated for review</span></div>
        <div class="activity-stat"><b>{attention_count}</b><span>items waiting for your decision</span></div>
        <div class="safety-lock">🔒 0 unauthorized calendar writes</div>
      </aside>
    </div>
    <div class="quick-strip">
      <div class="quick-card"><div><span>Next deadline</span><b>{next_deadline_title}</b></div><div class="quick-value">{next_deadline_value}</div></div>
      <div class="quick-card"><div><span>Course scope</span><b>{scope_display}</b></div><div class="quick-value">{len([c for c in st.session_state['course_scope'].split(',') if c.strip()])}</div></div>
      <div class="quick-card"><div><span>Review queue <span class="info-dot" title="Items waiting for you to verify the source evidence before a calendar action.">?</span></span><b>Evidence required before action</b></div><div class="quick-value">{attention_count}</div></div>
    </div>
    """,
    unsafe_allow_html=True,
)

st.markdown(
    """
    <div class="help-fab">
      <details>
        <summary title="Open quick help" aria-label="Open quick help">?</summary>
        <div class="help-fab-panel">
          <b>How to use AI Scroll</b>
          <div class="help-fab-step"><span>1</span><div>Connect the demo or a read-only mailbox.</div></div>
          <div class="help-fab-step"><span>2</span><div>Run the agent to filter and merge course mail.</div></div>
          <div class="help-fab-step"><span>3</span><div>Review the task and its exact source evidence.</div></div>
          <div class="help-fab-step"><span>4</span><div>Approve only the correct calendar proposal.</div></div>
          <div class="help-fab-note">Nothing is written to a calendar until you explicitly approve it. Open “Help &amp; guide” in the sidebar for definitions.</div>
        </div>
      </details>
    </div>
    """,
    unsafe_allow_html=True,
)

with st.sidebar:
    st.markdown("## AI Scroll")
    st.caption("Evidence-backed academic planning")
    with st.popover("❔ Help & guide", use_container_width=True):
        st.markdown("#### Quick start")
        st.markdown(
            "1. **Connect** the demo or a read-only mailbox.\n"
            "2. **Run** the inbox agent.\n"
            "3. **Review** the extracted task and exact email evidence.\n"
            "4. **Approve** an eligible calendar proposal."
        )
        st.markdown("#### What the labels mean")
        st.markdown(
            "- **Timeline item:** one consolidated course task.\n"
            "- **Review queue:** proposals waiting for your decision.\n"
            "- **Unauthorized writes:** calendar changes made without approval; this must remain zero.\n"
            "- **Demo:** runs locally without an API key or mailbox access."
        )
        st.caption("Hover over any small ? for contextual help.")
    st.divider()
    st.markdown("### Workspace")
    mode = st.radio("Extraction mode", ["Demo", "Live model"], help="Demo requires no API key.")
    st.info("Calendar proposals remain local until you explicitly confirm them.")
    with st.expander("Urgency policy"):
        st.markdown("- **High:** within 72 hours\n- **Medium:** 4–7 days\n- **Low:** more than 7 days\n- **Clarification:** unsafe to infer")

agent_tab, single_tab, chain_tab, safety_tab, evaluation_tab, review_tab = st.tabs(
    [
        "Today / 今日",
        "Inbox / 邮件",
        "Timeline / 时间线",
        "Calendar review / 日历审核",
        "Evaluation / 评估",
        "Label review / 标签审核",
    ]
)

with agent_tab:
    st.markdown('<div class="eyebrow">Inbox automation</div>', unsafe_allow_html=True)
    st.subheader("Mailbox control center / 邮箱控制中心")
    st.caption("Connect once, then AI Scroll reads course mail automatically. / 只需连接一次，AI Scroll 就会自动读取课程邮件。")

    guide_agent_run = st.session_state.get("agent_run")
    guide_plan_results = st.session_state.get("last_plan_results", [])
    if guide_plan_results:
        guide_step = 5
    elif st.session_state.get("backward_plan"):
        guide_step = 4
    elif guide_agent_run is not None:
        guide_step = 3
    elif connected:
        guide_step = 2
    else:
        guide_step = 1
    guide_steps = [
        ("Connect mailbox", "连接邮箱", "Choose Demo, Gmail or Outlook.", "选择演示、Gmail 或 Outlook。"),
        ("Run inbox scan", "扫描邮箱", "Let the Agent find course tasks.", "让 Agent 查找课程任务。"),
        ("Review evidence", "检查证据", "Open Calendar review and inspect the DDL.", "打开日历审核并检查 DDL。"),
        ("Approve calendar plan", "确认日历计划", "Confirm only after checking every session.", "核对所有时段后再确认。"),
    ]
    guide_html = ""
    for number, (en_title, zh_title, en_copy, zh_copy) in enumerate(guide_steps, start=1):
        state = "done" if number < guide_step else "active" if number == guide_step else ""
        icon = "✓" if number < guide_step else str(number)
        guide_html += (
            f'<div class="guided-step {state}"><i>{icon}</i>'
            f'<b>{en_title}<br>{zh_title}</b>'
            f'<span>{en_copy}<br>{zh_copy}</span></div>'
        )
    completed_steps = min(4, guide_step - 1)
    st.markdown(
        '<div class="guided-shell"><div class="guided-head"><div>'
        '<b>Quick start · Follow these four steps / 快速开始 · 按照以下四步操作</b>'
        '<span>The highlighted card is your next action. / 高亮卡片就是你现在要做的操作。</span>'
        f'</div><div class="guided-progress">{completed_steps}/4 completed · 已完成</div></div>'
        f'<div class="guided-steps">{guide_html}</div></div>',
        unsafe_allow_html=True,
    )
    if guide_step == 2:
        st.info("Next: select **Run inbox scan / 扫描邮箱** below. / 下一步：点击下方的 **Run inbox scan / 扫描邮箱**。")
    elif guide_step == 3:
        st.info("Next: open **Calendar review / 日历审核**, check the evidence and generate the backward plan. / 下一步：打开 **Calendar review / 日历审核**，检查证据并生成倒推计划。")
    elif guide_step > 4:
        st.success("Guided workflow completed. / 引导流程已经完成。")

    real_mailbox_connected = gmail_authorized or outlook_authorized
    if not connected:
        st.markdown(
            '<div class="connect-guide">'
            '<div class="connect-guide-head"><div><b>Connect your first real mailbox</b>'
            '<span>For a personal Outlook address, the whole setup happens through Microsoft sign-in. AI Scroll only requests permission to read mail.</span>'
            '</div><span class="connect-badge">About 1 minute</span></div>'
            '<div class="connect-steps">'
            '<div class="connect-step"><i>1</i><b>Choose Outlook</b><span>Open the guided setup below.</span></div>'
            '<div class="connect-step"><i>2</i><b>Sign in to Microsoft</b><span>Use the Outlook account you want to test.</span></div>'
            '<div class="connect-step"><i>3</i><b>Allow Mail.Read</b><span>Read only; no send or delete permission.</span></div>'
            '<div class="connect-step"><i>4</i><b>Run the agent</b><span>Return here and start one inbox scan.</span></div>'
            '</div></div>',
            unsafe_allow_html=True,
        )
        start_outlook_col, demo_help_col = st.columns([1.3, 1])
        if start_outlook_col.button("Connect an Outlook account", type="primary", use_container_width=True):
            st.session_state["show_mailbox_setup"] = True
            st.rerun()
        if demo_help_col.button("Keep using the demo", type="secondary", use_container_width=True):
            st.session_state["demo_mailbox_connected"] = True
            st.session_state["mailbox_provider"] = "demo"
            st.rerun()
    elif outlook_authorized and active_provider != "outlook":
        st.success("Outlook authorization is ready. Select Outlook below to use it for the next scan.")

    connector_name = (
        "Gmail · read only" if active_provider == "gmail" and gmail_authorized
        else "Outlook · read only" if active_provider == "outlook" and outlook_authorized
        else "Local demo mailbox"
    )
    course_scope = st.session_state["course_scope"]
    scan_policy_label = html.escape(course_scope or "All detected course codes")
    st.markdown(
        '<div class="agent-grid">'
        f'<div class="agent-card"><span>Mailbox</span><b>{"Connected" if connected else "Not connected"}</b><small>{connector_name if connected else "Choose a connector to begin"}</small></div>'
        f'<div class="agent-card"><span>Course scope</span><b>{scan_policy_label}</b><small>Messages outside this scope stay out of the extraction pipeline.</small></div>'
        '<div class="agent-card"><span>Safety policy</span><b>Human approval</b><small>The agent can prepare proposals but cannot write to a calendar by itself.</small></div>'
        '</div>',
        unsafe_allow_html=True,
    )
    with st.expander("Agent scan policy"):
        st.text_input(
            "Course codes",
            key="course_scope",
            placeholder="PE6201, HR6102",
            help="Comma-separated. Leave blank to process every detected course code.",
        )
        st.caption("Only the subject, sender and matched course codes are shown in the decision log; ignored message bodies are not displayed.")
    st.markdown("#### 1 · Choose the mailbox source / 选择邮箱来源")
    st.caption("Only authorized mailboxes can be selected. Use the connection guide if Outlook or Gmail is not ready yet.")
    connect_col, gmail_col, outlook_col = st.columns(3)
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
    if outlook_col.button(
        "Using Outlook" if connected and active_provider == "outlook" else "Use Outlook" if outlook_authorized else "Outlook · connect below",
        type="secondary",
        use_container_width=True,
        disabled=not outlook_authorized or (connected and active_provider == "outlook"),
        help="Outlook access is read only.",
    ):
        st.session_state["mailbox_provider"] = "outlook"
        st.session_state["agent_run"] = None
        st.rerun()
    st.markdown("#### 2 · Scan the inbox / 扫描邮箱")
    run_col, real_col = st.columns([2, 1])
    if run_col.button("Run inbox scan / 扫描邮箱", type="primary", use_container_width=True, disabled=not connected):
        try:
            st.session_state.pop("backward_plan", None)
            st.session_state.pop("last_plan_results", None)
            st.session_state.pop("last_calendar_result", None)
            connector = (
                GmailMailboxConnector() if active_provider == "gmail"
                else OutlookMailboxConnector() if active_provider == "outlook"
                else DemoMailboxConnector()
            )
            allowed_courses = {
                course.strip().upper()
                for course in st.session_state["course_scope"].split(",")
                if course.strip()
            }
            st.session_state["agent_run"] = InboxAgent(
                connector, allowed_courses=allowed_courses
            ).run(
                now=datetime.now().astimezone()
            )
            st.rerun()
        except Exception as exc:
            st.error(f"Mailbox run failed: {exc}")
    if real_col.button("Connection guide / 连接说明", type="secondary", use_container_width=True):
        st.session_state["show_mailbox_setup"] = not st.session_state.get("show_mailbox_setup", False)

    if st.session_state.get("show_mailbox_setup"):
        st.markdown("### Connect a mailbox")
        st.caption("Choose your provider. Personal Outlook is the quickest option on this computer.")
        outlook_setup, gmail_setup = st.tabs(["Outlook · recommended", "Gmail"])
        with outlook_setup:
            device_flow = {}
            if outlook_device_flow_path().is_file():
                try:
                    device_flow = json.loads(outlook_device_flow_path().read_text(encoding="utf-8"))
                except (OSError, json.JSONDecodeError):
                    device_flow = {}
            st.markdown(
                '<div class="setup-status"><span>Connection status</span>'
                f'<b>{"✓ Outlook is authorized" if outlook_authorized else "Outlook is not connected yet"}</b></div>',
                unsafe_allow_html=True,
            )
            st.markdown(
                "1. Select **Sign in with Microsoft** below.\n"
                "2. In the Microsoft window, enter the Outlook email you want to test.\n"
                "3. Accept the **Mail.Read** permission. This does not allow sending or deleting mail.\n"
                "4. Come back here and select **I finished sign-in — check connection**.\n"
                "5. Select **Use Outlook**, then **Run inbox scan**."
            )
            outlook_action, outlook_refresh = st.columns(2)
            if outlook_action.button(
                "Sign in with Microsoft",
                type="primary",
                use_container_width=True,
                disabled=outlook_authorized,
            ):
                outlook_device_flow_path().unlink(missing_ok=True)
                creation_flags = getattr(subprocess, "CREATE_NO_WINDOW", 0)
                subprocess.Popen(
                    [sys.executable, str(ROOT / "scripts" / "authorize_outlook_powershell.py")],
                    cwd=str(ROOT),
                    creationflags=creation_flags,
                )
                st.info("Authorization is starting. Select “Check / show login code” after a moment.")
            if outlook_refresh.button("Check / show login code", use_container_width=True):
                st.rerun()
            if device_flow.get("status") == "waiting":
                st.markdown("#### Microsoft device sign-in")
                st.code(device_flow.get("user_code", ""), language=None)
                st.link_button(
                    "Open Microsoft device login",
                    device_flow.get("verification_uri", "https://microsoft.com/devicelogin"),
                    type="primary",
                    use_container_width=True,
                )
                st.caption("Enter the code shown above on the Microsoft page, then return and check the connection again.")
            elif device_flow.get("status") == "error":
                st.error(device_flow.get("message", "Microsoft authorization failed."))
            elif device_flow.get("status") == "authorized":
                st.success("Microsoft authorization completed. Select Use Outlook above.")
            st.caption("Requested permission: Microsoft Graph Mail.Read (read only). Credentials stay in Microsoft's local sign-in cache.")
            with st.expander("Advanced: school or company Microsoft 365"):
                st.markdown(
                    "Use this route only when your organization permits app registration. Add a desktop/public client, "
                    "enable public client flows and grant delegated `Mail.Read`. Many university tenants block this, "
                    "so a personal Outlook account is recommended for the project demo."
                )
                st.link_button(
                    "Open Microsoft app registrations",
                    "https://entra.microsoft.com/#view/Microsoft_AAD_RegisteredApps/ApplicationsListBlade",
                    use_container_width=True,
                )
                configured_client = microsoft_client_id()
                entered_client = st.text_input(
                    "Application (client) ID",
                    value=configured_client,
                    placeholder="xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx",
                )
                entered_tenant = st.text_input(
                    "Directory (tenant) ID",
                    value=microsoft_tenant_id(),
                )
                if st.button("Save Microsoft app settings", use_container_width=True, disabled=not entered_client.strip()):
                    save_microsoft_config(entered_client, entered_tenant)
                    st.success(f"Saved locally to {microsoft_config_path()}")
                    st.rerun()
        with gmail_setup:
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
                if st.button("Refresh Gmail status", use_container_width=True):
                    st.rerun()
                st.caption(f"Token location: {gmail_token_path()}")
    agent_run = st.session_state.get("agent_run")
    if agent_run is None:
        st.markdown(
            f'<div class="agent-run"><b>{"Ready to scan" if connected else "Mailbox connection required"}</b><br><span>{"Select Run inbox scan. You will not paste any individual email." if connected else "Open the connection guide above and complete Microsoft or Google sign-in first."}</span></div>',
            unsafe_allow_html=True,
        )
    else:
        st.success(f"Agent completed a mailbox run through {agent_run.connector}.")
        metric_cols = st.columns(4)
        metric_cols[0].metric("Messages scanned", agent_run.scanned)
        metric_cols[1].metric("Academic mail", agent_run.academic)
        metric_cols[2].metric("Noise ignored", agent_run.ignored)
        metric_cols[3].metric("Needs review", agent_run.review_required)
        st.caption(f"Completed in {agent_run.duration_ms} ms · No ignored message body was sent to extraction.")
        with st.expander("View Agent tool trace / 查看 Agent 工具轨迹", expanded=True):
            st.caption("A reviewable ReAct-style trace showing tool decisions and results. / 可检查的 ReAct 风格轨迹，展示工具选择和执行结果。")
            for step in agent_run.trace:
                st.markdown(
                    f"**{step.phase} · `{step.tool}`**  \n{step.result}"
                )
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
        st.markdown("#### Mailbox decision log")
        st.caption("Audit metadata only. Ignored message bodies remain outside the extraction pipeline.")
        st.dataframe(
            [
                {
                    "Decision": decision.decision.title(),
                    "Course": ", ".join(decision.course_codes) or "—",
                    "Subject": decision.subject,
                    "Sender": decision.sender,
                    "Reason": decision.reason,
                }
                for decision in agent_run.decisions
            ],
            hide_index=True,
            use_container_width=True,
        )

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
    st.subheader("Review before any calendar action / 写入日历前先审核")
    st.caption("Choose a case, inspect the evidence, then confirm. / 选择案例、检查证据，然后再确认。")

    st.markdown("#### Calendar connection / 日历连接")
    calendar_source_left, calendar_source_right = st.columns(2)
    if calendar_source_left.button(
        "Using simulated calendar" if st.session_state["calendar_provider"] == "demo" else "Use simulated calendar",
        use_container_width=True,
        disabled=st.session_state["calendar_provider"] == "demo",
    ):
        st.session_state["calendar_provider"] = "demo"
        st.rerun()
    if calendar_source_right.button(
        "Using Google Calendar" if st.session_state["calendar_provider"] == "google" else "Use Google Calendar" if calendar_authorized else "Google Calendar · connect below",
        use_container_width=True,
        disabled=not calendar_authorized or st.session_state["calendar_provider"] == "google",
    ):
        st.session_state["calendar_provider"] = "google"
        st.rerun()
    with st.expander("Connect Google Calendar / 连接 Google 日历", expanded=not calendar_authorized):
        st.markdown(
            "1. In Google Cloud, enable **Google Calendar API**.\n"
            "2. Create an **OAuth client ID → Desktop app** and download the JSON.\n"
            "3. Save it at the private path shown below.\n"
            "4. Select **Authorize Google Calendar**, sign in, and allow calendar event access.\n"
            "5. Return here and select **Refresh connection**."
        )
        st.code(str(client_secrets_path()), language=None)
        calendar_setup_left, calendar_setup_right = st.columns(2)
        with calendar_setup_left:
            st.link_button(
                "Open Google Cloud credentials",
                "https://console.cloud.google.com/apis/credentials",
                use_container_width=True,
            )
            if st.button(
                "Authorize Google Calendar",
                type="primary",
                use_container_width=True,
                disabled=not client_secrets_path().is_file() or calendar_authorized,
            ):
                creation_flags = getattr(subprocess, "CREATE_NO_WINDOW", 0)
                subprocess.Popen(
                    [sys.executable, str(ROOT / "scripts" / "authorize_google_calendar.py")],
                    cwd=str(ROOT),
                    creationflags=creation_flags,
                )
                st.info("Google authorization opened. Finish consent, then refresh the connection.")
        with calendar_setup_right:
            st.markdown(
                '<div class="setup-status"><span>Connection status</span>'
                f'<b>{"✓ Google Calendar is connected" if calendar_authorized else "Google Calendar is not connected"}</b></div>',
                unsafe_allow_html=True,
            )
            if st.button("Refresh Google Calendar connection", use_container_width=True):
                st.rerun()
            st.caption(f"Private token: {google_calendar_token_path()}")
        st.caption("AI Scroll requests calendar event access only. An event is written only after the approval button below is selected.")

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
    using_google_calendar = st.session_state["calendar_provider"] == "google" and calendar_authorized
    store = GoogleCalendarStore() if using_google_calendar else InMemoryCalendarStore(st.session_state["calendar_events"])
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
        st.info(
            "The next button is the explicit approval step. It will write this reviewed event to your Google Calendar."
            if using_google_calendar
            else "The next button is the explicit approval step. The current target is the simulated calendar."
        )
        if st.button(
            "Confirm and add to Google Calendar" if using_google_calendar else "Confirm reviewed event and add to simulated calendar",
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
            st.caption(
                "The approved event was written through the Google Calendar API."
                if last_result.get("external_write")
                else "This run used the local simulated calendar. No external calendar was changed."
            )

        st.markdown("---")
        st.markdown('<div class="section-label">Smart backward plan · 智能倒推计划</div>', unsafe_allow_html=True)
        st.subheader("Turn the DDL into workable study sessions / 根据 DDL 安排学习时段")
        st.caption(
            "AI Scroll estimates the work, keeps a submission buffer and avoids calendar conflicts. "
            "/ AI Scroll 会估算工作量、保留提交缓冲时间并避开已有日历冲突。"
        )
        effort_col, buffer_col = st.columns(2)
        estimated_hours = effort_col.number_input(
            "Estimated work hours / 预计工作时数",
            min_value=1.0,
            max_value=40.0,
            value=float(suggested_effort_hours(safety_item)),
            step=0.5,
            help="You remain in control of the estimate. The default comes from the task type.",
        )
        buffer_hours = buffer_col.number_input(
            "Finish before DDL by / 提前完成时间",
            min_value=0.0,
            max_value=72.0,
            value=4.0,
            step=1.0,
            help="Reserved time for upload problems and final checks.",
        )
        plan_key = (
            safety_item.thread_id,
            safety_item.deadline_iso,
            float(estimated_hours),
            float(buffer_hours),
            "google" if using_google_calendar else "demo",
        )
        regenerate_plan = st.button("Generate or refresh backward plan / 生成或刷新倒推计划", use_container_width=True)
        cached_plan = st.session_state.get("backward_plan")
        if regenerate_plan:
            try:
                planning_now = datetime.now().astimezone().replace(second=0, microsecond=0)
                deadline_for_busy = datetime.fromisoformat(safety_item.deadline_iso)
                busy_windows = store.list_busy(planning_now, deadline_for_busy)
                planned = build_backward_plan(
                    safety_item,
                    now=planning_now,
                    estimated_hours=float(estimated_hours),
                    buffer_hours=float(buffer_hours),
                    busy=busy_windows,
                )
                st.session_state["backward_plan"] = {"key": plan_key, "value": planned}
                cached_plan = st.session_state["backward_plan"]
            except (PlanningError, RuntimeError) as exc:
                st.session_state.pop("backward_plan", None)
                cached_plan = None
                st.warning(f"Backward plan needs adjustment: {exc}")
        elif cached_plan and cached_plan.get("key") != plan_key:
            cached_plan = None

        if cached_plan is None:
            st.info(
                "Step 3: check the DDL evidence above, adjust the work estimate, then select "
                "**Generate or refresh backward plan**. / 第 3 步：检查上方 DDL 证据，调整工作量，然后点击"
                "**生成或刷新倒推计划**。"
            )

        if cached_plan and cached_plan.get("key") == plan_key:
            plan = cached_plan["value"]
            st.success(
                f"Prepared {len(plan.milestones)} work sessions before the "
                f"{plan.buffer_hours:g}-hour submission buffer. Nothing has been written yet. "
                f"/ 已生成 {len(plan.milestones)} 个学习时段，并预留 {plan.buffer_hours:g} 小时提交缓冲；目前尚未写入日历。"
            )
            for index, milestone in enumerate(plan.milestones, start=1):
                st.markdown(
                    '<div class="result-card">'
                    f'<span class="badge badge-blue">Step {index}</span>'
                    f'<div class="result-title">{html.escape(milestone.title)}</div>'
                    f'<div class="result-meta">{milestone.start.strftime("%d %b, %H:%M")}–{milestone.end.strftime("%H:%M")} · '
                    f'{html.escape(milestone.purpose)}</div></div>',
                    unsafe_allow_html=True,
                )
            plan_proposals = [milestone_proposal(safety_item, value) for value in plan.milestones]
            st.info(
                "The next button approves the displayed sessions; the DDL reminder is separate. "
                "/ 下一按钮用于确认这些学习时段；DDL 提醒需要单独确认。"
            )
            if st.button(
                "Confirm and add study plan to Google Calendar / 确认并写入 Google 日历"
                if using_google_calendar else "Confirm study plan and add to simulated calendar / 确认并写入模拟日历",
                type="primary",
                use_container_width=True,
            ):
                plan_results = [gate.commit(value, user_confirmed=True) for value in plan_proposals]
                st.session_state["last_plan_results"] = [value.model_dump() for value in plan_results]
            last_plan_results = st.session_state.get("last_plan_results", [])
            if last_plan_results and {
                value["proposal_id"] for value in last_plan_results
            } == {value.proposal_id for value in plan_proposals}:
                committed_count = sum(value["status"] == "committed" for value in last_plan_results)
                duplicate_count = sum(value["status"] == "deduplicated" for value in last_plan_results)
                st.success(
                    f"Study plan saved: {committed_count} new session(s), "
                    f"{duplicate_count} duplicate(s) prevented. "
                    f"/ 学习计划已保存：新增 {committed_count} 个时段，阻止 {duplicate_count} 个重复项目。"
                )
                st.caption(
                    "These sessions were written through the Google Calendar API."
                    if any(value.get("external_write") for value in last_plan_results)
                    else "These sessions are in the simulated calendar; no external calendar was changed."
                )
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
