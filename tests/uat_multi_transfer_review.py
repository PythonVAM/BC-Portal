from pathlib import Path
PROTO = (Path(__file__).parent.parent / 'transfer-hub-prototype.html').resolve()
from playwright.sync_api import sync_playwright

# The BC Lead review aggregates ALL transfers together: step6 (Cost) / step6b (FTEs)
# show every transfer's Many side combined; the step7 pivot shows Out/In by SET area
# across all transfers (direction-aware).
def run(pg,cc,gl,oneCc):
    pg.evaluate(f"""
      switchUser('om'); cc2Sel=[{{code:'{cc}',name:'X',type:'partial'}}];
      coGlPicked=new Set(); coDetail={{}}; coDetailSeen=new Set();
      go('step3'); toggleCoGl('{cc}|{gl}',true); go('step3b'); go('step4'); go('step5'); submitToLead();
      switchUser('jd'); openLeadView('step6');
      submittedBC.costInPersons={{'{cc}':[PEOPLE.find(p=>p.id==='lt')]}};
      switchUser('lt'); openCiFlow(); toggleCiInCc('__one__','{oneCc}','One',{{stopPropagation(){{}}}});
      go('ci-step2'); submitCostIn(); switchUser('jd'); openLeadView('step7');
    """)
with sync_playwright() as p:
    b=p.chromium.launch(); pg=b.new_context(viewport={'width':1500,'height':1300}).new_page()
    errs=[]; pg.on('pageerror',lambda e:errs.append('PE: '+str(e))); pg.on('dialog',lambda d:d.accept())
    pg.goto(f'file://{PROTO}'); pg.wait_for_load_state('networkidle')
    pg.evaluate("""switchUser('jd');
      plannedTransfers=[{person:PEOPLE.find(p=>p.id==='om'),manySide:'out'},{person:PEOPLE.find(p=>p.id==='om'),manySide:'out'}];
      go('step1'); document.getElementById('inp-bcname').value='Agg'; step1Next();""")
    run(pg,'7300RND-CC-041','5110-STAFF','5130'); pg.wait_for_timeout(250)
    pg.evaluate("advanceToNextTransfer()"); pg.wait_for_timeout(150)
    run(pg,'5110','5110-STAFF','5140'); pg.wait_for_timeout(300)

    # step7 cost pivot Out side spans both source SET areas (7000 + 5000)
    s7=pg.evaluate("""(()=>{const s=document.getElementById('screen-step7');
      const cost=[...s.querySelectorAll('table.s6-table')][0];
      const subHdrs=[...cost.querySelectorAll('thead tr:nth-child(2) th')].map(x=>x.textContent.trim());
      return {areaSubHdrs:subHdrs, balanced:/is balanced/i.test(s.innerText), submitAll:/Submit all to Group/.test(s.innerText)};})()""")
    # step6 Cost (both transfers' Many CCs) and step6b FTEs
    pg.evaluate("openLeadView('step6'); setCiAggView('cost-lead','cc')"); pg.wait_for_timeout(200)
    s6cost=pg.evaluate("[...document.querySelectorAll('#s6-agg-cost .cc-badge-out')].map(x=>x.textContent.trim()).sort()")
    pg.evaluate("go('step6b'); setCiAggView('fte-lead','cc')"); pg.wait_for_timeout(200)
    s6fte=pg.evaluate("[...document.querySelectorAll('#s6-agg-fte .cc-badge-out')].map(x=>x.textContent.trim()).sort()")
    print('s7:',s7,'| s6cost:',s6cost,'| s6fte:',s6fte)

    ok = (s7['balanced'] and s7['submitAll']
          and any('7000' in h for h in s7['areaSubHdrs']) and any('5000' in h for h in s7['areaSubHdrs'])
          and s6cost==['5110','7300RND-CC-041']
          and '7300RND-CC-041' in s6fte and '5110' in s6fte
          and not errs)
    print('PASS' if ok else 'FAIL'); print('errors:',errs[:5])
    b.close()
print('done')
