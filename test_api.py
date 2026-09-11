#!/usr/bin/env python
"""
Test script to verify Dictionary API integration
"""
import os
import sys
import django

# Setup Django environment
sys.path.insert(0, "/Users/sujan/Desktop/Projects/VocabSwipe")
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings")
django.setup()

from vocab.utils.dictionary_api import DictionaryAPI

# Test words
test_words = ["ignore", "output", "bilingual", "chemical"]

print("=" * 60)
print("Testing Free Dictionary API Integration")
print("=" * 60)

for word in test_words:
    print(f"\n🔍 Fetching meanings for: '{word}'")
    meanings = DictionaryAPI.fetch_meanings(word, max_meanings=3)

    if meanings:
        print(f"✅ Found {len(meanings)} meaning(s):")
        for i, meaning in enumerate(meanings, 1):
            print(f"   {i}. {meaning}")
    else:
        print(f"❌ No meanings found")

print("\n" + "=" * 60)
print("Test completed!")
print("=" * 60)
