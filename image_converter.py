from pathlib import Path
from PIL import Image

# ============================================================
# CONFIGURATION
# ============================================================

ROOT_DIR = Path(__file__).resolve().parent
OUTPUT_DIR = ROOT_DIR / "converted_images"

SUPPORTED = {
    ".jpg",
    ".jpeg",
    ".png",
    ".webp",
    ".bmp",
    ".tiff",
    ".tif",
}

# ============================================================
# HELPERS
# ============================================================

def format_size(size):
    if size < 1024:
        return f"{size} B"

    if size < 1024 ** 2:
        return f"{size / 1024:.1f} KB"

    if size < 1024 ** 3:
        return f"{size / (1024 ** 2):.2f} MB"

    return f"{size / (1024 ** 3):.2f} GB"


def get_images():
    """
    Recursively find supported images from the script's root.
    Excludes the output directory.
    """

    return sorted(
        [
            path
            for path in ROOT_DIR.rglob("*")
            if path.is_file()
            and path.suffix.lower() in SUPPORTED
            and OUTPUT_DIR not in path.parents
        ]
    )


def list_images(images):

    print()
    print("=" * 80)
    print("AVAILABLE IMAGES")
    print("=" * 80)

    if not images:
        print("No supported images found.")
        return

    for index, image in enumerate(images, start=1):

        relative = image.relative_to(ROOT_DIR)

        print(
            f"{index:3}. "
            f"{str(relative):60} "
            f"{format_size(image.stat().st_size):>10}"
        )

    print("=" * 80)


# ============================================================
# FORMAT MENU
# ============================================================

def choose_format():

    print()
    print("=" * 60)
    print("SELECT OUTPUT FORMAT")
    print("=" * 60)

    print("1. WebP")
    print("2. JPG")
    print("3. PNG")
    print("4. BMP")
    print("5. TIFF")
    print("6. Back")

    while True:

        choice = input("\nChoice: ").strip()

        if choice == "1":
            return "WEBP"

        elif choice == "2":
            return "JPEG"

        elif choice == "3":
            return "PNG"

        elif choice == "4":
            return "BMP"

        elif choice == "5":
            return "TIFF"

        elif choice == "6":
            return None

        else:
            print("Invalid choice.")


# ============================================================
# QUALITY MENU
# ============================================================

def choose_quality(output_format):

    if output_format not in {"WEBP", "JPEG"}:
        return None

    print()
    print("=" * 60)
    print("QUALITY")
    print("=" * 60)

    print("1. Maximum quality")
    print("2. High quality")
    print("3. Balanced")
    print("4. Smaller file")
    print("5. Custom")

    while True:

        choice = input("\nChoice: ").strip()

        if choice == "1":
            return 95

        elif choice == "2":
            return 90

        elif choice == "3":
            return 85

        elif choice == "4":
            return 75

        elif choice == "5":

            try:

                quality = int(
                    input("Enter quality (1-100): ")
                )

                if 1 <= quality <= 100:
                    return quality

                print("Quality must be between 1 and 100.")

            except ValueError:
                print("Enter a number.")

        else:
            print("Invalid choice.")


# ============================================================
# IMAGE SELECTION
# ============================================================

def select_images(images):

    while True:

        list_images(images)

        print()
        print("Selection:")
        print("1. One image")
        print("2. Multiple images")
        print("3. All images")
        print("4. Back")

        choice = input("\nChoice: ").strip()

        # ----------------------------------------------------
        # One
        # ----------------------------------------------------

        if choice == "1":

            try:

                number = int(
                    input("Image number: ")
                )

                if 1 <= number <= len(images):
                    return [images[number - 1]]

                print("Invalid image number.")

            except ValueError:
                print("Enter a number.")

        # ----------------------------------------------------
        # Multiple
        # ----------------------------------------------------

        elif choice == "2":

            raw = input(
                "Enter numbers separated by commas "
                "(example: 1,3,7): "
            )

            try:

                numbers = [
                    int(x.strip())
                    for x in raw.split(",")
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
# CONVERSION
# ============================================================

def convert_image(
    source,
    output_format,
    quality
):

    relative = source.relative_to(ROOT_DIR)

    # Change extension.
    extension_map = {
        "WEBP": ".webp",
        "JPEG": ".jpg",
        "PNG": ".png",
        "BMP": ".bmp",
        "TIFF": ".tiff",
    }

    new_extension = extension_map[output_format]

    destination = (
        OUTPUT_DIR
        / relative.with_suffix(new_extension)
    )

    destination.parent.mkdir(
        parents=True,
        exist_ok=True
    )

    original_size = source.stat().st_size

    print()
    print("-" * 75)
    print(f"Input:       {relative}")
    print(f"Original:    {format_size(original_size)}")
    print(f"Format:      {output_format}")

    try:

        image = Image.open(source)

        image.load()

        # ----------------------------------------------------
        # JPEG does not support transparency.
        # ----------------------------------------------------

        if output_format == "JPEG":

            if image.mode not in {"RGB", "L"}:
                print(
                    "Transparency detected. "
                    "Converting to RGB."
                )

                background = Image.new(
                    "RGB",
                    image.size,
                    "white"
                )

                if image.mode == "RGBA":
                    background.paste(
                        image,
                        mask=image.getchannel("A")
                    )
                else:
                    image = image.convert("RGBA")
                    background.paste(
                        image,
                        mask=image.getchannel("A")
                    )

                image = background

            image.save(
                destination,
                "JPEG",
                quality=quality,
                optimize=True,
                progressive=True
            )

        # ----------------------------------------------------
        # WEBP
        # ----------------------------------------------------

        elif output_format == "WEBP":

            image.save(
                destination,
                "WEBP",
                quality=quality,
                method=6
            )

        # ----------------------------------------------------
        # PNG
        # ----------------------------------------------------

        elif output_format == "PNG":

            image.save(
                destination,
                "PNG",
                optimize=True,
                compress_level=9
            )

        # ----------------------------------------------------
        # BMP
        # ----------------------------------------------------

        elif output_format == "BMP":

            image.save(
                destination,
                "BMP"
            )

        # ----------------------------------------------------
        # TIFF
        # ----------------------------------------------------

        elif output_format == "TIFF":

            image.save(
                destination,
                "TIFF",
                compression="tiff_lzw"
            )

        final_size = destination.stat().st_size

        difference = original_size - final_size

        print(
            f"Output:      {destination.relative_to(ROOT_DIR)}"
        )

        print(
            f"New size:    {format_size(final_size)}"
        )

        if difference > 0:

            print(
                f"Saved:       {format_size(difference)}"
            )

        else:

            print(
                f"Increase:    {format_size(abs(difference))}"
            )

    except Exception as error:

        print(f"ERROR:       {error}")


# ============================================================
# MAIN
# ============================================================

def main():

    print()
    print("=" * 80)
    print("                    MEDICARE IMAGE CONVERTER")
    print("=" * 80)

    print(f"Root:   {ROOT_DIR}")
    print(f"Output: {OUTPUT_DIR}")

    while True:

        images = get_images()

        print()
        print("=" * 80)
        print(f"Images found: {len(images)}")
        print("=" * 80)

        print("1. Convert images")
        print("2. List images")
        print("3. Refresh image list")
        print("4. Exit")

        choice = input("\nChoice: ").strip()

        # ----------------------------------------------------
        # Convert
        # ----------------------------------------------------

        if choice == "1":

            if not images:
                print("No images found.")
                continue

            selected = select_images(images)

            if not selected:
                continue

            output_format = choose_format()

            if output_format is None:
                continue

            quality = choose_quality(output_format)

            print()
            print("=" * 80)
            print("CONVERSION SUMMARY")
            print("=" * 80)

            print(
                f"Images:       {len(selected)}"
            )

            print(
                f"Format:       {output_format}"
            )

            if quality:
                print(
                    f"Quality:      {quality}"
                )

            print()

            confirm = input(
                "Start conversion? (y/n): "
            ).strip().lower()

            if confirm != "y":

                print("Cancelled.")
                continue

            for image in selected:

                convert_image(
                    image,
                    output_format,
                    quality
                )

            print()
            print("=" * 80)
            print("CONVERSION COMPLETE")
            print("=" * 80)

            input(
                "\nPress Enter to return to menu..."
            )

        # ----------------------------------------------------
        # List
        # ----------------------------------------------------

        elif choice == "2":

            list_images(images)

            input(
                "\nPress Enter to return to menu..."
            )

        # ----------------------------------------------------
        # Refresh
        # ----------------------------------------------------

        elif choice == "3":

            print("Image list refreshed.")

        # ----------------------------------------------------
        # Exit
        # ----------------------------------------------------

        elif choice == "4":

            print("Exiting.")
            break

        else:

            print("Invalid choice.")


if __name__ == "__main__":
    main()