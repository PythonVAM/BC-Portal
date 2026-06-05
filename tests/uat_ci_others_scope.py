from pathlib import Path
PROTO = (Path(__file__).parent.parent / 'transfer-hub-prototype.html').resolve()
from playwright.sync_api import sync_playwright

# Regression for the "Other Cost In contributors" section on the CI screen:
#  1) it must list only contributors who share one of the current user's assigned
#     CCs (not every CI contributor in the boundary change);
#  2) it must start collapsed and expand on click.
# Scenario: CC-X (7300RND-CC-041) -> lt + ds ; CC-Y (5110) -> fa. Viewed as lt
# (assigned to CC-X only), the section should show ds and NOT fa.
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
          const el=document.getElementById('ci-others-wrap-cost');
          const title=el.querySelector('.ci-others-title').textContent.trim();
          const txt=el.innerText;
          return {
            collapsedGlyph: title.startsWith('▶'),
            expandedGlyph: title.startsWith('▼'),
            tableCount: el.querySelectorAll('table.ci-others-table').length,
            hasDaniel: /Daniel Stein/.test(txt),
            hasFarah: /Farah Ahmed/.test(txt),
            summaryOne: /1 other contributor/.test(title),
          };
        })()""")

    collapsed=snap()
    print('COLLAPSED (default):', collapsed)
    pg.evaluate("ciOthersCollapsed['cost']=false; renderCiOthersTable('cost')"); pg.wait_for_timeout(150)
    expanded=snap()
    print('EXPANDED:', expanded)

    ok = (collapsed['collapsedGlyph'] and collapsed['tableCount']==0 and collapsed['summaryOne']
          and expanded['expandedGlyph'] and expanded['tableCount']>0
          and expanded['hasDaniel'] and not expanded['hasFarah'] and not errs)
    print('PASS' if ok else 'FAIL')
    print('errors:', errs[:5])
    b.close()
print('done')
