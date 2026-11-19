"""Satın Alma departmanı (v1: ajanlı; ADR-015).

`DEPARTMENT` ajansız tanımdır (kayıt defteri, karar motoru, testler). Ajanlı hâli `with_agent`.
"""

from collections.abc import Callable
from dataclasses import replace

from flowpilot.core.registry import Department, Intent
from flowpilot.llm import LLMClient

DEPARTMENT = Department(
    key="procurement",
    name="Satın Alma",
    description=(
        "Tedarikçilerle ilişkiler ve şirketin dışarıdan mal/hizmet alımı: tedarikçi teklifleri, "
        "fiyat listeleri, satın alma talepleri, tedarikçiye verilen siparişler."
    ),
    intents=(
        Intent(
            "new_quote",
            "Bir tedarikçi şirketimize fiyat teklifi gönderiyor (çoğunlukla PDF/Excel ekli).",
            ("SAT-2026-031 talebiniz için fiyat teklifimiz ektedir.",),
            label="Yeni teklif",
        ),
        Intent(
            "price_update",
            "Bir tedarikçi fiyat listesini veya ürün fiyatlarını güncelliyor.",
            ("1 Aralık itibarıyla geçerli güncel fiyat listemiz ektedir.",),
            label="Fiyat güncellemesi",
        ),
        Intent(
            "order_status_inquiry",
            "Bir tedarikçi, şirketimizin ona verdiği siparişin durumunu soruyor ya da teyit "
            "istiyor.",
            ("PO-2026-0902 siparişinin imzalı formu bize ulaşmadı, teyit eder misiniz?",),
            label="Sipariş durumu sorusu",
        ),
        Intent(
            "supplier_complaint",
            "Bir tedarikçi şikâyet, itiraz veya anlaşmazlık bildiriyor.",
            ("Şartname değişikliği bize yazılı bildirilmedi ve ek maliyet doğurdu.",),
            label="Tedarikçi şikâyeti",
        ),
        Intent(
            "purchase_request",
            "Şirket içinden bir birim malzeme veya hizmet satın alınmasını talep ediyor.",
            ("Hat 3 bakımı için 2 adet pompa ve 12 filtre gerekiyor.",),
            label="İç satın alma talebi",
        ),
    ),
)


def with_agent(llm_factory: Callable[[], LLMClient]) -> Department:
    """Ajanlı Satın Alma (ADR-015). Model bileşim kökünde, ilk kullanımda kurulur."""
    from flowpilot.departments.procurement.actions import PROPOSAL_TYPES
    from flowpilot.departments.procurement.agent import ProcurementAgent
    from flowpilot.departments.procurement.tools import TOOLS

    return replace(
        DEPARTMENT,
        agent=ProcurementAgent(llm_factory),
        proposal_types=PROPOSAL_TYPES,
        tools=TOOLS,
    )
