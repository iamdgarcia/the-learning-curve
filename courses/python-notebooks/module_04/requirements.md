# Requirements

## User Goal

Improve the final project so it combines the patterns built in `module_03` and acts as a practical content-creation pipeline.

## Functional Requirements (EARS)

- WHEN a user provides a blog topic, THE SYSTEM SHALL generate a 3-5 section outline.
- WHEN each section is created, THE SYSTEM SHALL route the section to a specialist style (`explanatory`, `how_to`, or `case_study`).
- WHEN a section route is selected, THE SYSTEM SHALL use route-specific research and writing prompts.
- WHEN a section draft is produced, THE SYSTEM SHALL run a reflective quality review.
- IF the reflective review requests revision, THEN THE SYSTEM SHALL rewrite the section using the critique.
- WHEN all sections are complete, THE SYSTEM SHALL run a final editor pass on the full markdown draft.
- WHEN the final post is produced, THE SYSTEM SHALL save it to a safe slug-based markdown filename.

## Non-Functional Requirements

- THE SYSTEM SHALL be readable and maintainable with typed function signatures.
- THE SYSTEM SHALL include docstrings for all workflow functions.
- THE SYSTEM SHALL provide deterministic fallbacks for empty planner or router outputs.

## Edge Cases

- Empty/invalid planner output → fallback sections are used.
- Invalid router destination → `explanatory` is used.
- Non-string LLM response content → normalize to string before use.
