"""Save subagent hand-back reports (verbatim) from the session transcript: grab.py id=name ..."""
import json, sys, re
T = '<transcript>.jsonl'
O = '<fig3-work>/bf3/replies/'
want = dict(a.split('=') for a in sys.argv[1:])
found = {}
for line in open(T):
    for aid, name in want.items():
        key = f'agent-message from=\\"{aid}\\"'
        if key not in line: continue
        e = json.loads(line)
        c = e.get('content') or (e.get('message') or {}).get('content')
        blobs = [c] if isinstance(c, str) else [x.get('text', '') if isinstance(x, dict) else str(x) for x in (c or [])]
        for b in blobs:
            i = b.find(f'agent-message from="{aid}"')
            if i < 0: continue
            body = b[i:].split('The report follows:', 1)[1].split('</agent-message>')[0]
            body = '\n'.join(l[2:] if l.startswith('  ') else l for l in body.split('\n')).strip('\n')
            found[name] = body
for name, body in found.items():
    open(O + name + '.txt', 'w').write(body + '\n'); print(name, len(body))
print('missing', [n for n in want.values() if n not in found])
