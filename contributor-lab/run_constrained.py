"""Schema-constrained follow-up using the same cases, rules, and context conditions.
Registered after observing output-format failures in run-01. Exploratory, not preregistered.
"""
import argparse
import json
from pathlib import Path
import statistics
import time
from bounded_context import LlamaTokenizer, post_json
from fixtures import CASES, CRITERIA, POLICY, noisy_state

SCHEMA={'type':'object','properties':{'action':{'type':'string','enum':list(CRITERIA)}},'required':['action'],'additionalProperties':False}


def main():
    parser=argparse.ArgumentParser()
    parser.add_argument('--lfm-url',default='http://127.0.0.1:8080')
    parser.add_argument('--output',default='results/run-02-constrained')
    args=parser.parse_args()
    out=Path(args.output);out.mkdir(parents=True,exist_ok=True)
    tokenizer=LlamaTokenizer(args.lfm_url)
    details=[]
    for case in CASES:
        for condition in ['compact','distractors']:
            request={'model':'lfm3-1.7b','messages':[{'role':'system','content':POLICY+'\nClassify the next operation. Return JSON with action. Do not execute a tool.'},
                         {'role':'user','content':case['state'] if condition=='compact' else noisy_state(case['state'])}],
                     'temperature':0.1,'top_k':50,'repeat_penalty':1.1,'max_tokens':128,'seed':11,
                     'chat_template_kwargs':{'enable_thinking':False},
                     'response_format':{'type':'json_schema','json_schema':{'name':'next_operation','strict':True,'schema':SCHEMA}}}
            row={'case_id':case['id'],'condition':condition,'backend':'lfm3_constrained','expected':case['expected'],'request':request,
                 'rendered_prompt_tokens':tokenizer.count_request(request['messages'])}
            started=time.monotonic()
            try:
                response=post_json(args.lfm_url,'/v1/chat/completions',request,timeout=180)
                content=response['choices'][0]['message'].get('content') or ''
                parsed=json.loads(content)
                valid=set(parsed)=={'action'} and parsed['action'] in CRITERIA
                row.update(response=response,prediction=parsed.get('action'),schema_valid=valid,
                           correct=valid and parsed['action']==case['expected'],usage=response.get('usage',{}))
            except Exception as exc:
                row.update(error=str(exc),schema_valid=False,correct=False,prediction=None)
            row['elapsed_seconds']=time.monotonic()-started
            details.append(row)
            with (out/'raw-inference.jsonl').open('a') as file:file.write(json.dumps(row,ensure_ascii=False)+'\n')
            print(f"{condition} {case['id']}: {row['prediction']} expected={case['expected']} seconds={row['elapsed_seconds']:.2f}",flush=True)
    groups=[]
    for condition in ['compact','distractors']:
        subset=[r for r in details if r['condition']==condition]
        groups.append({'backend':'lfm3_constrained','condition':condition,'n':len(subset),'correct':sum(r['correct'] for r in subset),
                      'schema_valid':sum(r['schema_valid'] for r in subset),'accuracy':sum(r['correct'] for r in subset)/len(subset),
                      'errors':sum('error' in r for r in subset),'median_seconds':statistics.median(r['elapsed_seconds'] for r in subset),
                      'total_seconds':sum(r['elapsed_seconds'] for r in subset),
                      'total_input_tokens':sum(r.get('usage',{}).get('prompt_tokens',0) for r in subset),
                      'total_output_tokens':sum(r.get('usage',{}).get('completion_tokens',0) for r in subset),
                      'failed_cases':[r['case_id'] for r in subset if not r['correct']]})
    result={'experiment':'Exploratory constrained-format follow-up, same 16 authored workflow cases','requests':len(details),'results':groups,
            'lfm_rendered_token_deltas':sorted(set(r['usage']['prompt_tokens']-r['rendered_prompt_tokens'] for r in details if 'usage' in r)),
            'confounds':'Follow-up prompt changes final output-format sentence and adds schema grammar. No exact prompt-controlled causal attribution. No repetitions, held-out dataset, frontier baseline, end-to-end tools, or teacher training. Timing under shared server contention.'}
    (out/'summary.json').write_text(json.dumps(result,indent=2)+'\n')
    print(json.dumps(result,indent=2),flush=True)


if __name__=='__main__':
    main()
