import subprocess, os, json

os.chdir('/Users/claudius/clawd/frontion-site')

r = subprocess.run(['git', 'log', '--oneline', '-3'], capture_output=True, text=True, timeout=15)
print('GIT LOG:', r.stdout.strip())
print('GIT LOG ERR:', r.stderr.strip())

r2 = subprocess.run(['git', 'status', '--short'], capture_output=True, text=True, timeout=15)
print('GIT STATUS:', r2.stdout.strip())

with open('energy/2026-07-06.json') as f:
    d = json.load(f)
print(f'BRIEF: {d["date"]} - {d["title"]} - {len(d["sections"])} sections')

with open('energy/index.json') as f:
    idx = json.load(f)
print(f'INDEX: {len(idx)} entries, first: {idx[0]["date"]} - {idx[0]["title"]}')