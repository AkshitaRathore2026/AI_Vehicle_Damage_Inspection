from argparse import ArgumentParser
from pathlib import Path
import sys

PROJECT_ROOT = Path(__file__).resolve().parents[2]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from app.ai.model_loader import get_damage_detector
from app.ai.visualization import draw_detections


def parse_args():
    parser = ArgumentParser(description="Run local vehicle damage inference.")
    parser.add_argument("--image", required=True)
    parser.add_argument("--output", default="ml/outputs/inference_result.jpg")
    parser.add_argument("--mock", action="store_true")
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    image_path = Path(args.image)
    if not image_path.exists():
        raise FileNotFoundError(f"Image not found: {image_path}")

    detector = get_damage_detector(use_mock=args.mock)
    detections = detector.detect(image_path)
    output_path = draw_detections(image_path, detections, Path(args.output))

    print(f"Detections: {len(detections)}")
    for detection in detections:
        print(detection)
    print(f"Annotated image saved to: {output_path}")


if __name__ == "__main__":
    main()
