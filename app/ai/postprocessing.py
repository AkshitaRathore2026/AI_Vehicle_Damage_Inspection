HIGH_RISK_DAMAGE_TYPES = {"broken_glass", "bumper_damage"}


def calculate_bbox_area_ratio(
    bbox_x1: float,
    bbox_y1: float,
    bbox_x2: float,
    bbox_y2: float,
    image_width: int,
    image_height: int,
) -> float:
    bbox_width = max(0.0, bbox_x2 - bbox_x1)
    bbox_height = max(0.0, bbox_y2 - bbox_y1)
    image_area = max(1, image_width * image_height)
    return (bbox_width * bbox_height) / image_area


def calculate_severity(
    damage_type: str,
    confidence: float,
    bbox_x1: float,
    bbox_y1: float,
    bbox_x2: float,
    bbox_y2: float,
    image_width: int,
    image_height: int,
) -> str:
    area_ratio = calculate_bbox_area_ratio(
        bbox_x1=bbox_x1,
        bbox_y1=bbox_y1,
        bbox_x2=bbox_x2,
        bbox_y2=bbox_y2,
        image_width=image_width,
        image_height=image_height,
    )

    if damage_type in HIGH_RISK_DAMAGE_TYPES and confidence >= 0.65:
        return "high"
    if confidence >= 0.80 or area_ratio >= 0.08:
        return "high"
    if confidence >= 0.55 or area_ratio >= 0.03:
        return "medium"
    return "low"
