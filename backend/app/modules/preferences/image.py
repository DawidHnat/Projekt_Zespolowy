"""Decode and re-encode account backgrounds with a maintained image library (SCRUM-148).

A RIFF/WEBP header is not proof of a valid image. The upload is fully decoded within
pixel limits and written again as a fresh WebP, so no original bytes or metadata
(EXIF, XMP, ICC) are stored.
"""

import io
import warnings

from app.core.errors import ApiError

# Same limits as the browser preparation step (frontend/src/shared/media/image-model.ts).
MAX_BACKGROUND_EDGE = 2560
MAX_BACKGROUND_PIXELS = 40_000_000


def reencode_background(data: bytes) -> bytes:
    from PIL import Image  # Loaded on first upload only.

    try:
        with warnings.catch_warnings():
            # Treat Pillow's decompression-bomb warning as an error, not a log line.
            warnings.simplefilter("error", Image.DecompressionBombWarning)
            with Image.open(io.BytesIO(data), formats=["WEBP"]) as source:
                width, height = source.size
                if (
                    width < 1
                    or height < 1
                    or max(width, height) > MAX_BACKGROUND_EDGE
                    or width * height > MAX_BACKGROUND_PIXELS
                ):
                    raise ApiError(
                        413, "IMAGE_TOO_LARGE", "Obraz tła przekracza limit 2560 px lub 40 MP"
                    )
                source.load()  # Full decode: truncated or corrupt data fails here.
                frame = source.convert("RGBA" if "A" in source.getbands() else "RGB")
    except ApiError:
        raise
    except Exception as error:  # noqa: BLE001 - any decoder failure on untrusted input is a 415.
        raise ApiError(415, "UNSUPPORTED_MEDIA_TYPE", "Niepoprawny obraz WebP") from error

    output = io.BytesIO()
    # A new frame carries no EXIF/XMP/ICC; nothing from the upload is copied over.
    frame.save(output, format="WEBP", quality=85, method=4)
    return output.getvalue()
