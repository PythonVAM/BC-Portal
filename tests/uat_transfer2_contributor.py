from pathlib import Path
PROTO = (Path(__file__).parent.parent / 'transfer-hub-prototype.html').resolve()
from playwright.sync_api import sync_playwright

# Repro: Lead defines 2 transfers (same contact 'om' both, Cost Out). Complete + balance
# transfer 1, advance to transfer 2, then switch to the contributor and check whether the
# Cost Out task appears on their dashboard.
def do_co_and_balance(pg, cc, gl, oneCc):
    pg.evaluate(f"""
      switchUser('om'); cc2Sel=[{{code:'{cc}',name:'X',type:'partial'}}];
      coGlPicked=new Set(); coDetail={{}}; coDetailSeen=new Set();
      go('step3'); toggleCoGl('{cc}|{gl}',true); go('step3b'); go('step4'); go('step5'); submitToLead();
      switchUser('jd'); openLeadView('step6');
      submittedBC.costInPersons={{'{cc}':[PEOPLE.find(p=>p.id==='lt')]}};
      switchUser('lt'); openCiFlow(); toggleCiInCc('__one__','{oneCc}','One',{{stopPropagation(){{}}}});
      go('ci-step2'); go('ci-step4'); submitCostIn();
    """)

with sync_playwright() as p:
    b=p.chromium.launch(); pg=b.new_context(viewport={'width':1400,'height':1300}).new_page()
    errs=[]; pg.on('pageerror',lambda e:errs.append('PE: '+str(e)))
    dialogs=[]; pg.on('dialog',lambda d:(dialogs.append(d.message),d.accept()))
    pg.goto(f'file://{PROTO}'); pg.wait_for_load_state('networkidle')
    pg.evaluate("""switchUser('jd');
      plannedTransfers=[{person:PEOPLE.find(p=>p.id==='om'),manySide:'out'},{person:PEOPLE.find(p=>p.id==='om'),manySide:'out'}];
      go('step1'); document.getElementById('inp-bcname').value='MT'; step1Next();""")

    # Transfer 1 complete + balanced
    do_co_and_balance(pg,'7300RND-CC-041','5110-STAFF','5130'); pg.wait_for_timeout(200)

    # Lead advances to transfer 2
    pg.evaluate("switchUser('jd'); openLeadView('step7'); advanceToNextTransfer();"); pg.wait_for_timeout(150)

    state=pg.evaluate("""({
      cur:submittedBC.currentTransferNo,
      activeContribs:submittedBC.contributors.map(p=>p.id),
      coSubmissionsKeys:Object.keys(submittedBC.coSubmissions||{}),
      status:submittedBC.status
    })""")
    print('after advance:', state)

    # Switch to the transfer-2 contributor ('om') and check their dashboard task
    contribView=pg.evaluate("""(()=>{switchUser('om'); go('dashboard');
      return {coTasks:getCostOutTasks().length,
              dashHasTask:/Cost Out tasks assigned to you/.test(document.getElementById('dashboard-content').innerText)};})()""")
    print('contributor (om) view after advance:', contribView)

    ok = (state['cur']==2 and state['coSubmissionsKeys']==[] and state['status']=='awaiting-co'
          and contribView['coTasks']>=1 and contribView['dashHasTask'] and not errs)
    print('PASS' if ok else 'FAIL')
    print('errors:', errs[:5])
    b.close()
print('done')
