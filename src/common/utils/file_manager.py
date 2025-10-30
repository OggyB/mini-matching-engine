import json
from pathlib import Path
from loguru import logger


class FileManager:
    """
    Simple file manager for reading and writing JSON lines.
    """
    def __init__(self, filepath: str):
        """Initialize the file manager."""
        self.path = Path(filepath).resolve()
        try:
            if not self.path.parent.exists():
                self.path.parent.mkdir(parents=True, exist_ok=True)
                logger.debug(f"Created directory: {self.path.parent}")
        except Exception as e:
            logger.error(f"Failed to create directory {self.path.parent}: {e}")

    def write_json(self, data: dict | list, append: bool = True) -> None:
        """ Write JSON data to file (line by line)."""
        mode = "a" if append else "w"

        try:
            with self.path.open(mode, encoding="utf-8") as f:
                if isinstance(data, list):
                    for item in data:
                        f.write(json.dumps(item, ensure_ascii=False) + "\n")
                else:
                    f.write(json.dumps(data, ensure_ascii=False) + "\n")

            logger.debug(f"Wrote data to {self.path}")
        except Exception as e:
            logger.error(f"Failed to write to {self.path}: {e}")

    def read_json(self) -> list[dict]:
        """Read and parse all JSON lines from file."""
        if not self.path.exists():
            logger.error(f"File not found: {self.path}")
            return []

        items = []
        with self.path.open("r", encoding="utf-8") as f:
            for i, line in enumerate(f, start=1):
                line = line.strip()
                if not line:
                    continue
                try:
                    items.append(json.loads(line))
                except json.JSONDecodeError as e:
                    logger.warning(f"Skipping malformed JSON on line {i}: {e}")

        logger.info(f"Loaded {len(items)} records from {self.path}")
        return items

    def clear(self) -> None:
        """Clear all file contents."""
        try:
            self.path.write_text("")
            logger.debug(f"Cleared file: {self.path}")
        except Exception as e:
            logger.error(f"Failed to clear {self.path}: {e}")
