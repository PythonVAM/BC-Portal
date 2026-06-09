from pathlib import Path
PROTO = (Path(__file__).parent.parent / 'transfer-hub-prototype.html').resolve()
from playwright.sync_api import sync_playwright

# Phase 3: a BC can hold several Many->One transfers (instances). The Lead can
# "Add another transfer" only once the current one balances; completed instances are
# archived on submittedBC.archivedInstances and the working fields reset for the new
# one. Step 7 shows a combined summary and submits all instances to Group together.
def run_instance(pg, cc, gl, oneCc):
    pg.evaluate(f"""
      switchUser('om'); cc2Sel=[{{code:'{cc}',name:'X',type:'partial'}}];
      coGlPicked=new Set(); coDetail={{}}; coDetailSeen=new Set();
      go('step3'); toggleCoGl('{cc}|{gl}',true); go('step3b'); go('step4'); go('step5'); submitToLead();
      switchUser('jd'); openLeadView('step6');
      submittedBC.costInPersons={{'{cc}':[PEOPLE.find(p=>p.id==='lt')]}};
      switchUser('lt'); openCiFlow(); toggleCiInCc('__one__','{oneCc}','One',{{stopPropagation(){{}}}});
      go('ci-step2'); go('ci-step4'); submitCostIn();
      switchUser('jd'); openLeadView('step7');
    """)

with sync_playwright() as p:
    b=p.chromium.launch(); pg=b.new_context(viewport={'width':1400,'height':1300}).new_page()
    errs=[]; pg.on('pageerror',lambda e:errs.append('PE: '+str(e)))
    dialogs=[]; pg.on('dialog',lambda d:(dialogs.append(d.message),d.accept()))
    pg.goto(f'file://{PROTO}'); pg.wait_for_load_state('networkidle')
    pg.evaluate("""switchUser('jd'); contribs=[PEOPLE.find(p=>p.id==='om')]; go('step1');
      document.getElementById('inp-bcname').value='Multi-instance'; saveAndNotifyCoPersons();""")

    run_instance(pg,'7300RND-CC-041','5110-STAFF','5130'); pg.wait_for_timeout(300)
    inst1=pg.evaluate("({balanced:activeInstanceBalanced(), instNo:submittedBC.instanceNo, archived:(submittedBC.archivedInstances||[]).length, hasAddBtn:/Add another transfer/.test(document.getElementById('screen-step7').innerText)})")
    print('after instance 1:', inst1)

    # "Add another transfer" archives the current one and resets to step1
    pg.evaluate("addAnotherInstance()"); pg.wait_for_timeout(150)
    afterAdd=pg.evaluate("({screen:document.querySelector('.screen.active')?.id, instNo:submittedBC.instanceNo, archived:submittedBC.archivedInstances.length, ccDataEmpty:Object.keys(submittedBC.ccData).length===0})")
    print('after addAnother:', afterAdd)

    # Guard: trying to add a 3rd before instance 2 balances must be blocked
    pg.evaluate("contribs=[PEOPLE.find(p=>p.id==='om')]; saveAndNotifyCoPersons();"); pg.wait_for_timeout(100)
    blocked=pg.evaluate("(()=>{const n=submittedBC.archivedInstances.length; addAnotherInstance(); return submittedBC.archivedInstances.length===n;})()")
    print('add-before-complete blocked:', blocked, '| dialog:', dialogs[-1][:50] if dialogs else None)

    run_instance(pg,'5110','5110-STAFF','5140'); pg.wait_for_timeout(300)
    inst2=pg.evaluate("""(()=>{const s=document.getElementById('screen-step7');
      return {balanced:activeInstanceBalanced(), instNo:submittedBC.instanceNo, archived:submittedBC.archivedInstances.length,
              banner:/Transfers in this boundary change — 2 total/.test(s.innerText),
              combined:/Combined \\(FY26\\)/.test(s.innerText),
              canSubmit:/Submit all to Group/.test(s.innerText)};})()""")
    print('after instance 2:', inst2)

    ok = (inst1['balanced'] and inst1['instNo']==1 and inst1['archived']==0 and inst1['hasAddBtn']
          and afterAdd['screen']=='screen-step1' and afterAdd['instNo']==2 and afterAdd['archived']==1 and afterAdd['ccDataEmpty']
          and blocked and any('must be completed and balanced' in d for d in dialogs)
          and inst2['balanced'] and inst2['archived']==1 and inst2['banner'] and inst2['combined'] and inst2['canSubmit']
          and not errs)
    print('PASS' if ok else 'FAIL')
    print('errors:', errs[:5])
    b.close()
print('done')
