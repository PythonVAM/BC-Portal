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
    # Flat table now: data rows are MU · Cost centre · Project · UV · FY25..FY29
    # (FY26 at index 5); the last row is the grand total (colspan label · FY25..FY29,
    # FY26 at index 2). Summing the data rows' FY26 must match the total.
    match=True
    if rows:
        total = rows[-1]
        fy26_sum = sum(float(r[5]) for r in rows[:-1] if len(r) > 5 and r[5] not in ('—', ''))
        fy26_total = float(total[2]) if len(total) > 2 else 0
        match = abs(fy26_sum - fy26_total) < 0.05
        print(f'FY26 allocated sum: {fy26_sum:.1f} vs grand total: {fy26_total:.1f}  -> match: {match}')

    # The BC Lead's FTE screen (step6b) shows the same UV-allocated FTEs view when
    # R&D (gl+project+uv) CCs are in the BC — collapsed by default, expandable.
    pg.evaluate("""
      switchUser('jd'); contribs=[PEOPLE.find(p=>p.id==='om')]; go('step1');
      document.getElementById('inp-bcname').value='UV lead'; saveAndNotifyCoPersons();
      switchUser('om'); cc2Sel=[{code:'7300RND-CC-041',name:'CT',type:'partial'},{code:'5110',name:'Plat',type:'partial'}];
      coGlPicked=new Set(); coDetail={}; coDetailSeen=new Set();
      go('step3'); toggleCoGl('7300RND-CC-041|5110-STAFF',true); toggleCoGl('5110|5110-STAFF',true);
      go('step3b'); go('step4');
      fteData=[{cc:'7300RND-CC-041',loc:'GB-LON-001',city:'London',country:'UK',azW:'Employee - Regular',wt:'Lab',fy25:Array(12).fill(2),fy26:Array(12).fill(2),fy27:3,fy28:0,fy29:0}];
      go('step5'); submitToLead();
      switchUser('jd'); openLeadView('step6'); go('step6b');
    """); pg.wait_for_timeout(300)
    # The UV block follows the FTE summary's By SET Area / By cost centre / Detail
    # toggle (no separate Show rows expander). Default view = cc.
    lead=pg.evaluate("""(()=>{const sc=document.getElementById('screen-step6b');
      const hasUv=/UV FTEs out/.test(sc.innerText);
      const tbl=document.getElementById('lead-uv-ftes-table');
      const ccHeads=[...tbl.querySelectorAll('thead th')].map(h=>h.textContent.replace(/[▶▼].*/,'').trim()).filter(Boolean).slice(0,2);
      return {hasUv, ccHeads, ccRows:tbl.querySelectorAll('tbody tr').length, hasExpander:!!sc.querySelector('.rv-expand-btn')};})()""")
    pg.evaluate("setCiAggView('fte-lead','detail')"); pg.wait_for_timeout(150)
    leadDet=pg.evaluate("""(()=>{const tbl=document.getElementById('lead-uv-ftes-table');
      const heads=[...tbl.querySelectorAll('thead th')].map(h=>h.textContent.replace(/[▶▼].*/,'').trim()).filter(Boolean).slice(0,4);
      return {heads, dataRows:tbl.querySelectorAll('tbody tr').length, totalRow:/Total — R&D cost centres/.test(tbl.innerText)};})()""")
    pg.evaluate("setCiAggView('fte-lead','area')"); pg.wait_for_timeout(150)
    leadArea=pg.evaluate("(document.querySelector('#lead-uv-ftes-table thead th')?.textContent||'').includes('SET Area')")
    print('LEAD step6b UV cc:', lead, '| detail:', leadDet, '| area header:', leadArea)

    ok = (wrap['visible'] and match
          # Lead UV block follows the toggle, no expander.
          and lead['hasUv'] and not lead['hasExpander']
          and lead['ccHeads']==['MU','Cost centre'] and lead['ccRows']>=2
          and leadDet['heads']==['MU','Cost centre','Project','UV']
          and leadDet['dataRows']>1 and leadDet['totalRow'] and leadArea
          and not errs)
    print('PASS' if ok else 'FAIL')
    print('errors:',errs[:5])
    b.close()
print("done")
