from __future__ import annotations

from pathlib import Path

from docx import Document
from docx.enum.section import WD_SECTION
from docx.enum.table import WD_CELL_VERTICAL_ALIGNMENT, WD_TABLE_ALIGNMENT
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.oxml import OxmlElement
from docx.oxml.ns import qn
from docx.shared import Inches, Pt, RGBColor


ROOT = Path(__file__).resolve().parents[1]
OUTPUT = ROOT / "05_report" / "AI_Scroll_Trade_Off_Analysis_Draft.docx"


def set_cell_fill(cell, color: str) -> None:
    tc_pr = cell._tc.get_or_add_tcPr()
    shd = tc_pr.find(qn("w:shd"))
    if shd is None:
        shd = OxmlElement("w:shd")
        tc_pr.append(shd)
    shd.set(qn("w:fill"), color)


def set_cell_margins(cell, top=65, start=115, bottom=65, end=115) -> None:
    tc = cell._tc
    tc_pr = tc.get_or_add_tcPr()
    tc_mar = tc_pr.first_child_found_in("w:tcMar")
    if tc_mar is None:
        tc_mar = OxmlElement("w:tcMar")
        tc_pr.append(tc_mar)
    for margin, value in (("top", top), ("start", start), ("bottom", bottom), ("end", end)):
        node = tc_mar.find(qn(f"w:{margin}"))
        if node is None:
            node = OxmlElement(f"w:{margin}")
            tc_mar.append(node)
        node.set(qn("w:w"), str(value))
        node.set(qn("w:type"), "dxa")


def set_repeat_table_header(row) -> None:
    tr_pr = row._tr.get_or_add_trPr()
    tbl_header = OxmlElement("w:tblHeader")
    tbl_header.set(qn("w:val"), "true")
    tr_pr.append(tbl_header)


def add_table(document: Document, headers: list[str], rows: list[list[str]], widths: list[float]) -> None:
    table = document.add_table(rows=1, cols=len(headers))
    table.alignment = WD_TABLE_ALIGNMENT.CENTER
    table.style = "Table Grid"
    set_repeat_table_header(table.rows[0])
    for index, header in enumerate(headers):
        cell = table.rows[0].cells[index]
        cell.width = Inches(widths[index])
        set_cell_fill(cell, "1F5E4A")
        cell.vertical_alignment = WD_CELL_VERTICAL_ALIGNMENT.CENTER
        set_cell_margins(cell)
        paragraph = cell.paragraphs[0]
        paragraph.alignment = WD_ALIGN_PARAGRAPH.CENTER
        run = paragraph.add_run(header)
        run.bold = True
        run.font.color.rgb = RGBColor(255, 255, 255)
        run.font.size = Pt(8.7)
    for row_index, values in enumerate(rows):
        cells = table.add_row().cells
        for index, value in enumerate(values):
            cells[index].width = Inches(widths[index])
            cells[index].vertical_alignment = WD_CELL_VERTICAL_ALIGNMENT.CENTER
            set_cell_margins(cells[index])
            if row_index % 2:
                set_cell_fill(cells[index], "F2F7F5")
            paragraph = cells[index].paragraphs[0]
            paragraph.alignment = WD_ALIGN_PARAGRAPH.LEFT if index == 0 else WD_ALIGN_PARAGRAPH.CENTER
            run = paragraph.add_run(value)
            run.font.size = Pt(8.7)


def add_body(document: Document, text: str) -> None:
    paragraph = document.add_paragraph(text)
    paragraph.style = document.styles["Body Text"]


def build() -> None:
    doc = Document()
    section = doc.sections[0]
    section.page_width = Inches(8.5)
    section.page_height = Inches(11)
    section.top_margin = Inches(0.72)
    section.bottom_margin = Inches(0.72)
    section.left_margin = Inches(0.78)
    section.right_margin = Inches(0.78)

    styles = doc.styles
    normal = styles["Normal"]
    normal.font.name = "Aptos"
    normal.font.size = Pt(10.5)
    normal.font.color.rgb = RGBColor(0, 0, 0)
    normal.paragraph_format.space_after = Pt(6)
    normal.paragraph_format.line_spacing = 1.08
    body = styles["Body Text"]
    body.font.name = "Aptos"
    body.font.size = Pt(10.5)
    body.font.color.rgb = RGBColor(0, 0, 0)
    body.paragraph_format.space_after = Pt(7)
    body.paragraph_format.line_spacing = 1.12
    for style_name, size in (("Title", 22), ("Heading 1", 15), ("Heading 2", 12)):
        style = styles[style_name]
        style.font.name = "Aptos Display"
        style.font.size = Pt(size)
        style.font.color.rgb = RGBColor(0, 0, 0)
        style.font.bold = True
        style.paragraph_format.keep_with_next = True
        style.paragraph_format.space_before = Pt(12 if style_name != "Title" else 0)
        style.paragraph_format.space_after = Pt(5)
    title_style_pr = styles["Title"]._element.get_or_add_pPr()
    title_style_border = title_style_pr.find(qn("w:pBdr"))
    if title_style_border is not None:
        title_style_pr.remove(title_style_border)

    title = doc.add_paragraph(style="Title")
    title.add_run("AI Scroll Business and Technical Trade Off Analysis")
    title_pr = title._p.get_or_add_pPr()
    title_border = title_pr.find(qn("w:pBdr"))
    if title_border is not None:
        title_pr.remove(title_border)
    subtitle = doc.add_paragraph()
    subtitle.alignment = WD_ALIGN_PARAGRAPH.LEFT
    run = subtitle.add_run("PE6201 End of Course Project   |   Wang Chen Yu Jason   |   Draft 27 September 2026")
    run.bold = True
    run.font.size = Pt(10)
    run.font.color.rgb = RGBColor(56, 56, 56)
    status = doc.add_paragraph()
    status_run = status.add_run("Evidence status  ")
    status_run.bold = True
    status.add_run(
        "This draft uses the current deterministic development run. Final model metrics and measured cost will replace the provisional values after the 50 labels are reviewed and frozen."
    )

    doc.add_heading("Problem and decision", level=1)
    add_body(doc, (
        "University students receive deadlines, class changes, submission rules and administrative requests across many emails. "
        "The difficult cases are not single messages with the word deadline; they are chains in which a later email changes a date, room or requirement. "
        "The closest alternative is manual search followed by copying information into a calendar. That process is slow and can preserve an obsolete instruction. "
        "I am building AI Scroll to convert selected academic emails into one evidence-backed course timeline and a calendar proposal. "
        "The main design decision is to automate interpretation and preparation while keeping the final calendar write under explicit user control."
    ))

    doc.add_heading("System scope and hybrid architecture", level=1)
    add_body(doc, (
        "AI Scroll accepts manually selected or pre-filtered academic emails. It identifies the course and task, normalizes an explicit date and time zone, retrieves related messages, applies later corrections, and shows the exact source sentence. "
        "It then proposes create, update, clarification or no-action. The current prototype never writes to an external calendar. An in-memory adapter demonstrates the approval gate and deduplication path without changing a real account."
    ))
    add_body(doc, (
        "A hybrid architecture is more appropriate than either rules or a language model alone. A foundation model is useful for varied wording and implicit academic actions. Retrieval and thread matching are needed when evidence is spread across messages. "
        "Deterministic code is better for ISO date validation, fixed urgency thresholds, duplicate prevention and approval enforcement because these rules must be inspectable and repeatable. "
        "This separation also limits the effect of a malformed or overconfident model response: structured validation can reject it before any action is proposed."
    ))

    doc.add_heading("Build versus buy and operating design", level=1)
    add_body(doc, (
        "I build the workflow, structured schema, thread matcher, merge history, urgency policy, evaluation scripts and confirmation gate. I would rent the language-model API and use existing Gmail and Google Calendar APIs for infrastructure. "
        "Buying model capability reduces development time and avoids hosting large weights, but it introduces provider cost, latency and privacy exposure. The application therefore sends only selected academic content, stores minimal structured output, and keeps the model endpoint replaceable through configuration."
    ))
    add_body(doc, (
        "Scheduled processing creates a cost-versus-freshness trade-off. A naive job that calls a model every 15 minutes makes 2,880 monthly calls even when no new email exists; hourly polling makes 720. My design checks message identifiers and labels without a model, then calls the model only for new or changed emails. "
        "At an assumed 20 new academic emails per day, the model-call count remains 600 per 30-day month for both hourly and 15-minute inbox checks. The final report will multiply measured average input and output tokens by dated provider prices rather than use an unsupported estimate."
    ))

    doc.add_heading("Data and evaluation", level=1)
    add_body(doc, (
        "The reproducible development dataset contains 50 synthetic academic emails across 38 threads. Thirty are independent emails. Eight are genuine multi-email threads containing 20 emails. The set also contains 11 update messages, three clarification cases and one cancellation. "
        "Each email has draft gold labels for course, task type, title, deadline, urgency, evidence, relation and calendar action. A human review screen now requires every row to be approved before a checksum-protected frozen label file can be created."
    ))
    add_table(doc, ["Dataset unit", "Count"], [
        ["Emails", "50"], ["Threads", "38"], ["Independent emails", "30"],
        ["Multi-email threads", "8"], ["Emails in multi-email threads", "20"],
    ], [4.9, 1.2])
    add_body(doc, (
        "I compare the same cases with a keyword-and-date baseline and report each capability separately. Dates use a fixed reference time of 26 September 2026 at 12:00 SGT. Deadline accuracy uses only the 43 deadline-bearing cases, while false deadlines are counted on seven no-deadline cases. "
        "Cross-email merging uses only the eight genuine chains. Clarification precision and recall show whether safety comes from selective abstention or indiscriminate refusal. Calendar safety is tested separately and requires zero unauthorized writes."
    ))

    doc.add_heading("Development evidence", level=1)
    add_body(doc, (
        "The current deterministic pipeline is stronger than the simple baseline on the draft labels. It identifies 43 of 50 task types, 40 of 43 exact deadlines, 48 of 50 urgency labels, 45 of 50 calendar actions and the final state of all eight multi-email chains. "
        "The baseline reaches 28 of 50 task types, 32 of 43 deadlines, 41 of 50 urgency labels, 28 of 50 calendar actions and no multi-email merges. The current system also detects all three draft clarification cases. These results guide debugging; they are not the final claimed model performance because the labels remain pending human review and the data is synthetic."
    ))
    add_table(doc, ["Capability", "Baseline", "Current pipeline"], [
        ["Course identification", "50/50", "50/50"],
        ["Task type", "28/50", "43/50"],
        ["Exact deadline", "32/43", "40/43"],
        ["Urgency", "41/50", "48/50"],
        ["Calendar action", "28/50", "45/50"],
        ["Cross-email final state", "0/8", "8/8"],
    ], [3.4, 1.35, 1.55])

    doc.add_heading("Risks and implemented controls", level=1)
    add_body(doc, (
        "The highest-impact failure is a missed or incorrect deadline. AI Scroll keeps a verbatim evidence trail and asks for clarification when date, time or time zone is unsafe to infer. Later related messages retain field-level change history, and cancellations block calendar proposals. "
        "Duplicate proposals are deduplicated, expired items are rejected, and unconfirmed writes cannot reach the calendar adapter. The development safety test blocked the unconfirmed attempt, prevented the duplicate, blocked both unsafe cases and recorded zero unauthorized writes."
    ))
    add_body(doc, (
        "Privacy remains a deployment constraint because academic emails may contain personal information. The first version uses synthetic or manually selected text and avoids raw-inbox ingestion. A real deployment should request narrow OAuth scopes, filter metadata before model processing, encrypt stored structured data and define retention rules. "
        "Users should see the source and proposal before approval, because even a high measured extraction score cannot justify silent calendar changes."
    ))

    doc.add_heading("Limitations and next evidence", level=1)
    add_body(doc, (
        "The current evidence cannot prove real-world generalization. The dataset is synthetic, its holdout was produced by the same generator, and only eight threads test cross-email reasoning. The deterministic development pipeline is not the final language-model configuration. "
        "The next evaluation will freeze human-reviewed labels, run one exact model and prompt over all cases, preserve raw outputs and token logs, calculate dated cost per email and thread, and report the remaining errors without tuning on the test or holdout splits."
    ))

    footer = section.footer.paragraphs[0]
    footer.alignment = WD_ALIGN_PARAGRAPH.CENTER
    footer_run = footer.add_run("PE6201   AI Scroll   Business and Technical Trade Off Analysis")
    footer_run.font.size = Pt(8)
    footer_run.font.color.rgb = RGBColor(90, 90, 90)

    doc.core_properties.title = "AI Scroll Business and Technical Trade Off Analysis"
    doc.core_properties.author = "Wang Chen Yu Jason"
    doc.core_properties.subject = "PE6201 End of Course Project"
    OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    doc.save(OUTPUT)
    print(OUTPUT)


if __name__ == "__main__":
    build()
