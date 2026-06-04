from pathlib import Path
PATHS = (Path(__file__).parent.parent / 'transfer-hub-paths.html').resolve()
from playwright.sync_api import sync_playwright
with sync_playwright() as p:
    b=p.chromium.launch()
    ctx=b.new_context(viewport={'width':1280,'height':1100})
    pg=ctx.new_page()
    errs=[]
    pg.on('pageerror',lambda e: errs.append('PE: '+str(e)))
    pg.on('console',lambda m: errs.append('CON: '+m.text) if m.type=='error' else None)
    pg.goto(f'file://{PATHS}')
    pg.wait_for_load_state('networkidle')
    pg.wait_for_timeout(300)

    diag=pg.evaluate("""
      (() => {
        const sections=Array.from(document.querySelectorAll('.editable[data-section]')).map(e=>e.dataset.section);
        return {
          editableSections: sections,
          pathCards: document.querySelectorAll('.path-card').length,
          matrixRows: document.querySelectorAll('.matrix tbody tr').length,
        };
      })()
    """)
    print('Sections:',diag['editableSections'])
    print(f'Path cards: {diag["pathCards"]} (expected 5)')
    print(f'Matrix rows: {diag["matrixRows"]} (expected 5)')

    # Edit mode toggle
    pg.click('#btn-edit'); pg.wait_for_timeout(100)
    s=pg.evaluate("""
      ({
        editMode: document.body.classList.contains('edit-mode'),
        anyEditable: document.querySelector('.editable').contentEditable === 'true',
      })
    """)
    print(f'After Edit click: {s}')

    pg.click('#btn-cancel'); pg.wait_for_timeout(100)
    s2=pg.evaluate("document.body.classList.contains('edit-mode')")
    print(f'After Cancel: editMode={s2}')

    print('errors:',errs[:5])
    b.close()
print("done")
