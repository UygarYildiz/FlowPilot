"""Seed/simülasyon adaptörü (ADR-007): kurgusal şirketin e-postalarını dosyadan okur.

Biçim (`emails.json`):
    {"domain": "...", "emails": [{"id", "from", "to", "cc", "subject", "body",
                                   "minutes_ago", "attachments": ["dosya.pdf", ...]}]}
Her e-postanın `Message-ID`'si sabit olduğu için seed tekrar çalıştırılınca kayıt çoğalmaz.
"""

import json
import mimetypes
from collections.abc import Iterator
from datetime import UTC, datetime, timedelta
from pathlib import Path
from typing import Any

from flowpilot.core.ingestion.types import IncomingAttachment, IncomingEmail

_MIME_OVERRIDES = {
    ".xlsx": "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
    ".csv": "text/csv",
}


def _mime(path: Path) -> str:
    return _MIME_OVERRIDES.get(path.suffix.lower()) or (
        mimetypes.guess_type(path.name)[0] or "application/octet-stream"
    )


class SeedSource:
    name = "seed"

    def __init__(self, seed_dir: str | Path, now: datetime | None = None) -> None:
        self._dir = Path(seed_dir)
        self._now = now or datetime.now(UTC)

    def _load(self) -> dict[str, Any]:
        return json.loads((self._dir / "emails.json").read_text(encoding="utf-8"))

    def fetch(self) -> Iterator[IncomingEmail]:
        data = self._load()
        domain = data.get("domain", "seed.invalid")
        for item in data["emails"]:
            attachments = []
            for filename in item.get("attachments", []):
                path = self._dir / "attachments" / filename
                attachments.append(
                    IncomingAttachment(
                        filename=filename, mime=_mime(path), content=path.read_bytes()
                    )
                )
            yield IncomingEmail(
                message_id=f"<{item['id']}@{domain}>",
                from_addr=item["from"].lower(),
                to_addrs=[a.lower() for a in item.get("to", [])],
                cc_addrs=[a.lower() for a in item.get("cc", [])],
                subject=item["subject"],
                body_text=item["body"].strip(),
                received_at=self._now - timedelta(minutes=item.get("minutes_ago", 0)),
                attachments=attachments,
            )
