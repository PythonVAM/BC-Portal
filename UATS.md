# UATs — Transfer Hub Prototype regression tests

These are Playwright-based UATs that drive the prototype in a real browser and assert behaviour. They're the "before you commit" sanity check for any non-trivial change.

---

## Setup (one-time)

You'll need Python 3 and the Playwright Chromium driver:

```bash
pip install playwright
playwright install chromium
```

Each test below is self-contained. Save them into a `tests/` folder inside your project directory. They expect the prototype HTML at the path shown in the `pg.goto(...)` line — update that path to match your local file, or set a `PROTOTYPE_PATH` env var and read it (I've left the original `file:///mnt/user-data/outputs/...` URLs in place; change them once on first save).

Run any one test with:

```bash
python tests/uat_grouped_e2e.py
```

Run them all at once:

```bash
for f in tests/uat_*.py; do echo "=== $f ==="; python "$f"; done
```

---

## The regression suite

Listed in suggested run-order, from cheap to expensive.

### 1. JS syntax check (not a Playwright test, but run it first)

Extracts the embedded `<script>` from the HTML and runs `node --check` on it. Catches syntax errors instantly before you waste time on browser-driven tests.

```bash
grep -oP "<script>[\s\S]*?</script>" transfer-hub-prototype.html \
  | sed 's/<script>//; s|</script>||' > /tmp/v.js
node --check /tmp/v.js && echo OK
```

If it doesn't say `OK`, fix the syntax error and re-run.

### 2. `uat_grouped_e2e.py` — End-to-end balance check

Runs a full Lead → CO Contributor → Lead → CI Contributor → Lead flow with multiple CCs (R&D, SMM, SMM, IT). The CI contributor mirrors the CO values exactly so the BC should be balanced. Asserts:

- Lead's final review screen displays "is balanced" and NOT "not balanced".
- No JS console errors during the flow.

This is the most comprehensive test. If only one is run after a change, run this one.

```python
from playwright.sync_api import sync_playwright
with sync_playwright() as p:
    b=p.chromium.launch()
    ctx=b.new_context(viewport={'width':1320,'height':1200})
    pg=ctx.new_page()
    errs=[]
    pg.on('pageerror',lambda e: errs.append('PAGEERR: '+str(e)))
    pg.on('console',lambda m: errs.append('CONSOLE: '+m.text) if m.type=='error' else None)
    pg.goto('file:///mnt/user-data/outputs/transfer-hub-prototype.html')
    pg.wait_for_load_state('networkidle')
    pg.evaluate("""switchUser('jd'); contribs=[PEOPLE.find(p=>p.id==='om')]; go('step1');"""); pg.wait_for_timeout(60)
    pg.evaluate("""document.getElementById('inp-bcname').value='Grouped E2E'; saveAndNotifyCoPersons();"""); pg.wait_for_timeout(60)
    pg.evaluate("""
      switchUser('om');
      cc2Sel=[
        {code:'7300RND-CC-041',name:'Clinical Trials',type:'partial'},
        {code:'6200COM-CC-115',name:'Brand Marketing — Oncology',type:'partial'},
        {code:'6200COM-CC-116',name:'Brand Marketing — Immunology',type:'partial'},
        {code:'5110',name:'Platform Engineering',type:'partial'},
      ];
      coGlPicked=new Set(); coDetail={}; coDetailSeen=new Set();
      go('step3');
      toggleCoGl('7300RND-CC-041|5110-STAFF',true);
      toggleCoGl('6200COM-CC-115|6310-MKT',true);
      toggleCoGl('6200COM-CC-116|6320-MED',true);
      toggleCoGl('5110|5110-STAFF',true);
      go('step3b');
      go('step4'); go('step5'); submitToLead();
      switchUser('jd'); openLeadView('step6');
      costInPersons={};
      Object.keys(submittedBC.ccData).forEach(cc=>{costInPersons[cc]=[PEOPLE.find(p=>p.id==='lt')];});
      step6Proceed();
      switchUser('lt'); openCiFlow();
      Object.keys(submittedBC.costInPersons).forEach(out=>toggleCiInCc(out,'5130','Infrastructure',{stopPropagation(){}}));
      go('ci-step2');
      const bySource={};
      ciData.forEach(r=>{ (bySource[r.sourceCc]=bySource[r.sourceCc]||[]).push(r); });
      Object.entries(bySource).forEach(([src,rows])=>{
        const co=submittedBC.ccData[src]||[];
        rows.forEach((r,i)=>{ if(co[i]){ r.fy25=[...co[i].fy25]; r.fy26=[...co[i].fy26]; r.fy27=co[i].fy27; r.fy28=co[i].fy28; r.fy29=co[i].fy29; } });
      });
      const coFte={};
      (submittedBC.fteData||[]).forEach(r=>{(coFte[r.cc]=coFte[r.cc]||[]).push(r);});
      const ciFteBySrc={};
      ciFteData.forEach(r=>{ (ciFteBySrc[r.sourceCc]=ciFteBySrc[r.sourceCc]||[]).push(r); });
      Object.entries(ciFteBySrc).forEach(([src,rows])=>{
        const co=coFte[src]||[];
        rows.forEach((r,i)=>{ if(co[i]){ r.fy25=[...co[i].fy25]; r.fy26=[...co[i].fy26]; r.fy27=co[i].fy27; r.fy28=co[i].fy28; r.fy29=co[i].fy29; } });
      });
      submitCostIn();
      switchUser('jd'); openLeadView('step7');
    """); pg.wait_for_timeout(200)
    txt=pg.evaluate("document.body.innerText")
    print('balanced:', 'is balanced' in txt.lower(), 'not balanced:', 'not balanced' in txt.lower())
    print('errors:',errs[:5])
    b.close()
print("done")
```

**Expected output:**
```
balanced: True not balanced: False
errors: []
done
```

### 3. `uat_selection.py` — Detail screen bulk selection

Drives the row-click, shift-click, and header-checkbox patterns on the Cost Out Detail screen.

```python
from playwright.sync_api import sync_playwright
with sync_playwright() as p:
    b=p.chromium.launch()
    ctx=b.new_context(viewport={'width':1320,'height':1200})
    pg=ctx.new_page()
    errs=[]
    pg.on('pageerror',lambda e: errs.append('PE: '+str(e)))
    pg.on('console',lambda m: errs.append('CON: '+m.text) if m.type=='error' else None)
    pg.goto('file:///mnt/user-data/outputs/transfer-hub-prototype.html')
    pg.wait_for_load_state('networkidle')
    pg.evaluate("""
      switchUser('om');
      cc2Sel=[
        {code:'7300RND-CC-041',name:'Clinical Trials',type:'partial'},
        {code:'5110',name:'Platform Engineering',type:'partial'},
      ];
      coGlPicked=new Set(); coDetail={}; coDetailSeen=new Set(); coDetailSel=new Set(); coDetailLastSel={};
      go('step3');
      toggleCoGl('7300RND-CC-041|5110-STAFF',true);
      toggleCoGl('5110|5110-STAFF',true);
      go('step3b');
    """); pg.wait_for_timeout(150)
    total=pg.evaluate("Object.keys(coDetail).length")
    print(f'Total detail rows: {total} (expected 13 = 12 R&D + 1 IT)')

    # Row-click selection
    pg.evaluate("""
      const tr=document.querySelector('#co-detail-blocks tr[data-cod-row]');
      tr.click();
    """); pg.wait_for_timeout(60)
    print(f'After row-click on row 1: {pg.evaluate("coDetailSel.size")} selected (expected 1)')

    # Shift-click range
    pg.evaluate("""
      const rows=Array.from(document.querySelectorAll('#co-detail-blocks tr[data-cod-row]'));
      coDetailSel.clear(); coDetailLastSel={}; refreshCoDetailSelectionVisuals();
      rows[0].click();
      const evt=new MouseEvent('click',{shiftKey:true,bubbles:true,cancelable:true});
      rows[4].dispatchEvent(evt);
    """); pg.wait_for_timeout(60)
    print(f'After Shift+click row 5: {pg.evaluate("coDetailSel.size")} selected (expected 5)')

    # Header checkbox — select all in first block
    pg.evaluate("""
      coDetailSel.clear(); coDetailLastSel={}; refreshCoDetailSelectionVisuals();
      const hdrCb=document.querySelector('#co-detail-blocks thead .cosel-chk input[type=checkbox]');
      hdrCb.click();
    """); pg.wait_for_timeout(60)
    after_hdr=pg.evaluate("coDetailSel.size")
    rd_only=pg.evaluate("[...coDetailSel].every(k=>{const d=coDetail[k];return d&&d.cc==='7300RND-CC-041';})")
    print(f'After header-tick R&D: {after_hdr} selected (expected 12), all R&D-only: {rd_only}')

    # Checkbox shift-click
    pg.evaluate("""
      coDetailSel.clear(); coDetailLastSel={}; refreshCoDetailSelectionVisuals();
      const rowCbs=Array.from(document.querySelectorAll('#co-detail-blocks tr[data-cod-row] td.cosel-chk input[type=checkbox]'));
      rowCbs[0].click();
      const evt=new MouseEvent('click',{shiftKey:true,bubbles:true,cancelable:true});
      rowCbs[2].dispatchEvent(evt);
    """); pg.wait_for_timeout(60)
    print(f'After Shift+click checkbox row 3: {pg.evaluate("coDetailSel.size")} selected (expected 3)')

    # Clicking inside a row's input should NOT toggle the row
    pg.evaluate("""
      coDetailSel.clear(); coDetailLastSel={}; refreshCoDetailSelectionVisuals();
      const inp=document.querySelector('#co-detail-blocks tr[data-cod-row] td.cod-num input.cod-input');
      inp.click();
    """); pg.wait_for_timeout(60)
    print(f'After click on FY27 input: {pg.evaluate("coDetailSel.size")} selected (expected 0)')

    print('errors:',errs[:5])
    b.close()
print("done")
```

**Expected output:**
```
Total detail rows: 13 (expected 13 = 12 R&D + 1 IT)
After row-click on row 1: 1 selected (expected 1)
After Shift+click row 5: 5 selected (expected 5)
After header-tick R&D: 12 selected (expected 12), all R&D-only: True
After Shift+click checkbox row 3: 3 selected (expected 3)
After click on FY27 input: 0 selected (expected 0)
errors: []
done
```

### 4. `uat_cosel_selection.py` — Select screen bulk selection

Mirrors the same checks on the Cost Out Select screen (where ticking the box determines GL inclusion in the submission, rather than transient selection).

```python
from playwright.sync_api import sync_playwright
with sync_playwright() as p:
    b=p.chromium.launch()
    ctx=b.new_context(viewport={'width':1320,'height':1200})
    pg=ctx.new_page()
    errs=[]
    pg.on('pageerror',lambda e: errs.append('PE: '+str(e)))
    pg.on('console',lambda m: errs.append('CON: '+m.text) if m.type=='error' else None)
    pg.goto('file:///mnt/user-data/outputs/transfer-hub-prototype.html')
    pg.wait_for_load_state('networkidle')
    pg.evaluate("""
      switchUser('om');
      cc2Sel=[
        {code:'7300RND-CC-041',name:'Clinical Trials',type:'partial'},
        {code:'5110',name:'Platform Engineering',type:'partial'},
      ];
      coGlPicked=new Set(); coSelLastSel={};
      go('step3');
    """); pg.wait_for_timeout(150)
    print(f'Clickable rows on Select: {pg.evaluate("document.querySelectorAll(\\"#co-select-blocks tr[data-co-row]\\").length")} (Partial only)')

    # Row-click toggles tick
    pg.evaluate("document.querySelector('#co-select-blocks tr[data-co-row]').click()"); pg.wait_for_timeout(80)
    print(f'After row-click on row 1: {pg.evaluate("coGlPicked.size")} GL ticked (expected 1)')

    # Shift-click range
    pg.evaluate("""
      coGlPicked.clear(); coSelLastSel={}; renderCoSelect();
      const rows=Array.from(document.querySelectorAll('#co-select-blocks tr[data-co-row]'));
      rows[0].click();
    """); pg.wait_for_timeout(80)
    pg.evaluate("""
      const rows=Array.from(document.querySelectorAll('#co-select-blocks tr[data-co-row]'));
      const evt=new MouseEvent('click',{shiftKey:true,bubbles:true,cancelable:true});
      rows[3].dispatchEvent(evt);
    """); pg.wait_for_timeout(80)
    print(f'After Shift+click row 4: {pg.evaluate("coGlPicked.size")} GL ticked (expected 4)')

    # Header checkbox
    pg.evaluate("""
      coGlPicked.clear(); coSelLastSel={}; renderCoSelect();
      document.querySelector('#co-select-blocks thead .cosel-chk input[type=checkbox]:not([disabled])').click();
    """); pg.wait_for_timeout(80)
    print(f'After header-tick first block: {pg.evaluate("coGlPicked.size")} GLs ticked')

    print('errors:',errs[:5])
    b.close()
print("done")
```

**Expected output:**
```
Clickable rows on Select: 10 (Partial only)
After row-click on row 1: 1 GL ticked (expected 1)
After Shift+click row 4: 4 GL ticked (expected 4)
After header-tick first block: 5 GLs ticked
errors: []
done
```

### 5. `uat_uv_fte.py` — UV FTE allocation block

Sets up an R&D Cost Out, navigates to Review, checks the UV FTEs out block exists and the math sums correctly to the CC totals.

```python
from playwright.sync_api import sync_playwright
with sync_playwright() as p:
    b=p.chromium.launch()
    ctx=b.new_context(viewport={'width':1320,'height':1100})
    pg=ctx.new_page()
    errs=[]
    pg.on('pageerror',lambda e: errs.append('PE: '+str(e)))
    pg.on('console',lambda m: errs.append('CON: '+m.text) if m.type=='error' else None)
    pg.goto('file:///mnt/user-data/outputs/transfer-hub-prototype.html')
    pg.wait_for_load_state('networkidle')
    pg.evaluate("""
      switchUser('om');
      cc2Sel=[{code:'7300RND-CC-041',name:'Clinical Trials',type:'partial'}];
      coGlPicked=new Set(); coDetail={};
      go('step3'); toggleCoGl('7300RND-CC-041|5110-STAFF',true);
      go('step3b'); go('step4'); go('step5');
    """); pg.wait_for_timeout(300)
    wrap=pg.evaluate("""
      (() => {
        const w=document.getElementById('rv-uv-ftes-wrap');
        return {visible:w?.style.display!=='none',text:w?.innerText.slice(0,200)};
      })()
    """)
    print('UV FTE wrap visible:', wrap['visible'])
    print('Aggregate text:', wrap['text'])

    # Toggle expanded
    pg.evaluate("toggleRvUvFteRows();"); pg.wait_for_timeout(150)
    rows=pg.evaluate("""
      (() => Array.from(document.querySelectorAll('#rv-uv-ftes-table tbody tr')).map(
        tr => Array.from(tr.querySelectorAll('td')).map(c=>c.textContent.trim())
      ))()
    """)
    # Last row is Total FTE for CC; sum the rows above and confirm match
    if rows:
        total = rows[-1]
        # Sum FY26 (index 3 in CC row: Project, UV, FY25, FY26, FY27, FY28, FY29)
        fy26_sum = sum(float(r[3]) for r in rows[:-1] if len(r) > 3 and r[3] not in ('—', ''))
        fy26_total = float(total[3]) if len(total) > 3 else 0
        print(f'FY26 allocated sum: {fy26_sum:.1f} vs Total FTE for CC: {fy26_total:.1f}  -> match: {abs(fy26_sum - fy26_total) < 0.05}')
    print('errors:',errs[:5])
    b.close()
print("done")
```

**Expected output:** (numbers will vary based on seed data, but the `match: True` is the key assertion)
```
UV FTE wrap visible: True
Aggregate text: FY25 ▶	FY26 ▶	...
FY26 allocated sum: 35.5 vs Total FTE for CC: 35.5  -> match: True
errors: []
done
```

### 6. `uat_unified_cost_tables.py` — Flat unified cost tables

Asserts that on Lead step 6, every CC's Cost Out table is **flat** (no dept sub-grouping or collapse), uses the **unified columns** (`GL account · Product · Project · UV` + FY), renders **N/A** for columns a row's shape doesn't use, and shows values in **$m**. (Replaces the old `uat_dept_collapse.py`, which exercised the removed dept-collapse feature.)

```python
from pathlib import Path
PROTO = (Path(__file__).parent.parent / 'transfer-hub-prototype.html').resolve()
from playwright.sync_api import sync_playwright
with sync_playwright() as p:
    b=p.chromium.launch()
    ctx=b.new_context(viewport={'width':1400,'height':1100})
    pg=ctx.new_page()
    errs=[]
    pg.on('pageerror',lambda e: errs.append('PE: '+str(e)))
    pg.on('console',lambda m: errs.append('CON: '+m.text) if m.type=='error' else None)
    pg.goto(f'file://{PROTO}')
    pg.wait_for_load_state('networkidle')
    pg.evaluate("""
      switchUser('jd');
      contribs=[PEOPLE.find(p=>p.id==='om')];
      go('step1');
      document.getElementById('inp-bcname').value='Unified cost tables test';
      saveAndNotifyCoPersons();
      switchUser('om');
      cc2Sel=[
        {code:'7300RND-CC-041',name:'Clinical Trials',type:'partial'},
        {code:'6200COM-CC-115',name:'Brand Marketing — Oncology',type:'partial'},
        {code:'5110',name:'Platform Engineering',type:'partial'},
      ];
      coGlPicked=new Set(); coDetail={};
      go('step3');
      toggleCoGl('7300RND-CC-041|5110-STAFF',true);
      toggleCoGl('6200COM-CC-115|6310-MKT',true);
      toggleCoGl('5110|5110-STAFF',true);
      go('step3b'); go('step4'); go('step5'); submitToLead();
      switchUser('jd'); go('step6');
    """); pg.wait_for_timeout(400)

    state=pg.evaluate("""
      (() => {
        const wrap=document.getElementById('rv-by-cc-wrap');
        const tbl=wrap.querySelector('.rv-cc-block .rv-table');
        const heads=Array.from(tbl.querySelectorAll('thead tr:first-child th'))
          .map(h=>h.textContent.replace(/[▶▼].*/,'').trim()).filter(Boolean);
        return {
          expandBtns: wrap.querySelectorAll('.dept-expand-btn').length,
          collapsedBlocks: wrap.querySelectorAll('.dept-group-collapsed').length,
          headers: heads,
          naCells: wrap.querySelectorAll('.rv-cc-block .rv-table td.cod-na').length,
          dollarM: /\\d\\.\\d{2}/.test(tbl.innerText),
        };
      })()
    """)
    print('Lead step 6 Cost Out:', state)
    print('errors:',errs[:5])
    b.close()
print("done")
```

**Expected output:**
```
Lead step 6 Cost Out: {'expandBtns': 0, 'collapsedBlocks': 0, 'headers': ['GL account', 'Product', 'Project', 'UV', 'FY25', 'FY26', 'FY27', 'FY28', 'FY29'], 'naCells': 25, 'dollarM': True}
errors: []
done
```

### 7. `uat_paths_doc.py` — Path documentation smoke test

Loads the standalone path-docs HTML, verifies sections render, edit mode toggles correctly, and cancel restores state. Doesn't test persistent storage (depends on environment).

```python
from playwright.sync_api import sync_playwright
with sync_playwright() as p:
    b=p.chromium.launch()
    ctx=b.new_context(viewport={'width':1280,'height':1100})
    pg=ctx.new_page()
    errs=[]
    pg.on('pageerror',lambda e: errs.append('PE: '+str(e)))
    pg.on('console',lambda m: errs.append('CON: '+m.text) if m.type=='error' else None)
    pg.goto('file:///mnt/user-data/outputs/transfer-hub-paths.html')
    pg.wait_for_load_state('networkidle')
    pg.wait_for_timeout(300)

    diag=pg.evaluate("""
      (() => {
        const sections=Array.from(document.querySelectorAll('.editable[data-section]')).map(e=>e.dataset.section);
        return {
          editableSections: sections,
          pathCards: document.querySelectorAll('.path-card').length,
          matrixRows: document.querySelectorAll('.matrix tbody tr').length,
        };
      })()
    """)
    print('Sections:',diag['editableSections'])
    print(f'Path cards: {diag["pathCards"]} (expected 5)')
    print(f'Matrix rows: {diag["matrixRows"]} (expected 5)')

    # Edit mode toggle
    pg.click('#btn-edit'); pg.wait_for_timeout(100)
    s=pg.evaluate("""
      ({
        editMode: document.body.classList.contains('edit-mode'),
        anyEditable: document.querySelector('.editable').contentEditable === 'true',
      })
    """)
    print(f'After Edit click: {s}')

    pg.click('#btn-cancel'); pg.wait_for_timeout(100)
    s2=pg.evaluate("document.body.classList.contains('edit-mode')")
    print(f'After Cancel: editMode={s2}')

    print('errors:',errs[:5])
    b.close()
print("done")
```

**Expected output:**
```
Sections: ['dimensions', 'path-rnd-partial', 'path-rnd-full', 'path-smm-partial', 'path-it-partial', 'path-cross-cutting', 'open-questions']
Path cards: 5 (expected 5)
Matrix rows: 5 (expected 5)
After Edit click: {'editMode': True, 'anyEditable': True}
After Cancel: editMode=False
errors: []
done
```

---

## Notes on writing more UATs

A few patterns that have proven useful:

- **Always register `pageerror` and `console` error listeners** at the top of the test. They catch JS errors that would otherwise pass silently.
- **Use `pg.evaluate(...)` to drive state directly** — calling `cc2Sel = [...]; go('step3'); toggleCoGl(...)` is faster and more reliable than clicking through the UI.
- **`pg.wait_for_timeout(150)` after a state change** gives the renderers time to settle. 60ms is usually too short for cascading re-renders.
- **Take screenshots** with `pg.screenshot(path='/tmp/foo.png', full_page=True)` when debugging visual regressions. Don't commit them.
- **Set viewport explicitly** — different widths trigger different sticky behaviour. Most tests use `1320` or `1400` for desktop-ish layouts.

If you find a bug, write a UAT for it before fixing — that's how the suite stays useful.
