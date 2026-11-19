"""Satış ve Sipariş departmanı (v1: ajansız, manuel işlenir; ajan v3'te)."""

from flowpilot.core.registry import Department, Intent

DEPARTMENT = Department(
    key="sales_orders",
    name="Satış ve Sipariş",
    description=(
        "Müşterilerin şirketimizden aldığı ürünler: yeni siparişler, sipariş değişiklikleri, "
        "müşterilerin sipariş durumu soruları, fiyat/ürün talepleri."
    ),
    intents=(
        Intent(
            "new_order",
            "Bir müşteri şirketimize yeni sipariş veriyor.",
            ("Aşağıdaki ürünler için sipariş vermek istiyoruz: 8 adet tahrik makarası.",),
            label="Yeni sipariş",
        ),
        Intent(
            "order_change",
            "Bir müşteri mevcut siparişinde değişiklik veya iptal istiyor.",
            ("SO-2026-0440 siparişindeki miktarı 10'dan 14'e çıkarmak istiyoruz.",),
            label="Sipariş değişikliği",
        ),
        Intent(
            "order_status_inquiry",
            "Bir müşteri verdiği siparişin durumunu soruyor.",
            ("Geçen hafta verdiğimiz sipariş ne zaman sevk edilecek?",),
            label="Sipariş durumu sorusu",
        ),
        Intent(
            "customer_request",
            "Bir müşteri fiyat teklifi, ürün bilgisi veya katalog istiyor ya da memnuniyetsizlik "
            "bildiriyor.",
            ("ATL-KNV-220 için güncel fiyat ve teslim süresi alabilir miyiz?",),
            label="Müşteri talebi",
        ),
    ),
)
