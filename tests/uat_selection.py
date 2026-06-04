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
