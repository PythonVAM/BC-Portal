from pathlib import Path
PROTO = (Path(__file__).parent.parent / 'transfer-hub-prototype.html').resolve()
from playwright.sync_api import sync_playwright

# The read-only Cost Out AND FTE Out context views on the Lead (step 6/7) and
# Cost In (step 1/2/3) screens are collapsible: collapsed by default, showing a
# per-year totals row; expanding reveals the full flat table.
with sync_playwright() as p:
    b=p.chromium.launch()
    pg=b.new_context(viewport={'width':1500,'height':1100}).new_page()
    errs=[]
    pg.on('pageerror',lambda e: errs.append('PE: '+str(e)))
    pg.goto(f'file://{PROTO}')
    pg.wait_for_load_state('networkidle')
    pg.evaluate("""
      switchUser('jd'); contribs=[PEOPLE.find(p=>p.id==='om')];
      go('step1'); document.getElementById('inp-bcname').value='CO collapse'; saveAndNotifyCoPersons();
      switchUser('om');
      cc2Sel=[{code:'7300RND-CC-041',name:'A',type:'partial'},{code:'5110',name:'C',type:'partial'}];
      coGlPicked=new Set(); coDetail={}; coDetailSeen=new Set();
      go('step3'); toggleCoGl('7300RND-CC-041|5110-STAFF',true); toggleCoGl('5110|5110-STAFF',true);
      go('step3b'); go('step4');
      fteData=[{cc:'7300RND-CC-041',loc:'GB-LON-001',city:'London',country:'UK',azW:'Employee - Regular',wt:'Lab',fy25:Array(12).fill(1),fy26:Array(12).fill(1.5),fy27:2,fy28:0,fy29:0}];
      go('step5'); submitToLead();
      switchUser('jd'); openLeadView('step6');
      submittedBC.costInPersons={}; Object.keys(submittedBC.ccData).forEach(cc=>{submittedBC.costInPersons[cc]=[PEOPLE.find(p=>p.id==='lt')];});
      renderRvByCC();
    """); pg.wait_for_timeout(300)

    def toggles(screen):
        return pg.evaluate(f"""(()=>{{
          const s=document.getElementById('screen-{screen}');
          const t=Array.from(s.querySelectorAll('[onclick^="toggleCoView"]'));
          const co=t.filter(x=>!/FTEs/.test(x.textContent)), fte=t.filter(x=>/FTEs/.test(x.textContent));
          return {{n:t.length, collapsed:t.every(x=>x.textContent.trim().startsWith('▶')),
                   totals:/Cost out total/.test(s.innerText),
                   nFte:fte.length, fteTotals:/FTEs out total/.test(s.innerText)}};
        }})()""")

    # Step 6 now uses the shared Cost/FTE summary component (By SET Area / By cost
    # centre / Detail toggle), not per-view collapsibles. Verify the toggle + that
    # Detail shows the flat unified table (N/A cells).
    s6cost=pg.evaluate("[...document.querySelectorAll('#s6-agg-cost .method-btn')].map(x=>x.textContent.trim())")
    s6fte=pg.evaluate("[...document.querySelectorAll('#s6-agg-fte .method-btn')].map(x=>x.textContent.trim())")
    pg.evaluate("setCiAggView('cost-lead','area')"); pg.wait_for_timeout(150)
    s6area=pg.evaluate("(document.querySelector('#s6-agg-cost .rv-table thead th')?.textContent||'').includes('SET Area')")
    pg.evaluate("setCiAggView('cost-lead','detail')"); pg.wait_for_timeout(150)
    s6det=pg.evaluate("!!document.querySelector('#s6-agg-cost .rv-table td.cod-na')")
    print('STEP6 cost toggle:', s6cost, 'fte toggle:', s6fte, 'area header:', s6area, 'detail N/A cells:', s6det)

    # Step 7 is now two blocks (Cost, FTEs), each with a collapsed "By SET Area"
    # gate that reveals the per-area collapsible Cost Out / FTEs Out views.
    pg.evaluate("openLeadView('step7')"); pg.wait_for_timeout(300)
    s7gates=pg.evaluate("""[...document.querySelectorAll('#screen-step7 [onclick^="toggleCoView"]')].filter(x=>/By SET Area/.test(x.textContent)).map(x=>x.textContent.trim())""")
    pg.evaluate("""[...document.querySelectorAll('#screen-step7 [onclick^="toggleCoView"]')].filter(x=>/By SET Area/.test(x.textContent)).forEach(g=>g.click())""")
    pg.wait_for_timeout(250)
    s7=pg.evaluate("""(()=>{const s=document.getElementById('screen-step7');
      const t=[...s.querySelectorAll('[onclick^="toggleCoView"]')];
      const co=t.filter(x=>/Cost Out/.test(x.textContent));
      const fte=t.filter(x=>/FTEs Out/.test(x.textContent));
      return {coAreas:co.length, coCollapsed:co.every(x=>x.textContent.trim().startsWith('▶')), coTotals:/Cost out total/.test(s.innerText),
              fteAreas:fte.length, fteCollapsed:fte.every(x=>x.textContent.trim().startsWith('▶')), fteTotals:/FTEs out total/.test(s.innerText),
              twoMatrices:s.querySelectorAll('table.s6-table').length===2};})()""")
    print('STEP7 gates:', s7gates, '| areas:', s7)
    # Receiver flow: ci-step1 = Cost summary, ci-step2 = FTEs summary — each has the
    # By SET Area / By cost centre / Detail toggle (not per-CC collapsibles).
    pg.evaluate("switchUser('lt'); openCiFlow();"); pg.wait_for_timeout(200)
    c1=pg.evaluate("[...document.querySelectorAll('#screen-ci-step1 .method-btn')].map(x=>x.textContent.trim())"); print('CI1 toggle:', c1)
    pg.evaluate("go('ci-step2')"); pg.wait_for_timeout(200)
    c2=pg.evaluate("[...document.querySelectorAll('#screen-ci-step2 .method-btn')].map(x=>x.textContent.trim())"); print('CI2 toggle:', c2)

    ok = (s6cost==['By SET Area','By cost centre','Detail'] and s6fte==['By SET Area','By cost centre','Detail'] and s6area and s6det
          # Step 7: two aggregate matrices + collapsed By SET Area gates revealing
          # per-area Cost Out / FTEs Out views with per-year totals.
          and len(s7gates)==2 and all(g.startswith('▶') for g in s7gates) and s7['twoMatrices']
          and s7['coAreas']>=1 and s7['coCollapsed'] and s7['coTotals']
          and s7['fteAreas']>=1 and s7['fteCollapsed'] and s7['fteTotals']
          # Receiver Cost (ci-step1) + FTEs (ci-step2): SET Area / CC / Detail toggle.
          and c1==['By SET Area','By cost centre','Detail']
          and c2==['By SET Area','By cost centre','Detail']
          and not errs)
    print('PASS' if ok else 'FAIL')
    print('errors:', errs[:5])
    b.close()
print('done')
