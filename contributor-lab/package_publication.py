"""Prepare publication artifacts, verify results, and package the open-source lab."""
from pathlib import Path
import hashlib
import json
import re
import subprocess
import sys
import zipfile
import markdown

base=Path(__file__).resolve().parent
check=subprocess.run([sys.executable,'-m','unittest','-v','test_bounded_context'],cwd=base,capture_output=True,text=True)
(base/'unit-test-output.txt').write_text(check.stdout+check.stderr)
assert check.returncode==0,check.stderr
assert 'Ran 17 tests' in check.stderr
aggregate=subprocess.run([sys.executable,'aggregate_results.py'],cwd=base,capture_output=True,text=True)
assert aggregate.returncode==0,aggregate.stderr
results=json.loads((base/'results/aggregate.json').read_text())
assert results['total_diagnostic_inference_requests']==140
assert [r['correct'] for r in results['constrained']['results']]==[7,3]
assert results['thinking']['correct']==10
assert [r['exact_correct'] for r in results['run1'] if r['backend']=='d1']==[11,9]
assert results['evidence_selection']['false_negative']==3
assert results['evidence_selection']['compiled_prompt_tokens']==214

article=(base/'community-article.md').read_text()
assert article.count('```')%2==0
assert 'not posted' in article
assert '10 of 16' in article and '11 of 16' in article and '7 of 16' in article
appendix=(base/'RESULTS.md').read_text()
body=markdown.markdown(article+'\n\n---\n\n'+appendix,extensions=['fenced_code','tables'])
style='body{font-family:system-ui,sans-serif;line-height:1.65;max-width:900px;margin:40px auto;padding:0 24px;color:#243043}h1,h2,h3{line-height:1.25;color:#153659}h2{margin-top:2em}pre{background:#f2f5f9;padding:16px;overflow:auto;border-radius:6px}blockquote{border-left:4px solid #315e89;padding-left:18px;margin-left:0}a{color:#185f9b;overflow-wrap:anywhere}@media print{body{font-size:10pt;margin:0}pre{white-space:pre-wrap}}'
html='<!doctype html><html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>Why a small agent needs more than a smaller prompt</title><style>'+style+'</style></head><body>'+body+'</body></html>'
(base/'community-article.html').write_text(html)

# Future dev.to payload: explicitly UNPUBLISHED; never sent by this script.
payload={'article':{'title':'Why a small agent needs more than a smaller prompt','published':False,'body_markdown':article+'\n\n---\n\n'+appendix,'tags':['ai','opensource','machinelearning','python'],'description':'A source-backed Hermes exploration with real local LFM3/d1 diagnostics, bounded-context code, and negative results.'}}
(base/'devto-draft-payload.json').write_text(json.dumps(payload,indent=2,ensure_ascii=False)+'\n')

files=[]
for path in sorted(base.rglob('*')):
 if path.is_file() and not any(part in {'__pycache__','.git','.venv'} for part in path.relative_to(base).parts) and path.suffix not in {'.pyc','.zip'}:
  files.append(path)
manifest=[{'path':str(path.relative_to(base)),'sha256':hashlib.sha256(path.read_bytes()).hexdigest(),'bytes':path.stat().st_size} for path in files if path.name!='MANIFEST.json']
(base/'MANIFEST.json').write_text(json.dumps(manifest,indent=2)+'\n')
files=[p for p in files if p.name!='MANIFEST.json']+[base/'MANIFEST.json']
archive=base.parent/'small-agent-contributor-exploration.zip'
with zipfile.ZipFile(archive,'w',zipfile.ZIP_DEFLATED) as bundle:
 for path in files:bundle.write(path,arcname='small-agent-contributor-exploration/'+str(path.relative_to(base)))
with zipfile.ZipFile(archive) as bundle:
 assert bundle.testzip() is None
 assert len(bundle.namelist())==len(files)
 for item in manifest:
  content=bundle.read('small-agent-contributor-exploration/'+item['path'])
  assert hashlib.sha256(content).hexdigest()==item['sha256']
print(json.dumps({'tests':'17 passed','complete_main_inference_requests':140,'aborted_completed_responses':3,'article_words':len(article.split()),'archive_bytes':archive.stat().st_size,'packaged_files':len(files),'manifest_verified':True,'publicly_published':False,'html':str(base/'community-article.html'),'archive':str(archive)},indent=2))
