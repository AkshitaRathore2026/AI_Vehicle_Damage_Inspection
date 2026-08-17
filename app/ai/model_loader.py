from pathlib import Path

from app.ai.detector import DamageDetector, MockDamageDetector, YoloDamageDetector
from app.core.config import get_settings


def get_damage_detector(use_mock: bool | None = None) -> DamageDetector:
    settings = get_settings()
    if use_mock is None:
        use_mock = settings.use_mock_detector
    if use_mock:
        return MockDamageDetector()

    return YoloDamageDetector(
        model_path=Path(settings.model_path),
        confidence_threshold=settings.model_confidence_threshold,
        model_name=settings.model_name,
        model_version=settings.model_version,
    )
