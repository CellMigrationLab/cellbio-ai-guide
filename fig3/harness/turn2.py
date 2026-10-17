"""Turn-2 script for a code run: first ```python block of the LAST hand-back of agent <id>; written to <dest>/script.py and queued."""
import json, re, sys, os, shutil
aid, src, dest, task = sys.argv[1:5]
T = '<tasks>/'
last = None
for l in open(T + aid + '.output'):
    try: d = json.loads(l)
    except Exception: continue
    for c in (d.get('message') or {}).get('content') or [] if d.get('type') == 'assistant' else []:
        if isinstance(c, dict) and c.get('type') == 'tool_use' and 'andback' in c.get('name', ''):
            last = '\n'.join(str(v) for v in c['input'].values())
b = re.findall(r'```python\s*\n(.*?)```', last or '', re.S)
if not b: sys.exit('no python block in last hand-back')
os.makedirs(dest, exist_ok=True)
img = 'dapi' if task == 'nuclei' else 'bf'
for f in [f'{img}.tif']: shutil.copy(f'{src}/{f}', f'{dest}/{f}')
open(f'{dest}/script.py', 'w').write(b[0])
open('queue.txt', 'a').write(f'{dest} {task} py\n')
print('queued', dest, len(b[0].splitlines()), 'lines')
