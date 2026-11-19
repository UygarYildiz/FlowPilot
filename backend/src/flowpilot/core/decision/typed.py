"""Karar modeliyle (Clef / Jev) sınıflandırma.

Generatif yoldan farkı: model yalnızca izinli cevaplara olasılık verir, geçersiz cevap üretemez.
Sorular kayıt defterinden kurulur:
    act.<departman>     noul   — "Bu departmanın bu e-postada yapması gereken bir iş var mı?"
    intent.<departman>  choice — departmanın intent'lerinden hangisi?
    priority            score  — düşük / normal / yüksek / acil
Bir departman p(act) ≥ 0,5 ise rota olur; rotanın güveni p(act)'tır.
typed-v3: act yerine `primary` (choice) + `also.<departman>` (noul); p(act) bunlardan hesaplanır.
İnsan incelemesi: rotası olan bir departmanın güveni eşiğin altındaysa, rotası olmayan bir
departman "belki"yse (p ≥ 1 − eşik) ya da hiçbir departman çıkmadıysa.
"""

from dataclasses import dataclass
from typing import Any

from flowpilot.core.decision.engine import Classification
from flowpilot.core.decision.prompt import EmailForDecision, build_user_prompt
from flowpilot.core.decision.schema import ModelRoute, PriorityValue
from flowpilot.core.registry import UNKNOWN, DepartmentRegistry
from flowpilot.llm import LLMError
from flowpilot.llm.decision_model import DecisionModelClient

PROMPT_VERSION = "typed-v2"
# typed-v3: önce "asıl departman hangisi?" (tek seçim), sonra departman başına "ayrıca iş var mı?".
# P(departman) = P(asıl) + (1 − P(asıl)) · P(ayrıca); sonrası (rota, eşik, inceleme) v2 ile aynı.
PROMPT_VERSIONS = ("typed-v2", "typed-v3")
NO_DEPARTMENT = "none"

# typed-v1 bağlamsızdı: model müşteriyi tedarikçiyle karıştırdı (satış e-postaları Satın Alma'ya).
# v2: e-postanın kime geldiği, kimin satıcı/alıcı olduğu baştan söylenir; gönderen rolü sorulur.
COMPANY_CONTEXT = (
    "Bu e-postayı Atlas Endüstri A.Ş. aldı. Atlas Endüstri konveyör makarası, kaplin gibi makine "
    "yedek parçaları üretir ve bunları MÜŞTERİLERİNE SATAR. Hammadde, parça ve hizmetleri ise "
    "TEDARİKÇİLERİNDEN SATIN ALIR. Nakliye/kargo/gümrük firmaları Atlas'ın sevkiyatlarını taşır. "
    "@atlas-endustri.example adresleri Atlas'ın kendi çalışanlarıdır."
)
DIRECTION_HINT = (
    "Remember the direction of trade: a sender who buys from Atlas (orders, order changes, price "
    "or catalogue requests for Atlas products) is a CUSTOMER; a sender who sells to Atlas (quotes, "
    "price lists, invoices for what Atlas bought) is a SUPPLIER."
)
SENDER_ROLES = {
    "supplier": "A company that sells goods or services to Atlas, or wants to",
    "customer": "A company that buys Atlas products, or wants to",
    "carrier": "A shipping, cargo, freight forwarding or customs company",
    "internal": "An Atlas Endüstri employee (@atlas-endustri.example)",
    "other": "Anyone else: newsletters, ads, banks, job applicants, automated messages",
}
ROUTE_CUTOFF = 0.5
PRIORITY_LEVELS: tuple[PriorityValue, ...] = ("low", "normal", "high", "urgent")
PRIORITY_CRITERIA = [
    "Low: informational only, no action needed soon",
    "Normal: routine business work",
    "High: near deadline, complaint, or money at risk",
    "Urgent: needs action today (production stop, urgent delivery)",
]


def build_questions(
    registry: DepartmentRegistry, version: str = PROMPT_VERSION
) -> dict[str, dict[str, Any]]:
    if version not in PROMPT_VERSIONS:
        raise ValueError(f"Bilinmeyen soru sürümü: {version}")
    questions: dict[str, dict[str, Any]] = {
        "sender_role": {
            "type": "choice",
            "instructions": "Who is the sender of this email, from Atlas Endüstri's point of view?",
            "criteria": SENDER_ROLES,
        }
    }
    if version == "typed-v3":
        questions["primary"] = {
            "type": "choice",
            "instructions": (
                "Which department of Atlas Endüstri is mainly responsible for acting on this "
                f"email? Choose none if no department needs to act. {DIRECTION_HINT}"
            ),
            "criteria": {
                **{d.key: f"{d.name}: {d.description}" for d in registry},
                NO_DEPARTMENT: "No department needs to act (ads, newsletters, spam, job "
                "applications, misdirected or automated messages)",
            },
        }
    for department in registry:
        if version == "typed-v3":
            questions[f"also.{department.key}"] = {
                "type": "noul",
                "instructions": (
                    f"Besides the email's main department, does the {department.name} department "
                    f"ALSO have its own work to do on this email? {department.name} handles: "
                    f"{department.description} Answer no if {department.name} is itself the main "
                    "department, or would only be informed."
                ),
            }
        else:
            questions[f"act.{department.key}"] = {
                "type": "noul",
                "instructions": (
                    f"Does the {department.name} department of Atlas Endüstri need to take "
                    f"action on this email? {department.name} handles: {department.description} "
                    "Answer yes only if this department must do some work; being copied for "
                    f"information is not enough. {DIRECTION_HINT}"
                ),
            }
        questions[f"intent.{department.key}"] = {
            "type": "choice",
            "instructions": (
                f"Assuming the {department.name} department handles this email, "
                "what kind of email is it for them?"
            ),
            "criteria": {intent.key: intent.description for intent in department.intents},
        }
    questions["priority"] = {
        "type": "score",
        "instructions": "How urgent is this email for the company?",
        "criteria": PRIORITY_CRITERIA,
    }
    return questions


@dataclass
class DecisionModelClassifier:
    client: DecisionModelClient
    registry: DepartmentRegistry
    model_name: str
    threshold: float = 0.75
    prompt_version: str = PROMPT_VERSION

    def __call__(self, email: EmailForDecision) -> Classification:
        state = f"{COMPANY_CONTEXT}\n\n{build_user_prompt(email)}"
        try:
            questions = build_questions(self.registry, self.prompt_version)
            answers = self.client.ask(state=state, questions=questions)
            if self.prompt_version == "typed-v3":
                _, primary = answers.choice("primary")
                act = {}
                for d in self.registry:
                    main = primary.get(d.key, 0.0)
                    act[d.key] = main + (1 - main) * answers.noul(f"also.{d.key}")
            else:
                act = {d.key: answers.noul(f"act.{d.key}") for d in self.registry}
            intents = {d.key: answers.choice(f"intent.{d.key}") for d in self.registry}
            priority_score, _ = answers.score("priority")
        except LLMError as exc:
            # Karar modeli geçersiz cevap üretemez; bu ancak API sözleşmesi bozulursa olur.
            return Classification(
                routes=[],
                reasoning="",
                needs_review=True,
                review_reason=f"karar modeli cevabı okunamadı: {exc}",
                attempts=1,
                errors=[str(exc)],
            )

        priority = PRIORITY_LEVELS[min(max(round(priority_score), 0), len(PRIORITY_LEVELS) - 1)]
        routed = sorted((key for key, p in act.items() if p >= ROUTE_CUTOFF), key=lambda k: -act[k])
        routes = [
            ModelRoute(
                department=key,
                intent=intents[key][0],
                priority=priority,
                confidence=round(act[key], 4),
                suggested_action="",
            )
            for key in routed
        ]

        review = []
        if not routes:
            top = max(act.values(), default=0.0)
            routes = [
                ModelRoute(
                    department=UNKNOWN,
                    intent=None,
                    priority="low",
                    confidence=round(1 - top, 4),
                    suggested_action="",
                )
            ]
            review.append("hiçbir departmanla eşleşmedi")
        if low := [
            r.department
            for r in routes
            if r.department != UNKNOWN and r.confidence < self.threshold
        ]:
            review.append(f"güven eşiğin ({self.threshold}) altında: {', '.join(low)}")
        if maybe := [k for k, p in act.items() if k not in routed and p >= 1 - self.threshold]:
            review.append(f"belirsiz departman: {', '.join(maybe)}")

        names = {d.key: d.name for d in self.registry}
        reasoning = "Departman olasılıkları: " + ", ".join(
            f"{names[k]} %{round(p * 100)}" for k, p in sorted(act.items(), key=lambda kv: -kv[1])
        )
        return Classification(
            routes=routes,
            reasoning=reasoning,
            needs_review=bool(review),
            review_reason="; ".join(review) or None,
            attempts=1,
            raw_output={
                "act": act,
                "intents": {k: {"choice": c, "probabilities": p} for k, (c, p) in intents.items()},
                "priority_score": priority_score,
                "sender_role": answers.choice("sender_role")[0]
                if "sender_role" in answers.answers
                else None,
            },
        )
