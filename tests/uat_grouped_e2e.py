from pathlib import Path
PROTO = (Path(__file__).parent.parent / 'transfer-hub-prototype.html').resolve()
from playwright.sync_api import sync_playwright
with sync_playwright() as p:
    b=p.chromium.launch()
    ctx=b.new_context(viewport={'width':1320,'height':1200})
    pg=ctx.new_page()
    errs=[]
    pg.on('pageerror',lambda e: errs.append('PAGEERR: '+str(e)))
    pg.on('console',lambda m: errs.append('CONSOLE: '+m.text) if m.type=='error' else None)
    pg.goto(f'file://{PROTO}')
    pg.wait_for_load_state('networkidle')
    pg.evaluate("""switchUser('jd'); contribs=[PEOPLE.find(p=>p.id==='om')]; go('step1');"""); pg.wait_for_timeout(60)
    pg.evaluate("""document.getElementById('inp-bcname').value='Grouped E2E'; saveAndNotifyCoPersons();"""); pg.wait_for_timeout(60)
    pg.evaluate("""
      switchUser('om');
      cc2Sel=[
        {code:'7300RND-CC-041',name:'Clinical Trials',type:'partial'},
        {code:'6200COM-CC-115',name:'Brand Marketing — Oncology',type:'partial'},
        {code:'6200COM-CC-116',name:'Brand Marketing — Immunology',type:'partial'},
        {code:'5110',name:'Platform Engineering',type:'partial'},
      ];
      coGlPicked=new Set(); coDetail={}; coDetailSeen=new Set();
      go('step3');
      toggleCoGl('7300RND-CC-041|5110-STAFF',true);
      toggleCoGl('6200COM-CC-115|6310-MKT',true);
      toggleCoGl('6200COM-CC-116|6320-MED',true);
      toggleCoGl('5110|5110-STAFF',true);
      go('step3b');
      go('step4'); go('step5'); submitToLead();
      switchUser('jd'); openLeadView('step6');
      costInPersons={};
      Object.keys(submittedBC.ccData).forEach(cc=>{costInPersons[cc]=[PEOPLE.find(p=>p.id==='lt')];});
      step6Proceed();
      switchUser('lt'); openCiFlow();
      Object.keys(submittedBC.costInPersons).forEach(out=>toggleCiInCc(out,'5130','Infrastructure',{stopPropagation(){}}));
      go('ci-step2');
      const bySource={};
      ciData.forEach(r=>{ (bySource[r.sourceCc]=bySource[r.sourceCc]||[]).push(r); });
      Object.entries(bySource).forEach(([src,rows])=>{
        const co=submittedBC.ccData[src]||[];
        rows.forEach((r,i)=>{ if(co[i]){ r.fy25=[...co[i].fy25]; r.fy26=[...co[i].fy26]; r.fy27=co[i].fy27; r.fy28=co[i].fy28; r.fy29=co[i].fy29; } });
      });
      const coFte={};
      (submittedBC.fteData||[]).forEach(r=>{(coFte[r.cc]=coFte[r.cc]||[]).push(r);});
      const ciFteBySrc={};
      ciFteData.forEach(r=>{ (ciFteBySrc[r.sourceCc]=ciFteBySrc[r.sourceCc]||[]).push(r); });
      Object.entries(ciFteBySrc).forEach(([src,rows])=>{
        const co=coFte[src]||[];
        rows.forEach((r,i)=>{ if(co[i]){ r.fy25=[...co[i].fy25]; r.fy26=[...co[i].fy26]; r.fy27=co[i].fy27; r.fy28=co[i].fy28; r.fy29=co[i].fy29; } });
      });
      submitCostIn();
      switchUser('jd'); openLeadView('step7');
    """); pg.wait_for_timeout(200)
    txt=pg.evaluate("document.body.innerText")
    print('balanced:', 'is balanced' in txt.lower(), 'not balanced:', 'not balanced' in txt.lower())
    print('errors:',errs[:5])
    b.close()
print("done")
