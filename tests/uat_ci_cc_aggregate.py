from pathlib import Path
PROTO = (Path(__file__).parent.parent / 'transfer-hub-prototype.html').resolve()
from playwright.sync_api import sync_playwright

# The One-side contributor's summary is ONE table for Cost and ONE for FTEs: a row
# per (Many) cost centre showing its FY totals, expandable to the full detail, plus
# a grand-total row. Appears on ci-step2 (cost), ci-step3 (FTEs) and the review
# screen ci-step4 (both, via the -r4 element ids).
with sync_playwright() as p:
    b=p.chromium.launch(); pg=b.new_context(viewport={'width':1500,'height':1300}).new_page()
    errs=[]; pg.on('pageerror',lambda e:errs.append('PE: '+str(e)))
    pg.goto(f'file://{PROTO}'); pg.wait_for_load_state('networkidle')
    pg.evaluate("""
      switchUser('jd'); contribs=[PEOPLE.find(p=>p.id==='om')];
      go('step1'); document.getElementById('inp-bcname').value='CC aggregate'; saveAndNotifyCoPersons();
      switchUser('om');
      cc2Sel=[{code:'7300RND-CC-041',name:'Clinical Trials',type:'partial'},{code:'5110',name:'Platform Eng',type:'partial'}];
      coGlPicked=new Set(); coDetail={}; coDetailSeen=new Set();
      go('step3'); toggleCoGl('7300RND-CC-041|5110-STAFF',true); toggleCoGl('5110|5110-STAFF',true);
      go('step3b'); go('step4');
      fteData=[{cc:'7300RND-CC-041',loc:'GB-LON-001',city:'London',country:'UK',azW:'Employee - Regular',wt:'Lab',fy25:Array(12).fill(2),fy26:Array(12).fill(2),fy27:2,fy28:0,fy29:0}];
      go('step5'); submitToLead();
      switchUser('jd'); openLeadView('step6');
      submittedBC.costInPersons={'7300RND-CC-041':[PEOPLE.find(p=>p.id==='lt')],'5110':[PEOPLE.find(p=>p.id==='lt')]};
      switchUser('lt'); openCiFlow(); go('ci-step2');
    """); pg.wait_for_timeout(400)

    def summary(el_id):
        return pg.evaluate(f"""(()=>{{const el=document.getElementById('{el_id}');if(!el)return null;
          return {{tables:el.querySelectorAll('table.s6-table').length,
                   ccRows:[...el.querySelectorAll('.s6-tr-out .cc-badge-out')].map(x=>x.textContent.trim()).sort(),
                   toggles:el.querySelectorAll('[onclick^="toggleCoView"]').length,
                   hasTotal:/Total — all cost centres/.test(el.innerText),
                   title:el.querySelector('div')?.textContent.trim().slice(0,30)}};}})()""")

    cost=summary('ci-cc-agg-cost'); print('COST:', cost)
    # Expand a CC row -> its detail table appears inline
    pg.evaluate("toggleCoView('ciagg-co:7300RND-CC-041')"); pg.wait_for_timeout(150)
    costDetail=pg.evaluate("document.querySelectorAll('#ci-cc-agg-cost .rv-table').length")
    print('cost detail tables after expand:', costDetail)

    pg.evaluate("go('ci-step3')"); pg.wait_for_timeout(300)
    fte=summary('ci-cc-agg-fte'); print('FTE:', fte)

    pg.evaluate("ciActiveCcCode='7300RND-CC-041'; go('ci-step4')"); pg.wait_for_timeout(300)
    r4c=summary('ci-cc-agg-cost-r4'); r4f=summary('ci-cc-agg-fte-r4')
    print('REVIEW cost:', r4c, '| fte:', r4f)

    ok = (cost and cost['tables']==1 and cost['ccRows']==['5110','7300RND-CC-041']
          and cost['toggles']==2 and cost['hasTotal'] and cost['title'].startswith('Cost out by cost centre')
          and costDetail==1
          and fte and fte['tables']==1 and fte['ccRows']==['5110','7300RND-CC-041'] and fte['hasTotal']
          and fte['title'].startswith('FTEs out by cost centre')
          and r4c and r4c['tables']==1 and r4c['hasTotal']
          and r4f and r4f['tables']==1 and r4f['hasTotal']
          and not errs)
    print('PASS' if ok else 'FAIL')
    print('errors:', errs[:5])
    b.close()
print('done')
