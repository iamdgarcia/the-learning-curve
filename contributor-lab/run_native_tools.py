"""Native function-calling control. One allowed operation per response.
No function is executed. Measures tool selection, not argument execution.
"""
import json
from pathlib import Path
import time
from bounded_context import post_json
from fixtures import CASES, CRITERIA, POLICY


def main():
 out=Path('results/run-05-native-tools');out.mkdir(parents=True,exist_ok=True)
 tools=[{'type':'function','function':{'name':k,'description':v,'parameters':{'type':'object','properties':{},'additionalProperties':False}}} for k,v in CRITERIA.items()]
 rows=[]
 for case in CASES:
  payload={'model':'lfm3-1.7b','messages':[{'role':'system','content':POLICY+'\nSelect the next operation by calling exactly one provided function. This is a classification test: no real operation is executed.'},{'role':'user','content':case['state']}],
           'tools':tools,'tool_choice':'required','parallel_tool_calls':False,'temperature':0.1,'max_tokens':256,'seed':11,'chat_template_kwargs':{'enable_thinking':False}}
  row={'case_id':case['id'],'condition':'compact','backend':'lfm3_native','expected':case['expected'],'request':payload}
  t=time.monotonic()
  try:
   response=post_json('http://127.0.0.1:8080','/v1/chat/completions',payload,timeout=180)
   calls=response['choices'][0]['message'].get('tool_calls') or []
   valid=len(calls)==1 and calls[0]['function']['name'] in CRITERIA
   prediction=calls[0]['function']['name'] if valid else None
   row.update(response=response,prediction=prediction,interface_valid=valid,correct=valid and prediction==case['expected'],usage=response.get('usage',{}))
  except Exception as e:row.update(error=str(e),correct=False,prediction=None,interface_valid=False)
  row['elapsed_seconds']=time.monotonic()-t;rows.append(row)
  with (out/'raw-inference.jsonl').open('a') as f:f.write(json.dumps(row)+'\n')
  print(case['id'],row['prediction'],'expected',case['expected'],'seconds',round(row['elapsed_seconds'],2),flush=True)
 result={'experiment':'Native tool-calling compact control','n':len(rows),'correct':sum(r['correct'] for r in rows),'interface_valid':sum(r['interface_valid'] for r in rows),'failed_cases':[r['case_id'] for r in rows if not r['correct']],'total_input_tokens':sum(r.get('usage',{}).get('prompt_tokens',0) for r in rows),'total_output_tokens':sum(r.get('usage',{}).get('completion_tokens',0) for r in rows),'confounds':'One sample; explored after initial format failures; no actual execution or parameter complexity. Native schemas add prompt tokens and change choice representation. Thinking disabled.'}
 (out/'summary.json').write_text(json.dumps(result,indent=2)+'\n');print(json.dumps(result,indent=2),flush=True)


if __name__=='__main__':main()
