"""Ek dosyalarının saklandığı yer (ADR-009): geliştirmede yerel disk, canlıda S3 uyumlu depolama."""

from pathlib import Path
from typing import Protocol


class AttachmentStorage(Protocol):
    def put(self, key: str, data: bytes) -> None: ...

    def get(self, key: str) -> bytes: ...


class LocalStorage:
    def __init__(self, base_dir: str | Path) -> None:
        self._base = Path(base_dir).resolve()

    def _path(self, key: str) -> Path:
        path = (self._base / key).resolve()
        if not path.is_relative_to(self._base):
            raise ValueError(f"Geçersiz depolama anahtarı: {key}")
        return path

    def put(self, key: str, data: bytes) -> None:
        path = self._path(key)
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(data)

    def get(self, key: str) -> bytes:
        return self._path(key).read_bytes()


class MemoryStorage:
    """Testler için."""

    def __init__(self) -> None:
        self.files: dict[str, bytes] = {}

    def put(self, key: str, data: bytes) -> None:
        self.files[key] = data

    def get(self, key: str) -> bytes:
        return self.files[key]
