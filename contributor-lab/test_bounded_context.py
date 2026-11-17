import json
from pathlib import Path
import tempfile
import unittest
from bounded_context import (ArtifactStore, BudgetExceeded, ContextCompiler, Evidence,
                             VerifiedState, choose_or_escalate)


class DeterministicTestCounter:
    """Deliberately byte-based test double; NEVER used for model token reporting."""
    def count_request(self, messages, tools=None):
        return len(json.dumps({'messages': messages, 'tools': tools}, ensure_ascii=False).encode())


class ContextTests(unittest.TestCase):
    def compiler(self, size=1600):
        return ContextCompiler(DeterministicTestCounter(), size, 100, 100)

    def test_pinned_constraint_survives(self):
        result = self.compiler().compile('Policy', 'Task', {'permission': 'read_only'},
            [Evidence('must', 'Never write', mandatory=True), Evidence('huge', 'x'*3000, 100)])
        self.assertIn('must', result.selected_ids)
        self.assertIn('huge', result.omitted_ids)
        self.assertIn('read_only', result.messages[1]['content'])

    def test_overflow_fails_closed(self):
        with self.assertRaises(BudgetExceeded):
            self.compiler(500).compile('Policy', 'Task', {}, [Evidence('must','x'*1000, mandatory=True)])

    def test_tool_schemas_are_charged(self):
        with self.assertRaises(BudgetExceeded):
            self.compiler(600).compile('Policy', 'Task', {}, tools=[{'schema':'x'*1000}])

    def test_complete_atomic_group_retained(self):
        group=[{'role':'assistant','content':'','tool_calls':[{'id':'a','type':'function','function':{'name':'read','arguments':'{}'}}]},
               {'role':'tool','tool_call_id':'a','content':'observed'}]
        result=self.compiler().compile('Policy','Task',{},recent_groups=[group])
        self.assertEqual(result.messages[-2:],group)

    def test_orphan_result_rejected(self):
        with self.assertRaises(ValueError):
            self.compiler().compile('Policy','Task',{},recent_groups=[[{'role':'tool','tool_call_id':'a','content':'x'}]])

    def test_missing_result_rejected(self):
        with self.assertRaises(ValueError):
            self.compiler().compile('Policy','Task',{},recent_groups=[[{'role':'assistant','tool_calls':[{'id':'a'}]}]])

    def test_duplicate_evidence_ids_rejected(self):
        with self.assertRaises(ValueError):
            self.compiler().compile('Policy','Task',{},[Evidence('a','one'),Evidence('a','two')])

    def test_nonfinite_score_rejected(self):
        with self.assertRaises(ValueError):
            self.compiler().compile('Policy','Task',{},[Evidence('a','one',float('nan'))])

    def test_inputs_are_not_mutated(self):
        state={'exact_id':'r-0042'}
        before=dict(state)
        self.compiler().compile('Policy','Task',state)
        self.assertEqual(state,before)

    def test_stable_selection(self):
        evidence=[Evidence('z','Z',1),Evidence('a','A',1)]
        a=self.compiler().compile('Policy','Task',{},evidence)
        b=self.compiler().compile('Policy','Task',{},list(reversed(evidence)))
        self.assertEqual(a.messages,b.messages)

    def test_store_exact_unicode(self):
        with tempfile.TemporaryDirectory() as directory:
            store=ArtifactStore(Path(directory))
            value='r-0042: acción — 你好'
            identifier=store.save(value)
            self.assertEqual(store.read(identifier),value)
            self.assertEqual(store.save(value),identifier)

    def test_store_rejects_path_traversal(self):
        with tempfile.TemporaryDirectory() as directory:
            with self.assertRaises(ValueError):
                ArtifactStore(Path(directory)).read('../secret')

    def test_completion_requires_readback(self):
        state=VerifiedState('done',write_authorized=True)
        self.assertFalse(state.authorize_action('finish'))
        state.readback_done=True
        state.observed_value='pending'
        self.assertFalse(state.authorize_action('finish'))
        state.observed_value='done'
        self.assertTrue(state.authorize_action('finish'))

    def test_uncertain_write_cannot_repeat(self):
        self.assertFalse(VerifiedState('done',True,uncertain_write=True).authorize_action('update_record'))

    def test_classifier_cannot_authorize_write(self):
        prediction=choose_or_escalate({'update_record':0.99,'escalate':0.01},0.8,{'update_record'})
        self.assertEqual(prediction,'update_record')
        self.assertFalse(VerifiedState('done',False).authorize_action(prediction))

    def test_unknown_action_rejected(self):
        self.assertFalse(VerifiedState('done',True).authorize_action('delete_everything'))

    def test_bad_or_ambiguous_distribution_abstains(self):
        for probs in [{'a':0.5,'b':0.5},{'a':float('nan')},{'a':2},{'a':0.4}]:
            self.assertEqual(choose_or_escalate(probs,0.8,{'a','b'}),'escalate')


if __name__=='__main__':
    unittest.main(verbosity=2)
