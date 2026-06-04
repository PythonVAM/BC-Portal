# Journal — Transfer Hub Prototype

This is a high-level history of significant changes to the prototype. New entries go at the bottom. Use this to find when a feature was introduced or a decision was changed.

For canonical rules (the things you should treat as settled), read `CLAUDE.md` instead.

---

## Earlier history (pre-handover)

The prototype began in **April 2026** as a wireframe and evolved through many iterations. Highlights of the journey before handover to Claude Code:

- **April 2026** — Initial wireframe / UX exploration. Multi-step Cost Out and Cost In flows, multi-user simulation, dashboards, CSV import/export, sticky columns, SET-area summary established.
- **Mid-May 2026** — Added "BC Lead" role separation. Built the workflows reference document (12 patterns → simplified to 4 after agreeing role exclusivity). Built a one-page PowerPoint announcement deck for the SET BC Lead pitch (many design iterations, landing on an "authentic proposal" tone).
- **Late May 2026** — Substantial refactor enforcing SET BC Lead as orchestrator only (cannot also be CO/CI Contributor). Expanded personas to 30 people across 9 divisions. Added Dept (R&D/SMM/G&A) attribute to cost centres. Began Dept-splitting of the Cost Out and Cost In flows through 7 tranches.
- **End of May 2026** — Abandoned the tranche-based "Dept-split" approach after UX issues. Reverted to a clean v69 base. Rebuilt with the **select-then-detail** two-screen Cost Out approach.
- **Early June 2026** — Mapped the full **Cost Out decision matrix** through 15+ Q&A clarifications with the user. Settled the canonical rules now captured in `CLAUDE.md`.

The remainder of the journal below covers June 2026 and onward — the round of changes immediately before the handover to Claude Code.

---

## June 2026 — Build details

### Select-then-detail Cost Out flow

The Cost Out flow was rebuilt around two screens:

- **Cost Out — Select (step3)** — user ticks GLs at rolled-up level, grouped into Dept × Shape blocks. Full CCs appear with all GLs pre-ticked and locked.
- **Cost Out — Detail (step3b)** — ticked GLs explode into rows by the CC's shape. Editable; supports Add / Copy / Remove via a toolbar; CSV download/upload.

Settled Q&A includes: full CC skipping, GL gating, row-equals-submission model, no partial-amount constraint (BCs can interlock), forward-priority navigation that preserves edits on plain back but wipes on untick-then-retick, per-CC FTE entry decoupled from cost.

### Sticky "stable region"

Each screen has a two-tier sticky stack:
1. **Topbar fixed globally** (with a `body::before` covering the 16px gap above it).
2. **`.screen-head`** (title + breadcrumb) sticky at `top: 66px`.
3. **`.screen-action`** (summary bar + toolbar) sticky just below screen-head, with `top` computed dynamically by `syncStickyOffsets()`.

The hints banner and profile-panel intentionally scroll away.

### Bulk selection (Detail + Select)

Both Cost Out screens support: header checkbox per block, shift-click range select, row-click selection. Inputs inside rows stop propagation so editing a value doesn't toggle the row.

### UV FTEs out (R&D only)

The Review screen gained a third data block — UV FTEs out — visible only when the submission contains at least one R&D-shape CC. Allocation formula:

```
UV_FTE[project, uv, fy] = total_CC_FTE[fy] × (uv_staff_cost[fy] / total_staff_cost[fy])
```

Weight basis is **5110-STAFF only** (Salaries & wages). Per-FY allocation. Round-and-balance to 1dp so column sums match CC totals exactly. Edge cases handled: no STAFF rows → guidance message; STAFF cost = 0 for a period with FTE > 0 → `—` with footnote.

### Global 1dp FTE formatter

Introduced `fmtFte(n)` returning `Number(n).toLocaleString('en-US', {minimumFractionDigits:1, maximumFractionDigits:1})`. All 8 previous local `const fmtFte = (v) => fmt(v)` lambdas were stripped so the global takes over. The CI-specific `fmtFteCi` (negative-as-red-parens) now wraps `fmtFte`. Editable FTE inputs also use `fmtFte` for display.

Costs continue to use `fmt()` at 0 decimal places.

### Path documentation file

Created `transfer-hub-paths.html` — standalone documentation mapping the SET Area × BC Dept × Full/Partial paths. Includes:
- Dimensions overview
- Path matrix (5 × 3)
- Per-path narrative cards (collapsible)
- Open questions section
- **In-browser editing** with persistent storage via `window.storage`
- **Automatic changelog** — each save prompts for a description, captures pre-edit snapshot, supports non-destructive restore

Linked from the main prototype's topbar as "📖 Paths".

### Dept-grouped collapsible read-only tables

Every read-only Cost Out / FTE table seen by a Lead or CI Contributor now renders **dept-grouped and collapsed by default**. An aggregate row shows dept chip + row count + per-FY totals; expand reveals the full row table.

Applied to: Lead step 6 (renderRvByCC), CI step 1 (renderCiByCc), CI step 2 CO summary, CI steps 2&3 Others Table (per-person blocks and Net Available block), CI step 3 FTE summary.

**Not applied** to the editable Cost In / FTE In entry tables (CI step 2 `renderCiTable`, CI step 3 `renderCiFteTable`) — those stay flat for usability.

State: `ciDeptExp` Set, keyed by `<scope>::<dept>`. `toggleCiDeptGroup(scope, dept)` flips the bit and re-renders the active screen via the dispatcher pattern.

Helpers: `groupRowsByDept(rows)` for tables where row content carries the dept marker (project/product); `groupPairsByCcDept(pairs)` for FTE tables where dept must come from CC's bcDept attribute.

---

## Open / pending

(Mirror of CLAUDE.md section 4. Update both when items move.)

- Path docs are Cost Out focused; Cost In side, Lead approval flow, FTE rules from process angle not yet documented.
- Filter dropdowns on column headers (deferred).
- Bottom button row sticky-pin to viewport bottom (future).
- Step 4 (FTEs Out) `.screen-action` wrapping (low urgency).
- Dashboard dynamic content not wrapped with `screen-head` (low priority).
- `window.storage` only works in environments that expose it; falls back gracefully otherwise.

---

## How to add a new entry

When you finish a meaningful change:

1. Append a dated section below this line.
2. State the change in one paragraph (what was added / removed / fixed).
3. List the affected files / functions / line ranges if useful.
4. If a canonical rule changed, **also update `CLAUDE.md`** so future sessions inherit the new state.

```
### YYYY-MM-DD — Short title

(One paragraph here. Mention any Q&A decisions, any rules that changed.)
```

---

## New entries (post-handover)

<!-- Add new entries below this line as you work. -->
