from pathlib import Path
PROTO = (Path(__file__).parent.parent / 'transfer-hub-prototype.html').resolve()
from playwright.sync_api import sync_playwright

# On a MULTI-transfer BC, the Lead's combined Summary (step7) shows one Cost In
# Contributor picker PER TRANSFER — they assign a (different) receiver to each
# transfer separately. Single-transfer BCs keep the one global picker.
def submit_co(pg, no, contributor, cc, gl):
    pg.evaluate(f"""switchUser('{contributor}'); openCoTask({no});
      cc2Sel=[{{code:'{cc}',name:'X',type:'partial'}}]; coGlPicked=new Set(); coDetail={{}}; coDetailSeen=new Set();
      go('step3'); toggleCoGl('{cc}|{gl}',true); go('step3b'); go('step4'); go('step5'); submitToLead();""")

with sync_playwright() as p:
    b=p.chromium.launch(); pg=b.new_context(viewport={'width':1400,'height':1300}).new_page()
    errs=[]; pg.on('pageerror',lambda e:errs.append('PE: '+str(e))); pg.on('dialog',lambda d:d.accept())
    pg.goto(f'file://{PROTO}'); pg.wait_for_load_state('networkidle')

    # 2 transfers, different Cost Out contributors (Omar / Carlos).
    pg.evaluate("""switchUser('jd');
      plannedTransfers=[{person:PEOPLE.find(p=>p.id==='om'),manySide:'out'},
                        {person:PEOPLE.find(p=>p.id==='cb'),manySide:'out'}];
      go('step1'); document.getElementById('inp-bcname').value='PerTransferAssign'; step1Next();""")
    submit_co(pg,1,'om','7300RND-CC-041','5110-STAFF')
    submit_co(pg,2,'cb','5110','5110-STAFF')

    # Lead opens the combined Summary — expect a picker PER transfer, no single picker.
    pg.evaluate("switchUser('jd'); openTransferReview(1,'step7')"); pg.wait_for_timeout(200)
    structure=pg.evaluate("""(()=>{const s=document.getElementById('screen-step7');
      return {perTransferPickers:s.querySelectorAll('input[id^=\"ci-assign-search-\"]').length,
              singlePicker:!!document.getElementById('rv-one-person-search'),
              submitDisabled:!!s.querySelector('.btn-submit[disabled]')};})()""")
    print('summary structure:', structure)

    # Assign DIFFERENT receivers per transfer via the per-transfer pickers.
    pg.evaluate("assignTransferCiPerson(1,'lt'); assignTransferCiPerson(2,'pn');"); pg.wait_for_timeout(100)
    assigned=pg.evaluate("""({
      t1:[...new Set(Object.values(submittedBC.transfers[0].costInPersons).flat().map(p=>p.id))],
      t2:[...new Set(Object.values(submittedBC.transfers[1].costInPersons).flat().map(p=>p.id))]})""")
    print('assigned receivers:', assigned)

    # Each assigned receiver now sees ONLY their transfer's Cost In task.
    routing=pg.evaluate("""(()=>{
      switchUser('lt'); go('dashboard'); const lt=getCiIncoming().map(x=>x.transferNo);
      switchUser('pn'); go('dashboard'); const pn=getCiIncoming().map(x=>x.transferNo);
      return {lt, pn};})()""")
    print('CI routing:', routing)

    # Single-transfer BC still uses the one global picker (regression guard).
    single=pg.evaluate("""(()=>{switchUser('jd');
      plannedTransfers=[{person:null,manySide:'out'}]; contribs=[PEOPLE.find(p=>p.id==='om')];
      go('step1'); document.getElementById('inp-bcname').value='Single'; saveAndNotifyCoPersons();
      switchUser('om'); openCoTask(1); cc2Sel=[{code:'7300RND-CC-041',name:'A',type:'partial'}]; coGlPicked=new Set(); coDetail={}; coDetailSeen=new Set();
      go('step3'); toggleCoGl('7300RND-CC-041|5110-STAFF',true); go('step3b'); go('step4'); go('step5'); submitToLead();
      switchUser('jd'); openTransferReview(1,'step7');
      return {singlePicker:!!document.getElementById('rv-one-person-search'),
              perTransferPickers:document.querySelectorAll('#screen-step7 input[id^=\"ci-assign-search-\"]').length};})()""")
    print('single-transfer:', single)

    ok = (structure['perTransferPickers']==2 and not structure['singlePicker'] and structure['submitDisabled']
          and assigned['t1']==['lt'] and assigned['t2']==['pn']
          and routing['lt']==[1] and routing['pn']==[2]
          and single['singlePicker'] and single['perTransferPickers']==0
          and not errs)
    print('PASS' if ok else 'FAIL')
    print('errors:', errs[:5])
    b.close()
print('done')
