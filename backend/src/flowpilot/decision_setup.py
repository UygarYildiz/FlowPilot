"""Ayarlara göre sınıflandırıcıyı kurar (bileşim kökü; çekirdeğin dışında).

FLOWPILOT_DECISION_ENGINE=llm       → generatif model (FLOWPILOT_LLM_PROVIDER: fake | gemini)
FLOWPILOT_DECISION_ENGINE=clef      → Cloudflare Clef karar modeli (FLOWPILOT_CLEF_MODEL)
FLOWPILOT_DECISION_ENGINE=subq      → SubQ Snap karar modeli (FLOWPILOT_SUBQ_MODEL, SUBQ_API_KEY)
"""

from flowpilot.config import Settings
from flowpilot.core.decision.engine import Classifier, LLMClassifier
from flowpilot.core.decision.typed import DecisionModelClassifier
from flowpilot.core.registry import DepartmentRegistry
from flowpilot.llm import LLMError
from flowpilot.llm.factory import build_llm


def build_classifier(
    settings: Settings, registry: DepartmentRegistry, engine: str | None = None
) -> Classifier:
    engine = engine or settings.decision_engine
    if engine == "llm":
        llm, model_name = build_llm(settings)
        return LLMClassifier(llm, registry, model_name, threshold=settings.decision_threshold)
    if engine == "clef":
        from flowpilot.llm.decision_model import ClefClient

        client = ClefClient(
            account_id=settings.cloudflare_account_id,
            api_token=settings.cloudflare_api_token,
            model=settings.clef_model,
        )
        return DecisionModelClassifier(
            client,
            registry,
            f"cloudflare:{settings.clef_model}",
            threshold=settings.decision_threshold,
            prompt_version=settings.typed_prompt,
        )
    if engine == "subq":
        from flowpilot.llm.decision_model import SubQClient

        subq = SubQClient(api_key=settings.subq_api_key, model=settings.subq_model)
        return DecisionModelClassifier(
            subq,
            registry,
            f"subq:{settings.subq_model}",
            threshold=settings.decision_threshold,
            prompt_version=settings.typed_prompt,
        )
    raise LLMError(f"Bilinmeyen karar motoru: {engine}")
