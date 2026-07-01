# BC Workflow Options — Design Conversation

> A record of the working session that produced the `workflow-options/` interactive
> process-flow diagrams and the comparison / best-practice assessment. Reconstructed
> from the session transcript. User turns are quoted; assistant turns are summarised
> with the concrete actions taken.

---

## 1. Kicking off

**User:** I want to build out some options for the BC Workflow, and I'd like to build these as clickable HTML apps.

**Assistant:** Asked clarifying questions before building. Answers received:
- *What are these options?* → **Alternative end-to-end flows** (different ways to orchestrate a BC, each a clickable walkthrough to compare).
- *How should they relate to the existing prototype?* → **Fresh lightweight mockups** (standalone, not tied to `transfer-hub-prototype.html`).

**User:** Clarified that "apps" means an **interactive workflow / process-flow diagram** built in HTML — *not* a data-capture clone of the existing app. Provided the "Proposed Workflow" graphic (7 steps: SET BC Lead sets up → delegates Cost Out → Cost Out Contributor submits → Lead reviews / delegates Cost In → Cost In Contributor submits → Lead reviews → Lead submits to Group) and said: start by making an HTML version of this.

**Assistant:** Built `workflow-options/proposed.html` — a faithful, self-contained recreation of the graphic (maroon Lead boxes, white Cost Out / Cost In boxes, gold numbered badges, chevron connectors, legend), made interactive (hover lift; click a step to reveal a detail card), and data-driven from a `STEPS` array so more options are easy to add.

---

## 2. The index

**User:** Yes build the index.

**Assistant:** Built `workflow-options/index.html` — a landing page listing the options as cards, each with a mini colour-coded flow preview; data-driven (`OPTIONS` array) with "Coming soon" support. Added a back-link on the proposed page.

**User:** Reported that GitHub URLs only showed source, not rendered pages.

**Assistant:** Explained GitHub Pages serves from the default branch (not the feature branch); offered the htmlpreview proxy for immediate viewing and a PR-to-`main` for permanent Pages URLs.

**User:** Open a PR and merge please.

**Assistant:** Opened and squash-merged the PR to `main` so the pages go live via GitHub Pages.

---

## 3. Option 1 — constraints & pros/cons

**User:** Add specific constraints and pros/cons to Option 1. Roles are pervasive/mutually exclusive (a SET BC Lead is only ever a Lead, never a Contributor, and vice versa). Contributors are assumed to be Finance Business Partners (FBPs) or GFS Analysts. Advantage: the SET BC Lead definitely gets visibility of all BCs in their SET Area. Trade-off: sometimes an FBP should sign off, and in this flow that only happens as a manual offline activity (Lead shares info) unless the FBP was a Contributor.

**Assistant:** Added an "About this option" section (Constraints / Advantages / Trade-offs) as three colour-coded cards beneath the diagram.

---

## 4. BC roles vs business roles

**User:** Make clear which roles are **BC-specific** (SET BC Lead, BC Lead, BC Contributor) vs **generic business** roles, and how they map per option. In Option 1 the SET BC Lead and BC Lead are effectively one role, filled by an FP&A person; the Contributor is an FBP or GFS Analyst. In Option 2 the BC Lead becomes the FBP; the Contributor is a GFS Analyst or Junior Local Finance. The SET BC Lead is always FP&A in all options.

**Assistant (with confirmation):** Confirmed the Option-2 restructure via a question (answer: **relabel so the FBP is the BC Lead**; roles mapping to live **per-option**). Then:
- Added a "Roles in this option" mapping panel to each option page.
- Restructured Option 2 so the **BC Lead (orchestration) = FBP** (purple), with the **SET BC Lead (FP&A)** appearing only at the final Submit to Group.
- Added "Simple to implement" to Option 1's advantages.

---

## 5. The options, one by one

Each option is a standalone interactive diagram with a roles panel, constraints/pros/cons, and (later) a best-practice card.

**Option 2 — FBPs as BC Leads** (`fbp-signoff.html`)
The FBP is brought into the Lead's steps and adds an in-system step where the BC Lead submits to the SET BC Lead before Group. Advantages: everyone with a stake stays informed; simple to implement. Trade-offs: FBPs who were Contributors can no longer contribute; bigger change impact for areas relying on local finance rather than GFS.

**Option — Fluid roles** (`fluid-roles.html`)
The business-role → BC-role mapping is fluid: whoever creates a BC becomes its Lead (any business role). Per-BC exclusivity (a BC's Lead can't be its Contributor, but can be on another BC). SET BC Lead kept informed via notification rules (shown as an annotation, not a flow step). Advantages: closer to existing ways of working; less rigid. Trade-offs: more complex to implement; harder to document; complex notification rules.

**Option — Fluid roles + Consulted** (`fluid-roles-consulted.html`)
As fluid, but the BC Lead names "Consulted" people at setup and the system notifies only those named (no auto-determination). Simpler to implement; risk of human error if the Lead forgets someone.

**Option — Optional FBP approval** (`optional-fbp-approval.html`)
Option 1's flow with an **optional** FBP approval node before Group (dashed, "Optional" tag). Removes today's offline approval; minimal deviation/rework. Trade-off: roles stay rigid and pervasive.

---

## 6. Side-by-side comparison

**User:** Side by side is definitely what I wanted to do next.

**Assistant:** Built `compare.html` — a scorecard matrix of all options (ordered rigid → fluid), with a sticky first column/header, coloured rating chips, and a prominent "Compare all options" button added to the index.

---

## 7. Best-practice assessment

**User:** Assess the options against public-domain best practice.

**Assistant:** Assessed against established governance principles — Segregation of Duties (COSO/ISACA), four-eyes / maker–checker, auditability, RACI (Consulted/Informed), systematic-over-discretionary controls, proportionate/risk-based control, and change-management adoption. Headline: FBPs-as-BC-Leads is strongest on control; the fluid options are best for adoption; the weak points are Option 1's offline approval and the fluid options' discretionary/complex notifications.

**User:** Add to scorecard and a best-practice assessment card. Confirmed this is **not** a SOX control situation.

**Assistant:** Added a "Best-practice alignment" band of rated rows to the scorecard (Segregation of duties, Independent approval before Group, Auditability, Accountability, Oversight visibility, Adoption/fit) and an assessment card; removed the SOX framing.

**User:** What's your objective recommendation?

**Assistant:** Recommended **Option 3 (BC Leads + Contributors + Optional FBP approval), with the approval made threshold-mandatory rather than discretionary** — closest to what's built, fixes the offline/un-auditable approval, and stays proportionate since it's not SOX. The recommendation flips to **FBPs as BC Leads** if FBPs already drive most BCs in practice.

**User:** Go for it.

**Assistant:** Added a gold recommendation banner to the top of the compare page.

**User:** I thought you were going to add a card to each option, not a block under the scorecard.

**Assistant:** Corrected: added a per-option "Best-practice assessment" card (six-row rating grid + option-specific verdict + link to compare) to every option page, and slimmed the block on the compare page.

---

## 8. The missing combination

**User:** One variation hasn't been considered — the proposed workflow, but with the Consulted option added.

**Assistant:** Built `proposed-consulted.html` (rigid roles + Consulted at setup; keep-informed only, not an approval) and wired it into the index and compare view.

---

## 9. Relabelling

**User:** Relabel the options as:
1. BC Leads + Contributors only
2. BC Leads (Consulted option) + Contributors
3. BC Leads + Contributors + Optional FBP approval
4. FBPs as BC Leads
5. Fluid BC Leads and Contributors
6. Fluid BC Leads (Consulted option) and Contributors

**Assistant:** Relabelled and renumbered all six options across page headings, browser titles, index cards (reordered 1–6), and compare columns; updated the recommendation banner / cross-references; reduced heading letter-spacing for the longer names. Filenames kept unchanged so existing links still work.

---

## Final option set

| # | Label | File |
|---|-------|------|
| 1 | BC Leads + Contributors only | `proposed.html` |
| 2 | BC Leads (Consulted option) + Contributors | `proposed-consulted.html` |
| 3 | BC Leads + Contributors + Optional FBP approval | `optional-fbp-approval.html` |
| 4 | FBPs as BC Leads | `fbp-signoff.html` |
| 5 | Fluid BC Leads and Contributors | `fluid-roles.html` |
| 6 | Fluid BC Leads (Consulted option) and Contributors | `fluid-roles-consulted.html` |
| — | Comparison + best-practice assessment | `compare.html` |
| — | Landing page | `index.html` |

**Recommendation on record:** Option 3 with a threshold-mandatory (rather than optional) FBP approval — proportionate, low-rework, and it closes the offline-approval gap. Flips to Option 4 (FBPs as BC Leads) if FBPs already drive most BCs today.

**Live:** `https://pythonvam.github.io/BC-Portal/workflow-options/`
