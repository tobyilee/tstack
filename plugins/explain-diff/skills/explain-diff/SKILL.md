---
name: explain-diff
description: Turn a raw code diff, commit, branch, or pull request into a personalized learning document — a single self-contained HTML "textbook" that explains the background first, gives the core intuition in plain words, adds interactive diagrams only where they reveal cause-and-effect, then walks through the code as a literate diff ordered by logical steps instead of file order, and ends with a short recall quiz that checks real understanding. Use this skill whenever the user wants to understand, learn from, study, onboard onto, or "explain" a diff, PR, commit, patch, or change set — e.g. "explain this PR to me", "help me understand what changed in this branch", "turn this diff into something I can read", "I need to review this but don't know the rendering code", "make a study doc from commit abc123", "이 PR 설명해줘", "이 변경 이해하게 도와줘" — even if they don't say "explain-diff". Prefer it over a plain code review whenever the goal is understanding rather than finding bugs.
---

# Explain Diff

Turn a diff into a document a person can *learn* from — something they could print and read in a café, not a wall of red and green lines.

A normal code review starts at the changed lines. That works only when the reader already knows the system. This skill reverses the order:

1. **Context before change** — what must I know to understand this change?
2. **Intuition before detail** — what is the one idea behind it?
3. **Interaction only where it teaches** — let the reader move a variable and see the effect, when prose cannot do that.
4. **Code as a narrative** — show the hunks in the order of the reasoning, not the order of the file system.
5. **Recall before review** — end with a short quiz, because reading a clear explanation *feels* like understanding even when it isn't.

The running example in this file: a Zen-garden drawing game whose view changed from top-down to isometric.

## Workflow

### Step 1 — Get the whole change, and the code around it

Accept any of: a pasted diff, a patch file, `git diff <range>`, a commit SHA (`git show`), a branch (`git diff main...HEAD`), or a PR (`gh pr diff <n>` and `gh pr view <n>` for the title and description).

Then read beyond the hunks. A hunk only shows what changed; to explain *why*, you need the code it touches: the full functions, the callers, the types, the config, the engine or framework it runs on. Read the PR description and commit messages too — they often state the motive. If you can only see the diff (no repo), say so in the document and infer carefully; mark guesses as guesses.

### Step 2 — Analyze before writing

Write these down for yourself first (a scratch note is fine). The document is built from them.

- **The one-sentence intuition.** The core idea in plain words, without identifiers. Zen garden: *"Make the garden feel three-dimensional using only 2D drawing tricks."* If you cannot write this sentence, you do not understand the change yet — read more code.
- **Prerequisite concepts.** What must a reader know to follow the change? Engine or framework, coordinate systems, data flow, the subsystem's old behavior, domain terms. Zen garden: the engine's canvas API, grid vs. screen coordinates, the old render loop, draw order / painter's algorithm.
- **The "before" picture.** How did the system work before this change? A reader cannot appreciate a change without the baseline.
- **Logical steps.** Group the hunks into 2–6 steps that follow the reasoning of the change. Zen garden: (1) add a projection function grid→screen, (2) change tile drawing to diamonds, (3) sort objects by depth so near stones cover far ones, (4) invert the projection for mouse picking. Each step should depend only on earlier steps.
- **Hunk coverage map.** Assign every hunk to a step. Mechanical hunks (renames, imports, formatting, generated files) go to a short "Other changes" list at the end. Nothing may silently disappear — a reader who later opens the real diff should find nothing you didn't mention.
- **Cause-and-effect candidates.** Which relationships are hard to grasp from text? (See Step 5.)
- **Edge-case pass.** For each function whose behavior changed, feed it a few boundary inputs in your head (or in a quick script) and trace old vs. new: null/missing values, empty strings, zero and negative numbers, large values, alternative formats the input may legally take (e.g. an HTTP header that may be a number *or* a date), and fields the new code adds but old data may lack. Also check every place a new value is produced and consumed: is it used everywhere it should be (a new `z` that changes draw order but not draw position), and do copies of the same constant stay in sync? A reader who understands a change should also know where it can break — and this pass is where most of the real insight comes from. Results feed section 6, and an old-vs-new table often feeds section 3.
- **Quiz candidates.** As you analyze, note the points where a reader could nod along without really getting it: why the steps come in this order, what breaks if one step is removed, what the new code does with an input the document never showed. These become section 7.

### Step 3 — Calibrate to the reader

The background section is the personalized part. Its depth depends on what this reader already knows.

1. Check what you already know: the user's prompt ("I know React but not WebGL"), their memory/CLAUDE.md, their role, the conversation so far. If that settles it, do not ask.
2. Otherwise ask **one short round** of 1–3 questions, naming the actual prerequisite concepts from Step 2 — e.g. "How familiar are you with: (a) isometric projection, (b) painter's algorithm / draw order, (c) this engine's render loop?" with options like *new to me / roughly / know it well*. Use AskUserQuestion when available. Never ask more than one round; the reader came to read, not to fill in forms.
3. If you cannot ask (non-interactive run), assume a capable engineer who is new to *this* subsystem, and say that assumption at the top of the document.

Apply the answer: concepts the reader knows well get one line ("You know isometric projection; here it's the 2:1 variant"). Concepts that are new get a real explanation with a small example. Put the deeper background inside `<details>` blocks so an expert can skip them and a beginner can open them.

### Step 4 — Write the document

Use the HTML skeleton in `assets/template.html` (copy it, then fill it in). It already has the diff styling, light/dark themes, print styles, section layout, and the quiz script — don't rewrite those.

Write in the language of the user's prompt (Korean prompt → Korean document). Keep code, identifiers, and file paths as they are. In Korean documents, write "review" as **리뷰** (코드 리뷰, 리뷰 메모, "리뷰를 요청한다"), not 검토 — it is the word developers actually use, and 검토 reads as a vaguer "look over".

The document has these sections, in this order:

**0. Header** — title (what the change does, in reader terms, not the PR title verbatim), source (PR/commit/branch), size (files, +/−), and the reader assumption from Step 3.

**1. Background: what you need to know first** — the prerequisite concepts and the "before" picture. Explain how the old system worked, how the relevant subsystem fits in, and any foundational concept. Prefer small concrete examples and simple static diagrams (inline SVG) over abstract definitions. End with a sentence that sets up the problem the change solves.

**2. The idea in one picture** — the one-sentence intuition, then a short paragraph (3–6 sentences) that expands it in plain words, like a good math teacher giving the meaning before the formula. Often a single before/after diagram belongs here. After this section the reader should be able to predict roughly what the code will do.

**3. Explore it (only if it earns its place)** — interactive widgets. See Step 5. If no widget passes the test, omit this section entirely; do not leave an empty heading.

**4. The change, step by step** — the literate diff. For each logical step:
   - A heading that names the step as an action ("Step 2 — Draw tiles as diamonds").
   - **Why this step**: 1–3 sentences linking it to the intuition and to the previous step.
   - **For each file in the step**: one line on the file's role in the system *before* showing its code ("`renderer.ts` owns the per-frame draw loop"). Then the relevant hunk(s), rendered as a diff block. Trim long hunks to the meaningful lines and note what you trimmed (`… 12 unchanged lines …`).
   - Short notes after the code that point at the important lines — what to look at, not a line-by-line paraphrase.
   - **Bridge**: one sentence on what this step makes possible or what problem it leaves for the next step ("Tiles now land in the right place, but a far stone can still paint over a near one — that's step 3.").

**5. Other changes** — the mechanical hunks from the coverage map, one line each.

**6. Review notes** — 3–8 bullets from the edge-case pass: concrete failure scenarios ("the new cache key omits `locale` → a German user can receive the page cached for an English user"), behavior changes that look like a pure refactor but aren't, missing tests, and questions for the author. Give each one an input and a consequence, and mark confirmed vs. guessed. Skip only if the pass genuinely found nothing.

**7. Check your understanding** — a recall quiz. People confuse the familiarity of well-written sentences with understanding; a reader can finish this document, feel fine, and then fail a colleague's basic question. The quiz exposes those gaps while the document is still open, and sends the reader back to the right section. It is a speed governor, not an exam: it holds the workflow to the pace of human understanding, and a sensible rule for the reader is *"I don't ask for review of this change until I pass."* Say that purpose in one line above the questions.

   - **About 5 questions** (3 is enough for a tiny diff), **medium difficulty**: answerable by someone who understood the document, not by someone who skimmed it, and not requiring anything the document didn't teach.
   - **Test structure and principle, not memory of details.** Good: "Why must the depth sort come after the projection step?", "A stone at grid (3, 1) and one at (1, 3) — which is drawn first, and why?", "If `screenToGrid` were left unchanged, what would the player notice?", "Which of these inputs behaves differently after this change?". Bad: "What is the value of `TILE_W`?", "Which file contains `depthKey`?" — those are answered by Ctrl-F, and knowing them proves nothing.
   - Spread the questions over the document: the "before" picture, the core intuition, at least one step-to-step dependency, and at least one edge case from the review notes. Prefer questions that make the reader *predict* or *apply* (a new input, a removed step) over ones that restate a sentence from the text.
   - Format: multiple choice, 3–4 options, exactly one correct. Wrong options are the plausible misreadings — what someone who half-understood would pick — never jokes or obvious filler. Vary which position holds the right answer.
   - Each question carries a short explanation (why the right answer is right, and what the tempting wrong one gets wrong) and a link to the section to re-read. Use the quiz markup in the template; its script hides explanations until the reader answers, counts first-try answers, offers a retry, and builds the printed answer key. Don't write your own quiz JS.

### Step 5 — Interactive widgets: the gate

Interactive elements are valuable only when they let the reader *explore a causal relationship* that static text or a picture cannot show well. A decorative slider is AI-generated ornament, and it costs the reader attention.

Before adding a widget, it must pass all three checks:

1. **Causal**: the reader changes an input that the code actually uses, and sees an output that the code actually computes.
2. **Hard to see statically**: the relationship is continuous, multi-variable, spatial, or temporal — a static figure would need many frames or a table to show it.
3. **Faithful**: the widget runs the *same logic as the diff* (port the real formula or algorithm into the page's JS, with the real constants), not an approximation that merely looks similar. Label which function it mirrors.

Zen garden passes: drag a stone and watch, live, its grid coordinates, its projected screen coordinates, its depth key, and the resulting draw order. Show before vs. after projection side by side if that helps.

Small diffs can still earn a small widget: when a change alters behavior on some inputs (a new null guard, a `.trim()`, a changed default), an **old-vs-new runner** — pick a sample input, see the old and new code's output side by side, differences highlighted — teaches faster than prose, because the reader discovers which inputs changed. It passes the gate when it runs both versions of the real code. A pure rename or move with no behavior change gets no widget.

Read `references/widgets.md` for widget patterns and implementation rules before writing one.

### Step 6 — Check and deliver

Before handing over, verify:

- Every hunk from the coverage map appears in section 4 or 5.
- Every code excerpt matches the real diff (copy it; do not retype from memory).
- Each widget passes the gate and works without network access (no external scripts except optionally one pinned CDN library; vanilla JS is preferred). The two font stylesheet `<link>`s in the template are the only other external requests; keep them, and keep the design tokens in `:root` as they are — they match the user's house style (Pretendard + JetBrains Mono, paper/ink/accent palette). Widgets and SVGs take colors from these tokens, never hard-coded hex.
- The page prints sensibly: widgets show their static fallback, `<details>` content is readable.
- The intuition sentence appears before any code.
- The quiz is there, every question can be answered from the document alone, no answer is a detail to memorize, and each question's `data-answer` matches the option you explain as correct.

Save the file in the current working directory as `explain-diff-<short-slug>.html` (or where the user asked), and give the user the path. Offer in one line to publish it as a shareable page if the environment supports that.

## Writing guidance

- Lead every section with the point, then the support.
- One term per concept. If the code says `worldPos` and you call it "grid coordinates", say once that they are the same thing, then stay consistent.
- Explain the *why* behind each decision you can infer — trade-offs, alternatives the author didn't choose — because that is what turns a diff into learning.
- Prefer concrete numbers: "tile (2, 1) lands at screen (32, 48)" teaches more than "tiles are offset".
- Keep the whole document readable in one sitting. If the diff is huge (dozens of files), focus sections 1–4 on the core change and list peripheral areas briefly; say what you left out.
