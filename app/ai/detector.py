from dataclasses import dataclass
from pathlib import Path
from typing import Protocol

from app.ai.constants import DAMAGE_CLASS_ID_TO_TYPE
from app.ai.postprocessing import calculate_severity


@dataclass(frozen=True)
class DetectionResult:
    damage_type: str
    confidence: float
    bbox_x1: float
    bbox_y1: float
    bbox_x2: float
    bbox_y2: float
    severity: str
    detected_by_model: str
    model_version: str


class DamageDetector(Protocol):
    def detect(self, image_path: Path) -> list[DetectionResult]:
        """Return damage detections for a single image."""


class MockDamageDetector:
    """Deterministic mock detector for testing the app flow before training YOLO."""

    def __init__(
        self,
        model_name: str = "mock-vehicle-damage-detector",
        model_version: str = "mock-0.1.0",
    ) -> None:
        self.model_name = model_name
        self.model_version = model_version

    def detect(self, image_path: Path) -> list[DetectionResult]:
        from PIL import Image

        with Image.open(image_path) as image:
            width, height = image.size

        box_width = width * 0.28
        box_height = height * 0.20
        x1 = width * 0.36
        y1 = height * 0.42
        x2 = min(width - 1, x1 + box_width)
        y2 = min(height - 1, y1 + box_height)
        confidence = 0.72
        damage_type = "dent"

        return [
            DetectionResult(
                damage_type=damage_type,
                confidence=confidence,
                bbox_x1=round(x1, 2),
                bbox_y1=round(y1, 2),
                bbox_x2=round(x2, 2),
                bbox_y2=round(y2, 2),
                severity=calculate_severity(
                    damage_type=damage_type,
                    confidence=confidence,
                    bbox_x1=x1,
                    bbox_y1=y1,
                    bbox_x2=x2,
                    bbox_y2=y2,
                    image_width=width,
                    image_height=height,
                ),
                detected_by_model=self.model_name,
                model_version=self.model_version,
            )
        ]


class YoloDamageDetector:
    """YOLO detector wrapper for a custom-trained vehicle damage model."""

    def __init__(
        self,
        model_path: Path,
        confidence_threshold: float,
        model_name: str,
        model_version: str,
    ) -> None:
        self.model_path = model_path
        self.confidence_threshold = confidence_threshold
        self.model_name = model_name
        self.model_version = model_version
        self._model = None

    def _load_model(self):
        if not self.model_path.exists():
            raise FileNotFoundError(f"YOLO model not found: {self.model_path}")
        if self._model is None:
            from ultralytics import YOLO

            self._model = YOLO(str(self.model_path))
        return self._model

    def detect(self, image_path: Path) -> list[DetectionResult]:
        from PIL import Image

        model = self._load_model()
        with Image.open(image_path) as image:
            image_width, image_height = image.size

        results = model.predict(
            source=str(image_path),
            conf=self.confidence_threshold,
            verbose=False,
        )

        detections: list[DetectionResult] = []
        for result in results:
            if result.boxes is None:
                continue
            for box in result.boxes:
                class_id = int(box.cls.item())
                damage_type = DAMAGE_CLASS_ID_TO_TYPE.get(class_id)
                if damage_type is None:
                    continue
                confidence = float(box.conf.item())
                x1, y1, x2, y2 = [float(value) for value in box.xyxy[0].tolist()]
                detections.append(
                    DetectionResult(
                        damage_type=damage_type,
                        confidence=round(confidence, 4),
                        bbox_x1=round(x1, 2),
                        bbox_y1=round(y1, 2),
                        bbox_x2=round(x2, 2),
                        bbox_y2=round(y2, 2),
                        severity=calculate_severity(
                            damage_type=damage_type,
                            confidence=confidence,
                            bbox_x1=x1,
                            bbox_y1=y1,
                            bbox_x2=x2,
                            bbox_y2=y2,
                            image_width=image_width,
                            image_height=image_height,
                        ),
                        detected_by_model=self.model_name,
                        model_version=self.model_version,
                    )
                )
        return detections
