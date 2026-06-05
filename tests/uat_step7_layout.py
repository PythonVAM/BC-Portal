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
      Object.keys(submittedBC.costInPersons).forEach(out=>toggleCiInCc(out,'5130','Infrastructure',{stopPropagation(){}}));
      go('ci-step2');
      const bySource={}; ciData.forEach(r=>{(bySource[r.sourceCc]=bySource[r.sourceCc]||[]).push(r);});
      Object.entries(bySource).forEach(([src,rows])=>{const co=submittedBC.ccData[src]||[];rows.forEach((r,i)=>{if(co[i]){r.fy25=[...co[i].fy25];r.fy26=[...co[i].fy26];r.fy27=co[i].fy27;r.fy28=co[i].fy28;r.fy29=co[i].fy29;}});});
      const coFte={}; (submittedBC.fteData||[]).forEach(r=>{(coFte[r.cc]=coFte[r.cc]||[]).push(r);});
      const ciFteBySrc={}; ciFteData.forEach(r=>{(ciFteBySrc[r.sourceCc]=ciFteBySrc[r.sourceCc]||[]).push(r);});
      Object.entries(ciFteBySrc).forEach(([src,rows])=>{const co=coFte[src]||[];rows.forEach((r,i)=>{if(co[i]){r.fy25=[...co[i].fy25];r.fy26=[...co[i].fy26];r.fy27=co[i].fy27;r.fy28=co[i].fy28;r.fy29=co[i].fy29;}});});
      submitCostIn(); switchUser('jd'); openLeadView('step7');
    """); pg.wait_for_timeout(400)

    base=pg.evaluate("""(()=>{const s=document.getElementById('screen-step7');
      return {aggLabels:[...s.querySelectorAll('.s6-td-label')].map(x=>x.textContent.trim()),
              nMatrices:s.querySelectorAll('table.s6-table').length,
              gates:[...s.querySelectorAll('[onclick^="toggleCoView"]')].filter(x=>/By SET Area/.test(x.textContent)).length,
              balanced:/is balanced/i.test(s.innerText)};})()""")
    print('base:', base)

    # Expand the Cost "By SET Area" gate -> Source (Cost Out) + Destination (Cost In) areas
    pg.evaluate("""(()=>{const g=[...document.querySelectorAll('#screen-step7 [onclick^="toggleCoView"]')].find(x=>/By SET Area/.test(x.textContent)); g.click();})()""")
    pg.wait_for_timeout(200)
    drill=pg.evaluate("""(()=>{const s=document.getElementById('screen-step7');
      const txt=s.innerText;
      return {hasSourceLabel:/Cost Out — by source SET area/i.test(txt),
              hasDestLabel:/Cost In — by destination SET area/i.test(txt),
              areaCoToggles:[...s.querySelectorAll('[onclick^="toggleCoView"]')].filter(x=>/· Cost Out/.test(x.textContent)).length,
              areaCiToggles:[...s.querySelectorAll('[onclick^="toggleCoView"]')].filter(x=>/· Cost In/.test(x.textContent)).length};})()""")
    print('cost drill:', drill)
    # Expand one source area -> row detail (N/A cells appear)
    pg.evaluate("""(()=>{const t=[...document.querySelectorAll('#screen-step7 [onclick^="toggleCoView"]')].find(x=>/· Cost Out/.test(x.textContent)); t.click();})()""")
    pg.wait_for_timeout(200)
    rows=pg.evaluate("""!!document.querySelector('#screen-step7 .rv-table-wrap table.rv-table td.cod-na')""")
    print('source area expands to rows:', rows)

    ok = (base['aggLabels']==['Cost Out','Cost In','Net cost','FTEs Out','FTEs In','Net FTEs']
          and base['nMatrices']==2 and base['gates']==2 and base['balanced']
          and drill['hasSourceLabel'] and drill['hasDestLabel']
          and drill['areaCoToggles']>=1 and drill['areaCiToggles']>=1
          and rows and not errs)
    print('PASS' if ok else 'FAIL')
    print('errors:', errs[:5])
    b.close()
print('done')
