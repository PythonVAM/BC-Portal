# CLAUDE.md — Transfer Hub Boundary Change Portal

> This file is loaded at the start of every Claude Code session in this directory. It tells Claude (and any human reading it) what this project is, what canonical decisions have been made, and how to work on it without re-arguing settled questions.

---

## 1. What this project is

A **single-file HTML prototype** of the Transfer Hub Boundary Change (BC) Portal — an internal finance tool for managing cost-centre and FTE transfers between divisions inside a large pharmaceutical company. The prototype simulates three roles:

- **SET BC Lead** — orchestrates a boundary change: sets up the request, assigns Cost Out and Cost In Contributors, reviews submissions, submits the final balanced BC to Group. Does not enter cost values themselves.
- **Cost Out Contributor** — enters the values being transferred *out* of their cost centres.
- **Cost In Contributor** — enters the offsetting values being transferred *in* to their cost centres.

The prototype is fully self-contained, with simulated personas, fake hierarchical data, and an in-memory state model. Multi-user behaviour is faked by a user-switcher in the topbar.

### Files

- **`transfer-hub-prototype.html`** (repo root) — the **canonical working file** and the prototype itself. ~6,074 lines of HTML/CSS/JS in one file. This is the single source of truth and the **only** prototype file Claude Code should ever edit. Edit it in place at the repo root.
- **`transfer-hub-paths.html`** (repo root) — standalone documentation file that maps the Cost Out paths across SET Area × BC Dept × Full/Partial combinations, with in-browser editing and persistent change history. Linked from the prototype's topbar ("📖 Paths").
- **`vN/index.html`** (e.g. `v2/`, `v3/`, `v4/`, `v5/`, …) — **frozen, read-only snapshots** of the prototype at past milestones. They exist so colleagues can open a stable link to a specific version (e.g. via GitHub Pages at `…/BC-Portal/v5/`). **Never edit, rename, or delete these.** They are an archive, not working code. All new work happens in the root `transfer-hub-prototype.html`, never in a `vN/` folder.

### Versioning & sharing (snapshot ritual)

The root `transfer-hub-prototype.html` is the live file that evolves PR by PR. The `vN/` folders are coarse, shareable checkpoints. The two don't conflict — commits give fine-grained history; the folders give stable links.

When a milestone is reached that's worth sharing with colleagues:
1. Copy the current root `transfer-hub-prototype.html` into a **new** `vN+1/index.html` (next number in sequence).
2. Leave that snapshot untouched from then on.
3. Carry on editing the root file as normal.

Do **not** promote/rename the root file into a `vN/` folder (that would remove the working file); always **copy**.

### Build / run

There is no build step. Open the HTML file in a browser. For testing, see `UATS.md`.

---

## 2. Canonical decisions (do not re-litigate without explicit confirmation)

These are settled. If a change would conflict with one of these, ask first.

### 2.1 Roles and orchestration

- **SET BC Lead is orchestrator only.** A Lead cannot also be a Cost Out or Cost In Contributor. This was enforced through a substantial refactor.
- **33 personas across 10 divisions**, with Lead and Contributor roles separated per person. Every persona division has a matching branch + cost centres in the org hierarchy (`ccTree`), so a user can always find their own division's CCs.
- **Multi-contributor submissions allowed.** In the prototype any CO Contributor may pick any CC; in production, contributors would be gated by SET area.
- **Last-writer-wins** if two CO Contributors pick the same CC.

### 2.2 Cost Out flow shape

The Cost Out flow is **select-then-detail** across two screens:

- **Cost Out — Select** (`step3`): user ticks GL accounts to transfer at the rolled-up level.
- **Cost Out — Detail** (`step3b`): the ticked GLs explode into row-level detail by their shape (see matrix below). Every row visible on this screen is part of the submission — the row checkbox is for *toolbar action* selection (Add / Copy / Remove), not for opting rows in or out.

### 2.3 Cost Out shape matrix (SET Area × BC Dept)

This is the *canonical* matrix driving the data shape on the Detail screen.

|                       | R&D dept              | SMM dept              | G&A dept              |
| --------------------- | --------------------- | --------------------- | --------------------- |
| **R&D Division (7000)**   | `gl+project+uv`       | `gl+project+uv`       | `gl+project+uv`       |
| **Commercial (6200)**     | `gl`                  | `gl+product`          | `gl`                  |
| **Digital & Tech (5000)** | `gl`                  | `gl`                  | `gl`                  |
| **Corporate (1000)**      | `gl`                  | `gl`                  | `gl`                  |
| **Operations (2000)**     | `gl`                  | `gl`                  | `gl`                  |

Implemented in `coShape(ccCode)`. Reading: R&D SET area always splits by Project × UV regardless of BC dept; Commercial SET only splits by Product when BC dept is SMM; everything else stays at GL only.

### 2.4 Full vs Partial CCs

- **Full CC** = entire cost centre transfers. Pre-ticked and locked on the Select screen; skipped from the Detail screen entirely (rows are auto-populated at default values backend-side). FTE rows are read-only for Full CCs.
- **Partial CC** = user picks GL accounts (must have ≥1 ticked on Select), then edits the resulting detail rows.
- If all of a contributor's CCs are Full, they skip the Detail screen and jump straight to FTEs Out.

### 2.5 Submission gates

- **Select screen**: every Partial CC must have ≥1 GL ticked.
- **Detail screen**: every Partial CC must have ≥1 row remaining (Add / Remove respects this).
- **FTEs Out**: no minimum — a CC may transfer 0 FTEs (cost-only transfer).

### 2.6 Currency

- **Stored in USD**, with a `Local` toggle on every cost screen that displays the per-CC currency from `ccAttr[code].cur`.
- **Editing is USD-only**; the Local view disables inputs to prevent accidental conversion edits.

### 2.7 FTEs Out — UV allocation (R&D only)

In the Review screen, R&D cost centres (`coShape(cc) === 'gl+project+uv'`) get an additional **UV FTEs out** block showing how the total CC FTEs allocate across Project × UV combinations.

**Formula per CC, per FY:**
```
UV_FTE[project, uv] = total_CC_FTE × (uv_staff_cost / total_staff_cost)
```

Where:
- `total_CC_FTE` = sum of `fteData` rows for this CC for this FY.
- `uv_staff_cost` and `total_staff_cost` = sum of detail rows where `gl === '5110-STAFF'`, grouped by Project × UV.
- **Per-FY allocation** — each FY uses that FY's weights, not a single canonical FY.

**Rounding**: raw values rounded to 1 decimal place. The row with the **largest raw value** absorbs any rounding drift so each column's allocated values sum exactly to the CC total.

**Edge cases:**
- If a CC has FTE > 0 but no STAFF cost rows in a given period, that cell shows `—` with a footnote.
- If a CC has no STAFF cost rows at all, the block shows: *"No R&D Project × UV STAFF cost rows to allocate against. Add 5110-STAFF cost out for R&D cost centres to see UV FTEs here."*

**Visibility**: the block is hidden entirely if no R&D-shape CCs are in the submission.

### 2.8 FTE formatting (global rule)

**All FTE values display at 1 decimal place** everywhere via the global `fmtFte()` formatter. Cost values stay at 0 decimal places via `fmt()`. Don't introduce local `const fmtFte = (v) => fmt(v)` lambdas — the global takes over.

### 2.9 Bulk selection (Detail screen AND Select screen)

Both the Cost Out Select and Cost Out Detail screens support:
1. **Header checkbox per block** — ticks every row in the block (Partial rows only on Select; Full CC rows are skipped because they're locked).
2. **Shift-click range select** — click row A, shift-click row B, all rows between get selected (or ticked).
3. **Row-click selection** — clicking anywhere on a row (outside the checkbox or other interactive elements) toggles its state.

State:
- Detail: `coDetailSel` (Set of rowKeys), `coDetailLastSel` (per-group anchor).
- Select: `coSelLastSel` (per-group anchor; `coGlPicked` is the existing tick set).

Inputs inside rows use `onclick="event.stopPropagation();"` to prevent row-click toggling when editing.

### 2.10 Sticky "stable region"

Every screen has a two-tier sticky stack that pins essential context as the user scrolls long tables:

- **Topbar** — `position: fixed; top: 16px; z-index: 60` globally. A `body::before` pseudo-element covers the 16px gap above it so scrolling content can't peek through.
- **`.screen-head`** — sticky at `top: 66px`, contains the screen's title and breadcrumb. Wraps inside each screen card.
- **`.screen-action`** — sticky just below screen-head. Contains the summary bar and toolbar. Its `top` is set dynamically by `syncStickyOffsets()` to abut the `.screen-head` exactly (1px overlap to eliminate sub-pixel gaps).
- `syncStickyOffsets()` runs at the end of `go()` and on `window.resize`, and at the end of `renderCoSelect()` / `renderCoDetail()` because their content affects screen-head height.

The **hints banner** and the **profile-panel** intentionally scroll away with content (they're reference info, not action affordances).

### 2.11 Flat unified read-only cost tables

Every **cost** table — entry screens and read-only context tables alike — uses **one flat table with a fixed column set**, matching the Cost Out Detail screen. There is **no dept sub-grouping and no collapse**; rows are sorted **Dept (R&D → SMM → G&A) → Cost Centre** and every row is shown.

**Unified columns:** `(Cost centre · Dept ·) GL account · Product · Project · UV` + the FY columns. The Cost centre + Dept columns are included on multi-CC tables (`roUniIdHead(true,hasSub)`) and omitted where the CC is already in a block/section header (`roUniIdHead(false,hasSub)`). Columns a row's shape doesn't use render as a greyed **N/A** (`.cod-na`):
- R&D-shape rows (`gl+project+uv`) fill Project + UV; Product = N/A.
- SMM-shape rows (`gl+product`) fill Product; Project + UV = N/A.
- GL-only rows: Product + Project + UV all = N/A.

**Helpers** (defined together near the top of the `<script>`):
- `roUniIdHead(showCc, hasSub)` — the fixed identity `<th>`s (adds `rowspan="2"` when a FY is month-expanded).
- `roUniIdCells(row, showCc)` — the fixed identity `<td>`s with N/A fill.
- `fmtCostM(v)` — cost value in **$m** (2dp), negatives in red parentheses.

**Where applied:** Lead step 6 (`renderRvByCC`, `renderRvCostOut`), CI step 1 (`renderCiByCc`), CI step 2 (`renderCiCoSummaryTable`, `renderCiTable`, `renderCiCoTable`, single-CC auto-populated view), CI steps 2 & 3 (`renderCiOthersTable`), CI step 3 FTE summary (`renderCiFteCoSummaryTable` — flat, FTEs not $m), CI per-CC review (`renderCiReview`), and step 7 (`coOutSection` / `ciInSection`, plus the aggregate Cost/FTE/Net matrix).

**Currency:** all cost values display in **USD millions ($m)** via `fmtM` / `fmtCostM`. The editable entry tables (`renderCiTable`, Cost Out Detail) display and accept input in $m and scale back to whole dollars (`×1e6`) for storage and balance math. FTE tables are unaffected (`fmtFte`, 1dp headcount).

---

## 3. Working conventions

### 3.1 Q&A before building

For any non-trivial change, **state your understanding back to the user and confirm before editing**. Settled rules above don't need re-confirmation; new decisions do. This was established early — the user values being asked clarifying questions over receiving wrong assumptions.

### 3.2 File editing

- **Read** the surrounding context with `view` before editing. The file is ~6k lines; using `grep -n` to navigate is essential.
- **Edit** with `str_replace` for targeted changes. Avoid rewriting whole functions when a 3-line edit will do.
- **Always run `node --check` on the JS** before claiming a change is complete:
  ```bash
  grep -oP "<script>[\s\S]*?</script>" transfer-hub-prototype.html | sed 's/<script>//; s|</script>||' > /tmp/v.js
  node --check /tmp/v.js
  ```
- **Run the regression UATs** (see `UATS.md`) after any meaningful change.

### 3.3 Formatting and tone

- Code style matches the existing file: 2-space indent, single-line `if` statements with no braces, terse JS expressions. Don't restyle existing code.
- Comments are **explanatory** (why, not what). Add one when a behaviour isn't obvious from the code.
- CSS class naming: existing patterns are `co-*`, `ci-*`, `rv-*`, `s6-*` (step 6), `s7-*` (step 7). Stick with them.

### 3.4 What's deliberately ad-hoc (won't break if changed, but worth flagging)

- The `SET_AREA_TYPE` map (line ~1195) lists the 7 SET area types (`corporate`, `operations`, `it`, `commercial`, `rnd`, `retail`, `risk`). Adding a new one only needs a `coShape()` change if it splits cost by an extra dimension — `retail`/`risk` are plain `gl` and fall through `coShape`'s default. Top-level SET areas must be kept in sync across `ccTree`, `SET_AREA_TYPE`, and `SET_AREAS` (step-7 aggregation).
- The `SIM` map (line ~1154) is hand-coded sample data per CC. It's not exhaustive; `getSimRows()` returns a default if a CC isn't listed.
- Persona definitions live in `PEOPLE` (search for `const PEOPLE`). Adding a new persona requires picking a `dept` and `role` consistent with the existing taxonomy.

---

## 4. Pending / known issues (snapshot at handover)

These are open at the time of writing this CLAUDE.md. Update or strike through as resolved.

- **Path documentation `transfer-hub-paths.html` is Cost Out focused.** Cost In paths and FTE rules from a process angle aren't documented yet — user said start with CO; expand later.
- **Filter dropdowns on column headers** (deferred by user).
- **Bottom button row sticky-pin to viewport bottom** — would mirror the top stable region. Future improvement.
- **Step 4 (FTEs Out) doesn't yet use `.screen-action` wrapping** — its toolbar would benefit, but data is usually short enough that it isn't urgent.
- **Dashboard's dynamic content** isn't wrapped with `screen-head` — would need `renderDashboard()` to emit the wrapper. Low priority.
- **`window.storage` for `transfer-hub-paths.html`** only works when opened in environments that expose the API. From a plain file:// URL it falls back gracefully but doesn't persist edits across reloads.

---

## 5. Don't do these

These have been tried and abandoned, or explicitly rejected:

- **Don't reintroduce "tick rows to opt in"** on the Detail screen. The model is: every row visible is part of the submission. The checkbox is for toolbar action selection only. This was a settled Q&A item.
- **Don't make the row checkbox toggle the row's submission state.** Same reason.
- **Don't re-add Section A inside CI screens** — it was removed deliberately.
- **Don't auto-convert Local-currency edits back to USD** — the rule is USD-only editing. The Local view is read-only. Round-tripping introduces rounding mismatch.
- **Don't restyle the existing code** while making a behaviour change. Keep diffs small and focused.
- **Don't introduce a new global formatter** for FTEs or costs without checking whether `fmtFte()` or `fmt()` already covers the case.
- **Don't edit, rename, or delete any `vN/index.html` snapshot** (`v2/`, `v3/`, …). They are frozen archives that colleagues may be linking to. All work goes in the root `transfer-hub-prototype.html`; new versions are made by *copying* the root file into a new `vN/` folder, never by editing an existing one.

---

## 6. Glossary

- **BC** = Boundary Change. The unit of work this app captures.
- **CC** = Cost Centre.
- **CO** / **CI** = Cost Out / Cost In.
- **GL** = General Ledger account.
- **UV** = Utilisation View (used in R&D — Discovery / Early / Late).
- **TA** = Therapy Area (Oncology, Immunology, CV & Renal).
- **SET Area** = the top-level branch of the cost-centre hierarchy (R&D Division, Commercial, etc.) — this is what `coShape` is keyed off.
- **BC Dept** = R&D / SMM / G&A, a CC-level attribute independent of SET Area.
- **SMM** = Sales, Marketing & Medical.
- **G&A** = General & Administrative.
- **Shape** = `'gl'` | `'gl+product'` | `'gl+project+uv'`. Determines Detail-screen row shape.
- **Full / Partial** = CC selection mode.
