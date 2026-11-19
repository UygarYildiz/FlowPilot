import pytest

from flowpilot.bootstrap import get_registry
from flowpilot.core.registry import Department, DepartmentRegistry, Intent, RegistryError

INTENT = Intent("x", "açıklama")


def test_bootstrap_registers_four_departments() -> None:
    assert get_registry().keys() == ["procurement", "finance", "sales_orders", "logistics"]


def test_rejects_reserved_duplicate_and_empty() -> None:
    registry = DepartmentRegistry([Department("a", "A", "", (INTENT,))])
    with pytest.raises(RegistryError):
        registry.register(Department("a", "A", "", (INTENT,)))
    with pytest.raises(RegistryError):
        registry.register(Department("unknown", "?", "", (INTENT,)))
    with pytest.raises(RegistryError):
        registry.register(Department("b", "B", ""))
    with pytest.raises(RegistryError):
        registry.register(Department("c", "C", "", (INTENT, INTENT)))


def test_test_department_can_be_added_without_core_changes() -> None:
    """Başarı kriteri 9'un ilk adımı: yeni departman yalnızca kayıtla eklenir."""
    registry = DepartmentRegistry([*get_registry(), Department("quality", "Kalite", "", (INTENT,))])
    assert registry.get("quality") is not None
    assert len(registry) == 5
