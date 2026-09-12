#!/usr/bin/env python
"""
Universal PDF Vocabulary Extractor
Converts vocabulary PDFs to CSV/TXT format for VocabSwipe

Usage:
    python convert_pdf_to_vocab.py <path_to_pdf> [output_name]

Examples:
    python convert_pdf_to_vocab.py vocabulary.pdf
    python convert_pdf_to_vocab.py ~/Desktop/words.pdf my_vocab_list
"""

import PyPDF2
import csv
import re
import sys
import os


def extract_words_from_pdf(pdf_path):
    """Extract all text from PDF"""
    all_text = ""
    try:
        with open(pdf_path, "rb") as file:
            pdf_reader = PyPDF2.PdfReader(file)
            print(f"📄 Reading PDF: {len(pdf_reader.pages)} pages")

            for page_num, page in enumerate(pdf_reader.pages, 1):
                text = page.extract_text()
                all_text += text + " "
                if page_num % 10 == 0:
                    print(f"   Processed {page_num} pages...")

            print(f"✅ Extracted text from all pages")
    except Exception as e:
        print(f"❌ Error reading PDF: {e}")
        return None

    return all_text


def parse_numbered_format(text):
    """
    Parse format like: 1word2word3word
    Common in vocabulary lists
    """
    pattern = r"(\d+)([a-zA-Zﬁﬂ]+)"
    matches = re.findall(pattern, text)

    words = []
    for num, word in matches:
        # Replace ligatures
        word = word.replace("ﬁ", "fi").replace("ﬂ", "fl")

        # Skip short words and common artifacts
        if len(word) < 2:
            continue

        skip_words = [
            "apeuni",
            "pte",
            "vocab",
            "list",
            "visit",
            "www",
            "com",
            "page",
            "of",
            "materials",
            "advanced",
            "study",
            "more",
            "for",
        ]
        if word.lower() in skip_words:
            continue

        words.append((int(num), word.lower()))

    # Sort by number
    words.sort(key=lambda x: x[0])
    return [word for num, word in words]


def parse_line_by_line(text):
    """
    Parse format where each word is on its own line
    """
    lines = text.split("\n")
    words = []

    for line in lines:
        line = line.strip()

        # Skip empty lines, numbers, short lines
        if not line or line.isdigit() or len(line) < 2:
            continue

        # Skip headers/footers
        if any(
            skip in line.lower() for skip in ["page", "chapter", "vocabulary", "list"]
        ):
            continue

        # If line is a single word (letters, hyphens, apostrophes only)
        if re.match(r"^[a-zA-Z][a-zA-Z\-\']*$", line):
            words.append(line.lower())

    return words


def clean_words(words):
    """Remove artifacts and duplicates"""
    cleaned = []
    seen = set()

    for word in words:
        # Remove 'page' suffix
        if word.endswith("page"):
            word = word[:-4]

        # Skip artifacts
        if len(word) < 2 or word in ["su", "so", "of", "to", "in", "a"]:
            continue

        # Remove duplicates
        if word not in seen:
            seen.add(word)
            cleaned.append(word)

    return cleaned


def save_vocabulary(words, output_base):
    """Save to both CSV and TXT formats"""
    csv_path = f"{output_base}.csv"
    txt_path = f"{output_base}.txt"

    # Save CSV
    with open(csv_path, "w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow(["word"])
        for word in words:
            writer.writerow([word])

    # Save TXT
    with open(txt_path, "w", encoding="utf-8") as f:
        for word in words:
            f.write(word + "\n")

    return csv_path, txt_path


def main():
    if len(sys.argv) < 2:
        print("Usage: python convert_pdf_to_vocab.py <pdf_path> [output_name]")
        print("\nExample:")
        print("  python convert_pdf_to_vocab.py vocabulary.pdf")
        print("  python convert_pdf_to_vocab.py ~/Desktop/words.pdf my_vocab")
        sys.exit(1)

    pdf_path = sys.argv[1]

    # Determine output name
    if len(sys.argv) >= 3:
        output_base = sys.argv[2]
    else:
        # Use PDF filename without extension
        output_base = os.path.splitext(os.path.basename(pdf_path))[0]

    print("=" * 60)
    print("PDF Vocabulary Extractor for VocabSwipe")
    print("=" * 60)
    print(f"Input:  {pdf_path}")
    print(f"Output: {output_base}.csv / {output_base}.txt")
    print()

    # Extract text
    text = extract_words_from_pdf(pdf_path)
    if not text:
        sys.exit(1)

    # Try numbered format first
    print("\n🔍 Trying numbered format (1word2word3word)...")
    words = parse_numbered_format(text)

    # If that didn't work well, try line-by-line
    if len(words) < 10:
        print("   Not enough words found, trying line-by-line format...")
        words = parse_line_by_line(text)

    print(f"   Found {len(words)} words")

    # Clean up
    print("\n🧹 Cleaning words...")
    words = clean_words(words)
    print(f"   {len(words)} words after cleanup")

    if len(words) == 0:
        print("\n❌ No words extracted. The PDF format may not be supported.")
        print("   Please check the PDF structure manually.")
        sys.exit(1)

    # Show sample
    print(f"\n📝 First 10 words:")
    for i, word in enumerate(words[:10], 1):
        print(f"   {i}. {word}")

    if len(words) > 10:
        print(f"\n📝 Last 5 words:")
        for word in words[-5:]:
            print(f"   • {word}")

    # Save files
    print("\n💾 Saving files...")
    csv_path, txt_path = save_vocabulary(words, output_base)

    print(f"\n✅ Success! Created:")
    print(f"   📄 {csv_path} ({len(words)} words)")
    print(f"   📄 {txt_path} ({len(words)} words)")

    print("\n" + "=" * 60)
    print("🎯 Ready to upload to VocabSwipe!")
    print("=" * 60)
    print(f"\nUpload either file to VocabSwipe.")
    print(f"Meanings will be auto-fetched from the dictionary.")

    # Estimate time for API fetching
    estimated_minutes = (len(words) * 0.5) / 60
    print(f"\n⏱️  Estimated upload time: ~{estimated_minutes:.0f} minutes")
    print(f"   (API fetches meanings at 0.5s per word)")
    print("=" * 60)


if __name__ == "__main__":
    main()
