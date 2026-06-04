"""Training data logger — captures (prompt, completion) pairs for fine-tuning."""
import json
import logging
from pathlib import Path

logger = logging.getLogger(__name__)

_DEFAULT_OUTPUT = Path(__file__).parent.parent.parent.parent / "data" / "training_pairs.jsonl"


class TrainingLogger:
    """
    Appends JSONL training examples suitable for supervised fine-tuning.

    Schema per line matches the OpenAI fine-tuning format:
      {"messages": [...], "completion": "...", "rating": null}

    Failure to log never raises — it only emits a debug log entry.
    """

    def __init__(self, output_path: Path | None = None):
        self.output_path = output_path or _DEFAULT_OUTPUT

    def log_pair(self, prompt: dict, completion: str, rating: int | None = None) -> None:
        """Append one training pair. Silent on failure."""
        try:
            self.output_path.parent.mkdir(parents=True, exist_ok=True)
            entry: dict = {**prompt, "completion": completion}
            if rating is not None:
                entry["rating"] = rating
            with open(self.output_path, "a", encoding="utf-8") as fh:
                fh.write(json.dumps(entry) + "\n")
        except Exception as exc:
            logger.debug(f"TrainingLogger: could not write pair: {exc}")
