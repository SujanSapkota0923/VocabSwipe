#!/usr/bin/env python
"""
Split a large vocabulary file into smaller chunks for easier uploading
"""
import sys
import os


def split_vocab_file(input_file, words_per_file=500):
    """Split vocabulary file into smaller chunks"""

    # Read all words
    with open(input_file, "r", encoding="utf-8") as f:
        words = [line.strip() for line in f if line.strip()]

    total_words = len(words)
    num_files = (total_words + words_per_file - 1) // words_per_file

    print(f"Splitting {total_words} words into {num_files} files...")
    print(f"Each file will have ~{words_per_file} words")
    print()

    # Get base name
    base_name = os.path.splitext(input_file)[0]

    # Split into chunks
    for i in range(num_files):
        start_idx = i * words_per_file
        end_idx = min((i + 1) * words_per_file, total_words)
        chunk = words[start_idx:end_idx]

        output_file = f"{base_name}_part{i+1}_of_{num_files}.txt"

        with open(output_file, "w", encoding="utf-8") as f:
            for word in chunk:
                f.write(word + "\n")

        print(f"✅ Created: {output_file} ({len(chunk)} words)")

    print()
    print(f"Done! Created {num_files} files.")
    print(f"Upload time per file: ~{(words_per_file * 1.5) / 60:.1f} minutes")


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python split_vocab_file.py <input_file> [words_per_file]")
        print("\nExample:")
        print("  python split_vocab_file.py vocabulary.txt 500")
        sys.exit(1)

    input_file = sys.argv[1]
    words_per_file = int(sys.argv[2]) if len(sys.argv) >= 3 else 500

    split_vocab_file(input_file, words_per_file)
