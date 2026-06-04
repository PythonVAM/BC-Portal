from pathlib import Path
PROTO = (Path(__file__).parent.parent / 'transfer-hub-prototype.html').resolve()
from playwright.sync_api import sync_playwright
with sync_playwright() as p:
    b=p.chromium.launch()
    ctx=b.new_context(viewport={'width':1320,'height':1200})
    pg=ctx.new_page()
    errs=[]
    pg.on('pageerror',lambda e: errs.append('PE: '+str(e)))
    pg.on('console',lambda m: errs.append('CON: '+m.text) if m.type=='error' else None)
    pg.goto(f'file://{PROTO}')
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
