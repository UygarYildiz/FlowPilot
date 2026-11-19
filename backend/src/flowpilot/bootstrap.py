"""Bileşim kökü: departmanları çekirdeğin kayıt defterine bağlar.

Çekirdek departman paketlerini import etmez (MIMARI.md kural 1); bu dosya çekirdeğin dışındadır.
Yeni departman = `departments/` altına yeni paket + aşağıdaki listeye bir satır (kural 4).
"""

from functools import lru_cache

from flowpilot.core.registry import DepartmentRegistry
from flowpilot.departments import finance, logistics, procurement, sales_orders
from flowpilot.llm import LLMClient

DEPARTMENTS = (
    procurement.DEPARTMENT,
    finance.DEPARTMENT,
    sales_orders.DEPARTMENT,
    logistics.DEPARTMENT,
)


def _llm() -> LLMClient:
    from flowpilot.config import get_settings
    from flowpilot.llm.factory import build_llm

    return build_llm(get_settings())[0]


@lru_cache
def get_registry() -> DepartmentRegistry:
    """Çalışan sistemin kayıt defteri: Satın Alma ajanlı (ADR-015); model ilk kullanımda kurulur."""
    return DepartmentRegistry(
        procurement.with_agent(_llm) if d.key == procurement.DEPARTMENT.key else d
        for d in DEPARTMENTS
    )
