from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path

from dotenv import load_dotenv


load_dotenv()


@dataclass(slots=True)
class Settings:
    """Application level configuration loaded from environment variables."""

    database_url: str = os.getenv("FAMILY_DB_URL", "sqlite:///family_tree.db")
    graphviz_engine: str = os.getenv("GRAPHVIZ_ENGINE", "dot")
    assets_dir: Path = Path(os.getenv("FAMILY_ASSETS_DIR", "generated"))
    report_dir: Path = Path(os.getenv("FAMILY_REPORT_DIR", "reports"))
    export_dir: Path = Path(os.getenv("FAMILY_EXPORT_DIR", "exports"))

    @property
    def use_sqlite_fallback(self) -> bool:
        return self.database_url.startswith("sqlite:")


settings = Settings()
for folder in (settings.assets_dir, settings.report_dir, settings.export_dir):
    folder.mkdir(parents=True, exist_ok=True)
