from PIL import Image, ImageOps
from io import BytesIO
from django.core.files.base import ContentFile
from pillow_heif import register_heif_opener

# Enable HEIC / HEIF support for Pillow
register_heif_opener()


def optimize_image(image_file, max_width=1600, quality=82):
    """
    Resize and compress an uploaded image.

    - Maximum width: 1600px
    - Keeps aspect ratio
    - Fixes phone-camera orientation
    - Converts images to RGB
    - Saves as JPEG
    """

    # Open uploaded image
    image = Image.open(image_file)

    # Fix orientation from phone cameras
    try:
        image = ImageOps.exif_transpose(image)
    except Exception:
        pass

    # Convert to RGB
    if image.mode in ("RGBA", "LA", "P"):
        background = Image.new(
            "RGB",
            image.size,
            "white"
        )

        if image.mode == "P":
            image = image.convert("RGBA")

        background.paste(
            image,
            mask=(
                image.getchannel("A")
                if image.mode == "RGBA"
                else None
            )
        )

        image = background

    elif image.mode != "RGB":
        image = image.convert("RGB")

    # Resize only if necessary
    if image.width > max_width:

        ratio = max_width / image.width

        new_height = int(
            image.height * ratio
        )

        image = image.resize(
            (max_width, new_height),
            Image.Resampling.LANCZOS
        )

    # Save optimized image as JPEG
    output = BytesIO()

    image.save(
        output,
        format="JPEG",
        quality=quality,
        optimize=True,
        progressive=True
    )

    output.seek(0)

    return ContentFile(
        output.read()
    )