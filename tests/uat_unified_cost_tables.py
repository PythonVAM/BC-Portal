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

    # Step 6 Cost Out uses the shared summary component; switch to Detail to inspect
    # the underlying flat unified table.
    pg.evaluate("setCiAggView('cost-lead','detail')")
    pg.wait_for_timeout(200)

    # Lead step 6 Cost Out table should be FLAT (no dept collapse), unified columns
    # with a Cost centre + Dept column (multi-CC table), $m.
    state=pg.evaluate("""
      (() => {
        const wrap=document.getElementById('s6-agg-cost');
        const tbl=wrap.querySelector('.rv-table');
        const heads=Array.from(tbl.querySelectorAll('thead tr:first-child th'))
          .map(h=>h.textContent.replace(/[▶▼].*/,'').trim()).filter(Boolean);
        return {
          expandBtns: wrap.querySelectorAll('.dept-expand-btn').length,   // expect 0
          collapsedBlocks: wrap.querySelectorAll('.dept-group-collapsed').length, // expect 0
          headers: heads,                                                 // CC/Dept/GL/Product/Project/UV + FY
          naCells: wrap.querySelectorAll('.rv-table td.cod-na').length,   // > 0
          dollarM: /\\d\\.\\d{2}/.test(tbl.innerText),                    // $m formatting present
        };
      })()
    """)
    print('Lead step 6 Cost Out:', state)

    ok = (state['expandBtns']==0 and state['collapsedBlocks']==0
          and state['headers'][:8]==['Cost centre','Dept','MU','Curr','GL account','Product','Project','UV']
          and state['naCells']>0 and state['dollarM'])
    print('PASS' if ok and not errs else 'FAIL')
    print('errors:',errs[:5])
    b.close()
print("done")
