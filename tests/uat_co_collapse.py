from pathlib import Path
PROTO = (Path(__file__).parent.parent / 'transfer-hub-prototype.html').resolve()
from playwright.sync_api import sync_playwright

# The read-only Cost Out context views on the Lead (step 6/7) and Cost In (step
# 1/2/4) screens are collapsible: collapsed by default, showing a per-year totals
# row; expanding reveals the full flat unified table.
with sync_playwright() as p:
    b=p.chromium.launch()
    pg=b.new_context(viewport={'width':1500,'height':1100}).new_page()
    errs=[]
    pg.on('pageerror',lambda e: errs.append('PE: '+str(e)))
    pg.goto(f'file://{PROTO}')
    pg.wait_for_load_state('networkidle')
    pg.evaluate("""
      switchUser('jd'); contribs=[PEOPLE.find(p=>p.id==='om')];
      go('step1'); document.getElementById('inp-bcname').value='CO collapse'; saveAndNotifyCoPersons();
      switchUser('om');
      cc2Sel=[{code:'7300RND-CC-041',name:'A',type:'partial'},{code:'5110',name:'C',type:'partial'}];
      coGlPicked=new Set(); coDetail={}; coDetailSeen=new Set();
      go('step3'); toggleCoGl('7300RND-CC-041|5110-STAFF',true); toggleCoGl('5110|5110-STAFF',true);
      go('step3b'); go('step4'); go('step5'); submitToLead();
      switchUser('jd'); openLeadView('step6');
      submittedBC.costInPersons={}; Object.keys(submittedBC.ccData).forEach(cc=>{submittedBC.costInPersons[cc]=[PEOPLE.find(p=>p.id==='lt')];});
      renderRvByCC();
    """); pg.wait_for_timeout(300)

    def toggles(screen):
        return pg.evaluate(f"""(()=>{{
          const s=document.getElementById('screen-{screen}');
          const t=Array.from(s.querySelectorAll('[onclick^="toggleCoView"]'));
          return {{n:t.length, collapsed:t.every(x=>x.textContent.trim().startsWith('▶')),
                   totals:/Cost out total/.test(s.innerText)}};
        }})()""")

    s6=toggles('step6'); print('STEP6:', s6)
    # Expand the first step-6 CO view -> full rows (N/A cells) appear
    pg.evaluate("""document.querySelector('#screen-step6 [onclick^="toggleCoView"]').click()"""); pg.wait_for_timeout(150)
    s6exp=pg.evaluate("""(()=>{const blk=document.querySelector('#screen-step6 .rv-cc-block');
      return {glyph:blk.querySelector('[onclick^="toggleCoView"]').textContent.trim().slice(0,8),
              hasRows:!!blk.querySelector('.rv-table-wrap table.rv-table td.cod-na')};})()""")
    print('STEP6 expanded first:', s6exp)

    pg.evaluate("openLeadView('step7')"); pg.wait_for_timeout(300); s7=toggles('step7'); print('STEP7:', s7)
    pg.evaluate("switchUser('lt'); openCiFlow();"); pg.wait_for_timeout(200); c1=toggles('ci-step1'); print('CI1:', c1)
    pg.evaluate("go('ci-step2')"); pg.wait_for_timeout(200); c2=toggles('ci-step2'); print('CI2:', c2)

    ok = (s6['n']>=2 and s6['collapsed'] and s6['totals']
          and s6exp['glyph'].startswith('▼') and s6exp['hasRows']
          and s7['n']>=1 and s7['collapsed'] and s7['totals']
          and c1['n']>=2 and c1['collapsed'] and c1['totals']
          and c2['n']==1 and c2['collapsed'] and c2['totals']
          and not errs)
    print('PASS' if ok else 'FAIL')
    print('errors:', errs[:5])
    b.close()
print('done')
