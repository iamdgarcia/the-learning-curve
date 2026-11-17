"""Document an aborted reasoning configuration without inventing missing results."""
import json
from pathlib import Path

base=Path(__file__).resolve().parent
path=base/'results/run-04-thinking'
rows=[json.loads(line) for line in (path/'raw-inference.jsonl').read_text().splitlines()]
result={'status':'aborted by researcher','planned_cases':16,'completed_cases':len(rows),'completed_case_ids':[r['case_id'] for r in rows],
        'reason':'Completed responses exhausted the 1024-token output cap in reasoning and returned no final JSON. Stopped instead of repeatedly paying for the same failure; replaced with explicit reasoning-budget follow-up.',
        'responses_at_length_limit':sum(r.get('response',{}).get('choices',[{}])[0].get('finish_reason')=='length' for r in rows),
        'final_answers_present':sum(bool(r.get('response',{}).get('choices',[{}])[0].get('message',{}).get('content')) for r in rows),
        'output_tokens_in_completed_responses':sum(r.get('response',{}).get('usage',{}).get('completion_tokens',0) for r in rows),
        'unknown_in_flight':'A request may have been in flight at cancellation. It is not counted as a completed measurement.',
        'interpretation':'Configuration failure/finite-budget limitation, not an estimate of reasoning-enabled model accuracy.'}
(path/'aborted-summary.json').write_text(json.dumps(result,indent=2)+'\n')
print(json.dumps(result,indent=2))
