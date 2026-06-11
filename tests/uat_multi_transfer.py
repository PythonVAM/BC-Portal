from pathlib import Path
PROTO = (Path(__file__).parent.parent / 'transfer-hub-prototype.html').resolve()
from playwright.sync_api import sync_playwright

# Step 1 lets the BC Lead define up to 5 transfers upfront, each = one contact + a
# Cost Out / Cost In direction (toggle next to the contact). "+ Add transfer" adds a
# block; capped at 5. Saving seeds submittedBC.plannedTransfers and activates the first.
with sync_playwright() as p:
    b=p.chromium.launch(); pg=b.new_context(viewport={'width':1300,'height':1100}).new_page()
    errs=[]; pg.on('pageerror',lambda e:errs.append('PE: '+str(e)))
    pg.goto(f'file://{PROTO}'); pg.wait_for_load_state('networkidle')
    pg.evaluate("switchUser('jd'); go('step1');"); pg.wait_for_timeout(150)
    init=pg.evaluate("({blocks:document.querySelectorAll('#transfer-blocks .contrib-panel').length, toggles:document.querySelectorAll('#transfer-blocks [onclick^=\"setTransferDir\"]').length})")
    # Fill block 0, add to 5, confirm cap
    pg.evaluate("setTransferPerson(0,'om'); setTransferDir(0,'out'); addTransferBlock(); setTransferPerson(1,'lt'); setTransferDir(1,'in'); addTransferBlock(); addTransferBlock(); addTransferBlock();")
    full=pg.evaluate("({blocks:document.querySelectorAll('#transfer-blocks .contrib-panel').length, addHidden:document.getElementById('add-transfer-btn').style.display==='none'})")
    pg.evaluate("addTransferBlock()")  # 6th ignored
    capped=pg.evaluate("plannedTransfers.length")
    # trim to 2 and save
    pg.evaluate("removeTransferBlock(4);removeTransferBlock(3);removeTransferBlock(2); document.getElementById('inp-bcname').value='MT'; step1Next();")
    bc=pg.evaluate("({total:submittedBC.totalTransfers, cur:submittedBC.currentTransferNo, dirs:submittedBC.plannedTransfers.map(t=>t.manySide), people:submittedBC.plannedTransfers.map(t=>t.person.id), active:submittedBC.contributors.map(p=>p.id), many:submittedBC.manySide, status:submittedBC.status})")
    print('init:',init,'| full:',full,'| capped:',capped,'| bc:',bc)
    ok = (init['blocks']==1 and init['toggles']==2
          and full['blocks']==5 and full['addHidden'] and capped==5
          and bc['total']==2 and bc['cur']==1 and bc['dirs']==['out','in'] and bc['people']==['om','lt']
          and bc['active']==['om'] and bc['many']=='out' and bc['status']=='awaiting-co'
          and not errs)
    print('PASS' if ok else 'FAIL'); print('errors:',errs[:5])
    b.close()
print('done')
