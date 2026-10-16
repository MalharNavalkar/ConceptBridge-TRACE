# Outcome checklist

- [x] **Readable lesson layout:** Inspected the DOM/CSS and fixed the actual cause: the legacy `.lesson-section` grid reserved a 31px index column that new lesson markup did not use, leaving body content auto-placed in that narrow track. Main article now uses available width; desktop article remains dominant beside a smaller Notes/Builds On/Quick Check/Sources column; tablet/mobile stack the sidebar below. Headings, paragraphs, formulas, tables, code and diagrams wrap/scroll within their own containers. No page-wide overflow or one-word-per-line wrapping was observed at tested widths.
- [x] **Logic Gates simulator:** Toggle inputs, select AND/OR/NOT/NAND/NOR/XOR/XNOR and observe the live output with labels, diagram, and truth-table reference.
- [x] **Full Adder simulator:** Toggle A/B/Cin; calculate Sum and Cout; display a labeled full-adder block circuit with equations, live signal values, and all eight table rows.
- [x] **4:1 MUX and 1:4 DEMUX simulators:** Four data inputs, independent selector lines, correctly routed outputs, labeled circuit diagram, and reference table.
- [x] **4:2 Encoder and 2:4 Decoder simulators:** One-hot mapping, address decoding, live output; invalid/undefined zero-or-multiple active encoder states are explained.
- [x] **Flip-flop simulator:** SR/JK/D/T inputs/state/clock; correct hold/set/reset/toggle/capture rules; active-high SR S=R=1 is invalid, visibly warned, and Q is preserved. Labels and unused controls adapt to the selected type.
- [x] **Counter and register simulators:** Step/reset a visible four-bit modulo-16 counter; clock a four-stage shift register with visible direction and state.
- [x] **Lesson links and accessibility:** Each lesson has its own integrated simulator or preserved Half Adder Lab action. Added no sidebar clutter. Inputs are labelled, keyboard-focusable and usable on mobile. Simulations are deterministic and local; no paid API or external AI service.
- [x] **Regression protection:** Retained login/logout, server-side per-account authorization, lesson progress, quiz history, the Half Adder Lab and project planner. Added pure simulator logic shared by the UI and Node tests.
- [x] **Verification:** Ran automated Python and Node suites, Python/JavaScript syntax checks, actual browser interaction at desktop/tablet/mobile widths, and HTTPS preview/asset checks. Results below.

## Verification evidence

- `python3 -m unittest discover -s tests -v`: **11 tests passed**, including curriculum completeness, account isolation, process-restart persistence, and preserved learning/planner behavior.
- `node tests/test_simulators.js`: **11 simulator checks passed**. `python3 -m compileall -q app migrations scripts tests` and `node --check` for `simulator-core.js`, `simulator-ui.js`, and `app.js` passed.
- Headless Chromium registered a disposable account against a temporary SQLite database, opened all nine lesson routes and simulator actions, exercised gates, Full Adder, MUX/DEMUX, encoder/decoder, SR/JK/D/T, counter, register and all four Half Adder Lab rows, and reported no uncaught JavaScript errors.
- Responsive geometry: at 1440px the lesson article measured 783px and sidebar 291px. At 820px and 390px both cards stacked in order. Document scroll width matched the viewport at all three widths; the lesson body used the article's full width. Mobile simulator controls worked.
- Current temporary preview: [https://8000-iqz5anvcpeovrl7flmzqr-e6595978.sg2.manus.computer/](https://8000-iqz5anvcpeovrl7flmzqr-e6595978.sg2.manus.computer/). Latest frontend assets and `/api/health` returned HTTP 200 over HTTPS. It opens at the account gate.
- No permanent hosting or production deployment was created. The existing temporary preview database was not used or changed by the disposable browser tests.
