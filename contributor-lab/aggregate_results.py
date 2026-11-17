"""Aggregate saved real model results, preserving initial exact and parsed metrics."""
import json
from pathlib import Path
import re
import statistics


def load(path):
 return [json.loads(line) for line in path.read_text().splitlines()]


def main():
 base=Path(__file__).resolve().parent
 results=base/'results'
 native=load(results/'run-01/raw-inference.jsonl')
 assert len(native)==64, f'Expected all 64 run-01 cells, collected {len(native)}'
 assert len({(r['case_id'],r['condition'],r['backend']) for r in native})==64
 groups=[]
 for method in ['lfm3','d1']:
  for cond in ['compact','distractors']:
   rows=[r for r in native if r['backend']==method and r['condition']==cond]
   operation_correct=0;interface_valid=0;fails=[]
   for r in rows:
    prediction=r.get('prediction') or ''
    if method=='d1':
     parsed=prediction
     interface_valid+=bool(prediction)
    elif prediction in ['update_record','read_back','finish','escalate']:
     parsed=prediction;interface_valid+=1
    else:
     functions=re.findall(r'<function=([^>\n]+)>',prediction)
     parsed=functions[0] if len(functions)==1 else None
    operation_correct += parsed==r['expected']
    if parsed!=r['expected']:fails.append({'case_id':r['case_id'],'operation':parsed,'expected':r['expected']})
   groups.append({'backend':method,'condition':cond,'n':len(rows),'exact_correct':sum(r['correct'] for r in rows),'requested_interface_valid':interface_valid,'operation_identity_correct':operation_correct,'failures':fails})
 constrained=json.loads((results/'run-02-constrained/summary.json').read_text())
 evidence=json.loads((results/'run-03-selection/summary.json').read_text())
 thinking=json.loads((results/'run-04b-thinking-budget/summary.json').read_text())
 tools=json.loads((results/'run-05-native-tools/summary.json').read_text())
 assert constrained['requests']==32 and evidence['n']==12 and thinking['n']==16 and tools['n']==16
 for run,expected in [('run-02-constrained',32),('run-04b-thinking-budget',16),('run-05-native-tools',16)]:
  rows=load(results/run/'raw-inference.jsonl')
  assert len(rows)==expected
  assert len({(r['case_id'],r['condition']) for r in rows})==expected
  expected_count=sum(r['correct'] for r in rows)
  summary=json.loads((results/run/'summary.json').read_text())
  actual_count=sum(x['correct'] for x in summary['results']) if 'results' in summary else summary['correct']
  assert expected_count==actual_count
 total=64+32+12+16+16
 output={'total_diagnostic_inference_requests':total,'not_counted':'Smoke calls and template/tokenizer requests','run1':groups,'constrained':constrained,'evidence_selection':evidence,'thinking':thinking,'native_tools':tools,'scope':'Hand-authored narrow workflow and relevance diagnostics, not standard benchmark or full Hermes integration. One sample per cell. No safety certification, teacher training, or frontier baseline.'}
 (results/'aggregate.json').write_text(json.dumps(output,indent=2)+'\n')
 print(json.dumps(output,indent=2))


if __name__=='__main__':main()
