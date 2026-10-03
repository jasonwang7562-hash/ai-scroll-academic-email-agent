import fs from "node:fs/promises";
import path from "node:path";
import { pathToFileURL } from "node:url";
import { execFile } from "node:child_process";
import { promisify } from "node:util";
import { Presentation, PresentationFile } from "@oai/artifact-tool";

const projectRoot = path.resolve(process.cwd());
const workspaceDir = "C:/Users/admin/Documents/Codex/2026-09-17/pe6201-group-project-continuation";
const SKILL_DIR = "C:/Users/admin/.codex/plugins/cache/openai-primary-runtime/presentations/26.909.12148/skills/presentations";
const RUNTIME_PYTHON = "C:/Users/admin/.cache/codex-runtimes/codex-primary-runtime/dependencies/python/python.exe";
const buildDir = path.join(workspaceDir, ".pptx-build");
const stagingDir = path.join(workspaceDir, ".pptx-finalizer");
const FINAL_PPTX = path.join(workspaceDir, "deliverables", "AI_Scroll_5_Minute_Presentation_v4.pptx");
await fs.mkdir(buildDir, { recursive: true });

const { resolvePresentationFont, applyPresentationChartFont, finalizePresentation } = await import(
  pathToFileURL(path.join(SKILL_DIR, "container_tools/artifact_tool_utils.mjs")).href
);
const family = resolvePresentationFont();
const deck = Presentation.create({ slideSize: { width: 1280, height: 720 } });

const C = {
  navy: "#092642", deep: "#061B31", teal: "#109B92", mint: "#DDF6F1",
  blue: "#4A90E2", coral: "#FF7468", ink: "#132B45", muted: "#66788D",
  pale: "#F3F7FA", line: "#DCE6EE", white: "#FFFFFF", green: "#1C8C6B",
};

const coverBytes = new Uint8Array(await fs.readFile(path.join(projectRoot, "06_demo", "assets", "ai_scroll_cover.png")));
const uiBytes = new Uint8Array(await fs.readFile(path.join(projectRoot, "06_demo", "ui_final_wide.png")));

function shape(slide, geometry, x, y, w, h, fill, line = "none", radius = undefined) {
  return slide.shapes.add({
    geometry,
    position: { left: x, top: y, width: w, height: h },
    fill,
    line: line === "none" ? { fill: "none", width: 0 } : { style: "solid", fill: line, width: 1 },
    ...(radius ? { borderRadius: radius } : {}),
  });
}

function text(slide, value, x, y, w, h, opts = {}) {
  const box = slide.shapes.add({
    geometry: "textbox",
    position: { left: x, top: y, width: w, height: h },
    fill: "none",
    line: { fill: "none", width: 0 },
  });
  box.text = value;
  box.text.style = {
    typeface: family,
    fontSize: opts.size ?? 22,
    bold: opts.bold ?? false,
    color: opts.color ?? C.ink,
    alignment: opts.align ?? "left",
    verticalAlignment: opts.valign ?? "top",
    autoFit: opts.autoFit ?? "shrinkText",
    lineSpacing: opts.lineSpacing ?? 1.05,
    insets: opts.insets ?? { left: 0, right: 0, top: 0, bottom: 0 },
  };
  return box;
}

function title(slide, value, number, dark = false) {
  text(slide, String(number).padStart(2, "0"), 62, 43, 55, 25, { size: 13, bold: true, color: dark ? "#8FDCD1" : C.teal });
  text(slide, value, 62, 76, 1080, 65, { size: 39, bold: true, color: dark ? C.white : C.ink });
  shape(slide, "rect", 62, 145, 68, 5, dark ? "#52D8C7" : C.teal);
}

function footer(slide, number, dark = false) {
  text(slide, "PE6201 Course Project · AI Scroll", 62, 684, 420, 20, { size: 11, color: dark ? "#AFC5D5" : "#8493A4" });
  text(slide, String(number), 1185, 684, 30, 20, { size: 11, bold: true, color: dark ? "#AFC5D5" : "#8493A4", align: "right" });
}

function addNote(slide, note) {
  slide.speakerNotes.textFrame.setText(note);
}

// 1. Cover
{
  const slide = deck.slides.add();
  slide.images.add({ blob: coverBytes, contentType: "image/png", alt: "Email evidence flowing into a reviewed calendar plan", fit: "cover", position: { left: 0, top: 0, width: 1280, height: 720 } });
  shape(slide, "rect", 0, 0, 610, 720, C.deep);
  text(slide, "AI Scroll", 70, 120, 470, 90, { size: 59, bold: true, color: C.white });
  text(slide, "An academic email agent that turns course messages into a verified plan", 74, 225, 440, 120, { size: 25, color: "#DDEBF4", lineSpacing: 1.15 });
  shape(slide, "rect", 74, 374, 72, 5, "#45D6C6");
  text(slide, "Jason Wang Chen Yu\nPE6201 Course Project", 74, 405, 340, 80, { size: 17, bold: true, color: "#BFD4E2", lineSpacing: 1.2 });
  text(slide, "Evidence first · Human approval before calendar writes", 74, 620, 470, 28, { size: 13, color: "#8FDCD1" });
  addNote(slide, `Hi, I’m Jason. My project is called AI Scroll. It is an academic email agent for students who receive deadlines, extensions and course updates across many messages. The system reads selected course emails, keeps the original evidence, merges related updates and prepares a practical study plan. It can then create calendar proposals, but only after the student reviews and approves them. In this presentation, I will explain the problem, the Agent design, the tools I built, and the current working result.`);
}

// 2. Problem
{
  const slide = deck.slides.add();
  slide.background.fill = C.pale;
  title(slide, "The problem: important actions are buried in email", 2);
  const rows = [
    ["01", "Deadlines arrive in different formats", "A date may appear in the subject, body, attachment or a later correction."],
    ["02", "One task can span several messages", "Students must decide whether a message creates, updates or cancels the same task."],
    ["03", "Manual calendar entry creates risk", "A wrong date or an automatic write can turn a useful assistant into a costly mistake."],
  ];
  rows.forEach((r, i) => {
    const y = 196 + i * 132;
    text(slide, r[0], 70, y, 66, 42, { size: 24, bold: true, color: C.teal });
    text(slide, r[1], 150, y - 2, 500, 35, { size: 22, bold: true });
    text(slide, r[2], 150, y + 39, 510, 55, { size: 16, color: C.muted, lineSpacing: 1.18 });
    shape(slide, "line", 150, y + 105, 500, 1, "none", C.line);
  });
  shape(slide, "roundRect", 745, 185, 450, 390, C.navy, "none", 22);
  text(slide, "A typical student inbox", 790, 220, 330, 32, { size: 20, bold: true, color: C.white });
  const mails = [
    ["Deadline", "Project due 1 Oct", "#FFEEE9"],
    ["Update", "Deadline extended to 4 Oct", "#DFF6F1"],
    ["Reminder", "Please submit on time", "#EAF2FC"],
    ["Noise", "Campus newsletter", "#F1F4F7"],
  ];
  mails.forEach((m, i) => {
    const y = 278 + i * 64;
    shape(slide, "roundRect", 790, y, 350, 49, m[2], "none", 11);
    text(slide, m[0], 806, y + 10, 78, 23, { size: 13, bold: true, color: C.ink });
    text(slide, m[1], 886, y + 10, 238, 23, { size: 13, color: C.ink });
  });
  text(slide, "The user needs one reliable final state", 790, 535, 350, 24, { size: 15, bold: true, color: "#8FDCD1" });
  footer(slide, 2);
  addNote(slide, `The main problem is not a lack of email. It is the effort required to turn several messages into one reliable decision. A deadline can appear in different formats, and a later message may extend or cancel it. Students also receive reminders, newsletters and platform notifications that look important but do not create a real deadline. If the user manually copies every date, errors are easy. If an Agent writes to a calendar automatically, the risk is even higher. So the product must understand the message chain and preserve evidence before it takes any external action.`);
}

// 3. Product flow
{
  const slide = deck.slides.add();
  slide.background.fill = C.white;
  title(slide, "Product flow from inbox to approved plan", 3);
  const labels = [
    ["1", "Read", "Mailbox connector"], ["2", "Filter", "Course scope"],
    ["3", "Extract", "Task and evidence"], ["4", "Merge", "Latest final state"],
    ["5", "Plan", "Backward schedule"], ["6", "Approve", "Calendar gate"],
  ];
  const nodes = [];
  labels.forEach((d, i) => {
    const x = 55 + i * 201;
    const node = shape(slide, "roundRect", x, 235, 160, 178, i === 5 ? C.navy : i >= 4 ? C.mint : "#F5F8FB", i === 5 ? C.navy : C.line, 18);
    nodes.push(node);
    shape(slide, "ellipse", x + 53, 255, 54, 54, i === 5 ? "#45D6C6" : C.teal);
    text(slide, d[0], x + 53, 266, 54, 28, { size: 18, bold: true, color: C.white, align: "center", valign: "middle" });
    text(slide, d[1], x + 18, 328, 124, 30, { size: 20, bold: true, color: i === 5 ? C.white : C.ink, align: "center" });
    text(slide, d[2], x + 16, 368, 128, 38, { size: 13, color: i === 5 ? "#BFD4E2" : C.muted, align: "center" });
  });
  for (let i = 0; i < nodes.length - 1; i++) {
    text(slide, "›", 217 + i * 201, 348, 36, 45, { size: 34, bold: true, color: "#70CFC4", align: "center", valign: "middle" });
  }
  text(slide, "The Agent prepares the decision. The student owns the final action.", 210, 485, 860, 44, { size: 25, bold: true, color: C.navy, align: "center" });
  text(slide, "Every proposal links back to an exact sentence from the source email.", 250, 545, 780, 30, { size: 17, color: C.muted, align: "center" });
  footer(slide, 3);
  addNote(slide, `AI Scroll follows six steps. First, a mailbox connector reads new messages. Second, a course scope filter removes unrelated mail before any model call. Third, the extraction layer identifies the task, deadline and exact evidence sentence. Fourth, the merge engine combines related emails and keeps the latest valid state. Fifth, the planner works backwards from the verified deadline to create manageable sessions. Finally, the approval gate shows the proposal to the student. The Agent prepares the plan, but the student owns the final calendar action. This separation is important for both safety and trust.`);
}

// 4. Agent and tools
{
  const slide = deck.slides.add();
  slide.background.fill = C.navy;
  title(slide, "The Agent loop and its tools", 4, true);
  const observe = shape(slide, "ellipse", 130, 210, 190, 190, "#123E5C", "#4DD8C7");
  const reason = shape(slide, "ellipse", 380, 210, 190, 190, "#174C68", "#4DD8C7");
  const act = shape(slide, "ellipse", 630, 210, 190, 190, "#146B70", "#4DD8C7");
  text(slide, "OBSERVE", 155, 264, 140, 28, { size: 18, bold: true, color: "#8FDCD1", align: "center" });
  text(slide, "Read inbox\nand current state", 155, 305, 140, 52, { size: 17, color: C.white, align: "center" });
  text(slide, "REASON", 405, 264, 140, 28, { size: 18, bold: true, color: "#8FDCD1", align: "center" });
  text(slide, "Choose tools\nand resolve updates", 405, 305, 140, 52, { size: 17, color: C.white, align: "center" });
  text(slide, "ACT", 655, 264, 140, 28, { size: 18, bold: true, color: "#8FDCD1", align: "center" });
  text(slide, "Prepare plan\nand stop for review", 655, 305, 140, 52, { size: 17, color: C.white, align: "center" });
  text(slide, "›", 330, 278, 40, 60, { size: 38, bold: true, color: "#4DD8C7", align: "center", valign: "middle" });
  text(slide, "›", 580, 278, 40, 60, { size: 38, bold: true, color: "#4DD8C7", align: "center", valign: "middle" });
  shape(slide, "roundRect", 900, 190, 305, 330, "#F7FBFD", "none", 20);
  text(slide, "Five working tools", 934, 222, 235, 32, { size: 21, bold: true });
  const tools = [
    ["mailbox.fetch_new", "Read new messages"], ["scan_policy.classify", "Filter course mail"],
    ["extract", "Create structured JSON"], ["thread_matcher + merge", "Consolidate updates"],
    ["calendar.approval_gate", "Block unapproved writes"],
  ];
  tools.forEach((d, i) => {
    const y = 278 + i * 47;
    shape(slide, "ellipse", 935, y + 2, 19, 19, i === 4 ? C.coral : C.teal);
    text(slide, String(i + 1), 935, y + 3, 19, 15, { size: 9, bold: true, color: C.white, align: "center" });
    text(slide, d[0], 967, y, 202, 18, { size: 12, bold: true, color: C.ink });
    text(slide, d[1], 967, y + 18, 202, 19, { size: 11, color: C.muted });
  });
  text(slide, "LLM: openai/gpt-5-mini through OpenRouter", 125, 520, 700, 28, { size: 17, bold: true, color: C.white });
  text(slide, "Deterministic rules still control date validation, urgency, deduplication and approval.", 125, 558, 720, 42, { size: 15, color: "#BFD4E2" });
  footer(slide, 4, true);
  addNote(slide, `The system uses a simple ReAct style loop: observe, reason and act. The Agent observes new messages and the existing timeline. It reasons about which tools are needed and whether a message is new, related or irrelevant. It then acts by preparing a timeline item or a calendar proposal, before stopping for review. The main tools read the mailbox, filter course messages, extract structured JSON, match and merge related threads, and enforce the calendar approval gate. I use GPT 5 Mini through OpenRouter for language understanding. Deterministic rules still validate dates, calculate urgency, remove duplicates and block unsafe writes.`);
}

// 5. Architecture
{
  const slide = deck.slides.add();
  slide.background.fill = C.pale;
  title(slide, "Hybrid architecture: AI for language, rules for control", 5);
  shape(slide, "roundRect", 65, 190, 535, 355, "#EAF3FC", "#C9DDF2", 22);
  shape(slide, "roundRect", 680, 190, 535, 355, "#E8F7F3", "#C5E6DE", 22);
  text(slide, "Language model", 105, 226, 440, 35, { size: 27, bold: true, color: "#245B8F" });
  text(slide, "Rented capability", 105, 268, 180, 24, { size: 14, bold: true, color: "#4F82B0" });
  text(slide, "Understands varied academic wording\nExtracts tasks and exact evidence\nSuggests whether a message updates an earlier task", 105, 322, 430, 140, { size: 19, color: C.ink, lineSpacing: 1.3 });
  text(slide, "Deterministic application", 720, 226, 440, 35, { size: 27, bold: true, color: C.green });
  text(slide, "Built for this project", 720, 268, 200, 24, { size: 14, bold: true, color: "#3E8D75" });
  text(slide, "Validates dates and Singapore time\nMerges threads and preserves history\nCalculates urgency and enforces approval", 720, 322, 430, 140, { size: 19, color: C.ink, lineSpacing: 1.3 });
  text(slide, "Build", 120, 585, 75, 25, { size: 16, bold: true, color: C.teal });
  text(slide, "workflow · merge logic · evaluation · safety", 198, 585, 440, 25, { size: 16, color: C.ink });
  text(slide, "Rent", 700, 585, 75, 25, { size: 16, bold: true, color: C.blue });
  text(slide, "language model · mailbox API · calendar API", 776, 585, 400, 25, { size: 16, color: C.ink });
  footer(slide, 5);
  addNote(slide, `I chose a hybrid architecture because the two parts of the problem need different strengths. The language model handles varied academic language, extracts evidence and interprets whether a message is a new task or an update. The application code handles the parts that must remain predictable: date validation, Singapore time, urgency thresholds, thread history, deduplication and approval. I built the workflow, merge logic, evaluation and safety controls. I rent the language model and the external mailbox and calendar APIs. This reduces development time while keeping the important project logic visible and testable.`);
}

// 6. Product experience
{
  const slide = deck.slides.add();
  slide.background.fill = C.white;
  title(slide, "Final product experience", 6);
  slide.images.add({ blob: uiBytes, contentType: "image/png", alt: "AI Scroll inbox with generated action plan", fit: "contain", position: { left: 55, top: 165, width: 1170, height: 493 }, geometry: "roundRect", borderRadius: "rounded-2xl" });
  shape(slide, "roundRect", 75, 175, 275, 45, C.navy, "none", 12);
  text(slide, "1 · Read the source email", 92, 187, 240, 20, { size: 14, bold: true, color: C.white });
  shape(slide, "roundRect", 930, 175, 270, 45, C.teal, "none", 12);
  text(slide, "2 · Review the action card", 945, 187, 240, 20, { size: 14, bold: true, color: C.white });
  footer(slide, 6);
  addNote(slide, `This is the current product experience. The left side behaves like an academic inbox. The middle panel keeps the selected email visible, including the exact sentence that created or changed the deadline. The right panel turns the message into a five step action plan. It shows the final deadline, the planned stages and the evidence used by the Agent. The scan button refreshes the interface using the actual mailbox pipeline. Settings stay in a collapsed sidebar, so the main screen remains simple. The user then opens Calendar Review, checks the proposal and confirms it. Without that confirmation, the system performs no calendar write.`);
}

// 7. Results and close
{
  const slide = deck.slides.add();
  slide.background.fill = C.pale;
  title(slide, "Current evidence and next steps", 7);
  const chart = slide.charts.add("bar", {
    position: { left: 55, top: 180, width: 760, height: 410 },
    categories: ["Task type", "Exact deadline", "Urgency", "Calendar action", "Cross-email merge"],
    series: [
      { name: "Keyword baseline", values: [56, 74.4, 82, 56, 0], fill: "#B7C4D1" },
      { name: "Current pipeline", values: [86, 93, 96, 90, 100], fill: C.teal },
    ],
    barOptions: { direction: "bar", grouping: "clustered", gapWidth: 48 },
    hasLegend: true,
    legend: { position: "bottom", overlay: false, textStyle: { typeface: family, fontSize: 12, fill: C.muted } },
    xAxis: { visible: true, min: 0, max: 100, majorUnit: 20, numberFormatCode: "0\"%\"", textStyle: { typeface: family, fontSize: 11, fill: C.muted }, majorGridlines: { style: "solid", fill: "#DCE6EE", width: 1 } },
    yAxis: { visible: true, textStyle: { typeface: family, fontSize: 12, fill: C.ink }, majorGridlines: null },
    dataLabels: { showValue: true, position: "outEnd", textStyle: { typeface: family, fontSize: 11, bold: true, fill: C.ink } },
    chartFill: "#FFFFFF",
    chartLine: { fill: "#DCE6EE", width: 1 },
    plotAreaFill: "#FFFFFF",
  });
  applyPresentationChartFont(chart, { fontFamily: family });
  const metrics = [
    ["6 / 6", "Live web-derived cases passed"],
    ["47", "Automated tests passed"],
    ["$0.01074", "Cost of the six-case live run"],
  ];
  metrics.forEach((m, i) => {
    const y = 190 + i * 118;
    shape(slide, "roundRect", 855, y, 340, 94, i === 2 ? C.navy : C.white, i === 2 ? C.navy : C.line, 16);
    text(slide, m[0], 882, y + 14, 150, 35, { size: 28, bold: true, color: i === 2 ? "#55D8C8" : C.teal });
    text(slide, m[1], 882, y + 54, 280, 24, { size: 13, color: i === 2 ? "#D5E7EF" : C.muted });
  });
  text(slide, "Next: freeze the 50 human labels, run the final evaluation and record the live demo.", 855, 560, 340, 58, { size: 17, bold: true, color: C.ink, lineSpacing: 1.18 });
  text(slide, "Draft-label comparison shown on the left. Final assessment numbers require label review.", 60, 620, 760, 24, { size: 12, color: C.muted });
  footer(slide, 7);
  addNote(slide, `The current evidence shows that the pipeline improves on a simple keyword and date baseline, especially for calendar actions and cross email merging. These comparison numbers still use draft labels, so I will not present them as the final assessment result until the 50 labels are reviewed and frozen. The completed live model check passed all six web derived edge cases, the code passes 47 automated tests, and the six case live run cost about 1.1 cents. The next steps are to freeze the labels, run the final evaluation and record the live demo. AI Scroll shows how an Agent can reduce email overload while keeping the student in control.`);
}

await fs.mkdir(stagingDir, { recursive: true });
await fs.mkdir(path.dirname(FINAL_PPTX), { recursive: true });
const candidatePath = path.join(stagingDir, "AI_Scroll_candidate.pptx");
await (await PresentationFile.exportPptx(deck)).save(candidatePath);
await promisify(execFile)(RUNTIME_PYTHON, [
  path.join(projectRoot, "06_demo", "add_ppt_transitions.py"),
  candidatePath,
]);

const result = await finalizePresentation({
  workspaceDir,
  candidatePath,
  finalPath: FINAL_PPTX,
  pythonExecutable: RUNTIME_PYTHON,
  integrityValidatorPath: path.join(SKILL_DIR, "container_tools", "inspect_presentation_package_integrity.py"),
  layoutValidatorPath: path.join(SKILL_DIR, "container_tools", "inspect_presentation_layout_geometry.py"),
  layoutArgs: ["--expected-slide-size-emu", "12192000,6858000", "--validate-heading-fit"],
  explicitTotalSlideCount: 7,
  requiredNativeTableOwnerSlides: [],
  requiredNativeChartOwnerSlides: [7],
  materializeLiteralChartWorkbooks: true,
  fontPolicy: { basis: "design", families: [family] },
  verifyArtifactToolImport: true,
  receiptPath: path.join(stagingDir, "AI_Scroll_5_Minute_Presentation_v4.validation.json"),
});

console.log(JSON.stringify({ finalPath: FINAL_PPTX, font: family, result }, null, 2));
