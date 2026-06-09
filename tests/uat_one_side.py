from pathlib import Path
PROTO = (Path(__file__).parent.parent / 'transfer-hub-prototype.html').resolve()
from playwright.sync_api import sync_playwright

# Phase 2 (+ receiver-flow): the "One" side is exactly ONE cost centre that absorbs
# the entire Many side. The receiver's Summary screen (ci-step3) has a single picker
# (capped at 1, contributor-picked); on submit the One side auto-mirrors every Many
# CC into the chosen CC and the balance gate passes.
with sync_playwright() as p:
    b=p.chromium.launch(); pg=b.new_context(viewport={'width':1400,'height':1200}).new_page()
    errs=[]; pg.on('pageerror',lambda e:errs.append('PE: '+str(e)))
    dialogs=[]; pg.on('dialog',lambda d:(dialogs.append(d.message),d.accept()))
    pg.goto(f'file://{PROTO}'); pg.wait_for_load_state('networkidle')
    pg.evaluate("""
      switchUser('jd'); contribs=[PEOPLE.find(p=>p.id==='om')]; go('step1');
      document.getElementById('inp-bcname').value='Phase2'; saveAndNotifyCoPersons();
      switchUser('om'); cc2Sel=[{code:'7300RND-CC-041',name:'CT',type:'partial'},{code:'5110',name:'Platform',type:'partial'}];
      coGlPicked=new Set(); coDetail={}; coDetailSeen=new Set();
      go('step3'); toggleCoGl('7300RND-CC-041|5110-STAFF',true); toggleCoGl('5110|5110-STAFF',true);
      go('step3b'); go('step4'); go('step5'); submitToLead();
      switchUser('jd'); openLeadView('step6');
      submittedBC.costInPersons={'7300RND-CC-041':[PEOPLE.find(p=>p.id==='lt')],'5110':[PEOPLE.find(p=>p.id==='lt')]};
      switchUser('lt'); openCiFlow(); go('ci-step3');
    """); pg.wait_for_timeout(300)

    npickers=pg.evaluate("document.querySelectorAll('#screen-ci-step3 [id^=\"ci-cc-hl-\"]').length")
    submitDisabledBefore=pg.evaluate("!!document.querySelector('#screen-ci-step3 .btn-submit[disabled]')")
    pg.evaluate("toggleCiInCc('__one__','5130','Infra',{stopPropagation(){}})"); pg.wait_for_timeout(120)
    after_pick=pg.evaluate("({one:getOneCc()&&getOneCc().code, srcs:Object.keys(ciInCcSel).sort(), submitDisabled:!!document.querySelector('#screen-ci-step3 .btn-submit[disabled]')})")
    # pick a different CC -> replaces (still exactly one distinct One CC)
    pg.evaluate("toggleCiInCc('__one__','5120','Data',{stopPropagation(){}})"); pg.wait_for_timeout(120)
    after_replace=pg.evaluate("({one:getOneCc()&&getOneCc().code, distinct:[...new Set(Object.values(ciInCcSel).flat().map(x=>x.code))]})")

    # Submit -> auto-mirror seeds ciData (all Many CCs into the one CC) and balances.
    pg.evaluate("submitCostIn()"); pg.wait_for_timeout(150)
    after_submit=pg.evaluate("({screen:document.querySelector('.screen.active')?.id, rows:ciData.length>0, allToOne:ciData.every(r=>r.cc==='5120'), sources:[...new Set(ciData.map(r=>r.sourceCc))].sort(), status:submittedBC.status})")

    print('pickers:', npickers, '| submitDisabledBefore:', submitDisabledBefore)
    print('after_pick:', after_pick, '| after_replace:', after_replace)
    print('after_submit:', after_submit)

    ok = (npickers==1 and submitDisabledBefore
          and after_pick['one']=='5130' and after_pick['srcs']==['5110','7300RND-CC-041'] and not after_pick['submitDisabled']
          and after_replace['one']=='5120' and after_replace['distinct']==['5120']  # cap to one
          and after_submit['screen']=='screen-ci-confirmation'
          and after_submit['rows'] and after_submit['allToOne'] and after_submit['sources']==['5110','7300RND-CC-041']
          and after_submit['status']=='ci-submitted'
          and not errs)
    print('PASS' if ok else 'FAIL')
    print('errors:', errs[:5])
    b.close()
print('done')
