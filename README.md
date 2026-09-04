# Image Tools

A collection of Python utilities for **image compression and format conversion**, built with [Pillow](https://python-pillow.org/).

These tools are designed to make it easier to reduce image file sizes, convert between common image formats, and prepare images for web projects.

## Features

### Image Compressor

* Recursively scans images inside the project directory.
* Supports:

  * JPG
  * JPEG
  * PNG
* Allows compression of:

  * A single image
  * Multiple selected images
  * All images
* Set a target file size such as:

  * `500KB`
  * `1MB`
  * `2MB`
* Progressively adjusts image quality to reach the target size.
* Can convert images to WebP when further compression is required.
* Can resize excessively large images.
* Preserves the original files.
* Stores compressed images separately.
* Preserves the original directory structure.
* Automatically excludes the generated `compressed_images` directory.

### Image Converter

* Converts images between supported formats.
* Supports common image formats including:

  * JPG / JPEG
  * PNG
  * WebP
* Allows selecting individual, multiple, or all images.
* Provides configurable output quality for formats that support lossy compression.
* Preserves the original files.
* Stores converted images separately.
* Recursively searches the project directory.
* Excludes generated conversion output from future scans.

## Requirements

* Python 3.10+
* Pillow

Install Pillow with:

```bash
pip install Pillow
```

## Usage

Clone the repository:

```bash
git clone https://github.com/PanavGhai/Image_Tools.git
cd Image_Tools
```

Install the dependency:

```bash
pip install Pillow
```

Run the compressor:

```bash
python compress_images.py
```

Run the converter:

```bash
python image_converter.py
```

## Compression

The compressor uses a target-size approach rather than simply applying a fixed quality level.

For example:

```text
Target size: 500KB
```

The tool progressively adjusts compression settings until it reaches the requested size or determines that the target cannot reasonably be achieved.

### Example targets

```text
50KB
100KB
500KB
1MB
2MB
```

Original images remain untouched.

## Format Conversion

Format conversion and compression are different operations.

For example:

```text
photo.jpg → photo.webp
```

with a quality setting controls how much image quality is retained during the WebP encoding process.

A higher quality generally produces a larger file, while a lower quality generally produces a smaller file.

### Lossless vs Lossy

Some conversions can introduce quality loss.

Generally:

| Conversion          | Potential quality loss            |
| ------------------- | --------------------------------- |
| PNG → PNG           | No                                |
| PNG → Lossless WebP | No                                |
| JPG → JPG           | Yes                               |
| JPG → WebP          | Yes, if lossy                     |
| PNG → Lossy WebP    | Yes                               |
| JPG → PNG           | Does not recover existing quality |

## Output Structure

Compressed and converted files are kept separate from the originals.

For example:

```text
Image_Tools/
├── compress_images.py
├── image_converter.py
├── compressed_images/
│   └── ...
├── converted_images/
│   └── ...
└── README.md
```

The tools preserve the directory structure of the source images where applicable.

## Why WebP?

WebP is particularly useful for web projects because it can provide significantly smaller files than traditional JPEG and PNG images while maintaining good visual quality.

It is especially useful for:

* Website backgrounds
* Product images
* Profile images
* Doctor/patient images
* Service images
* Other photographic content

PNG may still be preferable when transparency or lossless image quality is important.

## Safety

The tools are designed to keep the original images unchanged.

Generated files are written to separate output directories rather than replacing the source images.

## License

Add your preferred license here.
