# Training Data Schema

`training_pairs.jsonl` stores prompt/completion pairs for fine-tuning CareerGraph's reasoning model.

## Record format

Each line is a JSON object:

```json
{
  "prompt": {
    "system": "You are a career intelligence assistant...",
    "user": "Analyze the skill gap for ..."
  },
  "completion": "Based on your profile...",
  "rating": 5,
  "timestamp": "2025-01-15T10:30:00Z",
  "task_type": "gap_explanation"
}
```

## Fields

| Field | Type | Description |
|---|---|---|
| `prompt.system` | string | System instruction passed to the LLM |
| `prompt.user` | string | User message / context payload |
| `completion` | string | LLM response that was logged |
| `rating` | int \| null | Human rating 1–5 (null = unrated) |
| `timestamp` | string | ISO-8601 UTC timestamp |
| `task_type` | string | One of: `gap_explanation`, `roadmap`, `recommendation_narration` |

## Task types

- **gap_explanation** — explains why a user's readiness score is what it is
- **roadmap** — produces a weekly learning roadmap from a list of missing skills
- **recommendation_narration** — writes a `why_recommended` blurb for a job match

## Usage

Training pairs are appended automatically by `TrainingLogger` in
`app/engine/reasoning/training_logger.py` whenever the `ReasoningAgent` produces
a completion. To export for fine-tuning:

```bash
# Filter to rated pairs only
jq 'select(.rating != null)' data/training_pairs.jsonl > rated_pairs.jsonl
```
