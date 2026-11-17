# Results appendix

These are narrow authored diagnostics, not a standard benchmark. One sample per case/condition. No model action was executed against business records.

## Completed main suite

- 140 completed diagnostic inference requests across five main runs.
- Three additional completed requests in the aborted reasoning configuration are reported separately; smoke and tokenization calls are not included.

## Next-operation choices

- LFM3 bare-label, compact: exact label 0/16; retrospective operation identity 4/16.
- LFM3 bare-label, distractors: exact label 0/16; retrospective operation identity 2/16.
- d1 typed choice, compact: expected action 11/16; interface valid 16/16.
- d1 typed choice, distractors: expected action 9/16; interface valid 16/16.
- LFM3 constrained JSON, compact: expected action 7/16; schema valid 16/16.
- LFM3 constrained JSON, distractors: expected action 3/16; schema valid 16/16.
- LFM3 constrained JSON with explicit 128-token reasoning budget, compact: expected action 10/16; schema valid 16/16.
- LFM3 native-function compact control: expected action 3/16; parsed single-tool interface 5/16. Eleven responses exhausted the 256-token output limit.

## Evidence filter

- d1 relevance: 9/12 labels matched authored expectations at the default .5 threshold.
- Six snippets were relevant; three selected and three missed. No irrelevant snippet selected.
- Precision 1.0 and recall .5 are sample-specific, not deployment calibration.
- Read-only constraint scored about .136 and would have been dropped by the learned filter. Software retained an independent hard permission block.
- Final evidence-selected prompt: 214 input tokens, plus 128 output reserve and 96 margin, inside a proposed 1,024-token total working budget. No downstream model-success test was performed on this compiled view.

## Rendered prompt accounting

- All completed non-thinking text requests in run-01 and run-02 had zero difference between counted rendered-template tokens and reported provider prompt tokens.
- Separate four-tool compiler check: 294 prompt tokens; large optional archive omitted.
- This does not establish a physical 1K server deployment or correctness across media/backend variants.

## Reasoning configuration that was stopped

- Three completed 1,024-output-token responses exhausted the cap in reasoning, returning no final JSON.
- Completed output tokens: 3,072. Missing/in-flight cases are not manufactured or included in accuracy.
- Replaced with explicit reasoning-budget experiment, retained as a configuration failure.

## Interpretation

The strongest observed lesson is separation of concerns: output validity is not action correctness, relevance scoring is not policy retention, and finite reasoning/output budgets matter. Compact state helps in this diagnostic but does not solve general reasoning or establish a universal context threshold.

See METHODOLOGY.md for confounds and every raw request/response under results/.
