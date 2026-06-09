from pathlib import Path
PROTO = (Path(__file__).parent.parent / 'transfer-hub-prototype.html').resolve()
from playwright.sync_api import sync_playwright

# Phase 1b: when Cost In is the Many side, the One-side (ci-step*) bodies, the Lead
# step6/step7 and the CI per-CC aggregate all read in the correct direction — the
# Many side (stored in ccData) is labelled "Cost In" and the One side (ciData) is
# labelled "Cost Out". Driven end-to-end in IN mode; OUT mode left to uat_direction.
with sync_playwright() as p:
    b=p.chromium.launch(); pg=b.new_context(viewport={'width':1400,'height':1200}).new_page()
    errs=[]; pg.on('pageerror',lambda e:errs.append('PE: '+str(e)))
    pg.goto(f'file://{PROTO}'); pg.wait_for_load_state('networkidle')
    pg.evaluate("""
      switchUser('jd'); contribs=[PEOPLE.find(p=>p.id==='om')]; go('step1'); setBcManySide('in');
      document.getElementById('inp-bcname').value='IN E2E'; saveAndNotifyCoPersons();
      switchUser('om'); cc2Sel=[{code:'7300RND-CC-041',name:'CT',type:'partial'}];
      coGlPicked=new Set(); coDetail={}; coDetailSeen=new Set();
      go('step3'); toggleCoGl('7300RND-CC-041|5110-STAFF',true); go('step3b'); go('step4'); go('step5'); submitToLead();
      switchUser('jd'); openLeadView('step6');
      submittedBC.costInPersons={'7300RND-CC-041':[PEOPLE.find(p=>p.id==='lt'),PEOPLE.find(p=>p.id==='ds')]};
      const co=submittedBC.ccData['7300RND-CC-041']||[];
      ciResponses={}; ciResponses['ds::7300RND-CC-041']={person:PEOPLE.find(p=>p.id==='ds'),ccCode:'7300RND-CC-041',
        ciData:co.map(r=>({sourceCc:'7300RND-CC-041',gl:r.gl,prod:r.prod,fy25:(r.fy25||[]).map(v=>Math.round((v||0)/2)),fy26:(r.fy26||[]).map(v=>Math.round((v||0)/2)),fy27:Math.round((r.fy27||0)/2),fy28:Math.round((r.fy28||0)/2),fy29:Math.round((r.fy29||0)/2)}))};
      switchUser('lt'); openCiFlow(); go('ci-step1');
    """); pg.wait_for_timeout(400)

    # Receiver Cost screen (ci-step1). The summary shows the Many side (= Cost In when
    # In is the Many side), so its title reads "Cost in by cost centre".
    ci2=pg.evaluate("""(()=>{const s=document.getElementById('screen-ci-step1');
      const agg=document.getElementById('ci-cc-agg-cost').innerText;
      return {title:s.querySelector('.card-title').textContent.trim(),
              aggTitleCostIn:/Cost in by cost centre/i.test(agg)};})()""")
    print('CI1 (IN):', ci2)

    pg.evaluate("switchUser('jd'); openLeadView('step6')"); pg.wait_for_timeout(300)
    s6title=pg.evaluate("document.querySelector('#screen-step6 .card-title').textContent.trim()")
    pg.evaluate("openLeadView('step7')"); pg.wait_for_timeout(300)
    s7=pg.evaluate("[...document.querySelectorAll('#screen-step7 .s6-td-label')].map(x=>x.textContent.trim()).slice(0,6)")
    print('STEP6 title (IN):', s6title)
    print('STEP7 labels (IN):', s7)

    ok = (
        ci2['title']=='Cost'  # receiver screen uses a neutral title
        and ci2['aggTitleCostIn']
        and s6title=='Boundary change — Review Cost In · Assign Cost Out'
        and s7[:2]==['Cost In','Cost Out'] and 'FTEs In' in s7 and 'FTEs Out' in s7
        and not errs)
    print('PASS' if ok else 'FAIL')
    print('errors:', errs[:5])
    b.close()
print('done')
