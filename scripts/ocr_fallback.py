#!/usr/bin/env python3
"""
OCR Fallback for Scanned PDFs (PyMuPDF + EasyOCR)

Zero external system dependencies. Pure Python solution for Windows/Linux/macOS.

Usage:
    python ocr_fallback.py path/to/scanned.pdf
    python ocr_fallback.py path/to/scanned.pdf --lang en
"""

import argparse
import os
import sys
from pathlib import Path


def extract_ocr(pdf_path: str, lang: str = "ch"):
    """Extract text from scanned PDF using PyMuPDF + EasyOCR."""
    # Step 1: Load PDF
    try:
        import fitz
    except ImportError:
        print("[ERROR] 'pymupdf' not installed. Run: pip install pymupdf")
        return ""

    doc = fitz.open(pdf_path)
    total_pages = len(doc)
    print(f"[i] PDF loaded: {total_pages} pages")

    # Step 2: Initialize OCR
    try:
        import easyocr
        # EasyOCR lang codes
        lang_map = {"ch": ["ch_sim", "en"], "en": ["en"], "ja": ["ja", "en"], "ko": ["ko", "en"]}
        langs = lang_map.get(lang, ["ch_sim", "en"])
        print(f"[i] Initializing EasyOCR ({langs})... (downloads models on first run)")
        reader = easyocr.Reader(langs, gpu=False)  # Force CPU for stability
        print("[i] OCR ready.")
    except ImportError:
        print("[ERROR] 'easyocr' not installed. Run: pip install easyocr")
        doc.close()
        return ""
    except Exception as e:
        print(f"[ERROR] Failed to init EasyOCR: {e}")
        doc.close()
        return ""

    import cv2
    import numpy as np

    all_text = []
    for i in range(total_pages):
        page = doc[i]
        # Render at 200 DPI
        zoom = 200 / 72
        mat = fitz.Matrix(zoom, zoom)
        pix = page.get_pixmap(matrix=mat)

        # Convert to numpy (RGB)
        img_rgb = np.frombuffer(pix.samples, dtype=np.uint8).reshape((pix.height, pix.width, pix.n))

        # Convert to BGR for OpenCV
        if pix.n == 4:
            img_bgr = cv2.cvtColor(img_rgb, cv2.COLOR_RGBA2BGR)
        else:
            img_bgr = cv2.cvtColor(img_rgb, cv2.COLOR_RGB2BGR)

        # Resize if needed (limit 2000px max dimension)
        h, w = img_bgr.shape[:2]
        max_dim = 2000
        if h > max_dim or w > max_dim:
            scale = max_dim / max(h, w)
            new_w, new_h = int(w * scale), int(h * scale)
            img_bgr = cv2.resize(img_bgr, (new_w, new_h), interpolation=cv2.INTER_CUBIC)
            print(f"    [i] Resized from {w}x{h} to {new_w}x{new_h}")

        # Run EasyOCR
        try:
            result = reader.readtext(img_bgr, detail=0)  # detail=0 returns just text strings
        except Exception as e:
            print(f"  Page {i+1}/{total_pages}: OCR failed ({e})")
            continue

        text = "\n".join(result)
        if text.strip():
            all_text.append(text)
            print(f"  Page {i+1}/{total_pages}: {len(text)} chars")
        else:
            print(f"  Page {i+1}/{total_pages}: No text detected")

    doc.close()
    return "\n\n".join(all_text)


def main():
    parser = argparse.ArgumentParser(description="OCR Text Extraction for Scanned PDFs")
    parser.add_argument("pdf", type=str, help="Path to scanned PDF")
    parser.add_argument("--lang", type=str, default="ch", choices=["ch", "en", "ja", "ko"])
    parser.add_argument("--output", "-o", type=str, help="Output .md file path")

    args = parser.parse_args()

    pdf_path = Path(args.pdf).resolve()
    if not pdf_path.exists():
        print(f"[ERROR] File not found: {pdf_path}")
        sys.exit(1)

    print(f"[*] OCR-ing: {pdf_path} (lang={args.lang})")
    text = extract_ocr(str(pdf_path), args.lang)

    if text:
        out_path = args.output or str(pdf_path.parent / (pdf_path.stem + "_ocr.md"))
        front_matter = f"""---
title: "{pdf_path.stem} (OCR)"
type: reference
source: "OCR extraction from {pdf_path.name}"
status: draft
created: "2026-04-07"
---

# {pdf_path.stem} (OCR Extracted)

> Auto-extracted via EasyOCR (ch_sim+en). Please review and correct.

---

"""
        with open(out_path, "w", encoding="utf-8") as f:
            f.write(front_matter)
            f.write(text)
        print(f"\n[OK] Saved OCR output to {out_path}")
        print(f"     Total chars: {len(text)}")
    else:
        print("\n[FAIL] No text extracted. PDF may be blank or corrupt.")


if __name__ == "__main__":
    main()
