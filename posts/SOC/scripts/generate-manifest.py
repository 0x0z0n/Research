from pathlib import Path
import json
root=Path('..').resolve()
cats={}
count=0
for p in root.rglob('*'):
    if p.is_file() and p.name not in ['manifest.json'] and '.github' not in p.parts and 'scripts' not in p.parts:
        rel=p.relative_to(root).as_posix()
        cat=p.parent.name if p.parent!=root else 'Root'
        cats.setdefault(cat,[]).append({'title':p.stem.replace('-',' ').title(),'description':'','path':rel})
        count+=1
json.dump({'file_count':count,'categories':cats},open(root/'manifest.json','w'),indent=2)
print(count)
