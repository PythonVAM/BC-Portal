from pathlib import Path
PROTO = (Path(__file__).parent.parent / 'transfer-hub-prototype.html').resolve()
from playwright.sync_api import sync_playwright

# Phase 2: the "One" side is exactly ONE cost centre that absorbs the entire Many
# side. ci-step1 shows a single picker (capped at 1, contributor-picked); choosing a
# CC mirrors every Many CC into it; submission is balance-gated (the One total must
# equal the Many total in every year).
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
      switchUser('lt'); openCiFlow(); go('ci-step1');
    """); pg.wait_for_timeout(300)

    npickers=pg.evaluate("document.querySelectorAll('#ci-by-cc-wrap [id^=\"ci-cc-hl-\"]').length")
    pg.evaluate("toggleCiInCc('__one__','5130','Infra',{stopPropagation(){}})"); pg.wait_for_timeout(120)
    after_pick=pg.evaluate("({one:getOneCc()&&getOneCc().code, srcs:Object.keys(ciInCcSel).sort()})")
    # pick a different CC -> replaces (still exactly one distinct One CC)
    pg.evaluate("toggleCiInCc('__one__','5120','Data',{stopPropagation(){}})"); pg.wait_for_timeout(120)
    after_replace=pg.evaluate("({one:getOneCc()&&getOneCc().code, distinct:[...new Set(Object.values(ciInCcSel).flat().map(x=>x.code))]})")
    pg.evaluate("go('ci-step2')"); pg.wait_for_timeout(250)
    seed=pg.evaluate("({rows:ciData.length>0, allToOne:ciData.every(r=>r.cc==='5120'), sources:[...new Set(ciData.map(r=>r.sourceCc))].sort()})")

    # Balanced submit (auto-mirror) proceeds; then unbalance -> blocked.
    pg.evaluate("go('ci-step4'); submitCostIn()"); pg.wait_for_timeout(120)
    balanced_screen=pg.evaluate("document.querySelector('.screen.active')?.id")
    pg.evaluate("submittedBC.status='ci-submitted'; ciData[0].fy27=(ciData[0].fy27||0)+5000000; go('ci-step4'); submitCostIn()"); pg.wait_for_timeout(120)
    blocked_screen=pg.evaluate("document.querySelector('.screen.active')?.id")

    print('pickers:', npickers, '| after_pick:', after_pick, '| after_replace:', after_replace)
    print('seed:', seed, '| balanced_screen:', balanced_screen, '| blocked_screen:', blocked_screen)
    print('dialogs:', [d[:40] for d in dialogs])

    ok = (npickers==1
          and after_pick['one']=='5130' and after_pick['srcs']==['5110','7300RND-CC-041']
          and after_replace['one']=='5120' and after_replace['distinct']==['5120']  # cap to one
          and seed['rows'] and seed['allToOne'] and seed['sources']==['5110','7300RND-CC-041']
          and balanced_screen=='screen-ci-confirmation'  # balanced submit went through
          and blocked_screen=='screen-ci-step4'           # unbalanced submit blocked
          and any("doesn't balance" in d for d in dialogs)
          and not errs)
    print('PASS' if ok else 'FAIL')
    print('errors:', errs[:5])
    b.close()
print('done')
