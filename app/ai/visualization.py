from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

from app.ai.constants import DAMAGE_LABELS
from app.ai.detector import DetectionResult


BOX_COLORS = {
    "low": "#2E7D32",
    "medium": "#F9A825",
    "high": "#C62828",
}


def draw_detections(
    image_path: Path,
    detections: list[DetectionResult],
    output_path: Path,
) -> Path:
    output_path.parent.mkdir(parents=True, exist_ok=True)

    with Image.open(image_path).convert("RGB") as image:
        draw = ImageDraw.Draw(image)
        font = ImageFont.load_default()

        for detection in detections:
            color = BOX_COLORS[detection.severity]
            box = [
                detection.bbox_x1,
                detection.bbox_y1,
                detection.bbox_x2,
                detection.bbox_y2,
            ]
            draw.rectangle(box, outline=color, width=3)
            label = (
                f"{DAMAGE_LABELS[detection.damage_type]} "
                f"{detection.confidence:.2f} {detection.severity}"
            )
            text_box = draw.textbbox((box[0], box[1]), label, font=font)
            text_height = text_box[3] - text_box[1]
            text_width = text_box[2] - text_box[0]
            label_y = max(0, box[1] - text_height - 4)
            draw.rectangle(
                [box[0], label_y, box[0] + text_width + 4, label_y + text_height + 4],
                fill=color,
            )
            draw.text((box[0] + 2, label_y + 2), label, fill="white", font=font)

        image.save(output_path)

    return output_path
