"""Write prompt.md (first user message, verbatim) and reply.md (all assistant text) for every sub-agent run."""
import json, os, sys
T = '<tasks>/'
os.makedirs('prompts', exist_ok=True)
for f in ['ids.txt', 'ids_other.txt']:
    for line in open(f):
        line = line.strip()
        if not line: continue
        aid, name = line.split()[0].split('=')
        p = T + aid + '.output'
        if not os.path.exists(p): print('missing', name); continue
        prompt, texts, meta = None, [], {}
        for l in open(p):
            try: d = json.loads(l)
            except Exception: continue
            m = d.get('message', {})
            if prompt is None and d.get('type') == 'user' and isinstance(m.get('content'), str):
                prompt = m['content']; meta['start'] = d.get('timestamp')
            if d.get('type') == 'assistant':
                meta['model'] = m.get('model', meta.get('model')); meta['end'] = d.get('timestamp')
                for c in m.get('content', []) or []:
                    if c.get('type') == 'text': texts.append(c['text'])
                    if c.get('type') == 'tool_use' and c.get('name') == 'SubagentHandback':
                        texts.append(json.dumps(c.get('input'), ensure_ascii=False)[:20000])
        open(f'prompts/{name}.prompt.md', 'w').write(prompt or '')
        open(f'prompts/{name}.reply.md', 'w').write('\n\n'.join(texts))
        json.dump(dict(meta, agent_id=aid), open(f'prompts/{name}.meta.json', 'w'))
print(len(os.listdir('prompts')))
