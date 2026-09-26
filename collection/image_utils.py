from PIL import Image
from io import BytesIO
from django.core.files.base import ContentFile


def optimize_image(image_file, max_width=1600, quality=82):
    """
    Resize and compress an uploaded image.

    - Maximum width: 1600px
    - Keeps aspect ratio
    - Converts PNG/RGBA images to RGB
    - Saves as JPEG
    """

    image = Image.open(image_file)

    # Fix orientation from phone cameras
    try:
        from PIL import ImageOps
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
            mask=image.getchannel("A")
            if image.mode == "RGBA"
            else None
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

    # Save optimized JPEG
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