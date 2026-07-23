# Transfer Hub — Manual UAT Scripts

**User Acceptance Testing pack for the Boundary Change (BC) Portal prototype.**

These are *human-run* scripts: a tester follows the numbered steps in a browser and records Pass / Fail against each expected result. They are for business sign-off and demos — separate from the automated Playwright regression suite (`tests/uat_*.py`, documented in `UATS.md`).

---

## How to use this pack

### Environment
1. Open **`transfer-hub-prototype.html`** in Google Chrome (double-click the file, or use the shared GitHub Pages link).
2. There is **no login**. Multi-user behaviour is simulated by the **“Switch user (prototype)”** dropdown at the top-right of the screen. “Switch to *X*” = “now acting as *X*”.
3. All data is held **in memory**. **Reloading the page resets everything** to a clean state. Unless a script says “continues from …”, start each script from a fresh reload.

### The personas you’ll use
| Persona | Role in the tool | Division |
|---|---|---|
| **Jane Doherty** | SET BC Lead (orchestrator) | Oncology R&D |
| **Omar Mansour**, **Priya Nair**, **Carlos Beltran** | Contributors | Oncology R&D |
| **Lena Thoms**, **Daniel Stein** | Contributors | Digital & Tech |
| **Farah Ahmed**, **Greg Bell** | Contributors | Finance |
| **Sofia Klein** | Contributor | Operations |

> A **SET BC Lead is an orchestrator only** — they set up the BC, assign contributors, review and submit. A Lead can **never** be a Cost Out or Cost In contributor.

### Cost centres worth knowing (they behave differently by design)
| Cost centre | Behaviour on the Detail screen | Currency |
|---|---|---|
| `7300RND-CC-041` | R&D — splits by **Project × UV** | GBP |
| `7400RND-CC-051` | R&D — splits by **Project × UV** | GBP |
| `6200COM-CC-115` | Commercial + SMM — splits by **Product** | GBP |
| `6200COM-CC-116` | Commercial + SMM — splits by **Product** | USD |
| `5110` | Digital & Tech — **GL only** | GBP |
| `2110` | Operations — **GL only** | GBP |
| `7300RND-CC-043` | R&D — splits by Project × UV | **EUR** |

### Recording results
For each step’s expected result, mark **Pass** ✅ or **Fail** ❌. If Fail, note what you actually saw. Each script ends with an overall result + sign-off line. A master sign-off sheet is at the end.

### Coverage map
| Suite | Journey | Scripts |
|---|---|---|
| **A** | Lead — setup & assignment | UAT‑A1 … A5 |
| **B** | Cost Out contributor | UAT‑B1 … B7 |
| **C** | Cost In (receiver) & balance | UAT‑C1 … C4 |
| **D** | Multi / concurrent transfers & direction | UAT‑D1 … D5 |
| **E** | Golden path (full end-to-end) | UAT‑E1 |

---

# Suite A — Lead: setup & assignment

### UAT‑A1 · Create a boundary change with one transfer
**Role:** Jane Doherty (SET BC Lead) **Objective:** A Lead can create a BC, define one Cost Out transfer, and notify the contributor.
**Preconditions:** Fresh reload; switch user to **Jane Doherty**.

| # | Action | Expected result |
|---|---|---|
| 1 | On the dashboard, click **“+ New request”**. | The **“New boundary change request”** screen opens. |
| 2 | Enter a **BC name** (e.g. “Oncology lab consolidation”) and a short **description**. | Text is accepted; “Requested by” shows **Jane Doherty**. |
| 3 | In the first transfer block, pick a **contact** = **Omar Mansour**, and leave the direction toggle on **Cost Out**. | The block shows Omar Mansour · Cost Out. |
| 4 | Click **“Save & notify contributor(s) →”**. | You return to the dashboard; a confirmation of the saved BC is shown. No error. |
| 5 | Open the **“Switch user”** dropdown. | Contributors who were notified are indicated / the BC now exists in the system. |

**Overall result:** ☐ Pass ☐ Fail Tester: ________ Date: ______ Notes: ______________________

---

### UAT‑A2 · Define up to five transfers with mixed directions
**Role:** Jane Doherty **Objective:** A BC can carry up to 5 transfers, each with its own contact and direction; the cap and removal work.
**Preconditions:** Fresh reload; Jane Doherty; on **“New boundary change request”**.

| # | Action | Expected result |
|---|---|---|
| 1 | Enter a BC name. Add a transfer block (contact **Omar Mansour**, **Cost Out**). | Transfer 1 populated. |
| 2 | Click **“Add transfer”** and add: T2 = **Lena Thoms** / Cost Out; T3 = **Carlos Beltran** / Cost In; T4 = **Farah Ahmed** / Cost Out. | Four transfer blocks, each with its own contact + direction toggle. |
| 3 | Keep clicking **“Add transfer”**. | You can add a **5th** transfer, then the **Add transfer** control is disabled / hidden (max 5). |
| 4 | **Remove** the 5th transfer (its × / remove control). | It disappears; the remaining blocks renumber cleanly. |
| 5 | Set Transfer 3’s toggle from Cost In back to **Cost Out**, then to **Cost In** again. | The toggle flips each time and the block reflects the current direction. |
| 6 | Click **“Save & notify contributor(s) →”**. | Saved without error; all listed contributors are notified. |

**Overall result:** ☐ Pass ☐ Fail Tester: ________ Date: ______ Notes: ______________________

---

### UAT‑A3 · Lead is an orchestrator only (cannot be a contributor)
**Role:** Jane Doherty **Objective:** A SET BC Lead can never be picked as a Cost Out or Cost In contributor.
**Preconditions:** Fresh reload; Jane Doherty; on **“New boundary change request”**.

| # | Action | Expected result |
|---|---|---|
| 1 | Open the **contact** picker on a transfer block and search for **“Jane”** (or any other Lead, e.g. “Sarah Okafor”, “Clara Mendez”). | Lead personas do **not** appear as selectable contacts — only **Contributor** personas are offered. |
| 2 | Save a BC assigning Omar Mansour, then (later, on the Summary) open the **Cost In Contributor** picker and search for a Lead name. | Leads are **not** selectable as a Cost In contributor either. |

**Overall result:** ☐ Pass ☐ Fail Tester: ________ Date: ______ Notes: ______________________

---

### UAT‑A4 · Per-transfer Cost In assignment on the combined Summary
**Role:** Jane Doherty **Objective:** On a multi-transfer BC, the Lead assigns a **separate** Cost In contributor for **each** transfer from the combined Summary.
**Preconditions:** Continues after two Cost Out submissions exist (or run UAT‑D1 first). Simplest setup: create a BC with **T1 = Omar Mansour / Cost Out** and **T2 = Carlos Beltran / Cost Out**; have each submit their Cost Out (see Suite B); then switch to **Jane Doherty**.

| # | Action | Expected result |
|---|---|---|
| 1 | On Jane’s dashboard, open the BC and walk through to the **Summary** screen (Cost → FTEs → Summary). | The Summary aggregates **both** transfers together (banner “Transfers in this boundary change — 2 total”; combined FY totals). |
| 2 | Scroll to the assignment area at the bottom. | There is **one Cost In Contributor picker per transfer** — not a single shared box. Each names its transfer’s contributor and cost centres. |
| 3 | For **Transfer 1**, assign **Lena Thoms**; for **Transfer 2**, assign **Farah Ahmed**. | Each transfer shows its own assigned person (“… · notified”); the two can be **different** people. |
| 4 | Remove Transfer 1’s assignment (×) and re-assign **Greg Bell**. | Transfer 1 now shows Greg Bell; Transfer 2 is unaffected. |
| 5 | Observe the submit box. | It reflects the **overall** state (e.g. “awaiting Cost In”); **“Submit all to Group”** is **disabled** until every transfer is balanced. |

**Overall result:** ☐ Pass ☐ Fail Tester: ________ Date: ______ Notes: ______________________

---

### UAT‑A5 · BC overview — one row per transfer with live status
**Role:** Jane Doherty **Objective:** The Lead can see every transfer’s status and drill into any one.
**Preconditions:** A multi-transfer BC exists with transfers in different states (some awaiting Cost Out, some submitted).

| # | Action | Expected result |
|---|---|---|
| 1 | From Jane’s dashboard, open the BC overview. | One **row per transfer**: contributor · direction · assigned Cost In person · status + an action. |
| 2 | Read the status chips. | They match reality (e.g. “awaiting Cost Out”, “awaiting Cost In”, “Cost In received”). |
| 3 | Click a transfer row’s action to review it. | It opens **that** transfer’s review (the correct contributor, cost centres and values load). |

**Overall result:** ☐ Pass ☐ Fail Tester: ________ Date: ______ Notes: ______________________

---

# Suite B — Cost Out contributor

> Start each of these by having Jane Doherty create a BC naming the relevant contributor (Cost Out), then **switch user** to that contributor and open their **Cost Out** task from the dashboard. The flow is: **Cost centres → Select cost to transfer → Enter transfer detail → FTEs out → Review & submit**.

### UAT‑B1 · GL-only cost centre (simplest shape)
**Role:** Omar Mansour **Objective:** A GL-only CC produces GL-level rows with no Product/Project/UV split.
**Preconditions:** BC exists with T1 = Omar Mansour / Cost Out; switched to Omar; Cost Out task open.

| # | Action | Expected result |
|---|---|---|
| 1 | On **“Cost centres”**, add cost centre **`5110`** (Digital & Tech) and mark it **Partial**. | `5110` is listed as Partial. |
| 2 | Continue to **“Select cost to transfer”**; tick at least one GL account. | GLs are listed at rolled-up level; you can tick them. |
| 3 | Continue to **“Enter transfer detail”**. | Rows appear at **GL level only** — the Product, Project and UV columns show **N/A** (greyed). |
| 4 | Continue to **“FTEs out”**, then **“Review & submit”**, then **“Submit to Boundary Change Lead”**. | Submission succeeds; you return to the dashboard with the task marked submitted. |

**Overall result:** ☐ Pass ☐ Fail Tester: ________ Date: ______ Notes: ______________________

---

### UAT‑B2 · R&D cost centre — splits by Project × UV (+ UV FTE allocation)
**Role:** Omar Mansour **Objective:** An R&D CC explodes into Project × UV detail, and the Review shows the UV-allocated FTEs block.
**Preconditions:** BC with T1 = Omar / Cost Out; Omar’s Cost Out task open.

| # | Action | Expected result |
|---|---|---|
| 1 | Add cost centre **`7300RND-CC-041`**, mark **Partial**. | Listed as Partial. |
| 2 | On **Select**, tick the **`5110-STAFF`** GL (and any others). | Ticks accepted. |
| 3 | On **Enter transfer detail**, inspect the rows. | Rows split by **Project** and **UV**; the **TA** (Therapy Area) column is derived/greyed; **Product** for R&D rows is derived/greyed. |
| 4 | Enter some staff cost values, go to **FTEs out**, enter FTEs, then open **Review & submit**. | FTE values display to **1 decimal place**. |
| 5 | On the Review screen, find the **UV FTEs out** block. | It shows the CC’s FTEs allocated across **Project × UV**, with a By TA / By UV / By cost centre / Detail toggle, ending in a “Total — R&D cost centres” row. |

**Overall result:** ☐ Pass ☐ Fail Tester: ________ Date: ______ Notes: ______________________

---

### UAT‑B3 · Commercial + SMM cost centre — splits by Product
**Role:** Omar Mansour **Objective:** A Commercial CC whose BC dept is SMM splits detail by Product (not Project/UV).
**Preconditions:** Omar’s Cost Out task open.

| # | Action | Expected result |
|---|---|---|
| 1 | Add cost centre **`6200COM-CC-115`** (Commercial, SMM), mark **Partial**; tick a GL on Select. | Accepted. |
| 2 | On **Enter transfer detail**, inspect the rows. | Rows split by **Product**; **Project** and **UV** columns show **N/A** (greyed). |

**Overall result:** ☐ Pass ☐ Fail Tester: ________ Date: ______ Notes: ______________________

---

### UAT‑B4 · Full vs Partial cost centres
**Role:** Omar Mansour **Objective:** Full CCs are pre-ticked, locked, and skip the Detail screen; Partial CCs require a selection.
**Preconditions:** Omar’s Cost Out task open.

| # | Action | Expected result |
|---|---|---|
| 1 | Add **`5110`** as **Full** and **`2110`** as **Partial**. | Both listed with their types. |
| 2 | Go to **Select cost to transfer**. | `5110` (Full) is **pre-ticked and locked** (cannot untick); `2110` (Partial) needs you to tick ≥1 GL. |
| 3 | Try to continue **without** ticking any GL for `2110`. | You are **blocked** with a message that every Partial CC needs ≥1 GL. |
| 4 | Tick a GL for `2110`, continue to **Enter transfer detail**. | Only `2110` rows appear; **`5110` (Full) is skipped** from the Detail screen entirely. |
| 5 | Look at the FTE rows for the Full CC on the FTEs screen. | Full CC FTE rows are **read-only**. |

**Overall result:** ☐ Pass ☐ Fail Tester: ________ Date: ______ Notes: ______________________

---

### UAT‑B5 · FTEs Out allows zero (cost-only transfer) and shows 1 dp
**Role:** Omar Mansour **Objective:** A CC may transfer 0 FTEs; FTE values always show 1 decimal place.
**Preconditions:** Omar’s Cost Out task open with at least one Partial CC and GLs selected.

| # | Action | Expected result |
|---|---|---|
| 1 | Reach the **FTEs out** screen and leave all FTE values at **0**. | No minimum is enforced — you can proceed with 0 FTEs. |
| 2 | Enter a value like `3` in an FTE cell. | It displays as **3.0** (1 decimal place). |
| 3 | Continue to **Review & submit** and submit. | Submission succeeds with 0 FTEs on the other CCs. |

**Overall result:** ☐ Pass ☐ Fail Tester: ________ Date: ______ Notes: ______________________

---

### UAT‑B6 · Currency — Local view is read-only, USD-only editing
**Role:** Omar Mansour **Objective:** Cost is stored in USD; the Local toggle shows the CC’s own currency but disables editing.
**Preconditions:** Omar’s Cost Out task open; add **`7300RND-CC-043`** (EUR) and/or **`6200COM-CC-116`** (USD) as Partial.

| # | Action | Expected result |
|---|---|---|
| 1 | On a cost screen, note the default **USD** view; the inputs are **editable**. | Values entered/edited in USD (shown in $m). |
| 2 | Switch the toggle to **Local**. | Values redisplay in the CC’s currency (EUR / USD per CC); the **inputs become disabled** (read-only). |
| 3 | Switch back to **USD**. | Inputs are editable again; no values were changed by toggling. |

**Overall result:** ☐ Pass ☐ Fail Tester: ________ Date: ______ Notes: ______________________

---

### UAT‑B7 · Detail screen — every visible row is in the submission; toolbar selection
**Role:** Omar Mansour **Objective:** On the Detail screen the row checkbox selects rows for toolbar actions (Add/Copy/Remove) — it does **not** opt rows in/out; every visible row is submitted. Each Partial CC must keep ≥1 row.
**Preconditions:** Omar’s Cost Out task open on **Enter transfer detail** with a Partial CC having several rows.

| # | Action | Expected result |
|---|---|---|
| 1 | Tick a row’s checkbox. | The row is **selected** for toolbar actions; it is **not** removed from the submission. |
| 2 | Use the **header checkbox** to select all rows in a block, then **shift-click** a range, then **click a row** anywhere (outside inputs). | Header selects the block; shift-click selects a contiguous range; row-click toggles that row’s selection. |
| 3 | Select every row in a Partial CC and **Remove**. | You are **blocked / prevented** from leaving a Partial CC with **0 rows**. |

**Overall result:** ☐ Pass ☐ Fail Tester: ________ Date: ______ Notes: ______________________

---

# Suite C — Cost In (receiver) & balance

### UAT‑C1 · Receiver’s read-only flow + single One-side cost centre
**Role:** Lena Thoms (Cost In contributor) **Objective:** The receiver reviews 3 read-only screens, picks **one** offsetting cost centre, and the One side auto-mirrors the Many side.
**Preconditions:** A BC where Omar submitted Cost Out and Jane assigned **Lena Thoms** as the Cost In contributor for that transfer. Switch to **Lena Thoms** and open the **“Enter Cost In values →”** task.

| # | Action | Expected result |
|---|---|---|
| 1 | Walk the flow: **Cost → FTEs → Summary**. | The Cost and FTEs screens are **read-only** drill-downs of the incoming Cost Out; no value entry. |
| 2 | On **Summary**, view the total cost + total FTEs. | Totals match the Cost Out that was submitted. |
| 3 | Open the **single cost centre picker** and try to add **two** CCs. | It is **capped at one** — only a single One-side CC can be chosen. |
| 4 | Choose one cost centre (e.g. `5130`). Attempt to submit **before** picking. | Submission is **gated** until a CC is chosen; after choosing, the submit button enables. |
| 5 | Submit. | The One side is auto-mirrored into the chosen CC so it **balances by construction**; you return to the dashboard, task submitted. |

**Overall result:** ☐ Pass ☐ Fail Tester: ________ Date: ______ Notes: ______________________

---

### UAT‑C2 · Balance is achieved by construction
**Role:** Lena Thoms → Jane Doherty **Objective:** After the receiver submits, the transfer reconciles to ~zero.
**Preconditions:** Continues from UAT‑C1.

| # | Action | Expected result |
|---|---|---|
| 1 | Switch to **Jane Doherty**; open the BC and go to the **Summary**. | The Out / In / **Net** reconciliation shows **Net ≈ 0** for each year (cost and FTEs). |
| 2 | Read the balance message. | It confirms the transfer is **balanced** (not “not balanced”). |

**Overall result:** ☐ Pass ☐ Fail Tester: ________ Date: ______ Notes: ______________________

---

### UAT‑C3 · Lead submits a balanced single-transfer BC to Group
**Role:** Jane Doherty **Objective:** Once balanced, the Lead can submit to Group.
**Preconditions:** Continues from UAT‑C2 (single-transfer BC, balanced).

| # | Action | Expected result |
|---|---|---|
| 1 | On the **Summary**, locate the submit box. | It shows the balance check passed and offers **“Submit to Group”**. |
| 2 | Click **“Submit to Group”**. | A confirmation appears; the BC status becomes **Submitted to Group**. |

**Overall result:** ☐ Pass ☐ Fail Tester: ________ Date: ______ Notes: ______________________

---

### UAT‑C4 · Submitted BC is locked read-only for everyone
**Role:** Jane Doherty, then a contributor **Objective:** After submission, the BC is read-only for all roles.
**Preconditions:** Continues from UAT‑C3.

| # | Action | Expected result |
|---|---|---|
| 1 | As Jane, reopen the BC Summary. | It is shown as **read-only** (“Summary (read only)” / “Submitted to Group”); no editable actions. |
| 2 | Switch to the Cost Out contributor (Omar) and open the BC. | Omar sees a **read-only** view; cannot re-edit the submitted values. |

**Overall result:** ☐ Pass ☐ Fail Tester: ________ Date: ______ Notes: ______________________

---

# Suite D — Multi / concurrent transfers & direction

### UAT‑D1 · Concurrent transfers — all live at once
**Role:** Jane Doherty + contributors **Objective:** Every transfer starts immediately; contributors work in parallel, in any order.
**Preconditions:** Fresh reload; Jane Doherty.

| # | Action | Expected result |
|---|---|---|
| 1 | Create a BC with **T1 = Omar Mansour / Cost Out**, **T2 = Carlos Beltran / Cost Out**, **T3 = Lena Thoms / Cost Out**. Save & notify. | All three contributors are notified **at setup** (no “start next transfer” gating). |
| 2 | Switch to **Carlos Beltran** (T2) **first** and complete his Cost Out; then **Omar** (T1); then **Lena** (T3). | Each can work **in any order**; completing one does not block or wait on the others. |
| 3 | Switch to **Jane** and open the BC overview. | All three transfers show as progressed independently (their statuses reflect who has submitted). |

**Overall result:** ☐ Pass ☐ Fail Tester: ________ Date: ______ Notes: ______________________

---

### UAT‑D2 · Per-transfer routing — each person sees only their own task
**Role:** contributors **Objective:** A contributor is only shown the transfer(s) that belong to them.
**Preconditions:** Continues from UAT‑D1 (or any multi-transfer BC), before all submissions complete.

| # | Action | Expected result |
|---|---|---|
| 1 | Switch to **Omar Mansour**. | Omar sees **only Transfer 1’s** Cost Out task — not T2 or T3. |
| 2 | Switch to **Carlos Beltran**. | Carlos sees **only Transfer 2’s** task. |
| 3 | After Jane assigns **Lena Thoms** as Cost In on one transfer, switch to Lena. | Lena sees **only** the Cost In task for the transfer she was assigned. |

**Overall result:** ☐ Pass ☐ Fail Tester: ________ Date: ______ Notes: ______________________

---

### UAT‑D3 · Direction — Cost In as the “Many” side
**Role:** Jane Doherty + contributor **Objective:** A transfer can be set so the side with many cost centres is **Cost In**; the screens relabel accordingly.
**Preconditions:** Fresh reload; Jane Doherty; on **“New boundary change request”**.

| # | Action | Expected result |
|---|---|---|
| 1 | Create a BC with one transfer: contact **Priya Nair**, direction toggle set to **Cost In**. Save & notify. | The transfer is stored with Cost In as the Many side. |
| 2 | Switch to **Priya Nair** and open her task; enter the Many side across several cost centres. | The entry screens are relabelled so the Many side reads **“Cost In”** (and “FTEs In”); the offsetting One side reads **“Cost Out”**. |
| 3 | As Jane, review the transfer’s Summary. | Out / In are correctly attributed given the direction; the Net still reconciles. |

**Overall result:** ☐ Pass ☐ Fail Tester: ________ Date: ______ Notes: ______________________

---

### UAT‑D4 · Lead Summary aggregates across all transfers
**Role:** Jane Doherty **Objective:** The Summary pivots Out / In / Net across **every** transfer, by SET area and year.
**Preconditions:** A multi-transfer BC where ≥2 transfers have been fully entered.

| # | Action | Expected result |
|---|---|---|
| 1 | Open the **Summary**. | The Cost and FTE pivot tables include cost centres from **all** transfers, split **Out by SET area / In by SET area / Net**. |
| 2 | Change the **Year** toggle (FY25…FY29). | Both tables update to the selected year. |
| 3 | On the Cost pivot, switch **By Dept ↔ By cost centre**, and **USD ↔ Local**. | Rows and currency change accordingly; the FTE table stays in headcount (1 dp). |

**Overall result:** ☐ Pass ☐ Fail Tester: ________ Date: ______ Notes: ______________________

---

### UAT‑D5 · “Submit all to Group” gated on every transfer balancing
**Role:** Jane Doherty **Objective:** A multi-transfer BC cannot be submitted until **all** transfers are balanced.
**Preconditions:** A multi-transfer BC where **some** transfers are balanced and at least one is still awaiting Cost Out or Cost In.

| # | Action | Expected result |
|---|---|---|
| 1 | Open the **Summary** while a transfer is still pending. | **“Submit all to Group”** is **disabled**; the box lists what’s still pending (e.g. “1 awaiting Cost In”). |
| 2 | Complete the remaining transfer(s) so all balance. | The submit box updates to “All N transfers balanced”. |
| 3 | Click **“Submit all to Group”**. | **Every** transfer locks to **Submitted to Group**; the BC becomes read-only. |

**Overall result:** ☐ Pass ☐ Fail Tester: ________ Date: ______ Notes: ______________________

---

# Suite E — Golden path (full end-to-end)

### UAT‑E1 · One balanced boundary change, end to end
**Role:** all **Objective:** Prove the whole happy-path journey from creation to Group submission, single transfer.
**Preconditions:** Fresh reload.

| # | Action | Expected result |
|---|---|---|
| 1 | **Jane Doherty:** “+ New request” → name the BC → Transfer 1 = **Omar Mansour / Cost Out** → **Save & notify**. | BC created; Omar notified. |
| 2 | **Omar Mansour:** open the Cost Out task → add `7300RND-CC-041` (Partial) → Select a GL → enter Detail values → enter FTEs → **Submit to Boundary Change Lead**. | Cost Out submitted. |
| 3 | **Jane Doherty:** open the BC → Cost → FTEs → **Summary** → assign **Lena Thoms** as the Cost In contributor → notify. | Lena assigned & notified. |
| 4 | **Lena Thoms:** open the Cost In task → Cost → FTEs → Summary → pick one One-side cost centre → **Submit**. | Cost In submitted; transfer balances by construction. |
| 5 | **Jane Doherty:** reopen the **Summary**. | Balance check passes (Net ≈ 0); **“Submit to Group”** is available. |
| 6 | Click **“Submit to Group”**. | BC is **Submitted to Group** and locked read-only for all roles. |
| 7 | Throughout, watch for anything broken. | No blank screens, no obviously wrong totals, no JavaScript errors (if the browser console is open). |

**Overall result:** ☐ Pass ☐ Fail Tester: ________ Date: ______ Notes: ______________________

---

## Master sign-off

| Script | Title | Result (P/F) | Tester | Date | Notes |
|---|---|---|---|---|---|
| UAT‑A1 | Create BC with one transfer | | | | |
| UAT‑A2 | Up to five transfers, mixed directions | | | | |
| UAT‑A3 | Lead cannot be a contributor | | | | |
| UAT‑A4 | Per-transfer Cost In assignment | | | | |
| UAT‑A5 | BC overview per-transfer status | | | | |
| UAT‑B1 | GL-only cost centre | | | | |
| UAT‑B2 | R&D Project × UV + UV FTE allocation | | | | |
| UAT‑B3 | Commercial + SMM splits by Product | | | | |
| UAT‑B4 | Full vs Partial cost centres | | | | |
| UAT‑B5 | FTEs allow zero, 1 dp | | | | |
| UAT‑B6 | Currency Local view read-only | | | | |
| UAT‑B7 | Detail rows & toolbar selection | | | | |
| UAT‑C1 | Receiver read-only flow + single CC | | | | |
| UAT‑C2 | Balance by construction | | | | |
| UAT‑C3 | Lead submits balanced BC to Group | | | | |
| UAT‑C4 | Submitted BC locked read-only | | | | |
| UAT‑D1 | Concurrent transfers all live | | | | |
| UAT‑D2 | Per-transfer routing | | | | |
| UAT‑D3 | Direction — Cost In as Many side | | | | |
| UAT‑D4 | Summary aggregates all transfers | | | | |
| UAT‑D5 | Submit-all gated on all balanced | | | | |
| UAT‑E1 | Golden path end-to-end | | | | |

**Overall UAT outcome:** ☐ Accepted ☐ Accepted with issues ☐ Rejected
**Signed:** ______________________ **Role:** ______________________ **Date:** ______

---

*These scripts describe the prototype’s intended behaviour as designed. Where a script and the running prototype disagree, record it as a Fail with a note — that is exactly what UAT is for.*
