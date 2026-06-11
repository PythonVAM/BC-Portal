from pathlib import Path
PROTO = (Path(__file__).parent.parent / 'transfer-hub-prototype.html').resolve()
from playwright.sync_api import sync_playwright

# Step 7 (Lead Review · Submit to Group) is two drill-down blocks — Cost and FTEs.
# Each shows an aggregate Out/In/Net matrix, then a collapsed "By SET Area" gate
# that reveals Cost/FTE Out by source area and Cost/FTE In by destination area,
# each collapsible to row detail. The balance check must still hold.
with sync_playwright() as p:
    b=p.chromium.launch()
    pg=b.new_context(viewport={'width':1500,'height':1300}).new_page()
    errs=[]
    pg.on('pageerror',lambda e: errs.append('PE: '+str(e)))
    pg.goto(f'file://{PROTO}')
    pg.wait_for_load_state('networkidle')
    pg.evaluate("""
      switchUser('jd'); contribs=[PEOPLE.find(p=>p.id==='om')];
      go('step1'); document.getElementById('inp-bcname').value='S7 layout'; saveAndNotifyCoPersons();
      switchUser('om');
      cc2Sel=[{code:'7300RND-CC-041',name:'A',type:'partial'},{code:'5110',name:'C',type:'partial'}];
      coGlPicked=new Set(); coDetail={}; coDetailSeen=new Set();
      go('step3'); toggleCoGl('7300RND-CC-041|5110-STAFF',true); toggleCoGl('5110|5110-STAFF',true);
      go('step3b'); go('step4');
      fteData=[{cc:'7300RND-CC-041',loc:'GB-LON-001',city:'London',country:'UK',azW:'Employee - Regular',wt:'Lab',fy25:Array(12).fill(1),fy26:Array(12).fill(1),fy27:1,fy28:0,fy29:0}];
      go('step5'); submitToLead();
      switchUser('jd'); openLeadView('step6');
      submittedBC.costInPersons={}; Object.keys(submittedBC.ccData).forEach(cc=>{submittedBC.costInPersons[cc]=[PEOPLE.find(p=>p.id==='lt')];});
      switchUser('lt'); openCiFlow();
      toggleCiInCc('__one__','5130','Infrastructure',{stopPropagation(){}});
      go('ci-step2');
      const bySource={}; ciData.forEach(r=>{(bySource[r.sourceCc]=bySource[r.sourceCc]||[]).push(r);});
      Object.entries(bySource).forEach(([src,rows])=>{const co=submittedBC.ccData[src]||[];rows.forEach((r,i)=>{if(co[i]){r.fy25=[...co[i].fy25];r.fy26=[...co[i].fy26];r.fy27=co[i].fy27;r.fy28=co[i].fy28;r.fy29=co[i].fy29;}});});
      const coFte={}; (submittedBC.fteData||[]).forEach(r=>{(coFte[r.cc]=coFte[r.cc]||[]).push(r);});
      const ciFteBySrc={}; ciFteData.forEach(r=>{(ciFteBySrc[r.sourceCc]=ciFteBySrc[r.sourceCc]||[]).push(r);});
      Object.entries(ciFteBySrc).forEach(([src,rows])=>{const co=coFte[src]||[];rows.forEach((r,i)=>{if(co[i]){r.fy25=[...co[i].fy25];r.fy26=[...co[i].fy26];r.fy27=co[i].fy27;r.fy28=co[i].fy28;r.fy29=co[i].fy29;}});});
      submitCostIn(); switchUser('jd'); openLeadView('step7');
    """); pg.wait_for_timeout(400)

    # Step 7 is now two pivots — Cost (rows = Dept | Cost centre) and FTEs (rows =
    # Location | TA) — columns = [Out by SET area | In by SET area | Net], for the
    # selected year. A universal Year toggle + Dept/CC (cost) + Normal/UV (fte). No
    # By-SET-Area drill-down (that's on the prior screens). Balance check stays.
    hdr1=lambda i: f"""[...document.querySelectorAll('#screen-step7 table.s6-table')][{i}].querySelectorAll('thead tr:first-child th')"""
    base=pg.evaluate("""(()=>{const s=document.getElementById('screen-step7');
      const tbls=[...s.querySelectorAll('table.s6-table')];
      const h=t=>[...t.querySelectorAll('thead tr:first-child th')].map(x=>x.textContent.trim());
      return {nTables:tbls.length, costHdr:h(tbls[0]), fteHdr:h(tbls[1]),
              years:[...s.querySelectorAll('[onclick^="setS7Year"]')].map(x=>x.textContent.trim()),
              costRowToggle:[...s.querySelectorAll('[onclick^="setS7CostRowBy"]')].map(x=>x.textContent.trim()),
              fteViewToggle:[...s.querySelectorAll('[onclick^="setS7FteView"]')].map(x=>x.textContent.trim()),
              noDrill:[...s.querySelectorAll('[onclick^="toggleCoView"]')].length===0,
              balanced:/is balanced/i.test(s.innerText)};})()""")
    print('base:', base)

    # Toggle Cost rows to cost centre, FTE to UV — row-dimension header changes.
    pg.evaluate("setS7CostRowBy('cc')"); pg.wait_for_timeout(120)
    costRowLbl=pg.evaluate(f"{hdr1(0)}[0].textContent.trim()")
    pg.evaluate("setS7FteView('uv')"); pg.wait_for_timeout(120)
    fteRowLbl=pg.evaluate(f"{hdr1(1)}[0].textContent.trim()")
    pg.evaluate("setS7Year('fy27')"); pg.wait_for_timeout(120)
    activeYear=pg.evaluate("[...document.querySelectorAll('#screen-step7 [onclick^=\"setS7Year\"].active')].map(x=>x.textContent.trim())")
    print('toggles -> cost row:', costRowLbl, '| fte row:', fteRowLbl, '| year:', activeYear)

    ok = (base['nTables']==2
          and base['costHdr']==['Dept','Cost Out','Cost In','Net']
          and base['fteHdr']==['Location','FTEs Out','FTEs In','Net']
          and base['years']==['FY25','FY26','FY27','FY28','FY29']
          and base['costRowToggle']==['By Dept','By cost centre']
          and base['fteViewToggle']==['Normal','UV view']
          and base['noDrill'] and base['balanced']
          and costRowLbl=='Cost centre' and fteRowLbl=='TA' and activeYear==['FY27']
          and not errs)
    print('PASS' if ok else 'FAIL')
    print('errors:', errs[:5])
    b.close()
print('done')
