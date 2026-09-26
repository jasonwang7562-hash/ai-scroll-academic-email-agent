from __future__ import annotations

import csv
import json
from collections import Counter
from datetime import datetime
from pathlib import Path


ROOT = Path(__file__).resolve().parent
REFERENCE = datetime.fromisoformat("2026-09-26T12:00:00+08:00")


def urgency(deadline, text, clarification, no_action=False):
    if clarification:
        return "clarification"
    if no_action or deadline is None:
        return "low"
    if any(word in text.lower() for word in ("mandatory", "urgent")):
        return "high"
    hours = (datetime.fromisoformat(deadline) - REFERENCE).total_seconds() / 3600
    return "high" if hours <= 72 else "medium" if hours <= 168 else "low"


emails, labels, thread_gold = [], [], []


def add(email_id, thread_id, sent_at, subject, evidence, split, course, task_type,
        title, deadline, relation="new", action="create", clarification=None):
    body = f"Dear student,\n\n{evidence}\n\nRegards,\nCourse Team"
    if evidence not in body:
        raise ValueError(email_id)
    emails.append({
        "email_id": email_id, "thread_id": thread_id, "sent_at": sent_at,
        "subject": subject, "sender": "course-team@example.edu", "body": body,
        "split": split, "source_type": "synthetic",
    })
    labels.append({
        "email_id": email_id, "thread_id": thread_id, "course_gold": course,
        "task_type_gold": task_type, "task_title_gold": title,
        "deadline_gold": deadline,
        "timezone_gold": "Asia/Singapore" if deadline else None,
        "urgency_gold": urgency(deadline, body, clarification is not None, action == "do_not_create"),
        "urgency_reason": clarification or "Fixed policy applied at the evaluation reference time.",
        "evidence_gold": evidence, "relation_gold": relation,
        "calendar_action_gold": "ask_clarification" if clarification else action,
        "needs_clarification_gold": clarification is not None,
        "clarification_reason_gold": clarification, "split": split,
        "review_status": "pending_human_review", "reviewer_notes": "",
    })


# id, subject, evidence, course, type, title, deadline, action, clarification
singles = [
    ("s01","PE6201 Individual Project deadline","The PE6201 Individual Project must be submitted by 4 October 2026 at 11:59 PM SGT.","PE6201","assignment","Submit Individual Project","2026-10-04T23:59:00+08:00","create",None),
    ("s02","PE6202 automation reflection","Please upload the PE6202 automation reflection by 28 September 2026 at 6:00 PM SGT.","PE6202","assignment","Upload automation reflection","2026-09-28T18:00:00+08:00","create",None),
    ("s03","BC6501 quiz schedule","The BC6501 online quiz will open on 1 October 2026 at 10:00 AM SGT.","BC6501","exam","Attend online quiz","2026-10-01T10:00:00+08:00","create",None),
    ("s04","HR6102 case report","Submit the HR6102 case report by 10 October 2026 at 5:00 PM SGT.","HR6102","assignment","Submit case report","2026-10-10T17:00:00+08:00","create",None),
    ("s05","MG6003 presentation","Your MG6003 presentation begins on 27 September 2026 at 9:00 AM SGT.","MG6003","assignment","Deliver presentation","2026-09-27T09:00:00+08:00","create",None),
    ("s06","PE6201 consultation","The PE6201 project consultation is on 2 October 2026 at 3:00 PM SGT.","PE6201","other","Attend project consultation","2026-10-02T15:00:00+08:00","create",None),
    ("s07","AC6101 case upload","Upload the AC6101 case response by 29 September 2026 at 12:00 PM SGT.","AC6101","assignment","Upload case response","2026-09-29T12:00:00+08:00","create",None),
    ("s08","MK6204 research survey","Complete the MK6204 research survey by 5 October 2026 at 5:00 PM SGT.","MK6204","administrative","Complete research survey","2026-10-05T17:00:00+08:00","create",None),
    ("s09","CS6103 laboratory submission","The CS6103 laboratory file is due on 30 September 2026 at 11:59 PM SGT.","CS6103","assignment","Submit laboratory file","2026-09-30T23:59:00+08:00","create",None),
    ("s10","ES6001 reading response","Post the ES6001 reading response by 3 October 2026 at 9:00 AM SGT.","ES6001","assignment","Post reading response","2026-10-03T09:00:00+08:00","create",None),
    ("s11","PE6201 weekly resources","The PE6201 weekly resources are now available in NTU Learn.","PE6201","other","No action required",None,"do_not_create",None),
    ("s12","PE6202 draft discussion","Please bring your PE6202 draft next Friday for discussion.","PE6202","assignment","Bring project draft",None,"ask_clarification","The phrase 'next Friday' has no fixed reference date or time."),
    ("s13","BC6501 team meeting","The BC6501 team meeting is on 6 October 2026 at 2:00 PM.","BC6501","other","Attend team meeting",None,"ask_clarification","The time zone is missing."),
    ("s14","HR6102 registration form","Registration for the HR6102 workshop closes on 27 September 2026 at 11:59 PM SGT.","HR6102","administrative","Submit workshop registration","2026-09-27T23:59:00+08:00","create",None),
    ("s15","MG6003 final presentation","The MG6003 final presentation is scheduled for 12 October 2026 at 2:00 PM SGT.","MG6003","assignment","Deliver final presentation","2026-10-12T14:00:00+08:00","create",None),
    ("s16","AC6101 mid-term examination","The AC6101 mid-term examination starts on 6 October 2026 at 9:00 AM SGT.","AC6101","exam","Attend mid-term examination","2026-10-06T09:00:00+08:00","create",None),
    ("s17","MK6204 ethics form","Submit the MK6204 ethics form by 28 September 2026 at 12:00 PM SGT.","MK6204","administrative","Submit ethics form","2026-09-28T12:00:00+08:00","create",None),
    ("s18","CS6103 replacement class","The CS6103 replacement class will be held on 29 September 2026 at 7:00 PM SGT.","CS6103","class_change","Attend replacement class","2026-09-29T19:00:00+08:00","create",None),
    ("s19","ES6001 seminar cancellation","The ES6001 seminar scheduled for this week has been cancelled.","ES6001","class_change","Cancel seminar",None,"do_not_create",None),
    ("s20","PE6201 optional reading","The attached PE6201 article is optional background reading and has no submission requirement.","PE6201","other","No action required",None,"do_not_create",None),
    ("s21","PE6202 mandatory training","Mandatory PE6202 safety training must be completed by 3 October 2026 at 6:00 PM SGT.","PE6202","administrative","Complete safety training","2026-10-03T18:00:00+08:00","create",None),
    ("s22","BC6501 evening quiz","The BC6501 evening quiz starts today, 26 September 2026, at 8:00 PM SGT.","BC6501","exam","Attend evening quiz","2026-09-26T20:00:00+08:00","create",None),
    ("s23","HR6102 literature review","Upload the HR6102 literature review by 7 October 2026 at 5:00 PM SGT.","HR6102","assignment","Upload literature review","2026-10-07T17:00:00+08:00","create",None),
    ("s24","MG6003 peer comments","Please send your MG6003 peer comments by the end of tomorrow.","MG6003","assignment","Send peer comments",None,"ask_clarification","The relative deadline has no explicit date, time, or time zone."),
    ("s25","AC6101 individual assignment","The AC6101 individual assignment is due on 2 October 2026 at 11:59 PM SGT.","AC6101","assignment","Submit individual assignment","2026-10-02T23:59:00+08:00","create",None),
    ("s26","MK6204 in-class test","The MK6204 in-class test begins on 30 September 2026 at 8:00 AM SGT.","MK6204","exam","Attend in-class test","2026-09-30T08:00:00+08:00","create",None),
    ("s27","CS6103 student declaration","Submit the CS6103 student declaration by 15 October 2026 at 5:00 PM SGT.","CS6103","administrative","Submit student declaration","2026-10-15T17:00:00+08:00","create",None),
    ("s28","ES6001 group meeting","The ES6001 group meeting is confirmed for 1 October 2026 at 8:00 PM SGT.","ES6001","other","Attend group meeting","2026-10-01T20:00:00+08:00","create",None),
    ("s29","PE6201 networking session","The optional PE6201 networking session takes place on 8 October 2026 at 6:00 PM SGT.","PE6201","other","Attend optional networking session","2026-10-08T18:00:00+08:00","create",None),
    ("s30","PE6202 corrected report date","The final PE6202 report deadline is 5 October 2026 at 11:59 PM SGT; the previously mentioned 4 October date no longer applies.","PE6202","assignment","Submit final report","2026-10-05T23:59:00+08:00","create",None),
]

for i, spec in enumerate(singles, 1):
    split = "development" if i <= 14 else "test" if i <= 24 else "synthetic_holdout"
    add(spec[0], f"t_{spec[0]}", f"2026-09-{20 + ((i-1) % 6):02d}T09:00:00+08:00",
        spec[1], spec[2], split, spec[3], spec[4], spec[5], spec[6], action=spec[7], clarification=spec[8])


def chain(thread_id, split, course, task_type, title, items, final_deadline, final_status, final_action):
    source_ids = []
    for order, item in enumerate(items, 1):
        eid = f"{thread_id}_e{order}"
        source_ids.append(eid)
        add(eid, thread_id, item[0], item[1], item[2], split, course, task_type, title,
            item[3], relation=item[4] if len(item) > 4 else "new",
            action=item[5] if len(item) > 5 else "create")
    thread_gold.append({
        "thread_id": thread_id, "course_gold": course, "task_type_gold": task_type,
        "task_title_gold": title, "final_deadline_gold": final_deadline,
        "final_status_gold": final_status, "final_calendar_action_gold": final_action,
        "source_email_ids": source_ids, "split": split,
        "review_status": "pending_human_review", "reviewer_notes": "",
    })


chain("c01","development","PE6201","assignment","Submit project analysis",[
    ("2026-09-22T10:00:00+08:00","PE6201 project deadline","The PE6201 project analysis is due on 1 October 2026 at 11:59 PM SGT.","2026-10-01T23:59:00+08:00"),
    ("2026-09-25T10:00:00+08:00","PE6201 project deadline extended","The PE6201 project analysis deadline has been extended to 4 October 2026 at 11:59 PM SGT.","2026-10-04T23:59:00+08:00","update","update")],"2026-10-04T23:59:00+08:00","active","update")
chain("c02","development","PE6202","class_change","Attend automation workshop",[
    ("2026-09-23T08:00:00+08:00","PE6202 workshop venue","The PE6202 workshop is on 2 October 2026 at 10:00 AM SGT in Room A1.","2026-10-02T10:00:00+08:00"),
    ("2026-09-25T08:00:00+08:00","PE6202 workshop room change","The PE6202 workshop remains on 2 October 2026 at 10:00 AM SGT but has moved to Room B2.","2026-10-02T10:00:00+08:00","update","update")],"2026-10-02T10:00:00+08:00","active","update")
chain("c03","development","BC6501","assignment","Submit case analysis",[
    ("2026-09-22T12:00:00+08:00","BC6501 case analysis","Submit the BC6501 case analysis by email on 3 October 2026 at 5:00 PM SGT.","2026-10-03T17:00:00+08:00"),
    ("2026-09-25T12:00:00+08:00","BC6501 submission method updated","Submit the BC6501 case analysis through NTU Learn by 3 October 2026 at 5:00 PM SGT instead of email.","2026-10-03T17:00:00+08:00","update","update")],"2026-10-03T17:00:00+08:00","active","update")
chain("c04","test","HR6102","class_change","Attend research workshop",[
    ("2026-09-22T14:00:00+08:00","HR6102 research workshop","The HR6102 research workshop is scheduled for 4 October 2026 at 10:00 AM SGT.","2026-10-04T10:00:00+08:00"),
    ("2026-09-25T14:00:00+08:00","HR6102 workshop cancelled","The HR6102 research workshop on 4 October 2026 has been cancelled.",None,"cancel","do_not_create")],None,"cancelled","do_not_create")
chain("c05","test","MG6003","other","Attend project briefing",[
    ("2026-09-21T09:00:00+08:00","MG6003 project briefing","The MG6003 project briefing is on 6 October 2026 at 10:00 AM SGT.","2026-10-06T10:00:00+08:00"),
    ("2026-09-24T09:00:00+08:00","MG6003 briefing time corrected","The MG6003 project briefing on 6 October 2026 will begin at 2:00 PM SGT, not 10:00 AM.","2026-10-06T14:00:00+08:00","update","update"),
    ("2026-09-26T09:00:00+08:00","MG6003 briefing reminder","Reminder: the MG6003 project briefing is on 6 October 2026 at 2:00 PM SGT.","2026-10-06T14:00:00+08:00","update","update")],"2026-10-06T14:00:00+08:00","active","update")
chain("c06","test","AC6101","assignment","Submit group project",[
    ("2026-09-20T11:00:00+08:00","AC6101 group project","Submit the AC6101 group project by 7 October 2026 at 11:59 PM SGT.","2026-10-07T23:59:00+08:00"),
    ("2026-09-23T11:00:00+08:00","AC6101 appendix requirement","The AC6101 group project must now include a one-page appendix; the deadline remains 7 October 2026 at 11:59 PM SGT.","2026-10-07T23:59:00+08:00","update","update"),
    ("2026-09-25T11:00:00+08:00","AC6101 project reminder","Reminder: the AC6101 group project and appendix are due on 7 October 2026 at 11:59 PM SGT.","2026-10-07T23:59:00+08:00","update","update")],"2026-10-07T23:59:00+08:00","active","update")
chain("c07","synthetic_holdout","MK6204","exam","Attend final examination",[
    ("2026-09-20T15:00:00+08:00","MK6204 final examination","The MK6204 final examination is on 8 October 2026 at 9:00 AM SGT in Hall A.","2026-10-08T09:00:00+08:00"),
    ("2026-09-23T15:00:00+08:00","MK6204 examination venue","The MK6204 final examination on 8 October 2026 at 9:00 AM SGT has moved to Hall B.","2026-10-08T09:00:00+08:00","update","update"),
    ("2026-09-25T15:00:00+08:00","MK6204 examination time","The MK6204 final examination in Hall B will start on 8 October 2026 at 10:00 AM SGT.","2026-10-08T10:00:00+08:00","update","update")],"2026-10-08T10:00:00+08:00","active","update")
chain("c08","synthetic_holdout","CS6103","administrative","Submit laboratory declaration",[
    ("2026-09-20T16:00:00+08:00","CS6103 laboratory declaration","Submit the CS6103 laboratory declaration by 9 October 2026 at 5:00 PM SGT.","2026-10-09T17:00:00+08:00"),
    ("2026-09-23T16:00:00+08:00","CS6103 declaration extension","The CS6103 laboratory declaration deadline has been extended to 12 October 2026 at 5:00 PM SGT.","2026-10-12T17:00:00+08:00","update","update"),
    ("2026-09-25T16:00:00+08:00","CS6103 declaration reminder","Reminder: submit the CS6103 laboratory declaration by 12 October 2026 at 5:00 PM SGT.","2026-10-12T17:00:00+08:00","update","update")],"2026-10-12T17:00:00+08:00","active","update")


def write_jsonl(name, rows):
    with (ROOT / name).open("w", encoding="utf-8", newline="\n") as handle:
        for row in rows:
            handle.write(json.dumps(row, ensure_ascii=False) + "\n")


write_jsonl("evaluation_emails.jsonl", emails)
write_jsonl("gold_labels_draft.jsonl", labels)
write_jsonl("thread_gold_draft.jsonl", thread_gold)
with (ROOT / "gold_label_review.csv").open("w", encoding="utf-8-sig", newline="") as handle:
    writer = csv.DictWriter(handle, fieldnames=list(labels[0]))
    writer.writeheader()
    writer.writerows(labels)

counts = Counter(row["thread_id"] for row in emails)
summary = {
    "dataset_version": "draft-v1",
    "generated_at": datetime.now().astimezone().isoformat(timespec="seconds"),
    "evaluation_reference_time": REFERENCE.isoformat(),
    "total_emails": len(emails), "total_threads": len(counts),
    "independent_email_threads": sum(n == 1 for n in counts.values()),
    "multi_email_threads": sum(n > 1 for n in counts.values()),
    "emails_in_multi_email_threads": sum(n for n in counts.values() if n > 1),
    "split_email_counts": dict(Counter(row["split"] for row in emails)),
    "clarification_cases": sum(row["needs_clarification_gold"] for row in labels),
    "no_deadline_emails": sum(row["deadline_gold"] is None for row in labels),
    "deadline_update_messages": sum(row["relation_gold"] == "update" and row["deadline_gold"] is not None for row in labels),
    "cancel_messages": sum(row["relation_gold"] == "cancel" for row in labels),
    "label_status": "pending_human_review",
}
(ROOT / "dataset_summary.json").write_text(json.dumps(summary, indent=2), encoding="utf-8")
print(json.dumps(summary, indent=2))

