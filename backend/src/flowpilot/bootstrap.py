"""Bileşim kökü: departmanları çekirdeğin kayıt defterine bağlar.

Çekirdek departman paketlerini import etmez (MIMARI.md kural 1); bu dosya çekirdeğin dışındadır.
Yeni departman = `departments/` altına yeni paket + aşağıdaki listeye bir satır (kural 4).
"""

from functools import lru_cache

from flowpilot.core.registry import DepartmentRegistry
from flowpilot.departments import finance, logistics, procurement, sales_orders

DEPARTMENTS = (
    procurement.DEPARTMENT,
    finance.DEPARTMENT,
    sales_orders.DEPARTMENT,
    logistics.DEPARTMENT,
)


@lru_cache
def get_registry() -> DepartmentRegistry:
    return DepartmentRegistry(DEPARTMENTS)
