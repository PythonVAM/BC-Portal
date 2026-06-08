from pathlib import Path
PROTO = (Path(__file__).parent.parent / 'transfer-hub-prototype.html').resolve()
from playwright.sync_api import sync_playwright

# Regression for the per-contributor breakdown now folded into the Cost In summary
# (the old standalone "Other Cost In contributors" section was removed):
#  1) the summary lists only the current user's assigned CCs;
#  2) a shared CC's "Cost In (all)" row expands to a per-contributor split listing
#     only contributors who share THAT CC — not every CI contributor in the BC;
#  3) the breakdown starts collapsed and expands on click.
# Scenario: CC-X (7300RND-CC-041) -> lt + ds ; CC-Y (5110) -> fa. Viewed as lt
# (assigned to CC-X only), the split should show "You (draft)" + Daniel Stein and
# NOT Farah Ahmed (she's only on CC-Y, which lt isn't assigned to).
with sync_playwright() as p:
    b=p.chromium.launch()
    pg=b.new_context(viewport={'width':1400,'height':1100}).new_page()
    errs=[]
    pg.on('pageerror',lambda e: errs.append('PE: '+str(e)))
    pg.goto(f'file://{PROTO}')
    pg.wait_for_load_state('networkidle')
    pg.evaluate("""
      switchUser('jd'); contribs=[PEOPLE.find(p=>p.id==='om')];
      go('step1'); document.getElementById('inp-bcname').value='Others test'; saveAndNotifyCoPersons();
      switchUser('om');
      cc2Sel=[{code:'7300RND-CC-041',name:'X',type:'partial'},{code:'5110',name:'Y',type:'partial'}];
      ccData={}; fteData=[];
      ['7300RND-CC-041','5110'].forEach(c=>{ccData[c]=[{gl:'5110-STAFF',gln:'S',prod:'P',
        fy25:Array(12).fill(1000),fy26:Array(12).fill(1000),fy27:0,fy28:0,fy29:0}];});
      submitToLead();
      submittedBC.costInPersons={
        '7300RND-CC-041':[{...PEOPLE.find(p=>p.id==='lt')},{...PEOPLE.find(p=>p.id==='ds')}],
        '5110':[{...PEOPLE.find(p=>p.id==='fa')}]
      };
      switchUser('lt'); openCiFlow(); go('ci-step2');
    """); pg.wait_for_timeout(300)

    def snap():
        return pg.evaluate("""(()=>{
          const el=document.getElementById('ci-cc-agg-cost');
          const ccs=[...el.querySelectorAll('.cc-badge-out')].map(x=>x.textContent.trim());
          const inRow=el.querySelector('.s6-tr-in .s6-td-label');
          const txt=el.innerText;
          return {
            ccs,
            inCollapsed: inRow ? inRow.textContent.trim().startsWith('▶') : null,
            inExpanded: inRow ? inRow.textContent.trim().startsWith('▼') : null,
            hasYou: /You \\(draft\\)/.test(txt),
            hasDaniel: /Daniel Stein/.test(txt),
            hasFarah: /Farah Ahmed/.test(txt),
          };
        })()""")

    collapsed=snap()
    print('COLLAPSED (default):', collapsed)
    pg.evaluate("toggleCoView('ciagg-coin:7300RND-CC-041')"); pg.wait_for_timeout(150)
    expanded=snap()
    print('EXPANDED:', expanded)

    ok = (
        # only lt's assigned CC appears (CC-Y / 5110 excluded)
        collapsed['ccs']==['7300RND-CC-041']
        # breakdown collapsed by default — no contributor rows yet
        and collapsed['inCollapsed'] and not collapsed['hasDaniel'] and not collapsed['hasYou']
        # expanded shows You + the CC-sharing contributor (Daniel), never Farah
        and expanded['inExpanded'] and expanded['hasYou'] and expanded['hasDaniel']
        and not collapsed['hasFarah'] and not expanded['hasFarah']
        and not errs)
    print('PASS' if ok else 'FAIL')
    print('errors:', errs[:5])
    b.close()
print('done')
