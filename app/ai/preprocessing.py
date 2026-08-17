from pathlib import Path

from PIL import Image


def validate_readable_image(image_path: Path) -> tuple[int, int]:
    with Image.open(image_path) as image:
        image.verify()

    with Image.open(image_path) as image:
        return image.size


def load_image_size(image_path: Path) -> tuple[int, int]:
    with Image.open(image_path) as image:
        return image.size
