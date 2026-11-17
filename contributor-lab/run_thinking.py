"""Exploratory reasoning-enabled control: all same 16 compact cases.
Keeps output schema and question fixed; enables thinking and increases output budget.
Not maximum-capability evaluation. Saving full returned reasoning for audit.
"""
import argparse
import json
from pathlib import Path
import time
from bounded_context import post_json
from fixtures import CASES, POLICY
from run_constrained import SCHEMA


def main():
 parser=argparse.ArgumentParser()
 parser.add_argument('--output',default='results/run-04b-thinking-budget')
 args=parser.parse_args()
 out=Path(args.output);out.mkdir(parents=True,exist_ok=True)
 rows=[]
 for case in CASES:
  payload={'model':'lfm3-1.7b','messages':[{'role':'system','content':POLICY+'\nClassify the next operation. Return JSON with action. Do not execute a tool.'},{'role':'user','content':case['state']}],
           'temperature':0.1,'max_tokens':512,'reasoning_budget_tokens':128,'seed':11,'chat_template_kwargs':{'enable_thinking':True},
           'response_format':{'type':'json_schema','json_schema':{'name':'next_operation','strict':True,'schema':SCHEMA}}}
  row={'case_id':case['id'],'condition':'compact','backend':'lfm3_thinking','expected':case['expected'],'request':payload}
  t=time.monotonic()
  try:
   response=post_json('http://127.0.0.1:8080','/v1/chat/completions',payload,timeout=180)
   row['response']=response
   row['usage']=response.get('usage',{})
   row['finish_reason']=response['choices'][0]['finish_reason']
   msg=response['choices'][0]['message']
   row['reasoning_present']=bool(msg.get('reasoning_content') or msg.get('reasoning'))
   content=msg.get('content') or ''
   parsed=json.loads(content)
   valid=set(parsed)=={'action'} and parsed['action'] in SCHEMA['properties']['action']['enum']
   row.update(prediction=parsed.get('action'),schema_valid=valid,correct=valid and parsed['action']==case['expected'],usage=response.get('usage',{}),finish_reason=response['choices'][0]['finish_reason'],reasoning_present=bool(msg.get('reasoning_content') or msg.get('reasoning')))
  except Exception as e:row.update(error=str(e),correct=False,prediction=None,schema_valid=False)
  row['elapsed_seconds']=time.monotonic()-t;rows.append(row)
  with (out/'raw-inference.jsonl').open('a') as f:f.write(json.dumps(row)+'\n')
  print(case['id'],row['prediction'],'expected',case['expected'],'seconds',round(row['elapsed_seconds'],2),flush=True)
 result={'experiment':'Exploratory thinking-enabled compact control','n':len(rows),'correct':sum(r['correct'] for r in rows),'schema_valid':sum(r['schema_valid'] for r in rows),'total_input_tokens':sum(r.get('usage',{}).get('prompt_tokens',0) for r in rows),'total_output_tokens':sum(r.get('usage',{}).get('completion_tokens',0) for r in rows),'failed_cases':[r['case_id'] for r in rows if not r['correct']],'reasoning_present_responses':sum(r.get('reasoning_present',False) for r in rows),'confounds':'One sample; explored after original failures; thinking enabled with explicit 128-token reasoning budget and 512 total output cap; not maximum-capability test; constrained generation can interact with reasoning. No noisy thinking condition.'}
 (out/'summary.json').write_text(json.dumps(result,indent=2)+'\n');print(json.dumps(result,indent=2),flush=True)


if __name__=='__main__':main()
