from pathlib import Path
PROTO = (Path(__file__).parent.parent / 'transfer-hub-prototype.html').resolve()
from playwright.sync_api import sync_playwright
with sync_playwright() as p:
    b=p.chromium.launch()
    ctx=b.new_context(viewport={'width':1320,'height':1100})
    pg=ctx.new_page()
    errs=[]
    pg.on('pageerror',lambda e: errs.append('PE: '+str(e)))
    pg.on('console',lambda m: errs.append('CON: '+m.text) if m.type=='error' else None)
    pg.goto(f'file://{PROTO}')
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
