"""Load and resolve site.config.yaml."""
from __future__ import annotations

from pathlib import Path
from typing import Any
from urllib.parse import urlparse

import yaml


class Config:
    def __init__(self, path: Path):
        self.path = path.resolve()
        self.root = self.path.parent
        self.data: dict[str, Any] = yaml.safe_load(self.path.read_text()) or {}

    def section(self, name: str) -> dict[str, Any]:
        return self.data.get(name) or {}

    def resolve(self, rel: str | None) -> Path | None:
        return (self.root / rel) if rel else None

    @property
    def site(self) -> dict[str, Any]:
        return self.section("site")

    @property
    def vocab(self) -> dict[str, Any]:
        return self.section("vocabulary")

    @property
    def site_url(self) -> str:
        return str(self.site.get("url", "")).rstrip("/")

    @property
    def base_path(self) -> str:
        """URL path the site is served under, e.g. '/repo' or '' at a domain root."""
        return urlparse(self.site_url).path.rstrip("/")

    @property
    def namespace(self) -> str:
        return self.vocab["namespace"]

    @property
    def prefix(self) -> str:
        return self.vocab["curie_prefix"]

    def field(self, role: str) -> str:
        defaults = {
            "id": "id",
            "label": "preferred_label",
            "definition": "definition",
            "synonyms": "synonyms",
            "parents": "parents",
        }
        return (self.vocab.get("fields") or {}).get(role, defaults[role])

    @property
    def relations(self) -> dict[str, dict[str, Any]]:
        return self.vocab.get("relations") or {}
