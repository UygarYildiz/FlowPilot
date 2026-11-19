"""Decision Engine prompt'u. Departman ve intent listesi kayıt defterinden kurulur.

Prompt değiştiğinde `PROMPT_VERSION` artırılır; her karar hangi sürümle verildiğini saklar.
"""

from dataclasses import dataclass, field

from flowpilot.core.registry import UNKNOWN, DepartmentRegistry

PROMPT_VERSION = "decision-v1"

# Ek metinlerinden karar için yeterli bir kesit alınır (tam metin ajanlara gider).
ATTACHMENT_EXCERPT_CHARS = 1500


@dataclass(frozen=True)
class AttachmentForDecision:
    filename: str
    text: str | None
    parse_status: str


@dataclass(frozen=True)
class EmailForDecision:
    from_addr: str
    subject: str
    body_text: str
    to_addrs: list[str] = field(default_factory=list)
    cc_addrs: list[str] = field(default_factory=list)
    attachments: list[AttachmentForDecision] = field(default_factory=list)


def build_system_prompt(registry: DepartmentRegistry) -> str:
    lines = [
        "Atlas Endüstri A.Ş.'ye gelen kurumsal e-postaları sınıflandıran bir yönlendirme "
        "motorusun.",
        "Görevin: e-postayla hangi departman(lar)ın ilgilenmesi gerektiğine, her biri için amacına",
        "(intent), önceliğine ve önerilen işe karar vermek.",
        "",
        "Departmanlar ve intent'ler:",
    ]
    for department in registry:
        lines.append(f"\n## {department.key} — {department.name}\n{department.description}")
        for intent in department.intents:
            example = f' Örnek: "{intent.examples[0]}"' if intent.examples else ""
            lines.append(f"- {intent.key}: {intent.description}{example}")
    lines += [
        "",
        "Kurallar:",
        f"- department yalnızca yukarıdaki anahtarlardan biri ya da '{UNKNOWN}' olabilir.",
        "- intent, seçilen departmanın listesindeki anahtarlardan biri olmalı. "
        f"'{UNKNOWN}' için intent null.",
        "- E-posta birden fazla departmandan iş gerektiriyorsa her biri için ayrı rota ver. "
        "Yalnızca bilgi için CC'deki bir departmana rota verme; iş gerektirmeli.",
        f"- Hiçbir departmanla ilgili değilse (reklam, duyuru, belirsiz iç yazışma) tek rota: "
        f"'{UNKNOWN}'.",
        "- confidence dürüst olsun: emin değilsen düşük ver. Tahmin yürütme; belirsiz e-postalar "
        "insan incelemesine gider ve bu iyi bir şeydir.",
        "- priority: urgent = bugün aksiyon gerekir (duruş, acil teslim); high = yakın tarihli "
        "taahhüt, şikâyet, para kaybı riski; normal = olağan iş; low = bilgi amaçlı.",
        "- Alıcı adresi (ör. satinalma@) bir ipucudur ama içerik önceliklidir: yanlış adrese "
        "gönderilmiş e-postayı içeriğe göre yönlendir.",
        "- reasoning ve suggested_action Türkçe ve kısa olsun.",
    ]
    return "\n".join(lines)


def build_user_prompt(email: EmailForDecision) -> str:
    parts = [
        f"Gönderen: {email.from_addr}",
        f"Alıcı: {', '.join(email.to_addrs) or '-'}",
    ]
    if email.cc_addrs:
        parts.append(f"CC: {', '.join(email.cc_addrs)}")
    parts += [f"Konu: {email.subject}", "", "Gövde:", email.body_text or "(boş)"]
    for attachment in email.attachments:
        parts.append(f"\nEk: {attachment.filename} ({attachment.parse_status})")
        if attachment.text:
            excerpt = attachment.text[:ATTACHMENT_EXCERPT_CHARS]
            suffix = " …(kısaltıldı)" if len(attachment.text) > ATTACHMENT_EXCERPT_CHARS else ""
            parts.append(excerpt + suffix)
    return "\n".join(parts)
