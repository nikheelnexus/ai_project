import fitz  # PyMuPDF
import json
from pathlib import Path

from agent.agents import company_agent_template, text_util_agent, company_agent, document_agent


def pdf_to_json(pdf_path: str):
    """
    Convert PDF to JSON with pages containing text and image lists.

    Returns:
    {
        "pages": [
            {
                "page": 1,
                "text": "text from page 1",
                "images": [
                    "C:/full/path/to/page_1_0.jpg",
                    "C:/full/path/to/page_1_1.png"
                ]
            },
            ...
        ]
    }
    """
    pdf = Path(pdf_path)
    if not pdf.exists():
        return {"error": "PDF not found"}

    # Create output folder
    output_dir = pdf.parent / f"{pdf.stem}_json"
    output_dir.mkdir(exist_ok=True)

    result = {"pages": []}

    try:
        # Open PDF
        doc = fitz.open(pdf_path)

        # Process each page
        for i in range(len(doc)):
            page = doc[i]
            text = page.get_text().strip()

            # Get images
            images = []
            for img_idx, img in enumerate(page.get_images()):
                try:
                    img_data = doc.extract_image(img[0])
                    if img_data:
                        ext = img_data["ext"]
                        filename = f"page_{i + 1}_{img_idx}.{ext}"
                        filepath = output_dir / filename

                        # Save image
                        with open(filepath, "wb") as f:
                            f.write(img_data["image"])

                        # Store FULL PATH
                        images.append(str(filepath.absolute()))
                except:
                    continue

            # Add page data
            result["pages"].append({
                "page": i + 1,
                "text": text,
                "images": images  # Full paths
            })

        doc.close()

        # Save JSON
        json_path = output_dir / "document.json"
        with open(json_path, 'w', encoding='utf-8') as f:
            json.dump(result, f, indent=2)

        result["json_path"] = str(json_path.absolute())
        return result

    except Exception as e:
        return {"error": f"Failed: {str(e)}"}


# Alternative: Also include relative paths
def pdf_to_json_both_paths(pdf_path: str):
    """
    Returns both full and relative paths.

    Returns:
    {
        "pages": [
            {
                "page": 1,
                "text": "text",
                "images": [
                    {
                        "filename": "page_1_0.jpg",
                        "full_path": "C:/full/path/to/page_1_0.jpg",
                        "relative_path": "folder/page_1_0.jpg"
                    }
                ]
            }
        ]
    }
    """
    pdf = Path(pdf_path)
    if not pdf.exists():
        return {"error": "PDF not found"}

    output_dir = pdf.parent / f"{pdf.stem}_extracted"
    output_dir.mkdir(exist_ok=True)

    result = {"pages": []}

    try:
        doc = fitz.open(pdf_path)

        for i in range(len(doc)):
            page = doc[i]
            text = page.get_text().strip()

            images = []
            for img_idx, img in enumerate(page.get_images()):
                try:
                    img_data = doc.extract_image(img[0])
                    if img_data:
                        ext = img_data["ext"]
                        filename = f"page_{i + 1}_{img_idx}.{ext}"
                        filepath = output_dir / filename

                        with open(filepath, "wb") as f:
                            f.write(img_data["image"])

                        images.append({
                            "filename": filename,
                            "full_path": str(filepath.absolute()),
                            "relative_path": str(filepath.relative_to(output_dir.parent))
                        })
                except:
                    continue

            result["pages"].append({
                "page": i + 1,
                "text": text,
                "images": images
            })

        doc.close()

        json_path = output_dir / "data.json"
        with open(json_path, 'w', encoding='utf-8') as f:
            json.dump(result, f, indent=2)

        result["json_path"] = str(json_path.absolute())
        return result

    except Exception as e:
        return {"error": str(e)}


def extract_text_from_image(image_path: str,
                            output_dir: str = None,
                            replace_existing: bool = False) -> str:
    """
    Extract text from image using OCR and save as text file.

    Args:
        image_path: Path to the image file
        output_dir: Optional custom output directory (default: same as image)
        replace_existing: If True, replace existing .txt file; if False, skip

    Returns:
        Extracted text string

    Example:
        text = extract_text_from_image("C:/path/to/image.jpg")
        # Creates: "C:/path/to/image.txt" with the extracted text
    """
    try:
        # Convert to Path object
        img_path = Path(image_path)

        if not img_path.exists():
            print(f"❌ Image not found: {image_path}")
            return ""

        # Determine output directory
        if output_dir:
            output_path = Path(output_dir)
            output_path.mkdir(parents=True, exist_ok=True)
        else:
            output_path = img_path.parent

        # Create text file name (same name as image but with .txt extension)
        txt_filename = f"{img_path.stem}.txt"
        txt_path = output_path / txt_filename

        # Check if text file already exists
        if txt_path.exists() and not replace_existing:
            print(f"📝 Text file already exists: {txt_path}")
            print("   Skipping extraction (set replace_existing=True to overwrite)")

            # Read and return existing text
            with open(txt_path, 'r', encoding='utf-8') as f:
                return f.read().strip()

        # Open and process image
        extracted_text = document_agent.get_image_overview(str(img_path))

        # Save text to file
        with open(txt_path, 'w', encoding='utf-8') as f:
            f.write(extracted_text)

        print(f"✅ Text extracted from: {img_path.name}")
        print(f"📄 Text saved to: {txt_path}")

        return extracted_text.strip()

    except Exception as e:
        print(f"❌ Error extracting text from {image_path}: {e}")
        return ""


# Simple class version
class PDFExtractor:
    """Simple PDF extractor with full image paths."""

    @staticmethod
    def extract(pdf_path: str):
        """
        Extract PDF with full image paths.

        Returns:
            {
                "pages": [
                    {
                        "page": 1,
                        "text": "text",
                        "images": ["full/path/image1.jpg", "full/path/image2.png"]
                    }
                ],
                "json_file": "full/path/to/json.json"
            }
        """
        pdf = Path(pdf_path)

        if not pdf.exists():
            return {"error": "File not found"}

        print(f"📄 Processing: {pdf.name}")

        # Create output folder
        out_folder = pdf.parent / f"{pdf.stem}_data"
        out_folder.mkdir(exist_ok=True)

        result = {"pages": []}

        try:
            with fitz.open(pdf_path) as doc:
                for page_num in range(len(doc)):
                    page = doc.load_page(page_num)

                    # Page data
                    page_data = {
                        "page": page_num + 1,
                        "text": page.get_text().strip(),
                        "images": []
                    }

                    # Get images
                    images = page.get_images()

                    for img_idx, img in enumerate(images):
                        try:
                            xref = img[0]
                            img_info = doc.extract_image(xref)

                            if img_info:
                                img_ext = img_info["ext"]
                                img_data = img_info["image"]

                                # Save image
                                img_name = f"page_{page_num + 1}_{img_idx}.{img_ext}"
                                img_path = out_folder / img_name

                                with open(img_path, "wb") as f:
                                    f.write(img_data)

                                # Add FULL PATH to images list
                                page_data["images"].append(str(img_path.absolute()))

                        except:
                            continue

                    result["pages"].append(page_data)

            # Save JSON
            json_file = out_folder / "extraction.json"
            with open(json_file, 'w', encoding='utf-8') as f:
                json.dump(result, f, indent=2, ensure_ascii=False)

            print(f"✅ JSON saved: {json_file}")

            # Return data with full paths
            result["json_file"] = str(json_file.absolute())
            return result

        except Exception as e:
            print(f"❌ Error: {e}")
            return {"error": str(e)}


