from pathlib import Path
PROTO = (Path(__file__).parent.parent / 'transfer-hub-prototype.html').resolve()
from playwright.sync_api import sync_playwright

# The receiver's Detail view has a per-column filter: each identity column header has
# a filter control; opening one shows a searchable value checklist; unchecking values
# filters the rows live, with an active-filter chip bar, a "showing N of M" count and
# a grand total over the filtered rows. The CC view has no per-column filters.
with sync_playwright() as p:
    b=p.chromium.launch(); pg=b.new_context(viewport={'width':1400,'height':1000}).new_page()
    errs=[]; pg.on('pageerror',lambda e:errs.append('PE: '+str(e)))
    pg.goto(f'file://{PROTO}'); pg.wait_for_load_state('networkidle')
    pg.evaluate("""
      switchUser('jd'); contribs=[PEOPLE.find(p=>p.id==='om')]; go('step1');
      document.getElementById('inp-bcname').value='Filters'; saveAndNotifyCoPersons();
      switchUser('om'); cc2Sel=[{code:'7400RND-CC-051',name:'Pre-clin',type:'partial'},{code:'5110',name:'Plat',type:'partial'}];
      coGlPicked=new Set(); coDetail={}; coDetailSeen=new Set();
      go('step3'); toggleCoGl('7400RND-CC-051|5110-STAFF',true); toggleCoGl('5110|5110-STAFF',true);
      go('step3b'); go('step4'); go('step5'); submitToLead();
      switchUser('jd'); openLeadView('step6'); setOnePerson('lt'); step6Proceed();
      switchUser('lt'); openCiFlow();
    """); pg.wait_for_timeout(300)

    def showing():
        return pg.evaluate("(document.querySelector('#ci-cc-agg-cost').innerText.match(/showing (\\d+) of (\\d+)/)||[]).slice(1)")

    ccFlt=pg.evaluate("document.querySelectorAll('#ci-cc-agg-cost tbody tr:first-child button').length")
    pg.evaluate("setCiAggView('cost','detail')"); pg.wait_for_timeout(150)
    detFlt=pg.evaluate("document.querySelectorAll('#ci-cc-agg-cost tbody tr:first-child button').length")
    init=showing()
    pg.evaluate("ciFilterOpenToggle('cost','uv')"); pg.wait_for_timeout(120)
    panel=pg.evaluate("""(()=>{const p=document.querySelector('.ci-fltpanel');return p?{title:p.querySelector('strong').textContent,hasSearch:!!p.querySelector('input'),opts:[...p.querySelectorAll('label')].map(l=>l.dataset.val)}:null;})()""")
    pg.evaluate("ciFilterToggleVal('cost','uv','Late')"); pg.wait_for_timeout(120)
    filtered=showing()
    eff=pg.evaluate("""(()=>{const e=document.querySelector('#ci-cc-agg-cost');
      return {noLate:![...e.querySelectorAll('tbody tr')].some(tr=>/\\bLate\\b/.test(tr.innerText)&&!/Total/.test(tr.innerText)),
               chip:/UV: 3/.test(e.innerText), totalFiltered:/Total — filtered/.test(e.innerText)};})()""")
    pg.evaluate("ciFilterClearAll('cost')"); pg.wait_for_timeout(120)
    cleared=showing()

    print('ccFlt:',ccFlt,'detFlt:',detFlt,'init:',init)
    print('panel:',panel)
    print('after Late off:',filtered,eff)
    print('cleared:',cleared)

    ok = (ccFlt==0 and detFlt==6
          and init==['13','13']
          and panel and panel['title']=='Filter: UV' and panel['hasSearch'] and 'Late' in panel['opts']
          and filtered==['9','13'] and eff['noLate'] and eff['chip'] and eff['totalFiltered']
          and cleared==['13','13']
          and not errs)
    print('PASS' if ok else 'FAIL')
    print('errors:', errs[:5])
    b.close()
print('done')
