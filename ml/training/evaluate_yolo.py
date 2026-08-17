from argparse import ArgumentParser
from pathlib import Path
import sys

PROJECT_ROOT = Path(__file__).resolve().parents[2]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from ultralytics import YOLO


def parse_args():
    parser = ArgumentParser(description="Evaluate a trained YOLO damage model.")
    parser.add_argument("--data", default="ml/dataset/dataset.yaml")
    parser.add_argument("--weights", default="ml/weights/best.pt")
    parser.add_argument("--imgsz", type=int, default=640)
    parser.add_argument("--device", default="cpu")
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    weights_path = Path(args.weights)
    if not weights_path.exists():
        raise FileNotFoundError(f"Model weights not found: {weights_path}")

    model = YOLO(str(weights_path))
    metrics = model.val(
        data=args.data,
        imgsz=args.imgsz,
        device=args.device,
    )
    print(metrics)


if __name__ == "__main__":
    main()
