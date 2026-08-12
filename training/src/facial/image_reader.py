from dataclasses import dataclass
from io import BytesIO
from pathlib import Path

import cv2
import numpy as np
from PIL import Image, UnidentifiedImageError


class ImageReadError(ValueError):
    pass


@dataclass(frozen=True)
class LoadedImage:
    content: bytes
    bgr: np.ndarray
    image_format: str
    width: int
    height: int


def read_image(path: str | Path) -> LoadedImage:
    source = Path(path)
    try:
        content = source.read_bytes()
    except OSError as exc:
        raise ImageReadError("No fue posible leer el archivo.") from exc
    try:
        with Image.open(BytesIO(content)) as image:
            image.load()
            image_format = str(image.format or "").upper()
            width, height = image.size
    except (UnidentifiedImageError, OSError) as exc:
        raise ImageReadError("El archivo no contiene una imagen legible.") from exc
    array = np.frombuffer(content, dtype=np.uint8)
    bgr = cv2.imdecode(array, cv2.IMREAD_COLOR)
    if bgr is None:
        raise ImageReadError("OpenCV no pudo decodificar la imagen.")
    return LoadedImage(
        content=content,
        bgr=bgr,
        image_format=image_format,
        width=width,
        height=height,
    )
