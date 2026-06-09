from pathlib import Path
PROTO = (Path(__file__).parent.parent / 'transfer-hub-prototype.html').resolve()
from playwright.sync_api import sync_playwright

# The One-side summary is scoped to the cost centres routed to THIS contributor —
# a Many CC assigned to a different Cost In Contributor must not appear in their
# summary. Scenario: CC-X (7300RND-CC-041) -> lt ; CC-Y (5110) -> fa. Viewed as lt,
# the summary shows only CC-X, not CC-Y.
with sync_playwright() as p:
    b=p.chromium.launch()
    pg=b.new_context(viewport={'width':1400,'height':1100}).new_page()
    errs=[]
    pg.on('pageerror',lambda e: errs.append('PE: '+str(e)))
    pg.goto(f'file://{PROTO}')
    pg.wait_for_load_state('networkidle')
    pg.evaluate("""
      switchUser('jd'); contribs=[PEOPLE.find(p=>p.id==='om')];
      go('step1'); document.getElementById('inp-bcname').value='Scope test'; saveAndNotifyCoPersons();
      switchUser('om');
      cc2Sel=[{code:'7300RND-CC-041',name:'X',type:'partial'},{code:'5110',name:'Y',type:'partial'}];
      ccData={}; fteData=[];
      ['7300RND-CC-041','5110'].forEach(c=>{ccData[c]=[{gl:'5110-STAFF',gln:'S',prod:'P',
        fy25:Array(12).fill(1000),fy26:Array(12).fill(1000),fy27:0,fy28:0,fy29:0}];});
      submitToLead();
      submittedBC.costInPersons={
        '7300RND-CC-041':[{...PEOPLE.find(p=>p.id==='lt')}],
        '5110':[{...PEOPLE.find(p=>p.id==='fa')}]
      };
      switchUser('lt'); openCiFlow(); go('ci-step1');
    """); pg.wait_for_timeout(300)

    snap=pg.evaluate("""(()=>{const el=document.getElementById('ci-cc-agg-cost');
      const ccs=[...el.querySelectorAll('.cc-badge-out')].map(x=>x.textContent.trim());
      return {ccs, hasX:ccs.includes('7300RND-CC-041'), hasY:ccs.includes('5110'), tables:el.querySelectorAll('table.rv-table').length};})()""")
    print('lt summary:', snap)

    ok = (snap['tables']==1 and snap['hasX'] and not snap['hasY'] and snap['ccs']==['7300RND-CC-041'] and not errs)
    print('PASS' if ok else 'FAIL')
    print('errors:', errs[:5])
    b.close()
print('done')
