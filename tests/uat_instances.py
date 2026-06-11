from pathlib import Path
PROTO = (Path(__file__).parent.parent / 'transfer-hub-prototype.html').resolve()
from playwright.sync_api import sync_playwright

# A BC can hold up to 5 Many->One transfers, DEFINED UPFRONT at step 1 (each = a
# contact + direction). They auto-advance: once the active transfer balances the Lead
# clicks "Start next transfer" (advanceToNextTransfer), which archives the current one
# and activates the next planned transfer. Step 7 shows a combined summary and only
# offers "Submit all to Group" once every planned transfer is balanced.
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
    # Two transfers planned upfront (both Cost Out; same contact for the test).
    pg.evaluate("""switchUser('jd');
      plannedTransfers=[{person:PEOPLE.find(p=>p.id==='om'),manySide:'out'},{person:PEOPLE.find(p=>p.id==='om'),manySide:'out'}];
      go('step1'); document.getElementById('inp-bcname').value='Multi-transfer'; step1Next();""")

    run_instance(pg,'7300RND-CC-041','5110-STAFF','5130'); pg.wait_for_timeout(300)
    inst1=pg.evaluate("({balanced:activeInstanceBalanced(), cur:submittedBC.currentTransferNo, total:submittedBC.totalTransfers, archived:(submittedBC.archivedInstances||[]).length, hasNextBtn:/Start next transfer/.test(document.getElementById('screen-step7').innerText), submitDisabled:!!document.querySelector('#screen-step7 .btn-submit[disabled]')})")
    print('after transfer 1:', inst1)

    # "Start next transfer" archives the current one and activates planned transfer 2
    pg.evaluate("advanceToNextTransfer()"); pg.wait_for_timeout(150)
    afterAdd=pg.evaluate("({screen:document.querySelector('.screen.active')?.id, cur:submittedBC.currentTransferNo, archived:submittedBC.archivedInstances.length, ccDataEmpty:Object.keys(submittedBC.ccData).length===0})")
    print('after advance:', afterAdd)

    # Guard: advancing again before transfer 2 balances must be blocked
    blocked=pg.evaluate("(()=>{const n=submittedBC.archivedInstances.length; advanceToNextTransfer(); return submittedBC.archivedInstances.length===n;})()")
    print('advance-before-complete blocked:', blocked, '| dialog:', dialogs[-1][:50] if dialogs else None)

    run_instance(pg,'5110','5110-STAFF','5140'); pg.wait_for_timeout(300)
    inst2=pg.evaluate("""(()=>{const s=document.getElementById('screen-step7');
      return {balanced:activeInstanceBalanced(), instNo:submittedBC.instanceNo, archived:submittedBC.archivedInstances.length,
              banner:/Transfers in this boundary change — 2 total/.test(s.innerText),
              combined:/Combined \\(FY26\\)/.test(s.innerText),
              archivedOneCc:/Cost In 5130/.test(s.innerText),  // archived transfer's One CC resolves
              canSubmit:/Submit all to Group/.test(s.innerText)};})()""")
    print('after instance 2:', inst2)

    ok = (inst1['balanced'] and inst1['cur']==1 and inst1['total']==2 and inst1['archived']==0 and inst1['hasNextBtn'] and inst1['submitDisabled']
          and afterAdd['screen']=='screen-dashboard' and afterAdd['cur']==2 and afterAdd['archived']==1 and afterAdd['ccDataEmpty']
          and blocked and any('must be completed and balanced' in d for d in dialogs)
          and inst2['balanced'] and inst2['archived']==1 and inst2['banner'] and inst2['combined'] and inst2['archivedOneCc'] and inst2['canSubmit']
          and not errs)
    print('PASS' if ok else 'FAIL')
    print('errors:', errs[:5])
    b.close()
print('done')
