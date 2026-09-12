#!/usr/bin/env python
"""
Extract vocabulary words from APEUni PDF and convert to CSV
The PDF format has words numbered like: 1exhaust2exhilarate3restaurant...
"""
import PyPDF2
import csv
import re

# Path to the PDF file
pdf_path = "/Users/sujan/Desktop/APEUni_PTE_Advanced_Vocab.pdf"
output_csv = "/Users/sujan/Desktop/Projects/VocabSwipe/APEUni_PTE_Advanced_Vocab.csv"

print("=" * 60)
print("Extracting vocabulary from APEUni PDF...")
print("=" * 60)

# Extract text from PDF
all_text = ""
try:
    with open(pdf_path, "rb") as file:
        pdf_reader = PyPDF2.PdfReader(file)
        print(f"Total pages: {len(pdf_reader.pages)}")

        for page_num, page in enumerate(pdf_reader.pages, 1):
            text = page.extract_text()
            all_text += text + " "
            if page_num % 10 == 0:
                print(f"Processed {page_num} pages...")

        print(f"✅ Extracted text from all {len(pdf_reader.pages)} pages")
except Exception as e:
    print(f"❌ Error reading PDF: {e}")
    exit(1)

# Extract words using regex pattern
# Pattern: number followed by word(s), then another number
# Example: 1exhaust2exhilarate3restaurant
words = []

# Find all patterns like: digit(s) followed by letters
pattern = r"(\d+)([a-zA-Zﬁﬂ]+)"
matches = re.findall(pattern, all_text)

print(f"\n📊 Extraction Statistics:")
print(f"   Raw matches found: {len(matches)}")

# Process matches
for num, word in matches:
    # Clean the word
    word = word.strip()

    # Replace ligatures (ﬁ -> fi, ﬂ -> fl)
    word = word.replace("ﬁ", "fi").replace("ﬂ", "fl")

    # Skip if too short or looks like header/footer text
    if len(word) < 2:
        continue

    # Skip common non-word patterns
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

    # Add to list with the number for verification
    words.append((int(num), word.lower()))

# Sort by number to ensure correct order
words.sort(key=lambda x: x[0])

# Extract just the words
word_list = [word for num, word in words]

# Check for expected count (should be around 3170)
print(f"   Total words extracted: {len(word_list)}")
print(f"   Expected: ~3170 words")

if len(word_list) < 3000:
    print(f"\n⚠️  Warning: Found fewer words than expected!")
    print(f"   This might indicate an extraction issue.")
else:
    print(f"\n✅ Word count looks good!")

# Show first and last 10 words
print(f"\n📝 First 10 words:")
for i, word in enumerate(word_list[:10], 1):
    print(f"   {i}. {word}")

print(f"\n📝 Last 10 words:")
start_num = len(word_list) - 9
for i, word in enumerate(word_list[-10:], start_num):
    print(f"   {i}. {word}")

# Write to CSV
try:
    with open(output_csv, "w", newline="", encoding="utf-8") as csvfile:
        writer = csv.writer(csvfile)
        writer.writerow(["word"])  # Header
        for word in word_list:
            writer.writerow([word])

    print(f"\n✅ Successfully created CSV file:")
    print(f"   {output_csv}")
    print(f"   Total words: {len(word_list)}")
except Exception as e:
    print(f"❌ Error writing CSV: {e}")
    exit(1)

# Also create a simple text file (one word per line)
txt_output = output_csv.replace(".csv", ".txt")
try:
    with open(txt_output, "w", encoding="utf-8") as txtfile:
        for word in word_list:
            txtfile.write(word + "\n")

    print(f"\n✅ Also created text file:")
    print(f"   {txt_output}")
except Exception as e:
    print(f"⚠️  Warning: Could not create text file: {e}")

print("\n" + "=" * 60)
print("Conversion complete!")
print("=" * 60)
print(f"\n🎯 Ready to upload to VocabSwipe!")
print(f"\nYou can now upload either:")
print(f"  • {output_csv}")
print(f"  • {txt_output}")
print(f"\n💡 Meanings will be auto-fetched from the dictionary!")
print(f"   (This will take some time for 3000+ words)")
print("=" * 60)
