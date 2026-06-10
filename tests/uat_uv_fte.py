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

    # Step 5 Cost/FTE summaries use the shared component (cost: USD/Local + By SET Area
    # / By cost centre / Detail; FTE: same minus currency), reading the contributor's
    # own live data via the '-co' scope.
    s5=pg.evaluate("""(()=>({
      cost:[...document.querySelectorAll('#rv-co-agg .method-btn')].map(x=>x.textContent.trim()),
      fte:[...document.querySelectorAll('#rv-fte-agg .method-btn')].map(x=>x.textContent.trim()),
      costHead:document.querySelector('#rv-co-agg .rv-table thead th')?.textContent.trim(),
    }))()""")
    print('STEP5 summaries:', s5)
    s5ok = (s5['cost']==['USD','Local','By SET Area','By cost centre','Detail']
            and s5['fte']==['By SET Area','By cost centre','Detail']
            and s5['costHead']=='MU')

    # Switch the UV block's own toggle to Detail (flat Project × UV rows).
    pg.evaluate("setUvFteView('co','detail');"); pg.wait_for_timeout(150)
    rows=pg.evaluate("""
      (() => Array.from(document.querySelectorAll('#rv-uv-ftes-table tbody tr')).map(
        tr => Array.from(tr.querySelectorAll('td')).map(c=>c.textContent.trim())
      ))()
    """)
    # Detail rows are MU · Cost centre · TA · Product · Project · UV · FY25..FY29
    # (FY26 at index 7); the last row is the grand total (colspan label · FY25..FY29,
    # FY26 at index 2). Summing the data rows' FY26 must match the total.
    match=True
    if rows:
        total = rows[-1]
        fy26_sum = sum(float(r[7]) for r in rows[:-1] if len(r) > 7 and r[7] not in ('—', ''))
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
    # The UV block has its OWN By TA / By UV / By cost centre / Detail toggle (no
    # expander, independent of the FTE summary's toggle). Default view = uv (TA + UV).
    lead=pg.evaluate("""(()=>{const sc=document.getElementById('screen-step6b');
      const wrap=document.getElementById('lead-uv-ftes-table');
      const toggle=[...wrap.querySelectorAll('.method-btn')].map(x=>x.textContent.trim());
      const heads=[...wrap.querySelectorAll('.rv-table thead tr:first-child th')].map(h=>h.textContent.replace(/[▶▼].*/,'').trim()).filter(Boolean).slice(0,2);
      return {hasUv:/UV FTEs out/.test(sc.innerText), toggle, heads, active:[...wrap.querySelectorAll('.method-btn.active')].map(x=>x.textContent.trim()), hasExpander:!!sc.querySelector('.rv-expand-btn')};})()""")
    pg.evaluate("setUvFteView('lead','ta')"); pg.wait_for_timeout(120)
    leadTa=pg.evaluate("(document.querySelector('#lead-uv-ftes-table .rv-table thead th')?.textContent||'').trim()")
    pg.evaluate("setUvFteView('lead','cc')"); pg.wait_for_timeout(120)
    leadCc=pg.evaluate("[...document.querySelectorAll('#lead-uv-ftes-table .rv-table thead tr:first-child th')].map(h=>h.textContent.replace(/[▶▼].*/,'').trim()).filter(Boolean).slice(0,2)")
    pg.evaluate("setUvFteView('lead','detail')"); pg.wait_for_timeout(120)
    leadDet=pg.evaluate("""(()=>{const tbl=document.getElementById('lead-uv-ftes-table').querySelector('.rv-table');
      const heads=[...tbl.querySelectorAll('thead tr:first-child th')].map(h=>h.textContent.replace(/[▶▼].*/,'').trim()).filter(Boolean).slice(0,6);
      return {heads, dataRows:tbl.querySelectorAll('tbody tr').length, totalRow:/Total — R&D cost centres/.test(tbl.innerText)};})()""")
    # Independence: flipping the FTE summary's toggle must NOT change the UV block.
    pg.evaluate("setCiAggView('fte-lead','area')"); pg.wait_for_timeout(150)
    uvUnchanged=pg.evaluate("[...document.querySelectorAll('#lead-uv-ftes-table .rv-table thead tr:first-child th')].map(h=>h.textContent.replace(/[▶▼].*/,'').trim()).filter(Boolean).slice(0,6)")
    print('LEAD step6b UV default:', lead, '| ta head:', leadTa, '| cc heads:', leadCc, '| detail:', leadDet, '| after FTE->area:', uvUnchanged)

    ok = (wrap['visible'] and match and s5ok
          # Lead UV block: own 4-way toggle, no expander, default By UV (TA + UV).
          and lead['hasUv'] and not lead['hasExpander']
          and lead['toggle']==['By TA','By UV','By cost centre','Detail'] and lead['active']==['By UV']
          and lead['heads']==['TA','UV']
          and leadTa=='TA'
          and leadCc==['MU','Cost centre']
          and leadDet['heads']==['MU','Cost centre','TA','Product','Project','UV'] and leadDet['dataRows']>1 and leadDet['totalRow']
          # FTE summary toggle did not change the UV block (still Detail columns).
          and uvUnchanged==['MU','Cost centre','TA','Product','Project','UV']
          and not errs)
    print('PASS' if ok else 'FAIL')
    print('errors:',errs[:5])
    b.close()
print("done")
