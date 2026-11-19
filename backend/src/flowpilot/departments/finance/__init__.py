"""Finans departmanı (v1: ajansız, manuel işlenir; ajan v2'de)."""

from flowpilot.core.registry import Department, Intent

DEPARTMENT = Department(
    key="finance",
    name="Finans",
    description=(
        "Faturalar, ödemeler ve tahsilatlar: tedarikçilerden gelen faturalar, müşterilerin ödeme "
        "bildirimleri, ödeme durumu soruları, fatura itirazları."
    ),
    intents=(
        Intent(
            "invoice_received",
            "Bir tedarikçi şirketimize fatura gönderiyor (e-fatura, PDF fatura).",
            ("OZR2026000412 numaralı e-faturanız ektedir.",),
        ),
        Intent(
            "payment_notice",
            "Bir müşteri ödeme yaptığını bildiriyor (EFT/havale dekontu).",
            ("ATL-2026-1156 faturasının ödemesi bugün EFT ile gönderildi.",),
        ),
        Intent(
            "payment_status_inquiry",
            "Bir tedarikçi kendisine yapılacak ödemenin durumunu soruyor.",
            ("Vadesi geçen faturamızın ödemesi ne zaman yapılacak?",),
        ),
        Intent(
            "invoice_dispute",
            "Bir müşteri kendisine kesilen faturada hata bildiriyor veya düzeltme istiyor.",
            ("Faturada teslim edilmeyen ürünler de faturalandırılmış.",),
        ),
    ),
)
