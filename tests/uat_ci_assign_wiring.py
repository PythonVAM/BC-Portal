from pathlib import Path
PROTO = (Path(__file__).parent.parent / 'transfer-hub-prototype.html').resolve()
from playwright.sync_api import sync_playwright

# In the Many->One model, step 6 has a SINGLE Cost In Contributor picker (the One
# side is one CC handled by one person). Assigning a person routes EVERY Many CC to
# that person; the picker is capped at one (search box disappears once assigned, a
# remove button clears it). Set-up: 3 Cost Out contributors submit several CCs.
with sync_playwright() as p:
    b=p.chromium.launch()
    pg=b.new_context(viewport={'width':1400,'height':1100}).new_page()
    errs=[]
    pg.on('pageerror',lambda e: errs.append('PE: '+str(e)))
    pg.goto(f'file://{PROTO}')
    pg.wait_for_load_state('networkidle')
    pg.evaluate("""
      switchUser('jd');
      contribs=[PEOPLE.find(p=>p.id==='om'),PEOPLE.find(p=>p.id==='lt'),PEOPLE.find(p=>p.id==='fa')];
      go('step1'); document.getElementById('inp-bcname').value='CI assign test'; saveAndNotifyCoPersons();
      function doCo(uid, sel){
        switchUser(uid); cc2Sel=JSON.parse(JSON.stringify(sel)); ccData={}; fteData=[];
        sel.forEach(c=>{ ccData[c.code]=[{gl:'5110-STAFF',gln:'S',prod:'X',
          fy25:Array(12).fill(1000),fy26:Array(12).fill(1000),fy27:0,fy28:0,fy29:0}]; });
        submitToLead();
      }
      doCo('om',[{code:'7300RND-CC-041',name:'A',type:'partial'},{code:'5110',name:'B',type:'full'}]);
      doCo('lt',[{code:'6200COM-CC-115',name:'C',type:'partial'},{code:'6200COM-CC-116',name:'D',type:'partial'}]);
      doCo('fa',[{code:'2110',name:'E',type:'full'}]);
      switchUser('jd'); openLeadView('step6');
    """); pg.wait_for_timeout(300)

    pre=pg.evaluate("""(()=>{
      const blocks=document.querySelectorAll('#screen-step6 .rv-cc-block').length;  // no per-CC blocks now
      const pickers=document.querySelectorAll('#screen-step6 input[id^="rv-ci-search-"]').length;  // no per-CC pickers
      const one=document.getElementById('rv-one-person-search');
      let ddWorks=false;
      if(one){one.dispatchEvent(new Event('focus')); const dd=document.getElementById('rv-one-person-dd'); ddWorks=!!(dd&&dd.style.display==='block');}
      return {blocks, pickers, hasSinglePicker:!!one, ddWorks};})()""")
    print('step6 structure:', pre)

    # Assign one person via the single picker -> routed to every Many CC.
    assign=pg.evaluate("""(()=>{
      const inp=document.getElementById('rv-one-person-search');
      inp.dispatchEvent(new Event('focus')); inp.value='a'; inp.dispatchEvent(new Event('input'));
      const dd=document.getElementById('rv-one-person-dd');
      const opt=dd.querySelector('.person-option'); if(opt) opt.dispatchEvent(new Event('mousedown'));
      const distinct=[...new Set(Object.values(costInPersons).flat().map(p=>p.id))];
      const ccsCovered=Object.keys(costInPersons).filter(k=>(costInPersons[k]||[]).length).sort();
      return {distinctPersons:distinct.length, ccsCovered,
              searchGone:!document.getElementById('rv-one-person-search'),
              showsAssigned:/Cost In Contributor/.test(document.getElementById('screen-step6').innerText)};})()""")
    print('after assign:', assign)

    # Remove clears the whole One-side assignment.
    cleared=pg.evaluate("""(()=>{clearOnePerson(); return {anyAssigned:Object.values(costInPersons).some(a=>a&&a.length), searchBack:!!document.getElementById('rv-one-person-search')};})()""")
    print('after clear:', cleared)

    ok = (pre['blocks']==0 and pre['pickers']==0 and pre['hasSinglePicker'] and pre['ddWorks']
          and assign['distinctPersons']==1
          and assign['ccsCovered']==['2110','5110','6200COM-CC-115','6200COM-CC-116','7300RND-CC-041']
          and assign['searchGone']
          and not cleared['anyAssigned'] and cleared['searchBack']
          and not errs)
    print('PASS' if ok else 'FAIL')
    print('errors:', errs[:5])
    b.close()
print('done')
