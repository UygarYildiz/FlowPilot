"""Karar modeliyle (Clef / Jev) sınıflandırma.

Generatif yoldan farkı: model yalnızca izinli cevaplara olasılık verir, geçersiz cevap üretemez.
Sorular kayıt defterinden kurulur:
    act.<departman>     noul   — "Bu departmanın bu e-postada yapması gereken bir iş var mı?"
    intent.<departman>  choice — departmanın intent'lerinden hangisi?
    priority            score  — düşük / normal / yüksek / acil
Bir departman p(act) ≥ 0,5 ise rota olur; rotanın güveni p(act)'tır.
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

PROMPT_VERSION = "typed-v1"
ROUTE_CUTOFF = 0.5
PRIORITY_LEVELS: tuple[PriorityValue, ...] = ("low", "normal", "high", "urgent")
PRIORITY_CRITERIA = [
    "Low: informational only, no action needed soon",
    "Normal: routine business work",
    "High: near deadline, complaint, or money at risk",
    "Urgent: needs action today (production stop, urgent delivery)",
]


def build_questions(registry: DepartmentRegistry) -> dict[str, dict[str, Any]]:
    questions: dict[str, dict[str, Any]] = {}
    for department in registry:
        questions[f"act.{department.key}"] = {
            "type": "noul",
            "instructions": (
                f"Does the {department.name} department of Atlas Endüstri need to take action on "
                f"this email? {department.name} handles: {department.description} "
                "Answer yes only if this department must do some work; being copied for "
                "information is not enough."
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
        state = build_user_prompt(email)
        try:
            answers = self.client.ask(state=state, questions=build_questions(self.registry))
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
            },
        )
