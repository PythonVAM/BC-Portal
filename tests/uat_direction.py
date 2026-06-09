from pathlib import Path
PROTO = (Path(__file__).parent.parent / 'transfer-hub-prototype.html').resolve()
from playwright.sync_api import sync_playwright

# Phase 1 of the Many->One revision: the BC Lead chooses which side has MANY cost
# centres at setup (submittedBC.manySide). The "Many" side reuses the Cost Out
# screens (step2-5) relabelled to the chosen direction; the "One" side reuses the
# Cost In screens (ci-step*) relabelled to the opposite direction. Step indicators,
# screen titles and the Many-side body microcopy all follow the choice. Default is
# 'out' (legacy behaviour unchanged).
def titles(pg):
    return pg.evaluate("""(()=>{const t=id=>document.querySelector(id+' .card-title')?.textContent.trim();
      return {step3:t('#screen-step3'),step4:t('#screen-step4'),step6:t('#screen-step6'),
              ci1:t('#screen-ci-step1'),ci3:t('#screen-ci-step3')};})()""")

with sync_playwright() as p:
    b=p.chromium.launch(); pg=b.new_context(viewport={'width':1400,'height':1100}).new_page()
    errs=[]; pg.on('pageerror',lambda e:errs.append('PE: '+str(e)))
    pg.goto(f'file://{PROTO}'); pg.wait_for_load_state('networkidle')

    # --- Direction OUT (default): unchanged legacy labelling ---
    pg.evaluate("""switchUser('jd'); contribs=[PEOPLE.find(p=>p.id==='om')]; go('step1');""")
    out1=pg.evaluate("({h:document.getElementById('step1-contrib-heading').textContent,outActive:document.getElementById('dir-btn-out').classList.contains('active')})")
    pg.evaluate("""document.getElementById('inp-bcname').value='OUT'; saveAndNotifyCoPersons();
      switchUser('om'); cc2Sel=[{code:'7300RND-CC-041',name:'CT',type:'partial'}];
      coGlPicked=new Set(); coDetail={}; coDetailSeen=new Set(); go('step3');""")
    out_si=pg.evaluate("[...document.querySelectorAll('#si-step3 .step-label')].map(x=>x.textContent)")
    out_t=titles(pg)
    out_body=pg.evaluate("/selecting Cost Out/.test(document.getElementById('screen-step3').innerText)")

    # --- Direction IN ---
    pg.evaluate("""submittedBC=null; switchUser('jd'); contribs=[PEOPLE.find(p=>p.id==='om')]; go('step1'); setBcManySide('in');""")
    in1=pg.evaluate("({h:document.getElementById('step1-contrib-heading').textContent,inActive:document.getElementById('dir-btn-in').classList.contains('active')})")
    pg.evaluate("""document.getElementById('inp-bcname').value='IN'; saveAndNotifyCoPersons();
      switchUser('om'); cc2Sel=[{code:'7300RND-CC-041',name:'CT',type:'partial'}];
      coGlPicked=new Set(); coDetail={}; coDetailSeen=new Set(); go('step3');""")
    in_si=pg.evaluate("[...document.querySelectorAll('#si-step3 .step-label')].map(x=>x.textContent)")
    in_t=titles(pg)
    in_body=pg.evaluate("({selIn:/selecting Cost In/.test(document.getElementById('screen-step3').innerText), noOut:!/Cost Out/.test(document.getElementById('screen-step3').innerText)})")
    stored=pg.evaluate("submittedBC.manySide")

    print('OUT:', out1, out_si, out_t, 'body:', out_body)
    print('IN :', in1, in_si, in_t, in_body, 'stored:', stored)

    ok = (
        # OUT: legacy labels intact
        out1['h']=='Cost Out Contributor(s)' and out1['outActive']
        and out_si[1]=='Cost out — select' and out_si[3]=='FTEs out'
        and out_t['step3']=='Cost Out task — Select cost to transfer'
        and out_t['step6']=='Boundary change — Review Cost Out · Assign Cost In'
        and out_t['ci1']=='Cost In — Boundary change request' and out_body
        # IN: Many side = Cost In; One side = Cost Out
        and in1['h']=='Cost In Contributor(s)' and in1['inActive']
        and in_si[1]=='Cost in — select' and in_si[3]=='FTEs in'
        and in_t['step3']=='Cost In task — Select cost to transfer'
        and in_t['step4']=='Cost In task — FTEs in'
        and in_t['step6']=='Boundary change — Review Cost In · Assign Cost Out'
        and in_t['ci1']=='Cost Out — Boundary change request'
        and in_t['ci3']=='Cost Out — FTEs out'
        and in_body['selIn'] and in_body['noOut'] and stored=='in'
        and not errs)
    print('PASS' if ok else 'FAIL')
    print('errors:', errs[:5])
    b.close()
print('done')
