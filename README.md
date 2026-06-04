# BC-Portal

BC-Portal is a single-file HTML prototype of the **Transfer Hub Boundary Change (BC) Portal** — an internal finance tool for managing cost-centre and FTE transfers between divisions inside a large pharmaceutical company.

## Layout

- **`transfer-hub-prototype.html`** (repo root) — the **canonical working file** and the prototype itself. All development happens here, in place, at the repo root. This is the single source of truth.
- **`vN/index.html`** (`v2/`, `v3/`, `v4/`, `v5/`, …) — **frozen, shareable snapshots** of the prototype at past milestones, so colleagues can open a stable link to a specific version (e.g. via GitHub Pages at `…/BC-Portal/v5/`). These are an archive — **never edit, rename, or delete them.** New versions are made by *copying* the root file into the next `vN/` folder, never by editing an existing one.
- **`transfer-hub-paths.html`** (repo root) — standalone documentation mapping the Cost Out paths across SET Area × BC Dept × Full/Partial combinations, with in-browser editing and persistent change history. Linked from the prototype's topbar ("📖 Paths").

## Build / run

There is no build step — open the HTML file directly in a browser.

## Project context & testing

- **`CLAUDE.md`** — the project context: what the prototype is, the canonical decisions that are settled, and the working conventions to follow.
- **`UATS.md`** — the testing reference: the Playwright-based regression suite and the JS syntax check to run before committing.
- **`journal.md`** — a dated, high-level history of significant changes.
