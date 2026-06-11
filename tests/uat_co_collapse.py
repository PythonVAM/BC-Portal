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
      buildStep6();
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

    # The Lead's review is now a 3-screen flow (Cost = step6, FTEs = step6b, Summary
    # = step7), each using the shared Cost/FTE summary component (By SET Area / By cost
    # centre / Detail toggle). Cost lives on step6; FTEs on step6b. Verify the toggle +
    # that Detail shows the flat unified table (N/A cells).
    s6cost=pg.evaluate("[...document.querySelectorAll('#s6-agg-cost .method-btn')].map(x=>x.textContent.trim())")
    pg.evaluate("setCiAggView('cost-lead','area')"); pg.wait_for_timeout(150)
    s6area=pg.evaluate("(document.querySelector('#s6-agg-cost .rv-table thead th')?.textContent||'').includes('SET Area')")
    pg.evaluate("setCiAggView('cost-lead','detail')"); pg.wait_for_timeout(150)
    s6det=pg.evaluate("!!document.querySelector('#s6-agg-cost .rv-table td.cod-na')")
    pg.evaluate("go('step6b')"); pg.wait_for_timeout(150)
    s6fte=pg.evaluate("[...document.querySelectorAll('#s6-agg-fte .method-btn')].map(x=>x.textContent.trim())")
    print('STEP6 cost toggle:', s6cost, 'fte toggle:', s6fte, 'area header:', s6area, 'detail N/A cells:', s6det)

    # Step 7 is now two pivots (Cost, FTEs): columns = Out by SET area | In by SET
    # area | Net, for the selected year. A universal Year toggle + Dept/CC (cost) +
    # Normal/UV (fte); no By-SET-Area drill-down.
    pg.evaluate("openLeadView('step7')"); pg.wait_for_timeout(300)
    s7=pg.evaluate("""(()=>{const s=document.getElementById('screen-step7');
      const tbls=[...s.querySelectorAll('table.s6-table')];
      const h=t=>[...t.querySelectorAll('thead tr:first-child th')].map(x=>x.textContent.trim());
      return {twoTables:tbls.length===2, costHdr:h(tbls[0]), fteHdr:h(tbls[1]),
              years:[...s.querySelectorAll('[onclick^="setS7Year"]')].length,
              hasCostToggle:[...s.querySelectorAll('[onclick^="setS7CostRowBy"]')].length===2,
              noFteToggle:[...s.querySelectorAll(`[onclick^="setS7FteView"]`)].length===0,
              noDrill:[...s.querySelectorAll('[onclick^="toggleCoView"]')].length===0};})()""")
    print('STEP7 pivot:', s7)
    # Receiver flow: ci-step1 = Cost summary, ci-step2 = FTEs summary — each has the
    # By SET Area / By cost centre / Detail toggle (not per-CC collapsibles).
    pg.evaluate("switchUser('lt'); openCiFlow();"); pg.wait_for_timeout(200)
    c1=pg.evaluate("[...document.querySelectorAll('#screen-ci-step1 .method-btn')].map(x=>x.textContent.trim())"); print('CI1 toggle:', c1)
    pg.evaluate("go('ci-step2')"); pg.wait_for_timeout(200)
    c2=pg.evaluate("[...document.querySelectorAll('#screen-ci-step2 .method-btn')].map(x=>x.textContent.trim())"); print('CI2 toggle:', c2)

    ok = (s6cost==['USD','Local','By SET Area','By cost centre','Detail'] and s6fte==['By SET Area','By cost centre','Detail'] and s6area and s6det
          # Step 7: two Out|In|Net pivots with the year / dept-cc / normal-uv toggles
          # and no By-SET-Area drill-down.
          # (assign phase here, so no Cost In columns yet — just Out groups + Net)
          and s7['twoTables'] and s7['noDrill']
          and s7['costHdr'][0]=='Dept' and s7['costHdr'][-1]=='Net' and 'Cost Out' in s7['costHdr']
          and s7['fteHdr'][0]=='Location' and s7['fteHdr'][-1]=='Net' and 'FTEs Out' in s7['fteHdr']
          and s7['years']==5 and s7['hasCostToggle'] and s7['noFteToggle']
          # Receiver Cost (ci-step1) + FTEs (ci-step2): SET Area / CC / Detail toggle.
          and c1==['USD','Local','By SET Area','By cost centre','Detail']
          and c2==['By SET Area','By cost centre','Detail']
          and not errs)
    print('PASS' if ok else 'FAIL')
    print('errors:', errs[:5])
    b.close()
print('done')
