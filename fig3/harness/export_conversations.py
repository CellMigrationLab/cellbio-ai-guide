"""Write prompts/<name>.conversation.md: every user turn (prompt and follow-up answers) and every assistant text,
in order, verbatim. Tool calls are listed by name (+ query/url) so web lookups and image views are visible."""
import json, os
T = '<tasks>/'
os.makedirs('prompts', exist_ok=True)
for f in ['ids.txt', 'ids_other.txt']:
    for line in open(f):
        line = line.strip()
        if not line: continue
        aid, name = line.split()[0].split('=')
        p = T + aid + '.output'
        if not os.path.exists(p): continue
        out, seen = [], set()
        for l in open(p):
            try: d = json.loads(l)
            except Exception: continue
            if d.get('uuid') in seen: continue
            seen.add(d.get('uuid'))
            m = d.get('message') or {}
            c = m.get('content')
            if d.get('type') == 'user' and isinstance(c, str):
                out.append(f'## USER ({d.get("timestamp")})\n\n{c}')
            elif d.get('type') == 'user' and isinstance(c, list):
                for x in c:
                    if isinstance(x, dict) and x.get('type') == 'text':
                        out.append(f'## USER ({d.get("timestamp")})\n\n{x["text"]}')
            elif d.get('type') == 'assistant':
                for x in c or []:
                    if x.get('type') == 'text' and x['text'].strip():
                        out.append(f'## ASSISTANT ({d.get("timestamp")})\n\n{x["text"]}')
                    elif x.get('type') == 'tool_use':
                        i = x.get('input', {})
                        if 'andback' in x.get('name', ''):
                            out.append('## ASSISTANT (final report)\n\n' + '\n'.join(str(v) for v in i.values()))
                        else:
                            arg = i.get('query') or i.get('url') or i.get('file_path') or ''
                            out.append(f'*[tool: {x["name"]} {arg}]*')
        open(f'prompts/{name}.conversation.md', 'w').write('\n\n'.join(out))
print('ok')
