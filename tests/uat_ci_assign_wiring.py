from pathlib import Path
PROTO = (Path(__file__).parent.parent / 'transfer-hub-prototype.html').resolve()
from playwright.sync_api import sync_playwright

# Regression for the Cost-In assignment bug: on Lead step 6, every rendered CI
# person-picker must be wired and usable — even when the global cc2Sel doesn't
# carry every contributor's CC (the picker wiring keys off the rendered DOM, not
# cc2Sel). Mirrors the reported scenario: C1 = partial+full, C2 = 2 partial,
# C3 = 1 full; the C3 full-CC box used to be dead.
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
      // Force the divergence that triggered the original bug, then re-render.
      cc2Sel=cc2Sel.filter(c=>c.code!=='2110');
      renderRvByCC();
    """); pg.wait_for_timeout(300)

    # Every rendered CI box must open its dropdown on focus.
    boxes=pg.evaluate("""(()=>Array.from(document.querySelectorAll('input[id^="rv-ci-search-"]')).map(box=>{
      const code=box.id.replace('rv-ci-search-','');
      box.dispatchEvent(new Event('focus'));
      const dd=document.getElementById('rv-ci-dd-'+code);
      return {code, works:!!(dd&&dd.style.display==='block')};
    }))()""")
    print('CI search boxes:', boxes)

    # The 3rd contributor's full CC (2110) must accept an assignment end-to-end.
    assign=pg.evaluate("""(()=>{
      const code='2110', inp=document.getElementById('rv-ci-search-'+code);
      inp.dispatchEvent(new Event('focus')); inp.value='Carlos'; inp.dispatchEvent(new Event('input'));
      const dd=document.getElementById('rv-ci-dd-'+code);
      const opt=dd.querySelector('.person-option'); if(opt) opt.dispatchEvent(new Event('mousedown'));
      return (costInPersons[code]||[]).map(p=>p.first+' '+p.last);
    })()""")
    print('Assigned to 2110:', assign)

    ok = all(x['works'] for x in boxes) and assign==['Carlos Beltran'] and not errs
    print('PASS' if ok else 'FAIL')
    print('errors:', errs[:5])
    b.close()
print('done')
