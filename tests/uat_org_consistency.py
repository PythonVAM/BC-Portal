from pathlib import Path
PROTO = (Path(__file__).parent.parent / 'transfer-hub-prototype.html').resolve()
from playwright.sync_api import sync_playwright
with sync_playwright() as p:
    b=p.chromium.launch()
    pg=b.new_context(viewport={'width':1200,'height':900}).new_page()
    errs=[]
    pg.on('pageerror',lambda e: errs.append('PE: '+str(e)))
    pg.goto(f'file://{PROTO}')
    pg.wait_for_load_state('networkidle')

    d=pg.evaluate("""(() => {
      const tops=ccTree.children.map(c=>c.code);
      // Collect every leaf CC code in the tree.
      const leaves=[]; (function w(n){ if(n.leaf)leaves.push(n.code); (n.children||[]).forEach(w); })(ccTree);

      // 1) Every top-level SET area must be classified in both maps.
      const missingType=tops.filter(c=>!(c in SET_AREA_TYPE));
      const missingArea=tops.filter(c=>!(c in SET_AREAS));

      // 2) Every persona division should have a matching cost-centre dept in ccAttr,
      //    except 'Corporate Centre', which is the umbrella over Finance/HR.
      const personaDivs=[...new Set(Object.values(USER_PROFILES).map(u=>u.deptName))];
      const ccDepts=new Set(leaves.map(c=>gca(c).dept));
      const orphanDivs=personaDivs.filter(dn=>!ccDepts.has(dn) && dn!=='Corporate Centre');

      // 3) Every leaf CC must resolve to a real top-level SET area.
      const unresolved=leaves.filter(c=>ccSetArea(c).code==='?');

      return {
        topLevels:tops, missingType, missingArea, orphanDivs, unresolved,
        retailLeaves:leaves.filter(c=>gca(c).dept==='Retail Division'),
        riskLeaves:leaves.filter(c=>gca(c).dept==='Risk & Compliance'),
        commercialHasLead:Object.values(USER_PROFILES).some(u=>u.deptName==='Commercial'&&u.personaRole==='SET BC Lead'),
      };
    })()""")
    for k,v in d.items(): print(f'{k}: {v}')

    ok = (not d['missingType'] and not d['missingArea'] and not d['orphanDivs']
          and not d['unresolved'] and len(d['retailLeaves'])>0 and len(d['riskLeaves'])>0
          and d['commercialHasLead'] and not errs)
    print('PASS' if ok else 'FAIL')
    print('errors:', errs[:5])
    b.close()
print('done')
