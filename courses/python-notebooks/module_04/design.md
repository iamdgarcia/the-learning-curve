# Design

## Architecture

The pipeline uses a sequential orchestrator with pattern composition:

1. **Planning pattern**: planner returns ordered sections.
2. **Routing pattern**: per-section router selects specialist destination.
3. **Execution pattern**: specialized researcher/writer chains produce section drafts.
4. **Reflection pattern**: section critique gate decides approve vs revise.
5. **Final editorial pass**: full draft is polished and persisted.

## Data Models

- `Outline`: planner JSON schema (`sections: List[str]`).
- `Route`: router JSON schema (`destination`).
- `Review`: reflective QA schema (`verdict`, `critique`).

## Workflow

- `run_content_pipeline(topic)` orchestrates full execution.
- `plan_sections(topic)` creates ordered sections.
- `route_section(section_title, topic)` picks specialist style.
- `research_and_write_section(...)` generates section text.
- `reflect_and_improve(...)` reviews and revises if needed.
- `message_to_text(...)` normalizes LLM outputs for type-safe writes.

## Error Handling Matrix

- Planner returns no sections → fallback outline.
- Router returns unknown destination → default to `explanatory`.
- LLM returns list payload instead of string → normalize and continue.

## Testing Strategy

- Static validation via editor diagnostics (`get_errors`).
- Runtime smoke test by executing `final_project.py` with valid API keys.
