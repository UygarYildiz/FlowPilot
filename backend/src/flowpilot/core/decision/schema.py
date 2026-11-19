"""Modelden istenen çıktı şeması.

Departman ve intent değerleri kayıt defterine göre ayrıca doğrulanır (`engine.validate`).
"""

from typing import Literal

from pydantic import BaseModel, Field

PriorityValue = Literal["low", "normal", "high", "urgent"]


class ModelRoute(BaseModel):
    department: str = Field(description="Departman anahtarı veya 'unknown'.")
    intent: str | None = Field(
        default=None, description="Seçilen departmanın intent anahtarı; 'unknown' için null."
    )
    priority: PriorityValue = Field(description="low | normal | high | urgent")
    confidence: float = Field(ge=0.0, le=1.0, description="Bu rotanın doğru olma olasılığı (0–1).")
    suggested_action: str = Field(description="Departmanın yapması gereken iş, tek cümle.")


class ModelDecision(BaseModel):
    routes: list[ModelRoute] = Field(
        min_length=1, description="Bu e-postayla ilgilenmesi gereken her departman için bir rota."
    )
    reasoning: str = Field(description="Kararın kısa gerekçesi (en fazla 2 cümle, Türkçe).")
