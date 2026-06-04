from pathlib import Path
PROTO = (Path(__file__).parent.parent / 'transfer-hub-prototype.html').resolve()
from playwright.sync_api import sync_playwright
with sync_playwright() as p:
    b=p.chromium.launch()
    ctx=b.new_context(viewport={'width':1400,'height':1100})
    pg=ctx.new_page()
    errs=[]
    pg.on('pageerror',lambda e: errs.append('PE: '+str(e)))
    pg.on('console',lambda m: errs.append('CON: '+m.text) if m.type=='error' else None)
    pg.goto(f'file://{PROTO}')
    pg.wait_for_load_state('networkidle')
    pg.evaluate("""
      switchUser('jd');
      contribs=[PEOPLE.find(p=>p.id==='om')];
      go('step1');
      document.getElementById('inp-bcname').value='Dept collapse test';
      saveAndNotifyCoPersons();
      switchUser('om');
      cc2Sel=[
        {code:'7300RND-CC-041',name:'Clinical Trials',type:'partial'},
        {code:'6200COM-CC-115',name:'Brand Marketing — Oncology',type:'partial'},
        {code:'5110',name:'Platform Engineering',type:'partial'},
      ];
      coGlPicked=new Set(); coDetail={};
      go('step3');
      toggleCoGl('7300RND-CC-041|5110-STAFF',true);
      toggleCoGl('6200COM-CC-115|6310-MKT',true);
      toggleCoGl('5110|5110-STAFF',true);
      go('step3b'); go('step4'); go('step5'); submitToLead();
      switchUser('jd'); go('step6');
    """); pg.wait_for_timeout(400)

    initial=pg.evaluate("""
      (() => ({
        collapsedBlocks: document.querySelectorAll('.dept-group-collapsed').length,
        expandBtns: document.querySelectorAll('.dept-expand-btn').length,
        expState: ciDeptExp.size,
      }))()
    """)
    print('Initial Lead step 6 state:', initial)

    # Click expand on the first
    pg.evaluate("document.querySelector('.dept-group-collapsed .dept-expand-btn')?.click()"); pg.wait_for_timeout(120)
    after=pg.evaluate("""
      (() => ({
        collapsedBlocks: document.querySelectorAll('.dept-group-collapsed').length,
        expState: ciDeptExp.size,
      }))()
    """)
    print('After expanding first dept group:', after)
    print('errors:',errs[:5])
    b.close()
print("done")
