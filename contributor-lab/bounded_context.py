"""Standalone bounded-context research core. Not an installed Hermes plugin.

The scorer may rank optional evidence. It can NEVER authorize a write, remove
mandatory constraints, or replace deterministic completion verification.
"""
from __future__ import annotations
from dataclasses import dataclass, field
import hashlib
import json
import math
from pathlib import Path
import urllib.request


class BudgetExceeded(ValueError):
    pass


def post_json(base_url: str, path: str, payload: dict, timeout: float = 120) -> dict:
    request = urllib.request.Request(base_url.rstrip('/') + path,
        data=json.dumps(payload).encode(), headers={'Content-Type': 'application/json'})
    with urllib.request.urlopen(request, timeout=timeout) as response:
        return json.load(response)


class LlamaTokenizer:
    """Tokenize the actual rendered message+tool prompt with this server's template.
    Serving-window and output-budget checks remain required at dispatch time.
    """
    def __init__(self, base_url: str):
        self.base_url = base_url
        self.cache: dict[str, int] = {}

    def count_request(self, messages: list[dict], tools: list[dict] | None = None) -> int:
        payload = {'messages': messages, 'add_generation_prompt': True,
                   'chat_template_kwargs': {'enable_thinking': False}}
        if tools:
            payload['tools'] = tools
        key = json.dumps(payload, sort_keys=True, ensure_ascii=False)
        if key not in self.cache:
            prompt = post_json(self.base_url, '/apply-template', payload)['prompt']
            self.cache[key] = len(post_json(self.base_url, '/tokenize',
                {'content': prompt, 'add_special': False})['tokens'])
        return self.cache[key]


@dataclass(frozen=True)
class Evidence:
    identifier: str
    text: str
    score: float = 0.0
    mandatory: bool = False


@dataclass
class Compilation:
    messages: list[dict]
    prompt_tokens: int
    selected_ids: list[str]
    omitted_ids: list[str]
    output_reserve: int
    safety_margin: int


class ContextCompiler:
    def __init__(self, tokenizer, total_window: int, output_reserve: int = 256,
                 safety_margin: int = 128):
        if min(total_window, output_reserve, safety_margin) < 0:
            raise ValueError('Budgets must be nonnegative')
        if total_window <= output_reserve + safety_margin:
            raise BudgetExceeded('No input space remains')
        self.tokenizer = tokenizer
        self.total_window = total_window
        self.output_reserve = output_reserve
        self.safety_margin = safety_margin

    def compile(self, system: str, task: str, state: dict,
                evidence: list[Evidence] | None = None,
                recent_groups: list[list[dict]] | None = None,
                tools: list[dict] | None = None) -> Compilation:
        evidence = evidence or []
        groups = recent_groups or []
        self._validate_groups(groups)
        ids = [e.identifier for e in evidence]
        if len(ids) != len(set(ids)):
            raise ValueError('Evidence IDs must be unique')
        if any(not math.isfinite(e.score) for e in evidence):
            raise ValueError('Evidence scores must be finite')
        mandatory = [e for e in evidence if e.mandatory]
        optional = sorted((e for e in evidence if not e.mandatory),
                          key=lambda e: (-e.score, e.identifier))
        selected = list(mandatory)
        input_limit = self.total_window - self.output_reserve - self.safety_margin

        def render(items):
            capsule = {'task': task, 'authoritative_state': state,
                       'evidence': [{'id': e.identifier, 'text': e.text,
                                     'trust': 'untrusted_data'} for e in items]}
            return [{'role': 'system', 'content': system},
                    {'role': 'user', 'content': json.dumps(capsule, ensure_ascii=False)}] + [m for group in groups for m in group]

        messages = render(selected)
        count = self.tokenizer.count_request(messages, tools)
        if count > input_limit:
            raise BudgetExceeded(f'Mandatory context costs {count} tokens; input limit is {input_limit}. Split or escalate.')
        for item in optional:
            candidate = render(selected + [item])
            candidate_count = self.tokenizer.count_request(candidate, tools)
            if candidate_count <= input_limit:
                selected.append(item)
                messages, count = candidate, candidate_count
        selected_ids = [e.identifier for e in selected]
        return Compilation(messages, count, selected_ids,
                           [i for i in ids if i not in selected_ids],
                           self.output_reserve, self.safety_margin)

    @staticmethod
    def _validate_groups(groups):
        for group in groups:
            if not group or group[0].get('role') != 'assistant':
                raise ValueError('A recent group must start with its assistant call')
            calls = group[0].get('tool_calls') or []
            expected = [c.get('id') for c in calls]
            actual = [m.get('tool_call_id') for m in group[1:] if m.get('role') == 'tool']
            if not expected or any(not x for x in expected) or len(expected) != len(set(expected)):
                raise ValueError('Tool call IDs must be present and unique')
            if len(group) != len(calls) + 1 or sorted(expected) != sorted(actual):
                raise ValueError('Tool calls and results must remain a complete atomic group')
            if any(m.get('role') != 'tool' for m in group[1:]):
                raise ValueError('Only required tool results may follow the assistant call')


class ArtifactStore:
    """Exact immutable evidence by content-addressed ID. No lossy summaries."""
    def __init__(self, root: Path):
        self.root = root
        root.mkdir(parents=True, exist_ok=True)

    def save(self, text: str) -> str:
        identifier = hashlib.sha256(text.encode()).hexdigest()
        path = self.root / (identifier + '.txt')
        if not path.exists():
            path.write_text(text)
        return identifier

    def read(self, identifier: str, start: int = 0, end: int | None = None) -> str:
        if len(identifier) != 64 or any(c not in '0123456789abcdef' for c in identifier):
            raise ValueError('Invalid artifact ID')
        if start < 0 or (end is not None and end < start):
            raise ValueError('Invalid character range')
        return (self.root / (identifier + '.txt')).read_text()[start:end]


@dataclass
class VerifiedState:
    expected_value: str
    write_authorized: bool = False
    observed_value: str | None = None
    readback_done: bool = False
    uncertain_write: bool = False

    def authorize_action(self, action: str) -> bool:
        if action == 'update_record':
            return self.write_authorized and not self.uncertain_write
        if action == 'finish':
            return self.readback_done and self.observed_value == self.expected_value
        return action in {'read_back', 'escalate'}


def choose_or_escalate(probabilities: dict[str, float], threshold: float,
                       allowed: set[str], abstain: str = 'escalate') -> str:
    """Confidence threshold is experimental, not a proven calibration guarantee."""
    if not 0 <= threshold <= 1 or not probabilities:
        return abstain
    if any(not math.isfinite(p) or p < 0 or p > 1 for p in probabilities.values()):
        return abstain
    if abs(sum(probabilities.values()) - 1.0) > 1e-3:
        return abstain
    winner = max(probabilities, key=probabilities.get)
    return winner if winner in allowed and probabilities[winner] >= threshold else abstain
