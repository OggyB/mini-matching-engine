from pathlib import Path
import yaml
from common.models.config import Settings


def load_settings(file_path: str | Path | None = None) -> Settings:
    """Application configuration loader for all modules."""
    base_dir = Path(__file__).resolve().parents[3]
    yaml_path = file_path or (base_dir / "settings.yaml")

    with open(yaml_path, "r") as f:
        data = yaml.safe_load(f)

    return Settings(**data)


# singleton instance that shared by all modules
settings = load_settings()
