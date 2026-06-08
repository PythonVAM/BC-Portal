from pathlib import Path
PROTO = (Path(__file__).parent.parent / 'transfer-hub-prototype.html').resolve()
from playwright.sync_api import sync_playwright

# When a source Cost Centre has MORE THAN ONE Cost In Contributor, the Cost In
# screens show a per-CC aggregate (Cost Out / Cost In (all) / Net), like the
# Lead's Step 7 matrix. CCs with a single contributor are not shown. The "Cost In
# (all)" total combines the current user's draft with other contributors' submitted
# values, and updates live. Applies to cost (step 2) and FTEs (step 3).
with sync_playwright() as p:
    b=p.chromium.launch()
    pg=b.new_context(viewport={'width':1500,'height':1200}).new_page()
    errs=[]
    pg.on('pageerror',lambda e: errs.append('PE: '+str(e)))
    pg.goto(f'file://{PROTO}')
    pg.wait_for_load_state('networkidle')
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
      // 7300RND has TWO CI contributors (lt + ds); 5110 has ONE (fa) -> only 7300RND should aggregate
      submittedBC.costInPersons={'7300RND-CC-041':[PEOPLE.find(p=>p.id==='lt'),PEOPLE.find(p=>p.id==='ds')],'5110':[PEOPLE.find(p=>p.id==='fa')]};
      // ds has submitted HALF of the Cost Out for 7300RND
      const co=submittedBC.ccData['7300RND-CC-041']||[];
      ciResponses={}; ciResponses['ds::7300RND-CC-041']={person:PEOPLE.find(p=>p.id==='ds'),ccCode:'7300RND-CC-041',
        ciData:co.map(r=>({sourceCc:'7300RND-CC-041',gl:r.gl,prod:r.prod,
          fy25:(r.fy25||[]).map(v=>Math.round((v||0)/2)),fy26:(r.fy26||[]).map(v=>Math.round((v||0)/2)),
          fy27:Math.round((r.fy27||0)/2),fy28:Math.round((r.fy28||0)/2),fy29:Math.round((r.fy29||0)/2)}))};
      switchUser('lt'); openCiFlow(); go('ci-step2');
    """); pg.wait_for_timeout(400)

    cost=pg.evaluate("""(()=>{const el=document.getElementById('ci-cc-agg-cost');
      const ccs=[...el.querySelectorAll('.cc-badge-out')].map(x=>x.textContent.trim());
      const labels=[...el.querySelectorAll('.s6-td-label')].map(x=>x.textContent.trim());
      return {present:!!el.innerText.trim(), ccs, labels, hasNetCost:labels.includes('Net cost')};})()""")
    print('COST agg:', cost)

    pg.evaluate("go('ci-step3')"); pg.wait_for_timeout(300)
    fte=pg.evaluate("""(()=>{const el=document.getElementById('ci-cc-agg-fte');
      const ccs=[...el.querySelectorAll('.cc-badge-out')].map(x=>x.textContent.trim());
      const labels=[...el.querySelectorAll('.s6-td-label')].map(x=>x.textContent.trim());
      return {present:!!el.innerText.trim(), ccs, labels};})()""")
    print('FTE agg:', fte)

    ok = (cost['present'] and cost['ccs']==['7300RND-CC-041']  # only the shared CC
          and cost['labels']==['Cost Out','Cost In (all)','Net cost']
          and '5110' not in cost['ccs']
          and fte['present'] and fte['ccs']==['7300RND-CC-041']
          and fte['labels']==['FTEs Out','FTEs In (all)','Net FTEs']
          and not errs)
    print('PASS' if ok else 'FAIL')
    print('errors:', errs[:5])
    b.close()
print('done')
