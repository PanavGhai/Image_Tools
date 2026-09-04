from pathlib import Path
from PIL import Image

# ============================================================
# CONFIGURATION
# ============================================================

SOURCE_DIR = Path("static/images")
OUTPUT_DIR = Path("compressed_images")

SUPPORTED = {".jpg", ".jpeg", ".png"}

START_QUALITY = 90
MIN_QUALITY = 40
QUALITY_STEP = 5

# Images larger than this will be resized if compression alone
# cannot reasonably reach the target.
MAX_DIMENSION = 3840


# ============================================================
# SIZE HELPERS
# ============================================================

def format_size(size_bytes):
    """Convert bytes to a readable size."""

    if size_bytes < 1024:
        return f"{size_bytes} B"

    if size_bytes < 1024 ** 2:
        return f"{size_bytes / 1024:.1f} KB"

    if size_bytes < 1024 ** 3:
        return f"{size_bytes / (1024 ** 2):.2f} MB"

    return f"{size_bytes / (1024 ** 3):.2f} GB"


def parse_size(value):
    """
    Convert user input such as:

        1MB
        500KB
        2.5MB
        1000KB

    into bytes.
    """

    value = value.strip().upper().replace(" ", "")

    try:
        if value.endswith("KB"):
            number = float(value[:-2])
            return int(number * 1024)

        if value.endswith("MB"):
            number = float(value[:-2])
            return int(number * 1024 * 1024)

        if value.endswith("GB"):
            number = float(value[:-2])
            return int(number * 1024 * 1024 * 1024)

        # If no unit is supplied, assume MB.
        number = float(value)
        return int(number * 1024 * 1024)

    except ValueError:
        return None


# ============================================================
# IMAGE HELPERS
# ============================================================

def resize_if_needed(image):
    """
    Resize very large images while preserving aspect ratio.
    """

    width, height = image.size

    if max(width, height) <= MAX_DIMENSION:
        return image

    scale = MAX_DIMENSION / max(width, height)

    new_width = int(width * scale)
    new_height = int(height * scale)

    print(
        f"    Resizing: "
        f"{width}x{height} → {new_width}x{new_height}"
    )

    return image.resize(
        (new_width, new_height),
        Image.Resampling.LANCZOS
    )


def compress_jpeg(image, output_path, target_size):
    """
    Compress JPEG from the original image object.

    Every quality attempt starts from the same source image,
    preventing cumulative quality degradation.
    """

    quality = START_QUALITY

    while quality >= MIN_QUALITY:

        image.save(
            output_path,
            "JPEG",
            quality=quality,
            optimize=True,
            progressive=True
        )

        current_size = output_path.stat().st_size

        print(
            f"    Quality {quality}: "
            f"{format_size(current_size)}"
        )

        if current_size <= target_size:
            return True, quality

        quality -= QUALITY_STEP

    return False, None


def compress_webp(image, output_path, target_size):
    """
    Compress image as WebP.
    """

    quality = START_QUALITY

    while quality >= MIN_QUALITY:

        image.save(
            output_path,
            "WEBP",
            quality=quality,
            method=6
        )

        current_size = output_path.stat().st_size

        print(
            f"    WebP quality {quality}: "
            f"{format_size(current_size)}"
        )

        if current_size <= target_size:
            return True, quality

        quality -= QUALITY_STEP

    return False, None


# ============================================================
# SINGLE IMAGE PROCESSING
# ============================================================

def process_image(source, target_size):
    """
    Compress one image.
    """

    relative_path = source.relative_to(SOURCE_DIR)

    original_size = source.stat().st_size

    print()
    print("=" * 65)
    print(f"Image:       {relative_path}")
    print(f"Original:    {format_size(original_size)}")
    print(f"Target:      {format_size(target_size)}")

    # --------------------------------------------------------
    # Already below target
    # --------------------------------------------------------

    if original_size <= target_size:

        print("Status:      Already below target.")

        copy_path = OUTPUT_DIR / relative_path
        copy_path.parent.mkdir(parents=True, exist_ok=True)

        copy_path.write_bytes(source.read_bytes())

        return

    # --------------------------------------------------------
    # Open image
    # --------------------------------------------------------

    try:

        image = Image.open(source)
        image.load()

    except Exception as error:

        print(f"ERROR:       {error}")
        return

    print(
        f"Dimensions:  {image.width}x{image.height}"
    )

    # Resize extremely large images.
    image = resize_if_needed(image)

    extension = source.suffix.lower()

    # --------------------------------------------------------
    # JPEG
    # --------------------------------------------------------

    if extension in {".jpg", ".jpeg"}:

        if image.mode not in {"RGB", "L"}:
            image = image.convert("RGB")

        output_path = OUTPUT_DIR / relative_path
        output_path.parent.mkdir(parents=True, exist_ok=True)

        success, quality = compress_jpeg(
            image,
            output_path,
            target_size
        )

        if success:

            final_size = output_path.stat().st_size

            print()
            print("SUCCESS")
            print(f"Output:      {output_path}")
            print(f"Final size:  {format_size(final_size)}")
            print(f"Quality:     {quality}")
            print(
                f"Saved:       "
                f"{format_size(original_size - final_size)}"
            )

            return

        # JPEG couldn't reach target.
        # Convert to WebP.

        print()
        print("JPEG could not reach target.")
        print("Trying WebP...")

        webp_path = output_path.with_suffix(".webp")

        success, quality = compress_webp(
            image,
            webp_path,
            target_size
        )

        if success:

            output_path.unlink(missing_ok=True)

            final_size = webp_path.stat().st_size

            print()
            print("SUCCESS")
            print(f"Output:      {webp_path}")
            print(f"Final size:  {format_size(final_size)}")
            print(f"Format:      WebP")
            print(f"Quality:     {quality}")

            return

    # --------------------------------------------------------
    # PNG
    # --------------------------------------------------------

    elif extension == ".png":

        output_path = OUTPUT_DIR / relative_path
        output_path.parent.mkdir(parents=True, exist_ok=True)

        # First attempt: lossless PNG compression.
        print()
        print("Trying lossless PNG compression...")

        image.save(
            output_path,
            "PNG",
            optimize=True,
            compress_level=9
        )

        png_size = output_path.stat().st_size

        print(
            f"PNG result:  {format_size(png_size)}"
        )

        if png_size <= target_size:

            print()
            print("SUCCESS")
            print(f"Output:      {output_path}")
            print(f"Final size:  {format_size(png_size)}")
            print("Method:      Lossless PNG optimization")

            return

        # PNG still too large.
        # WebP is much more effective for photographs.
        print()
        print("PNG is still above target.")
        print("Trying WebP...")

        webp_path = output_path.with_suffix(".webp")

        success, quality = compress_webp(
            image,
            webp_path,
            target_size
        )

        if success:

            output_path.unlink(missing_ok=True)

            final_size = webp_path.stat().st_size

            print()
            print("SUCCESS")
            print(f"Output:      {webp_path}")
            print(f"Final size:  {format_size(final_size)}")
            print("Format:      WebP")
            print(f"Quality:     {quality}")

            return

    print()
    print("WARNING")
    print("Could not reach the requested size.")
    print(
        f"Best result: "
        f"{format_size((OUTPUT_DIR / relative_path).stat().st_size)}"
    )


# ============================================================
# IMAGE LIST
# ============================================================

def get_images():

    return sorted(
        [
            path
            for path in SOURCE_DIR.rglob("*")
            if path.is_file()
            and path.suffix.lower() in SUPPORTED
        ]
    )


def list_images(images):

    print()
    print("=" * 75)
    print("AVAILABLE IMAGES")
    print("=" * 75)

    if not images:
        print("No JPG or PNG images found.")
        return

    for index, image in enumerate(images, start=1):

        relative = image.relative_to(SOURCE_DIR)

        print(
            f"{index:3}. "
            f"{str(relative):50} "
            f"{format_size(image.stat().st_size):>10}"
        )

    print("=" * 75)


# ============================================================
# SELECTION
# ============================================================

def select_images(images):

    while True:

        list_images(images)

        print()
        print("Selection options:")
        print("  1. Select one image")
        print("  2. Select multiple images")
        print("  3. Select all images")
        print("  4. Back")

        choice = input("\nChoice: ").strip()

        # ----------------------------------------------------
        # One image
        # ----------------------------------------------------

        if choice == "1":

            try:

                number = int(
                    input("Enter image number: ")
                )

                if 1 <= number <= len(images):
                    return [images[number - 1]]

                print("Invalid image number.")

            except ValueError:
                print("Please enter a number.")

        # ----------------------------------------------------
        # Multiple images
        # ----------------------------------------------------

        elif choice == "2":

            raw = input(
                "Enter image numbers separated by commas "
                "(e.g. 1,3,5): "
            )

            try:

                numbers = [
                    int(value.strip())
                    for value in raw.split(",")
                ]

                selected = []

                for number in numbers:

                    if 1 <= number <= len(images):
                        selected.append(images[number - 1])
                    else:
                        print(
                            f"Ignoring invalid number: {number}"
                        )

                if selected:
                    return selected

            except ValueError:
                print("Invalid selection.")

        # ----------------------------------------------------
        # All
        # ----------------------------------------------------

        elif choice == "3":

            return images

        # ----------------------------------------------------
        # Back
        # ----------------------------------------------------

        elif choice == "4":

            return None

        else:

            print("Invalid choice.")


# ============================================================
# TARGET SIZE
# ============================================================

def get_target_size():

    while True:

        print()
        print("Enter the maximum size for each image.")
        print()
        print("Examples:")
        print("  1MB")
        print("  500KB")
        print("  2MB")
        print("  750KB")
        print()

        value = input("Target size: ")

        size = parse_size(value)

        if size is None or size <= 0:

            print(
                "Invalid size. Example: 1MB or 500KB."
            )

            continue

        return size


# ============================================================
# MAIN MENU
# ============================================================

def main():

    if not SOURCE_DIR.exists():

        print()
        print("ERROR")
        print(f"Directory not found: {SOURCE_DIR}")
        print()
        print(
            "Make sure this script is located in "
            "your MediCare project root."
        )

        return

    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    while True:

        images = get_images()

        print()
        print()
        print("=" * 75)
        print("                 MEDICARE IMAGE COMPRESSOR")
        print("=" * 75)
        print()
        print(f"Image directory : {SOURCE_DIR}")
        print(f"Output directory: {OUTPUT_DIR}")
        print(f"Images found    : {len(images)}")
        print()
        print("1. Compress images")
        print("2. List images")
        print("3. Exit")
        print()

        choice = input("Choice: ").strip()

        # ----------------------------------------------------
        # Compress
        # ----------------------------------------------------

        if choice == "1":

            if not images:

                print("No images found.")
                continue

            selected = select_images(images)

            if not selected:
                continue

            target_size = get_target_size()

            print()
            print("=" * 75)
            print("COMPRESSION SUMMARY")
            print("=" * 75)

            print(
                f"Images selected : {len(selected)}"
            )

            print(
                f"Target size     : "
                f"{format_size(target_size)}"
            )

            print()

            confirm = input(
                "Start compression? (y/n): "
            ).strip().lower()

            if confirm != "y":
                print("Cancelled.")
                continue

            for image in selected:

                process_image(
                    image,
                    target_size
                )

            print()
            print("=" * 75)
            print("COMPRESSION COMPLETE")
            print("=" * 75)
            print()
            print(
                f"Compressed files are located in:"
            )
            print(f"  {OUTPUT_DIR}")

            input(
                "\nPress Enter to return to the menu..."
            )

        # ----------------------------------------------------
        # List
        # ----------------------------------------------------

        elif choice == "2":

            list_images(images)

            input(
                "\nPress Enter to return to the menu..."
            )

        # ----------------------------------------------------
        # Exit
        # ----------------------------------------------------

        elif choice == "3":

            print("\nExiting.")
            break

        else:

            print("\nInvalid choice.")


# ============================================================
# RUN
# ============================================================

if __name__ == "__main__":
    main()