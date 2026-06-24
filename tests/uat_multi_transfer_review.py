from pathlib import Path
PROTO = (Path(__file__).parent.parent / 'transfer-hub-prototype.html').resolve()
from playwright.sync_api import sync_playwright

# The BC Lead review aggregates ALL (concurrent) transfers together: step6 (Cost) /
# step6b (FTEs) show every transfer's Many side combined; the step7 pivot shows Out/In
# by SET area across all transfers (direction-aware). Submit-all unlocks once every
# transfer balances.
def complete_transfer(pg, no, contributor, cc, gl, ci_person, one_cc):
    pg.evaluate(f"""
      switchUser('{contributor}'); openCoTask({no});
      cc2Sel=[{{code:'{cc}',name:'X',type:'partial'}}];
      coGlPicked=new Set(); coDetail={{}}; coDetailSeen=new Set();
      go('step3'); toggleCoGl('{cc}|{gl}',true); go('step3b'); go('step4'); go('step5'); submitToLead();
      switchUser('jd'); openTransferReview({no},'step6');
      costInPersons={{'{cc}':[PEOPLE.find(p=>p.id==='{ci_person}')]}};
      submitToCiPersons();
      switchUser('{ci_person}'); openCiFlow({no});
      toggleCiInCc('__one__','{one_cc}','One',{{stopPropagation(){{}}}});
      submitCostIn();
    """)

with sync_playwright() as p:
    b=p.chromium.launch(); pg=b.new_context(viewport={'width':1500,'height':1300}).new_page()
    errs=[]; pg.on('pageerror',lambda e:errs.append('PE: '+str(e))); pg.on('dialog',lambda d:d.accept())
    pg.goto(f'file://{PROTO}'); pg.wait_for_load_state('networkidle')
    pg.evaluate("""switchUser('jd');
      plannedTransfers=[{person:PEOPLE.find(p=>p.id==='om'),manySide:'out'},{person:PEOPLE.find(p=>p.id==='om'),manySide:'out'}];
      go('step1'); document.getElementById('inp-bcname').value='Agg'; step1Next();""")
    # Two concurrent transfers (different SET areas on the Many side).
    complete_transfer(pg,1,'om','7300RND-CC-041','5110-STAFF','lt','5130'); pg.wait_for_timeout(200)
    complete_transfer(pg,2,'om','5110','5110-STAFF','lt','5140'); pg.wait_for_timeout(250)

    # Lead Summary (step7): cost pivot Out side spans both source SET areas (7000 + 5000)
    pg.evaluate("switchUser('jd'); openTransferReview(2,'step7')"); pg.wait_for_timeout(200)
    s7=pg.evaluate("""(()=>{const s=document.getElementById('screen-step7');
      const cost=[...s.querySelectorAll('table.s6-table')][0];
      const subHdrs=[...cost.querySelectorAll('thead tr:nth-child(2) th')].map(x=>x.textContent.trim());
      return {areaSubHdrs:subHdrs, balanced:/is balanced/i.test(s.innerText), submitAll:/Submit all to Group/.test(s.innerText), allBal:allTransfersBalanced()};})()""")
    # step6 Cost (both transfers' Many CCs) and step6b FTEs
    pg.evaluate("openLeadView('step6'); setCiAggView('cost-lead','cc')"); pg.wait_for_timeout(200)
    s6cost=pg.evaluate("[...document.querySelectorAll('#s6-agg-cost .cc-badge-out')].map(x=>x.textContent.trim()).sort()")
    pg.evaluate("go('step6b'); setCiAggView('fte-lead','cc')"); pg.wait_for_timeout(200)
    s6fte=pg.evaluate("[...document.querySelectorAll('#s6-agg-fte .cc-badge-out')].map(x=>x.textContent.trim()).sort()")
    print('s7:',s7,'| s6cost:',s6cost,'| s6fte:',s6fte)

    ok = (s7['balanced'] and s7['submitAll'] and s7['allBal']
          and any('7000' in h for h in s7['areaSubHdrs']) and any('5000' in h for h in s7['areaSubHdrs'])
          and s6cost==['5110','7300RND-CC-041']
          and '7300RND-CC-041' in s6fte and '5110' in s6fte
          and not errs)
    print('PASS' if ok else 'FAIL'); print('errors:',errs[:5])
    b.close()
print('done')
