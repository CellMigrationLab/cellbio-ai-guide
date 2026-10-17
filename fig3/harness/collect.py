"""For each finished run: pull the reply text (all assistant text of the subagent transcript, verbatim) and the code
blocks; save replies/<name>.txt and <name>/script.py or <name>/macro.ijm; append to queue.txt. Idempotent."""
import json, re, os, sys
T = '<tasks>/'
os.makedirs('replies', exist_ok=True)
queued = set(open('queue.txt').read().split('\n')) if os.path.exists('queue.txt') else set()
for line in open('ids.txt'):
    line = line.strip()
    if not line: continue
    aid, rest = line.split('='); name, kind = rest.split()
    task = name.split('_')[-2]
    qline = f'{name} {task} {kind}'
    if qline in queued: continue
    p = T + aid + '.output'
    if not os.path.exists(p): continue
    texts, done = [], False
    for l in open(p):
        try: e = json.loads(l)
        except Exception: continue
        m = e.get('message') or {}
        for c in (m.get('content') or []) if e.get('type') == 'assistant' else []:
            if isinstance(c, dict) and c.get('type') == 'text': texts.append(c['text'])
            if isinstance(c, dict) and c.get('type') == 'tool_use' and 'andback' in c.get('name', ''):
                done = True; texts.append(json.dumps(c.get('input'))[:0] + '\n'.join(str(v) for v in c.get('input', {}).values()))
    full = '\n\n'.join(texts)
    lang = 'python' if kind == 'py' else '(?:ijm|javascript|java|imagej|macro)?'
    blocks = re.findall(r'```' + lang + r'\s*\n(.*?)```', full, re.S)
    if kind == 'ijm':
        blocks = [b for b in blocks if 'input' in b and ('open(' in b or 'open (' in b)] or blocks
    if not done or not blocks: continue
    open(f'replies/{name}.txt', 'w').write(full)
    if kind == 'py':
        open(f'{name}/script.py', 'w').write(blocks[0])
    else:
        code = blocks[0]
        img = 'dapi.tif' if task == 'nuclei' else 'bf.tif'
        d = os.path.abspath(name)
        code = re.sub(r'input\s*=\s*"[^"]*"\s*;', f'input = "{d}/{img}";', code, count=1)
        code = re.sub(r'output\s*=\s*"[^"]*"\s*;', f'output = "{d}/labels.tif";', code, count=1)
        open(f'{name}/macro.ijm', 'w').write(code)
    with open('queue.txt', 'a') as q: q.write(qline + '\n')
    print('queued', qline, len(blocks), 'blocks')
