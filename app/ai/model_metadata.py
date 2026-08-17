from dataclasses import dataclass
from pathlib import Path

from app.ai.constants import DAMAGE_CLASS_ID_TO_TYPE
from app.core.config import get_settings


@dataclass(frozen=True)
class ModelMetadata:
    model_name: str
    model_version: str
    model_path: str
    confidence_threshold: float
    class_mapping: dict[int, str]
    status: str


def get_model_metadata(use_mock: bool | None = None) -> ModelMetadata:
    settings = get_settings()
    if use_mock is None:
        use_mock = settings.use_mock_detector

    if use_mock:
        return ModelMetadata(
            model_name="mock-vehicle-damage-detector",
            model_version="mock-0.1.0",
            model_path="not_applicable",
            confidence_threshold=settings.model_confidence_threshold,
            class_mapping=DAMAGE_CLASS_ID_TO_TYPE,
            status="mock",
        )

    model_path = Path(settings.model_path)
    return ModelMetadata(
        model_name=settings.model_name,
        model_version=settings.model_version,
        model_path=str(model_path),
        confidence_threshold=settings.model_confidence_threshold,
        class_mapping=DAMAGE_CLASS_ID_TO_TYPE,
        status="ready" if model_path.exists() else "missing",
    )
