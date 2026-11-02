"""Maintainer tool: rebuilds the skill's code knowledge graph and code map after any change to scripts/ or assets/.
   python tools/build_code_graph.py
1. graphify extracts the engine and brand code offline (tree-sitter AST, no LLM, no API key).
2. services.json becomes graph data too: services, the files they read and write, the scripts they run and the
   tools they need. That pipeline is invisible to an AST, because make_film.py starts each service as its own
   process, across Python, Node and PowerShell.
3. graphify merges the two graphs and clusters them.
4. Writes references/code-graph/graph.json (query it with `graphify query|explain|path ... --graph <it>`) and
   references/code-map.md, the compact map the skill reads instead of opening every script.
Needs: pip install graphifyy (the PyPI name has two y's; the command is graphify).
"""
import collections, json, os, pathlib, re, shutil, subprocess, sys, tempfile

SKILL = pathlib.Path(__file__).resolve().parent.parent
OUT = SKILL / 'references' / 'code-graph'
ENV = dict(os.environ, GRAPHIFY_BACKEND='none', PYTHONIOENCODING='utf-8')


def graphify(*args):
    r = subprocess.run([sys.executable, '-m', 'graphify', *map(str, args)], env=ENV, capture_output=True, text=True, encoding='utf-8')
    if r.returncode:
        sys.exit(f'graphify {args[0]} failed:\n{r.stdout}\n{r.stderr}')
    return r.stdout


tmp = pathlib.Path(tempfile.mkdtemp(prefix='motion-graph-'))
src = tmp / 'src'
for d in ('scripts', 'assets'):
    shutil.copytree(SKILL / d, src / d, ignore=shutil.ignore_patterns('__pycache__', '*.png', '*.svg', '*.pdf'))

# ---------- 1. the code, through graphify ----------
graphify('extract', src, '--code-only', '--out', tmp / 'ast')
ast = json.loads((tmp / 'ast' / 'graphify-out' / 'graph.json').read_text(encoding='utf-8'))
file_ids = {n['source_file']: n['id'] for n in ast['nodes'] if n.get('source_file') and n['label'] == pathlib.Path(n['source_file']).name}

# ---------- 2. the pipeline, from services.json ----------
REG = json.loads((SKILL / 'scripts' / 'services.json').read_text(encoding='utf-8'))
nodes, links = {}, []


def node(nid, label, kind, **extra):
    nodes.setdefault(nid, {'id': nid, 'label': label, 'file_type': 'concept', 'norm_label': label.lower(), 'kind': kind,
                           'source_file': 'scripts/services.json', '_origin': 'manifest', **extra})
    return nid


def link(s, t, rel):
    links.append({'source': s, 'target': t, 'relation': rel, '_origin': 'manifest', 'confidence': 'EXTRACTED',
                  'confidence_score': 1.0, 'source_file': 'scripts/services.json', 'weight': 1.0})


def artifact(p):
    p = p.rstrip('?').replace('{film}/', '')
    p = {'{video}': 'build/<film>.mp4', '{out}': '<film>.mp4', '{srt}': '<film>.srt', '{voice_src}/*': '<voice folder>/*'}.get(p, p)
    m = re.match(r'\{engine\}/(.+)', p)
    if m and f'scripts/{m.group(1)}' in file_ids:          # an engine file: link to graphify's own file node
        return file_ids[f'scripts/{m.group(1)}']
    return node('artifact:' + p, p, 'artifact')


for name, s in REG['services'].items():
    sid = node('service:' + name, f'service {name}', 'service', does=s['does'])
    script = next((c for c in s.get('run', []) if re.search(r'\.(js|py|ps1)$', c)), None)
    if script:
        rel = script.replace('{engine}/', 'scripts/').replace('{film}/', 'assets/template/')
        if rel in file_ids:
            link(sid, file_ids[rel], 'runs')
    for u in s.get('uses', []):
        if f'scripts/{u}' in file_ids:
            link(sid, file_ids[f'scripts/{u}'], 'runs')
    for p in s['in']:
        link(sid, artifact(p), 'reads')
    for p in s['out']:
        link(sid, artifact(p), 'writes')
    for n in s.get('needs', []):
        link(sid, node('tool:' + n, n, 'tool'), 'needs')
for pname, steps in REG['pipelines'].items():
    pid = node('pipeline:' + pname, f'pipeline {pname}', 'pipeline')
    prev = pid
    for st in steps:
        names = [n for n in REG['services'] if n.startswith('voice-') and n != 'voice-cache'] if st == 'voice-*' else [st]
        for n in names:
            link(prev, 'service:' + n, 'next' if prev != pid else 'starts')
        prev = 'service:' + names[0]
link(node('service:orchestrator', 'make_film.py orchestrator', 'service', does='Runs a pipeline from services.json'),
     file_ids['scripts/make_film.py'], 'runs')
for pname in REG['pipelines']:
    link('service:orchestrator', 'pipeline:' + pname, 'runs')
svc_graph = {'directed': True, 'multigraph': False, 'graph': {}, 'nodes': list(nodes.values()), 'links': links, 'hyperedges': []}
(tmp / 'services.json').write_text(json.dumps(svc_graph, indent=1), encoding='utf-8')

# ---------- 3. merge and cluster, through graphify ----------
merged = tmp / 'merged' / 'graphify-out' / 'graph.json'
merged.parent.mkdir(parents=True)
graphify('merge-graphs', tmp / 'ast' / 'graphify-out' / 'graph.json', tmp / 'services.json', '--out', merged)
G = json.loads(merged.read_text(encoding='utf-8'))
# merge-graphs namespaces ids by the graph each came from, so the manifest's links to a script file made a stub
# copy of graphify's file node. Strip the namespace and keep one node per id (the labelled one): the services
# then attach to the real code nodes before clustering.
strip = lambda i: i.split('::', 1)[-1] if isinstance(i, str) else i
keep = {}
for n in G['nodes']:
    n['id'] = strip(n['id'])
    if n['id'] not in keep or ('label' in n and 'label' not in keep[n['id']]):
        keep[n['id']] = n
G['nodes'] = list(keep.values())
for e in G['links']:
    e['source'], e['target'] = strip(e['source']), strip(e['target'])
merged.write_text(json.dumps(G, ensure_ascii=False), encoding='utf-8')
graphify('cluster-only', tmp / 'merged', '--no-label', '--no-viz')
G = json.loads(merged.read_text(encoding='utf-8'))
OUT.mkdir(parents=True, exist_ok=True)
(OUT / 'graph.json').write_text(json.dumps(G, indent=1, ensure_ascii=False), encoding='utf-8')
hubs = graphify('god-nodes', '--graph', merged, '--top', '12')

# ---------- 4. the code map ----------
by_id = {n['id']: n for n in G['nodes']}
calls = collections.defaultdict(set)    # file -> files it calls into
for e in G['links']:
    if e['relation'] in ('calls', 'indirect_call'):
        a, b = by_id.get(e['source'], {}), by_id.get(e['target'], {})
        if a.get('source_file') and b.get('source_file') and a['source_file'] != b['source_file'] and b.get('_origin') != 'manifest':
            calls[a['source_file']].add(b['source_file'])
funcs = collections.defaultdict(list)
for n in G['nodes']:
    if n.get('label', '').endswith('()') and n.get('source_file') and n.get('_origin') != 'manifest':
        funcs[n['source_file']].append((int(re.sub(r'\D', '', n.get('source_location', '0')) or 0), n['label']))

L = ['# Code map (generated by tools/build_code_graph.py; do not edit by hand)', '',
     'Read this instead of opening the scripts. Open a file only at the lines you need. To ask the graph a',
     'question (needs `pip install graphifyy`): `graphify query "what writes cues.js?" --graph',
     'references/code-graph/graph.json`, or `graphify explain "render"`, or `graphify path "mix" "render"`.', '',
     '## Services (scripts/services.json)', '',
     'make_film.py runs these in order. Each one is one script that talks to the others only through files in the',
     'film folder. A service is skipped when its outputs are newer than its inputs and its command is unchanged.',
     'Run one alone with `make_film.py <film> --only <service>`; see the plan with `--dry-run`.', '',
     '| Service | Script | Reads | Writes | Needs | If it fails |', '|---|---|---|---|---|---|']
for name, s in REG['services'].items():
    script = next((c.split('/')[-1] for c in s.get('run', []) if re.search(r'\.(js|py|ps1)$', c)), 'built in')
    L.append(f'| {name} | {script} | {", ".join(s["in"]) or "-"} | {", ".join(s["out"]) or "-"} | '
             f'{", ".join(s.get("needs", [])) or "-"} | {s.get("on_fail", "stop")} |')
L += ['', 'Pipelines: ' + '; '.join(f'**{k}**: {" -> ".join(v)}' for k, v in REG['pipelines'].items()) + '.', '',
      'Paths: {film} is the film folder; {engine} is <project>/engine (a copy of scripts/); {build} is {film}/build',
      '(intermediate video and stamps.json); {video} is build/<film>.mp4; {out} is the delivered <film>.mp4; {srt} sits',
      'next to it.', '',
      '## Add or change a service', '',
      '1. Write the script so it reads and writes files only (no imports from other services), with its usage in',
      '   its first lines.',
      '2. Add it to scripts/services.json: run, in, out, needs, on_fail (and always: true only for cheap, idempotent',
      '   steps). Put it in a pipeline.',
      '3. Run `python tools/build_code_graph.py` so this map and the graph follow.', '',
      '## Files and their functions (line numbers)', '']
for f in sorted(funcs):
    fs = sorted(set(funcs[f]))
    L.append(f'- **{f}**' + (f' (calls into {", ".join(sorted(calls[f]))})' if calls[f] else '') + ': '
             + ', '.join(f'{lab} L{ln}' for ln, lab in fs))
L += ['', '## Hubs (most connected; change them with care, everything leans on them)', '', '```', hubs.strip(), '```', '']
(SKILL / 'references' / 'code-map.md').write_text('\n'.join(L), encoding='utf-8')
print(f'graph: {len(G["nodes"])} nodes, {len(G["links"])} edges -> {OUT / "graph.json"}')
print(f'map: {SKILL / "references" / "code-map.md"} ({len(L)} lines)')
shutil.rmtree(tmp, ignore_errors=True)
