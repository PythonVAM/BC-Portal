from pathlib import Path
PROTO = (Path(__file__).parent.parent / 'transfer-hub-prototype.html').resolve()
from playwright.sync_api import sync_playwright

# The Cost In screens show a per-CC summary at the top: EVERY assigned CC gets a
# compact matrix whose "Cost Out" / "FTEs Out" row is clickable to reveal that CC's
# full flat detail inline (replacing the old separate Cost Out summary block). CCs
# with MORE THAN ONE Cost In Contributor additionally show a "… In (all)" row (this
# user's draft + others' submitted) and a Net row. Applies to cost (step 2), FTEs
# (step 3) and the Review & submit screen (step 4).
def norm(labels):
    return [l.lstrip('▶▼ ').strip() for l in labels]

with sync_playwright() as p:
    b=p.chromium.launch()
    pg=b.new_context(viewport={'width':1500,'height':1300}).new_page()
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
      // lt is assigned BOTH CCs: 7300RND is SHARED (lt + ds); 5110 is lt only (single)
      submittedBC.costInPersons={'7300RND-CC-041':[PEOPLE.find(p=>p.id==='lt'),PEOPLE.find(p=>p.id==='ds')],'5110':[PEOPLE.find(p=>p.id==='lt')]};
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
      return {present:!!el.innerText.trim(), ccs, labels,
              sepSummaryGone:!document.getElementById('ci-co-summary-table'),
              outIsClickable: !!el.querySelector('.s6-tr-out .s6-td-label[onclick]')};})()""")
    print('COST agg:', cost)

    # Expand 5110's Cost Out -> its detail table appears inline within the aggregate.
    pg.evaluate("toggleCoView('ciagg-co:5110')"); pg.wait_for_timeout(200)
    expanded=pg.evaluate("document.querySelectorAll('#ci-cc-agg-cost .rv-table').length")
    print('detail tables after expanding 5110:', expanded)

    pg.evaluate("go('ci-step3')"); pg.wait_for_timeout(300)
    fte=pg.evaluate("""(()=>{const el=document.getElementById('ci-cc-agg-fte');
      const ccs=[...el.querySelectorAll('.cc-badge-out')].map(x=>x.textContent.trim());
      const labels=[...el.querySelectorAll('.s6-td-label')].map(x=>x.textContent.trim());
      return {present:!!el.innerText.trim(), ccs, labels,
              sepFteSummaryGone:!document.getElementById('ci-fte-co-summary-table')};})()""")
    print('FTE agg:', fte)

    # Review & submit screen (step 4) shows both aggregates too (own -r4 element ids).
    pg.evaluate("ciActiveCcCode='7300RND-CC-041'; go('ci-step4')"); pg.wait_for_timeout(300)
    rev=pg.evaluate("""(()=>{
      const c=document.getElementById('ci-cc-agg-cost-r4'),f=document.getElementById('ci-cc-agg-fte-r4');
      const lbl=el=>el?[...el.querySelectorAll('.s6-td-label')].map(x=>x.textContent.trim()):[];
      return {costLabels:lbl(c), fteLabels:lbl(f)};})()""")
    print('REVIEW agg:', rev)

    cl, fl = norm(cost['labels']), norm(fte['labels'])
    ok = (cost['present'] and cost['sepSummaryGone'] and cost['outIsClickable']
          and set(cost['ccs'])=={'7300RND-CC-041','5110'}  # ALL assigned CCs shown
          # single-contributor 5110 -> only one Cost Out row; shared 7300RND -> Out/In/Net
          and cl==['Cost Out','Cost Out','Cost In (all)','Net cost']
          and expanded==1
          and fte['present'] and fte['sepFteSummaryGone'] and set(fte['ccs'])=={'7300RND-CC-041','5110'}
          and fl==['FTEs Out','FTEs Out','FTEs In (all)','Net FTEs']
          and norm(rev['costLabels'])==['Cost Out','Cost Out','Cost In (all)','Net cost']
          and norm(rev['fteLabels'])==['FTEs Out','FTEs Out','FTEs In (all)','Net FTEs']
          and not errs)
    print('PASS' if ok else 'FAIL')
    print('errors:', errs[:5])
    b.close()
print('done')
