# ConceptBridge-TRACE — bilingual digital engineering curriculum

## Product scope

Expand the existing authenticated learning app from one Half Adder lesson into a usable nine-lesson digital engineering curriculum. Preserve the existing ConceptBridge branding, paper/navy/teal palette, navigation structure, working Half Adder lesson and truth-table lab, private student accounts, and project planner. Do not provision or publish hosting as part of this content expansion.

The curriculum is grouped into **Fundamentals** (Logic Gates Fundamentals; Binary Number Systems; Boolean Algebra and Simplification), **Combinational Logic** (Half Adder; Full Adder; Multiplexers and Demultiplexers; Encoders and Decoders), and **Sequential Logic** (SR, JK, D and T Flip-Flops; Counters and Registers). Each lesson has a stable slug, ordered position, difficulty, prerequisites, objectives, English/Hindi/Hinglish explanations, worked examples, an appropriate diagram or interactive demonstration, a relevant truth table when applicable, a short topic-specific quiz with specific answer explanations, and stored completion state.

## Implementation architecture

- Keep FastAPI serving the current static frontend and APIs; keep SQLAlchemy, Alembic, session/CSRF protections, per-account ownership checks, and the current planner untouched except for backward-compatible route/schema extensions.
- Define a single Python lesson catalogue in `app/data/curriculum.py` with full, language-specific lesson records and quiz answer keys. Expose signed-in students only safe lesson copy and question prompts/options; never return answer keys before quiz submission.
- Add catalogue/detail and per-slug open/completion API operations. Retain `/api/lesson`, `/api/lesson/open`, and `/api/lesson/complete` for compatibility; the Learn UI uses the new catalogue routes and the original Half Adder Lab remains available.
- Add `lesson_slug` to quiz attempts with an additive Alembic migration and a backward-compatible default of `half-adder` for existing attempts. Score submissions against the selected lesson's own server-side question bank and persist score, total, slug, result explanations, activity, and revision concepts under the authenticated user.
- Build the Learn catalogue and dynamic lesson/quiz views using the existing component classes, language switch, question/progress components, and hash navigation. A single lesson detail renders real objectives, explanations, examples, an interactive demonstration or diagram, relevant truth table, quiz link, and completion button; no fake lesson statistics or generic duplicate filler.
- Dashboard and progress view consume account-owned catalogue completion rows and quiz attempts grouped by lesson. Display genuinely recorded values; unstarted lessons remain unstarted. Keep project endpoints and UI behavior unchanged.
- The current text collapse is caused by a legacy `.lesson-section` two-column 31px/1fr grid: new detail markup has no `.section-index`, so body paragraphs and truth-table wrappers auto-place into the 31px first track. Reset sections within `.lesson-main-card` to full-width block flow, add `min-width:0` at grid children, allow formula wrapping and table-contained horizontal scrolling, and keep the sidebar a smaller desktop column. At tablet/mobile widths stack it after the lesson content.
- Implement deterministic, reusable browser logic in `app/static/js/simulator-core.js` and use those exact functions from the UI. Each lesson's embedded simulator is reached by a clear “Try it / Open simulator” action; keep the Half Adder action linked to the existing Lab. Render labeled, accessible inline SVG schematics beside controls; keep the lesson's relevant truth/state table available below. Add gates, full adder, 4:1 MUX/1:4 DEMUX, 4:2 encoder/2:4 decoder, SR/JK/D/T state transitions, a 4-bit counter and a shift register, plus preserve the existing binary and Boolean teaching demos. No paid service, API, or external runtime is needed.

## Project structure

- `app/data/curriculum.py`, `app/data/curriculum-sources.md`: ordered bilingual curriculum content, interactive-demo descriptors, relevant truth tables, quiz options/answers/explanations, and source citations.
- `app/data/lesson.py` and `app/data/quiz.py`: existing Half Adder compatibility modules; reuse, do not delete.
- `app/main.py`: authenticated catalogue, detail, open/complete, and selected-lesson quiz endpoints plus actual account-owned progress aggregates.
- `app/models.py` and `migrations/versions/`: per-user progress reuse and additive quiz-attempt lesson slug migration.
- `app/static/js/simulator-core.js`: pure validated gate, adder, selector/decoder, encoder, flip-flop, counter, and shift-register functions shared by the browser and Node assertions.
- `app/static/js/simulator-ui.js`: localized simulator purpose/instructions, labeled inline diagrams, accessible controls, and lesson-specific interactive panels.
- `app/static/js/app.js`, `app/templates/index.html`, and `app/static/css/app.css`: retain the app shell and navigation; fix detail-column sizing and responsive overflow behavior.
- `tests/test_simulators.js` and `tests/`: exercise simulator math and preserve catalogue, account-isolation, process-restart, Half Adder, and planner coverage.

## Existing infrastructure and safety

The project remains local-preview capable with SQLite and deployment-ready for PostgreSQL. The temporary preview is separate from production and no hosting services are provisioned. Preserve per-user server-side scoping, hashed password/session design, CSRF protection, no-store API handling, and add only backward-compatible schema changes. Running Alembic against an existing database must preserve sessions, attempts, projects, tasks, and completed progress.

## Design

Retain the original editorial engineering-notebook design: warm paper surface, navy text, teal interactive learning cues, amber revision cues, two-column learning areas, native controls, formulas alongside results, reduced-motion support, and existing responsive layout. The lesson library and lesson detail use the current cards, tags, truth tables, and call-to-action patterns rather than introducing a new visual system.

## Relevant existing limitations

No email verification or password-reset email yet (no SMTP integration). Hindi/Hinglish copy is learning content, not a substitute for review by a fluent technical educator. Permanent hosting remains a separate, approval-gated request; this task changes the temporary preview only.
