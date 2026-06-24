from pathlib import Path
PROTO = (Path(__file__).parent.parent / 'transfer-hub-prototype.html').resolve()
from playwright.sync_api import sync_playwright

# CONCURRENT transfers: a BC holds N independent Many->One transfers, all live at once.
# All contributors are notified at setup (parallel), each works their own transfer in
# any order, the Lead assigns each transfer's Cost In person from the overview, and
# "Submit all to Group" unlocks only once every transfer balances.

def complete_transfer(pg, no, contributor, cc, gl, ci_person, one_cc):
    pg.evaluate(f"""
      // Contributor enters Cost Out for THEIR transfer (via the real openCoTask path)
      switchUser('{contributor}'); openCoTask({no});
      cc2Sel=[{{code:'{cc}',name:'X',type:'partial'}}];
      coGlPicked=new Set(); coDetail={{}}; coDetailSeen=new Set();
      go('step3'); toggleCoGl('{cc}|{gl}',true); go('step3b'); go('step4'); go('step5'); submitToLead();
      // Lead assigns the Cost In person for this transfer from the overview
      switchUser('jd'); openTransferReview({no},'step6');
      costInPersons={{'{cc}':[PEOPLE.find(p=>p.id==='{ci_person}')]}};
      submitToCiPersons();
      // Assigned Cost In person responds for this transfer
      switchUser('{ci_person}'); openCiFlow({no});
      toggleCiInCc('__one__','{one_cc}','One',{{stopPropagation(){{}}}});
      submitCostIn();
    """)

with sync_playwright() as p:
    b=p.chromium.launch(); pg=b.new_context(viewport={'width':1400,'height':1300}).new_page()
    errs=[]; pg.on('pageerror',lambda e:errs.append('PE: '+str(e)))
    dialogs=[]; pg.on('dialog',lambda d:(dialogs.append(d.message),d.accept()))
    pg.goto(f'file://{PROTO}'); pg.wait_for_load_state('networkidle')

    # Lead defines 2 transfers with DIFFERENT contributors, both Cost Out.
    pg.evaluate("""switchUser('jd');
      plannedTransfers=[{person:PEOPLE.find(p=>p.id==='om'),manySide:'out'},
                        {person:PEOPLE.find(p=>p.id==='lt'),manySide:'out'}];
      go('step1'); document.getElementById('inp-bcname').value='Parallel'; step1Next();""")
    seeded=pg.evaluate("({transfers:submittedBC.transfers.length, statuses:submittedBC.transfers.map(t=>t.status), people:submittedBC.transfers.map(t=>t.person.id)})")
    print('seeded:', seeded)

    # PARALLEL NOTIFICATION: both contributors see their task immediately.
    notif=pg.evaluate("""(()=>{
      switchUser('om'); go('dashboard'); const om=getCostOutTasks().length;
      switchUser('lt'); go('dashboard'); const lt=getCostOutTasks().length;
      return {om, lt};})()""")
    print('parallel notifications:', notif)

    # Complete transfer 2 FIRST (out of order) to prove independence, then transfer 1.
    complete_transfer(pg,2,'lt','5110','5110-STAFF','om','5140'); pg.wait_for_timeout(150)
    midway=pg.evaluate("({t1:submittedBC.transfers[0].status, t2:submittedBC.transfers[1].status, allBal:allTransfersBalanced()})")
    print('after transfer 2 only:', midway)

    complete_transfer(pg,1,'om','7300RND-CC-041','5110-STAFF','lt','5130'); pg.wait_for_timeout(150)
    done=pg.evaluate("({t1:submittedBC.transfers[0].status, t2:submittedBC.transfers[1].status, allBal:allTransfersBalanced(), overall:bcOverallStatus()})")
    print('after both transfers:', done)

    # Lead overview: Submit all to Group is now enabled; submit it.
    overview=pg.evaluate("""(()=>{switchUser('jd'); openBcOverview();
      const html=document.getElementById('bc-overview-content').innerHTML;
      return {rows:(html.match(/Transfer \\d+/g)||[]).length,
              submitEnabled:!/Submit all to Group<\\/button>/.test(html.replace(/ disabled[^>]*/,'')) ? true : !/disabled/.test(html.split('Submit all to Group')[0].slice(-120))};})()""")
    print('overview:', overview)

    submitted=pg.evaluate("""(()=>{submitAllToGroup();
      return {overall:bcOverallStatus(), statuses:submittedBC.transfers.map(t=>t.status),
              locked:submittedBC.status==='submitted-to-group'};})()""")
    print('after submit all:', submitted)

    ok = (seeded['transfers']==2 and seeded['statuses']==['awaiting-co','awaiting-co'] and seeded['people']==['om','lt']
          and notif['om']==1 and notif['lt']==1
          and midway['t2']=='ci-submitted' and midway['t1']=='awaiting-co' and not midway['allBal']
          and done['t1']=='ci-submitted' and done['t2']=='ci-submitted' and done['allBal'] and done['overall']=='ready-to-group'
          and submitted['overall']=='submitted-to-group' and submitted['statuses']==['submitted-to-group','submitted-to-group'] and submitted['locked']
          and not errs)
    print('PASS' if ok else 'FAIL')
    print('errors:', errs[:5]); print('dialogs:', dialogs[:5])
    b.close()
print('done')
