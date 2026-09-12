#!/usr/bin/env python
"""
Clean up the extracted vocabulary - remove 'page' suffixes
"""
import csv

input_csv = "/Users/sujan/Desktop/Projects/VocabSwipe/APEUni_PTE_Advanced_Vocab.csv"
output_csv = (
    "/Users/sujan/Desktop/Projects/VocabSwipe/APEUni_PTE_Advanced_Vocab_cleaned.csv"
)
output_txt = (
    "/Users/sujan/Desktop/Projects/VocabSwipe/APEUni_PTE_Advanced_Vocab_cleaned.txt"
)

print("Cleaning vocabulary file...")

words = []
with open(input_csv, "r", encoding="utf-8") as f:
    reader = csv.reader(f)
    next(reader)  # Skip header
    for row in reader:
        if row:
            word = row[0].strip()
            # Remove 'page' suffix if present
            if word.endswith("page"):
                word = word[:-4]
            # Skip very short words or artifacts
            if len(word) >= 2 and word not in ["su", "so"]:
                words.append(word)

print(f"Original words: 3156")
print(f"Cleaned words: {len(words)}")
print(f"Removed: {3156 - len(words)} artifacts")

# Write cleaned CSV
with open(output_csv, "w", newline="", encoding="utf-8") as f:
    writer = csv.writer(f)
    writer.writerow(["word"])
    for word in words:
        writer.writerow([word])

# Write cleaned TXT
with open(output_txt, "w", encoding="utf-8") as f:
    for word in words:
        f.write(word + "\n")

print(f"\n✅ Created cleaned files:")
print(f"   {output_csv}")
print(f"   {output_txt}")
print(f"\nTotal vocabulary words: {len(words)}")
