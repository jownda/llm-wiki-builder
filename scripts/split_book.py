#!/usr/bin/env python3
"""
Split 本草纲目 into manageable chunks (~50KB each).
Splits at paragraph boundaries (blank lines) to avoid cutting in mid-sentence.
"""

from pathlib import Path

SOURCE = Path(__file__).parent.parent / "raw" / "documents" / "本草纲目.txt"
OUT_DIR = Path(__file__).parent.parent / "raw" / "documents" / "split"
OUT_DIR.mkdir(parents=True, exist_ok=True)

CHUNK_SIZE = 50000  # ~50KB per chunk, fits in most LLM contexts


def split_at_boundaries(content: str, chunk_size: int) -> list:
    """Split content into chunks at paragraph boundaries."""
    chunks = []
    pos = 0
    total = len(content)

    while pos < total:
        # Target end position
        target = pos + chunk_size
        if target >= total:
            chunks.append(content[pos:])
            break

        # Find nearest paragraph break (blank line or line ending) near target
        # Search backward from target for \n\n (paragraph break)
        search_start = target
        # Search up to 2000 chars back for a good split point
        window = content[max(pos, target - 2000):target]
        split_offset = window.rfind("\n\n")

        if split_offset == -1:
            # Try single newline
            split_offset = window.rfind("\n")

        if split_offset == -1:
            # No good break found, just cut
            split_pos = target
        else:
            split_pos = max(pos, target - 2000) + split_offset + 2  # +2 for \n\n

        chunk = content[pos:split_pos].strip()
        if chunk and len(chunk) > 100:
            chunks.append(chunk)
        pos = split_pos

    return chunks


def main():
    print(f"Reading {SOURCE}...")
    content = SOURCE.read_text(encoding="utf-8")
    print(f"  Total chars: {len(content):,}")
    print(f"  Total lines: {content.count(chr(10)) + 1:,}")

    chunks = split_at_boundaries(content, CHUNK_SIZE)
    print(f"\nSplit into {len(chunks)} chunks:")

    for i, chunk in enumerate(chunks):
        # First 50 chars to preview
        preview = chunk[:80].replace("\n", " / ").encode("utf-8").decode("gbk", errors="ignore")
        out_path = OUT_DIR / f"chunk_{i:03d}.txt"
        out_path.write_text(chunk, encoding="utf-8")
        print(f"  chunk_{i:03d}: {len(chunk):,} chars | {preview[:60]}...")

    print(f"\nDone! All chunks in {OUT_DIR}")


if __name__ == "__main__":
    main()
