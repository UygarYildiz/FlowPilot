"""Yanıt taslakları (`order_status_inquiry`, `supplier_complaint` → `reply_draft`; ADR-016).

Önce e-postadaki referanslar bulunur ve kayıtlarda aranır; model yalnızca e-postaya ve
bulunan kayıtlara dayanarak özet, öncelik önerisi ve yanıt taslağı yazar. Taslaktaki her sayı
e-postada ya da kayıtlarda geçmeli; geçmeyen uyarı olarak işaretlenir. Hiçbir e-posta gönderilmez.
"""

import json
import re
from typing import Any, Literal

from pydantic import BaseModel, Field

from flowpilot.departments.procurement.validation import Issue, numbers_in
from flowpilot.llm import LLMClient

TASK = "procurement.reply_draft"
REFERENCE = re.compile(r"\b(?:PO|SAT|SO|TK|AR)-\d{2,4}-\d{2,5}\b", re.IGNORECASE)
KIND_LABEL = {"order_status_inquiry": "sipariş durumu", "supplier_complaint": "tedarikçi şikâyeti"}

SYSTEM = """Sen Atlas Endüstri A.Ş.'nin satın alma biriminde çalışan bir asistansın.
Bir tedarikçinin e-postasını okuyup satın alma uzmanı için kısa bir özet, öncelik önerisi ve
Türkçe bir yanıt TASLAĞI hazırlayacaksın. Taslağı bir insan onaylayacak; sen hiçbir şey
göndermiyorsun.

Kurallar:
- Yalnızca e-postada ve sana verilen "Kayıtlarda bulunanlar" bölümünde yazan bilgileri kullan.
- Kayıtlarda olmayan tarih, tutar, miktar ya da teslim sözü YAZMA. Bilmediğin bir şey için
  "kontrol edip size dönüş yapacağız" de.
- Kayıt bulunamadıysa bunu taslakta açıkça belirt ve kontrol edeceğimizi yaz.
- Şikâyette suçlama ya da kabul yapma; konuyu ciddiye aldığımızı ve ilgili birimlerle görüşeceğimizi
  yaz. Toplantı talebi varsa uygun zamanları ileteceğimizi söyle, tarih uydurma.
- Öncelik: low (bilgi), normal (rutin), high (şikâyet, teslim riski, para), urgent (bugün işlem
  gerektiriyor). Gerekçesini tek cümleyle yaz.
- Yanıt nazik, kısa ve imzası "Atlas Endüstri Satın Alma" olsun.
"""


class ReplyExtraction(BaseModel):
    summary: str = Field(description="Satın alma uzmanı için 1-2 cümlelik özet")
    priority: Literal["low", "normal", "high", "urgent"]
    priority_reason: str
    reply_subject: str
    reply_body: str


class ReplyDraftData(BaseModel):
    """`reply_draft` önerisinin verisi."""

    kind: str
    to: str
    subject: str
    body: str
    summary: str
    priority: Literal["low", "normal", "high", "urgent"]
    priority_reason: str
    references: list[str] = Field(default_factory=list)
    records: list[dict[str, Any]] = Field(default_factory=list)
    issues: list[Issue] = Field(default_factory=list)


def references_in(*texts: str) -> list[str]:
    found: list[str] = []
    for text in texts:
        for match in REFERENCE.findall(text):
            ref = match.upper()
            if ref not in found:
                found.append(ref)
    return found


def build_prompt(
    *, kind: str, sender: str, subject: str, body: str, records: list[dict[str, Any]]
) -> str:
    found = (
        json.dumps(records, ensure_ascii=False, indent=1)
        if records
        else "Bu e-postadaki referanslar için kayıt bulunamadı."
    )
    return (
        f"Tür: {KIND_LABEL.get(kind, kind)}\nGönderen: {sender}\nKonu: {subject}\n\n"
        f"--- E-POSTA ---\n{body[:8000]}\n--- SON ---\n\n"
        f"--- KAYITLARDA BULUNANLAR ---\n{found}\n--- SON ---"
    )


def draft_reply(
    llm: LLMClient,
    *,
    kind: str,
    sender: str,
    subject: str,
    body: str,
    records: list[dict[str, Any]],
    references: list[str],
) -> ReplyDraftData:
    prompt = build_prompt(kind=kind, sender=sender, subject=subject, body=body, records=records)
    out = llm.generate(task=TASK, system=SYSTEM, prompt=prompt, schema=ReplyExtraction)
    allowed = numbers_in(f"{subject}\n{body}\n{json.dumps(records, ensure_ascii=False)}")
    issues = []
    for value in sorted(numbers_in(out.reply_body) - allowed):
        issues.append(
            Issue(
                field="body",
                level="warning",
                message=f"Taslaktaki {value} sayısı e-postada ve kayıtlarda geçmiyor; kontrol et.",
            )
        )
    return ReplyDraftData(
        kind=kind,
        to=sender,
        subject=out.reply_subject,
        body=out.reply_body,
        summary=out.summary,
        priority=out.priority,
        priority_reason=out.priority_reason,
        references=references,
        records=records,
        issues=issues,
    )
