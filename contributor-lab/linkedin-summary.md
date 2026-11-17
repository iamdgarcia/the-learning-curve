# LinkedIn announcement draft — not published

Can small local models run capable agent harnesses—or are we confusing a smaller prompt with better reasoning?

I explored Hermes’s context architecture and built a standalone bounded-context prototype with real local LFM3-1.7B and d1-2B diagnostics.

The useful findings were not a clean victory:

• Constrained JSON fixed output shape, not decision correctness: 32/32 valid responses, but 7/16 expected actions with compact state and 3/16 with distracting history.

• A bounded thinking phase improved the compact LFM3 result to 10/16. d1 reached 11/16 on the compact cases. That is too small and interface-dependent to declare a winner.

• The d1 relevance filter missed a read-only permission constraint. This is why learned relevance must not control policy retention.

• A simple compiler can preserve mandatory state, retain complete tool-call/result groups, and measure the rendered prompt—including tool schemas—before dispatch.

These are hand-authored diagnostic cases, not a standard agent benchmark, frontier-parity result, or production safety certification. The code retains failed actions and raw responses.

The architecture worth testing is:
verified external state + bounded context + selective tools + decision assistance + independent outcome checks.

Teacher-produced subtask memory and harness-matched distillation are next experiments, not work already completed.

I’m looking for contributors interested in reproducible evaluation, context-budget contracts, and calibrated escalation—not just reducing the context minimum.

Publication note: Add the actual public article and code URLs only after they exist. Do not replace this note with invented links. Suggested hashtags: #OpenSource #AIAgents #ContextEngineering
