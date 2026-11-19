"""Departman sözleşmesi ve kayıt defteri (ADR-004, v1 kapsamı 3.3).

Çekirdek departmanları yalnızca bu sözleşme üzerinden tanır; departman paketlerini import etmez
(MIMARI.md kural 1). Departmanlar `flowpilot.bootstrap` içinde kayıt defterine eklenir.

M2'de yalnızca `key/name/description/intents` kullanılır. Ajan, araçlar, öneri tipleri ve
görünümler M4–M5'te sözleşmeye eklenecek.
"""

from collections.abc import Iterable, Iterator
from dataclasses import dataclass, field

UNKNOWN = "unknown"


@dataclass(frozen=True)
class Intent:
    key: str
    description: str
    examples: tuple[str, ...] = ()


@dataclass(frozen=True)
class Department:
    key: str
    name: str
    description: str
    intents: tuple[Intent, ...] = field(default_factory=tuple)

    def intent_keys(self) -> set[str]:
        return {intent.key for intent in self.intents}


class RegistryError(ValueError):
    pass


class DepartmentRegistry:
    def __init__(self, departments: Iterable[Department] = ()) -> None:
        self._departments: dict[str, Department] = {}
        for department in departments:
            self.register(department)

    def register(self, department: Department) -> None:
        if department.key == UNKNOWN:
            raise RegistryError(f"'{UNKNOWN}' ayrılmış bir anahtardır")
        if department.key in self._departments:
            raise RegistryError(f"Departman zaten kayıtlı: {department.key}")
        if not department.intents:
            raise RegistryError(f"Departmanın en az bir intent'i olmalı: {department.key}")
        keys = [intent.key for intent in department.intents]
        if len(keys) != len(set(keys)):
            raise RegistryError(f"Tekrarlanan intent anahtarı: {department.key}")
        self._departments[department.key] = department

    def get(self, key: str) -> Department | None:
        return self._departments.get(key)

    def keys(self) -> list[str]:
        return list(self._departments)

    def __iter__(self) -> Iterator[Department]:
        return iter(self._departments.values())

    def __len__(self) -> int:
        return len(self._departments)
